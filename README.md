# Hallway

**The conference concierge that shows its work.**

Every conference app gives you a schedule and a list of strangers. Hallway
gives you a team of agents that share one memory: a graph of every talk,
speaker, topic, room and attendee. You say what you are interested in. Hallway
plans your day, tells you who to meet, and proves each suggestion by showing
the exact path through the graph that produced it. When you meet someone, it
remembers, and never suggests them again.

Built at Patch the Conference (WeMakeDevs, Bright Data SF, October 24 2026),
for the problem every attendee at GitHub Universe has next week.

## The problem it patches

Conferences fail in the hallway, not on the stage. Schedules change mid day.
The person you most needed to meet was two rooms away and you never knew.
Apps store the conference as rows and your day as a screenshot. Hallway stores
the conference as what it actually is: a connected graph of people, talks and
topics, with your own meetings written back into it as memory.

## How it works

Three agents, one FalkorDB graph (schema in `graph/schema.md`):

- **Scout** keeps the conference data fresh. Talks move rooms and times;
  Scout re-fetches the schedule and upserts it, reporting every change.
- **Planner** builds your day from talks that match your interests and never
  double-books you, checking each pick against your planned talks. When
  Scout reports a change, Planner repairs the plan and says what it cost.
- **Matchmaker** suggests who to meet. Every suggestion carries its graph
  path as the reason: you, to a topic, to a talk, to the person speaking on
  it. Three hops, on screen, auditable. It reads the graph's MET edges so it
  never suggests someone you already met, and its intro drafts stop at a
  human approval gate before anything is sent.

The money queries live in `graph/queries.py`. Matchmaking returns the nodes
and the path, not just an answer, because an answer you cannot trace is a
rumor.

## Architecture: where the harness ends and the graph begins

TrueForge is TypeScript first, so Hallway is split at the harness boundary:

- **Agent layer:** `trueforge/` holds the three agents as agent.json
  definitions (adapted from the TrueForge agent cookbook), launched with
  `npx @truefoundry/trueforge`, using its Chat UI, MCP tools, sandbox and
  human approvals.
- **Graph service:** the Python code in this repo. FalkorDB, the money
  queries, and a small HTTP API (`app/main.py`) that the agents call as
  tools, plus the FalkorDB MCP server as the preferred agent facing path
  (see `mcp/`). The Python agents in `agents/` run the same loop
  deterministically with no harness at all: that fallback is what the
  smoke tests prove, and it is the stage safety net.

## How each sponsor product is used

- **FalkorDB (Track 1)** is the core, not the storage. Multi-hop Cypher
  traversals do the matchmaking (Person to Topic to Talk to Person), MET
  edges are memory that survives across sessions and is shared by all three
  agents, PLANNED edges are shared schedule state, and every answer returns
  its path for explainability. Runs as one Docker container, or as the
  official FalkorDB module in a stock redis-server. For the agents, the
  graph is preferably exposed through FalkorDB's own MCP server
  (docs.falkordb.com/genai-tools/mcpserver/quickstart), with the Python
  client path kept as the tested fallback.
- **Bright Data (Track 2)** is the live data layer. Account entry:
  brightdata.com/cp/start (the venue credit code is redeemed there, see
  BUILD-PLAN.md; it is the only code on any hackathon page). Scout fetches
  the schedule through the Web Unlocker API and enriches speakers through
  the SERP API (`ingest/brightdata.py`), because conference sites are
  JavaScript heavy and hostile to plain scrapers. Two more doors to the
  same account: the Bright Data CLI (`npx -p @brightdata/cli bdata login`,
  then `bdata scrape <url>` and `bdata search "..."`; Scout uses it when
  BRIGHTDATA_MODE=cli) and the Bright Data MCP server (config in `mcp/`
  and `ingest/brightdata.py`), which is how the agent layer calls it.
  With no API key configured, the adapter serves bundled fixtures so the
  whole system still runs.
- **TrueFoundry TrueForge with OpenAI (Track 3)** is the agent harness.
  It starts with one command, nothing to clone:
  `npx @truefoundry/trueforge`. The agents in `trueforge/` run on OpenAI
  models configured as a standard provider (trueforge.dev/models), with
  the venue $50 credit key from platform.openai.com/api-keys, the Bright
  Data and FalkorDB MCP servers as tools, the sandbox for messy schedule
  parsing, and TrueForge human approvals as the gate in front of
  Matchmaker's intros. OpenAI also powers the optional natural language
  briefing in the runner. Without the harness or a key, the runner falls
  back to the local loop and then to a fully deterministic no-LLM mode:
  the demo never hard-depends on a service.
- **Qodo (Track 4)** reviews every pull request. The repo ships in small,
  single-purpose PRs from the first commit, Qodo reviews each one
  (install: docs.qodo.ai/install-qodo/github/qodo-multi-tenant; a manual
  review is triggered by commenting /agentic_review on a PR), and its
  findings get fixed in follow-up PRs. The PR links go in the submission.

## Quickstart

```bash
# 1. Graph database ( pick one )
docker compose up -d                                   # FalkorDB on 6379 + browser on 3000
# or, no Docker: redis-server --loadmodule falkordb-x64.so --port 6379

# 2. Python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 3. Seed the sample conference and run the agents
python -m graph.seed
python -m agents.runner --person rene --noninteractive

# 4. Web app
uvicorn app.main:app --port 8000    # http://localhost:8000

# 5. Smoke tests (need FalkorDB running)
python tests/test_smoke.py
```

## Status of this scaffold

Real and tested (against a live FalkorDB 6.0.3 module in redis-server
7.4.2, smoke suite 3/3): the graph layer (schema, seed, the four money
queries with path rendering), Scout's change detection, Planner's clash
free planning and repair, Matchmaker's drafting and approval adapter, the
FastAPI app and page, and the deterministic runner end to end.
Structured and documented, waiting on venue accounts: the TrueForge
agent.json definitions in `trueforge/`, the MCP server configs in `mcp/`,
Bright Data live keys (fixtures stand in), OpenAI credits, the GitHub
repo and the Qodo app. BUILD-PLAN.md is the runbook that flips each one
live. DEMO.md is the stage script.
