# WeMakeDevs Submission Pack: Hallway

Copy and paste each section below directly into the submission form at `https://wemakedevs.org/hackathons/ptc/submit`.

> **Reminder:** Select **ALL FOUR tracks** (FalkorDB, Bright Data, TrueForge, Qodo) before submitting.

---

## 1. Project Title
**Hallway**

## 2. Tagline
**The conference concierge that shows its work: three agents sharing one FalkorDB graph to plan your day, catch schedule changes, and prove every person you should meet with the exact graph path.**

## 3. Repository URL
`https://github.com/CloudCorpRecords/hallway`

## 4. Demo Video File
* **Local MP4 ready to upload (YouTube / Loom / Google Drive / form upload):**
  `/tmp/hallway/submission/hallway-demo.mp4`

---

## 5. The Conference Problem It Patches
Conferences fail in the hallway, not on the stage. Schedules change mid-day. The person you most needed to meet was two rooms away and you never knew. Standard event apps store the conference as disconnected rows and your day as a static screenshot. Hallway stores the conference as what it actually is: a connected graph of people, talks, rooms, companies, and topics, with your own hallway meetings written back into the graph as shared memory.

---

## 6. What Was Built & How It Works
Hallway gives you three collaborating agents (**Scout**, **Planner**, and **Matchmaker**) sharing one **FalkorDB** graph, exposed through a warm, interactive one-page web board (`app/`) and a zero-setup standalone **macOS Electron desktop app** (`Hallway.app` in `electron/`):

1. **Scout (`agents/scout.py` + `ingest/brightdata.py`):** Pulls conference schedules via **Bright Data** (Web Unlocker API, SERP API, CLI, and MCP), diffs them against the graph, reconciles moved rooms or times (`IN_ROOM`, `GIVES`, `ABOUT` edges), and surfaces a live change banner on the board.
2. **Planner (`agents/planner.py`):** Builds a clash-free day from talks matching your interests (`INTERESTED_IN`), explains every pick, refuses double-bookings in plain English naming the clashing talk, repairs your plan when Scout detects schedule moves, and generates a natural-language day briefing via `agents/llm.py`.
3. **Matchmaker (`agents/matchmaker.py` + `graph/queries.py`):** Suggests who to meet using multi-hop Cypher traversals (`Person -> Topic <- Talk <- Person`), renders the 3-hop path on screen as an auditable breadcrumb trail, builds a deterministic icebreaker from the shared talk and topic, writes `MET` edges to the graph so people you already met are never suggested again, and drafts grounded intro messages that stop at a **TrueForge** human approval gate (`trueforge-approval-gate`) before anything is sent.

---

## 7. Track Details (Select All 4 Tracks)

### Track 1: FalkorDB
FalkorDB is the reasoning core and shared memory of Hallway, not passive storage. Matchmaking runs 2-hop (`me -> Topic <- other`) and 3-hop (`me -> Topic <- Talk <- speaker`) Cypher path queries in `graph/queries.py` and returns the full `Path` object so the UI renders the exact chain (`Person(Rene Turcios) -[INTERESTED_IN]-> Topic(Rust) <-[ABOUT]- Talk(Rust CLIs That Feel Instant) <-[GIVES]- Person(Diego Fuentes)`). `PLANNED` edges store clash-free schedule state, and `MET` edges persist hallway meetings across sessions so once you click **We met in the hallway**, that person moves to the met panel and is excluded from future Cypher matchmaking. We also wired and verified the official `@falkordb/mcpserver` (`mcp/servers.json`) against our live graph (`18` Person nodes, `19` Talk nodes, `9` Topic nodes).

### Track 2: Bright Data
Conference sites are JavaScript-heavy and bot-hostile, and schedules change mid-day. Scout (`ingest/brightdata.py` and `agents/scout.py`) integrates Bright Data across three doors: the REST API (`web_unlocker1` Web Unlocker zone and `serp_api1` SERP zone, both created and verified live at the venue), the Bright Data CLI (`@brightdata/cli`), and the Bright Data MCP server (`@brightdata/mcp` in `mcp/servers.json`). During live venue testing against GitHub Universe, Web Unlocker fetched the live Next.js pages and we fixed a URL-encoding bug in SERP queries (`PR #12`). When live conference catalogs sit behind attendee-login portals or offline networks, the adapter falls back cleanly to bundled schedule fixtures so Scout's diffing (`t6` room move to Workshop 2 and `t11` time shift to `16:30`) is always demonstrable on stage.

### Track 3: TrueForge
Hallway's three agents are defined as TrueForge agent specifications in `trueforge/` (`scout.agent.json`, `planner.agent.json`, `matchmaker.agent.json`) and verified live against TrueForge (`npx @truefoundry/trueforge`, v0.180.0) bridged to `@falkordb/mcpserver`. Our LLM provider layer (`agents/llm.py`, `PR #11`) supports both Fireworks GLM (`fireworks/glm-5p3-flash`) and OpenAI (`gpt-4o`), powering Planner's natural-language day briefing and Matchmaker's grounded intro drafts, while falling back to deterministic templates if no key is present. Most importantly, Matchmaker's `send_intro` action is gated by human approval (`requiresApproval: true` / `trueforge-approval-gate`), proven both inside the live TrueForge harness (`tool.approval_required` events holding execution until human allow) and directly on the board UI.

### Track 4: Qodo
Hallway was built from commit one through small, single-purpose pull requests with automated test verification (`3/3` smoke tests, `29/29` full suite tests, `34/34` pytest tests) and `/agentic_review` triggers on our PRs:
- `https://github.com/CloudCorpRecords/hallway/pull/1` (TrueForge agent definitions & schema pass)
- `https://github.com/CloudCorpRecords/hallway/pull/5` (Expanded graph seed, talk explanations, icebreakers, full test suite)
- `https://github.com/CloudCorpRecords/hallway/pull/6` (Visual board UI, plan add/drop clash refusal, Scout changes feed)
- `https://github.com/CloudCorpRecords/hallway/pull/7` (README and DEMO stage script)
- `https://github.com/CloudCorpRecords/hallway/pull/8` (Scout stale edge cleanup and feed-missing reconciliation)
- `https://github.com/CloudCorpRecords/hallway/pull/9` (Pinned `requirements.txt` and `.python-version`)
- `https://github.com/CloudCorpRecords/hallway/pull/10` (Official `@falkordb/mcpserver` MCP wiring fix)
- `https://github.com/CloudCorpRecords/hallway/pull/11` (Multi-provider LLM layer with deterministic fallback)
- `https://github.com/CloudCorpRecords/hallway/pull/12` (Bright Data SERP query URL-encoding fix)
- `https://github.com/CloudCorpRecords/hallway/pull/13` (Auto-load `.env` in `graph/seed.py` for fresh shells)
- `https://github.com/CloudCorpRecords/hallway/pull/14` (Standalone Electron desktop app, interactive board actions, API test suite, and docs)
