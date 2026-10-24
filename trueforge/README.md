# TrueForge agent definitions

TrueForge (TrueFoundry's agent harness) is TypeScript first, has a built in
Chat UI, and starts with one command, nothing to clone:

    npx @truefoundry/trueforge

Docs: trueforge.dev/quickstart, trueforge.dev/create-agent/overview,
trueforge.dev/mcp-servers, and OpenAI as a standard provider:
trueforge.dev/models (Configuring a standard provider). The venue OpenAI key
lives at platform.openai.com/api-keys.

## The structure choice

Hallway is split at the harness boundary:

- **Agent layer (here):** three agent.json definitions, Scout, Planner and
  Matchmaker, adapted from the TrueForge agent cookbook examples
  (github.com/truefoundry/trueforge, examples/agent-cookbook/examples).
  They carry the prompts, the model choice (OpenAI), the tool lists and,
  for Matchmaker's send_intro tool, the human approval requirement.
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
