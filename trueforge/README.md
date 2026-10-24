# TrueForge agent definitions

TrueForge (TrueFoundry's agent harness) is TypeScript first, has a built in
Chat UI, and starts with one command, nothing to clone:

    npx @truefoundry/trueforge

Docs: trueforge.dev/quickstart, trueforge.dev/create-agent/overview,
trueforge.dev/mcp-servers, and models as providers:
trueforge.dev/models (Configuring a standard provider). The agents are
defined on Fireworks GLM (see Provider switching below for why, and for
how to switch them to OpenAI).

## The structure choice

Hallway is split at the harness boundary:

- **Agent layer (here):** three agent.json definitions, Scout, Planner and
  Matchmaker, adapted from the TrueForge agent cookbook examples
  (github.com/truefoundry/trueforge, examples/agent-cookbook/examples).
  They carry the prompts, the model choice (Fireworks GLM by default, see
  Provider switching below), the tool lists and, for Matchmaker's
  send_intro tool, the human approval requirement.
- **Graph service (Python, this repo):** FalkorDB plus the deterministic
  money queries. The agents reach it two ways: as tools over the small HTTP
  API in app/main.py, and through the FalkorDB MCP server (see ../mcp).
  The sandbox in TrueForge is the right home for messy schedule parsing at
  the venue.
- **Fallback (Python agents/):** the same three agents as a deterministic
  local loop. It is what the smoke tests exercise, and it is the stage
  safety net if the harness or the network misbehaves.

Field names in these agent.json files follow the cookbook examples as read
from the hackathon Resources page. Reconcile them against
trueforge.dev/create-agent/overview during the 10:00 workshop before first
launch; that is a venue step in BUILD-PLAN.md, not a code change.

## Provider switching: OpenAI or Fireworks

The three agent.json files name the model in the documented
provider/model form: `fireworks/glm-5p3-flash`. That is GLM 5.3 Flash on
Fireworks, the model the Python provider layer (agents/llm.py) is
live-verified against. One honesty flag: TrueForge's own docs, as read on
2026-10-24, document the provider/model form generically and do not spell
out Fireworks' exact provider string. If the harness wants a different
form for Fireworks, treat that as a one-line fix in each agent.json and
log what the harness accepted in coordination/handoffs.md.

To run the agents on OpenAI instead, change the model name in each
agent.json to `openai/gpt-4o` and configure the OpenAI provider key in the
harness (platform.openai.com/api-keys).

The Python side switches the same way, by environment (agents/llm.py):

    HALLWAY_LLM_PROVIDER=fireworks   # default; or openai
    FIREWORKS_API_KEY=...            # key for the fireworks provider
    OPENAI_API_KEY=...               # key for the openai provider
    FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1   # default
    OPENAI_BASE_URL=https://api.openai.com/v1                  # default
    HALLWAY_LLM_MODEL=accounts/fireworks/models/glm-5p3-flash  # default
                          # on fireworks; gpt-4o on openai

A key value of `proxy` works with the local credential proxies
(fw-proxy.py on 127.0.0.1:8791 for Fireworks, the same pattern as
gh-proxy.py for GitHub): the proxy attaches the real credential, so the
agents run with a live key that never sits in an env file. With no key
set, the Python agents skip the LLM entirely and use their deterministic
text; nothing about the demo depends on a provider answering.

Honest status, 2026-10-24: the OpenAI path is coded and covered by mocked
tests, but it is not live-verified. Rene claimed the venue OpenAI credit
and then found his OpenAI account balance is negative, so OpenAI API calls
are refused until that is settled with OpenAI. Fireworks is the live
default for both the harness definitions and the Python layer; its GLM
path is verified against the real API (see tests/live_llm_check.py).
