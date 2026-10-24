"""LLM provider layer: one chat() that speaks to OpenAI or Fireworks.

Both providers expose the OpenAI-compatible chat completions shape, so the
only differences are the base URL, the API key env var and the default
model. Configuration is environment only:

- HALLWAY_LLM_PROVIDER: "fireworks" (default) or "openai". Fireworks is the
  default because it is the provider verified live for this project; the
  OpenAI account is blocked by a negative balance (see trueforge/README.md).
- FIREWORKS_API_KEY / OPENAI_API_KEY: the key for the chosen provider. The
  literal value "proxy" works with the local credential proxies
  (fw-proxy.py on 127.0.0.1:8791, same pattern as gh-proxy.py): the proxy
  attaches the real credential, so code never holds it.
- FIREWORKS_BASE_URL / OPENAI_BASE_URL: override the API root. Defaults are
  https://api.fireworks.ai/inference/v1 and https://api.openai.com/v1.
- HALLWAY_LLM_MODEL: override the model. Defaults are
  accounts/fireworks/models/glm-5p3-flash (fireworks) and gpt-4o (openai).

Nothing here is required for the demo. configured() is False without a key,
and chat() returns None on any failure, so callers fall back to their
deterministic text and the stage path never depends on a network call.
Response parsing reads choices[0].message.content only: some models also
return a reasoning_content field beside it, and that is never the answer.

Budget note: glm-5p3-flash is a reasoning model, and its reasoning tokens
count against max_tokens. A 160 token budget came back with content=None
and finish_reason=length in live testing (all 160 tokens spent on
reasoning); 400 plus finished cleanly. Keep call budgets generous (600)
for short texts on reasoning models.

Standard library only (urllib), so the layer adds no dependency.
"""

import json
import os
import urllib.request

PROVIDERS = {
    "fireworks": {
        "key_env": "FIREWORKS_API_KEY",
        "base_env": "FIREWORKS_BASE_URL",
        "default_base": "https://api.fireworks.ai/inference/v1",
        "default_model": "accounts/fireworks/models/glm-5p3-flash",
    },
    "openai": {
        "key_env": "OPENAI_API_KEY",
        "base_env": "OPENAI_BASE_URL",
        "default_base": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
    },
}

DEFAULT_PROVIDER = "fireworks"
TIMEOUT = 30


def provider_name(env=None):
    env = os.environ if env is None else env
    name = (env.get("HALLWAY_LLM_PROVIDER")
            or DEFAULT_PROVIDER).strip().lower()
    return name if name in PROVIDERS else DEFAULT_PROVIDER


def config(env=None):
    """The resolved provider config, or None when no key is set."""
    env = os.environ if env is None else env
    name = provider_name(env)
    spec = PROVIDERS[name]
    key = (env.get(spec["key_env"]) or "").strip()
    if not key:
        return None
    base = (env.get(spec["base_env"]) or spec["default_base"]).rstrip("/")
    model = (env.get("HALLWAY_LLM_MODEL") or spec["default_model"]).strip()
    return {"provider": name, "api_key": key, "base_url": base,
            "model": model}


def configured(env=None):
    return config(env) is not None


def describe(env=None):
    """A log-safe one-liner: provider, model, base URL. Never the key."""
    cfg = config(env)
    if cfg is None:
        return "no LLM provider configured (deterministic mode)"
    return f"{cfg['provider']} / {cfg['model']} via {cfg['base_url']}"


def build_payload(cfg, messages, max_tokens=300, temperature=0.7):
    return {"model": cfg["model"], "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature}


def parse_content(body):
    """The answer text from a chat completions body, or None.

    Reads choices[0].message.content only, never reasoning_content.
    """
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
    if isinstance(content, str) and content.strip():
        return content.strip()
    return None


def _post(url, payload, api_key, timeout):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def chat(messages, max_tokens=300, temperature=0.7, env=None, transport=None):
    """One chat completion. Returns the answer text, or None when the
    provider is not configured or the call fails for any reason.

    transport is injectable for tests: a callable with the same signature
    as _post that returns the decoded response body.
    """
    cfg = config(env)
    if cfg is None:
        return None
    payload = build_payload(cfg, messages, max_tokens=max_tokens,
                            temperature=temperature)
    post = transport if transport is not None else _post
    try:
        body = post(f"{cfg['base_url']}/chat/completions", payload,
                    cfg["api_key"], TIMEOUT)
    except Exception:
        return None
    return parse_content(body)
