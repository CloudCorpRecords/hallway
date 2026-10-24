"""Unit tests for the LLM provider layer (agents/llm.py) and its two
call sites (Matchmaker intro draft, Planner plan summary).

No network and no graph: the transport is a fake that records the request
and returns a canned body, so provider selection, payload shape, response
parsing and the deterministic fallbacks are all pinned down offline. The
live path has its own script: tests/live_llm_check.py.

    python tests/test_llm.py     # standalone, PASS/FAIL per test + summary
    pytest tests/test_llm.py     # same assertions under pytest
"""

import contextlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents import llm, matchmaker, planner  # noqa: E402

LLM_ENV_KEYS = ("HALLWAY_LLM_PROVIDER", "HALLWAY_LLM_MODEL",
                "FIREWORKS_API_KEY", "FIREWORKS_BASE_URL",
                "OPENAI_API_KEY", "OPENAI_BASE_URL")

GLM = "accounts/fireworks/models/glm-5p3-flash"
MESSAGES = [{"role": "user", "content": "Say hello."}]

MATCH = {
    "person_id": "diego-fuentes",
    "name": "Diego Fuentes",
    "company": "Independent",
    "speaking_on": ["From Prototype to Production Agents"],
    "shared_topics": ["Rust", "Developer Tools"],
    "icebreaker": {"line": "Ask Diego about Rust CLIs."},
}

PLAN = [
    {"id": "t1", "title": "MCP in Production", "starts": "09:30",
     "ends": "10:15", "room": "Main Stage",
     "why": "matches your interest in MCP"},
    {"id": "t3", "title": "Agents That Remember", "starts": "10:30",
     "ends": "11:15", "room": "Main Stage",
     "why": "matches your interest in AI Agents"},
]


@contextlib.contextmanager
def llm_env(**values):
    """Run with only the given LLM env vars set; restore afterwards."""
    saved = {k: os.environ.get(k) for k in LLM_ENV_KEYS}
    for k in LLM_ENV_KEYS:
        os.environ.pop(k, None)
    os.environ.update(values)
    try:
        yield
    finally:
        for k in LLM_ENV_KEYS:
            if saved[k] is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = saved[k]


class FakeTransport:
    """Stands in for agents.llm._post. Records calls, returns a canned
    decoded body or raises a canned error."""

    def __init__(self, body=None, error=None):
        self.body = body
        self.error = error
        self.calls = []

    def __call__(self, url, payload, api_key, timeout):
        self.calls.append({"url": url, "payload": payload,
                           "api_key": api_key, "timeout": timeout})
        if self.error is not None:
            raise self.error
        return self.body


def ok_body(text):
    return {"choices": [{"message": {"content": text}}]}


@contextlib.contextmanager
def patched_transport(fake):
    original = llm._post
    llm._post = fake
    try:
        yield fake
    finally:
        llm._post = original


# ---------- provider selection and config ----------

def test_default_provider_is_fireworks_with_glm():
    with llm_env(FIREWORKS_API_KEY="test-key"):
        cfg = llm.config()
        assert cfg["provider"] == "fireworks", cfg
        assert cfg["model"] == GLM, cfg
        assert cfg["base_url"] == "https://api.fireworks.ai/inference/v1", cfg
        assert llm.configured()


def test_openai_provider_selection_and_defaults():
    with llm_env(HALLWAY_LLM_PROVIDER="openai", OPENAI_API_KEY="test-key"):
        cfg = llm.config()
        assert cfg["provider"] == "openai", cfg
        assert cfg["model"] == "gpt-4o", cfg
        assert cfg["base_url"] == "https://api.openai.com/v1", cfg


def test_no_key_means_unconfigured_and_chat_is_none():
    with llm_env():
        assert llm.config() is None
        assert not llm.configured()
        fake = FakeTransport(body=ok_body("unreachable"))
        assert llm.chat(MESSAGES, transport=fake) is None
        assert fake.calls == [], "no key must mean no call"


def test_base_url_and_model_overrides():
    with llm_env(FIREWORKS_API_KEY="proxy",
                 FIREWORKS_BASE_URL="http://127.0.0.1:8791/inference/v1/",
                 HALLWAY_LLM_MODEL="accounts/fireworks/models/other"):
        cfg = llm.config()
        assert cfg["base_url"] == "http://127.0.0.1:8791/inference/v1", cfg
        assert cfg["model"] == "accounts/fireworks/models/other", cfg


def test_unknown_provider_falls_back_to_fireworks():
    with llm_env(HALLWAY_LLM_PROVIDER="bogus", FIREWORKS_API_KEY="k"):
        assert llm.provider_name() == "fireworks"
        assert llm.config()["provider"] == "fireworks"


# ---------- payload and parsing ----------

def test_payload_shape_for_both_providers():
    for provider, key_env, model in (
            ("fireworks", "FIREWORKS_API_KEY", GLM),
            ("openai", "OPENAI_API_KEY", "gpt-4o")):
        with llm_env(HALLWAY_LLM_PROVIDER=provider, **{key_env: "k"}):
            payload = llm.build_payload(llm.config(), MESSAGES,
                                        max_tokens=99)
            assert payload["model"] == model, payload
            assert payload["messages"] == MESSAGES, payload
            assert payload["max_tokens"] == 99, payload
            assert "temperature" in payload, payload


def test_chat_posts_to_chat_completions_for_both_providers():
    for provider, key_env, base, model in (
            ("fireworks", "FIREWORKS_API_KEY",
             "https://api.fireworks.ai/inference/v1", GLM),
            ("openai", "OPENAI_API_KEY",
             "https://api.openai.com/v1", "gpt-4o")):
        with llm_env(HALLWAY_LLM_PROVIDER=provider, **{key_env: "sekret"}):
            fake = FakeTransport(body=ok_body(f"answer from {provider}"))
            out = llm.chat(MESSAGES, transport=fake)
            assert out == f"answer from {provider}", out
            (call,) = fake.calls
            assert call["url"] == f"{base}/chat/completions", call
            assert call["payload"]["model"] == model, call
            assert call["api_key"] == "sekret", call


def test_parse_content_reads_content_only():
    body = {"choices": [{"message": {
        "content": "the answer", "reasoning_content": "long thinking"}}]}
    assert llm.parse_content(body) == "the answer"
    only_reasoning = {"choices": [{"message": {
        "reasoning_content": "thinking only"}}]}
    assert llm.parse_content(only_reasoning) is None, \
        "reasoning_content must never be read as the answer"
    assert llm.parse_content({"choices": [{"message": {"content": "  "}}]}) \
        is None
    assert llm.parse_content({"choices": []}) is None
    assert llm.parse_content({}) is None
    assert llm.parse_content(None) is None


def test_chat_failure_and_garbage_return_none():
    with llm_env(FIREWORKS_API_KEY="k"):
        boom = FakeTransport(error=RuntimeError("network down"))
        assert llm.chat(MESSAGES, transport=boom) is None
        garbage = FakeTransport(body={"unexpected": True})
        assert llm.chat(MESSAGES, transport=garbage) is None


# ---------- matchmaker intro draft ----------

def test_intro_uses_llm_when_configured():
    with llm_env(FIREWORKS_API_KEY="k"):
        fake = FakeTransport(body=ok_body("LLM DRAFT: hi Diego."))
        with patched_transport(fake):
            text, source = matchmaker.intro_draft_with_source(
                "Rene Turcios", MATCH)
        assert text == "LLM DRAFT: hi Diego.", text
        assert source == f"llm:fireworks:{GLM}", source
        (call,) = fake.calls
        prompt = call["payload"]["messages"][-1]["content"]
        assert "Diego Fuentes" in prompt, prompt
        assert "From Prototype to Production Agents" in prompt, prompt


def test_intro_falls_back_to_template_without_key():
    with llm_env():
        text, source = matchmaker.intro_draft_with_source(
            "Rene Turcios", MATCH)
        assert source == "template", source
        assert text == matchmaker._template_intro("Rene Turcios", MATCH)
        assert text.startswith("Hi Diego,"), text
        assert "quick hallway chat" in text, text


def test_intro_falls_back_to_template_when_llm_fails():
    with llm_env(FIREWORKS_API_KEY="k"):
        fake = FakeTransport(error=RuntimeError("provider 500"))
        with patched_transport(fake):
            text, source = matchmaker.intro_draft_with_source(
                "Rene Turcios", MATCH)
        assert source == "template", source
        assert text == matchmaker._template_intro("Rene Turcios", MATCH)


# ---------- planner summary ----------

def test_plan_summary_uses_llm_when_configured():
    with llm_env(FIREWORKS_API_KEY="k"):
        fake = FakeTransport(body=ok_body("Your day is MCP heavy."))
        with patched_transport(fake):
            out = planner.plan_summary("Rene Turcios", PLAN)
        assert out == "Your day is MCP heavy.", out
        sent = fake.calls[0]["payload"]["messages"][-1]["content"]
        assert "MCP in Production" in sent, sent


def test_plan_summary_none_without_key_or_plan():
    with llm_env():
        assert planner.plan_summary("Rene Turcios", PLAN) is None
    with llm_env(FIREWORKS_API_KEY="k"):
        assert planner.plan_summary("Rene Turcios", []) is None
        fake = FakeTransport(error=RuntimeError("down"))
        with patched_transport(fake):
            assert planner.plan_summary("Rene Turcios", PLAN) is None


TESTS = [
    test_default_provider_is_fireworks_with_glm,
    test_openai_provider_selection_and_defaults,
    test_no_key_means_unconfigured_and_chat_is_none,
    test_base_url_and_model_overrides,
    test_unknown_provider_falls_back_to_fireworks,
    test_payload_shape_for_both_providers,
    test_chat_posts_to_chat_completions_for_both_providers,
    test_parse_content_reads_content_only,
    test_chat_failure_and_garbage_return_none,
    test_intro_uses_llm_when_configured,
    test_intro_falls_back_to_template_without_key,
    test_intro_falls_back_to_template_when_llm_fails,
    test_plan_summary_uses_llm_when_configured,
    test_plan_summary_none_without_key_or_plan,
]


def main():
    passed, failed = 0, []
    for test in TESTS:
        try:
            test()
            passed += 1
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failed.append(test.__name__)
            print(f"FAIL {test.__name__}: {exc}")
    print(f"LLM SUITE: {passed}/{len(TESTS)} tests passed, "
          f"{len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
