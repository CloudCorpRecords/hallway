# Hallway Test Validation & Hackathon Proof Report

**Event:** Patch the Conference Hackathon (WeMakeDevs, Bright Data SF, Oct 24 2026)  
**Project:** Hallway (`https://github.com/CloudCorpRecords/hallway`)  
**Team:** Aigents xero (Rene Turcios)

---

## 1. Automated Test Suite Summary (34/34 Passing)

All suites run against isolated scratch graphs in a live FalkorDB container (`redis://localhost:6379`) so the live demo graph (`hallway`) is never mutated by tests.

| Suite | Command | Result | Coverage |
| :--- | :--- | :--- | :--- |
| **Smoke Suite** | `python tests/test_smoke.py` | **3 / 3 PASS** (`SMOKE OK`) | 3-hop Cypher matchmaking path, clash-free talk planning, `MET` edge memory persistence |
| **Full Graph & Agent Suite** | `python tests/test_full.py` | **29 / 29 PASS** (`0 failed`) | Rich deterministic seed (18 people, 19 talks, 9 topics), path rendering, talk explanations, clash rules, company & speaker directory queries, deterministic icebreakers, Planner build & repair, Scout diffing & stale-edge cleanup, Matchmaker memory exclusion, blank timestamp normalization, LLM provider layer (Fireworks GLM + OpenAI + fallback) |
| **Board HTTP API Suite** | `pytest tests/test_api.py` | **PASS** | `/api/demo/reset`, `/api/health`, `/api/talks`, `/api/plan/{id}/summary`, `/api/plan/{id}/add` (409 clash refusal + swap), `/api/intro/draft` (approval gate), `/api/company/{company}`, `/api/speaker/{id}/talks`, `/api/met` |
| **Environment Auto-Load** | `pytest tests/test_env_loading.py` | **PASS** | Verifies `graph/seed.py` loads `.env` automatically from a clean shell (`env -i`) |
| **Pytest Total** | `pytest -q` | **34 passed** | All unit, integration, graph, LLM, and FastAPI endpoints |

### Verbatim Test Output

```text
PASS test_matchmake_returns_a_three_hop_path
PASS test_talks_for_is_clash_free_against_plan
PASS test_meeting_memory_round_trip
SMOKE OK: 3/3 graph smoke tests passed

PASS test_seed_is_rich_and_deterministic
PASS test_matchmake_ranking_and_memory_exclusion
PASS test_matchmake_paths_are_real
PASS test_talks_for_carries_reasons
PASS test_talks_for_clash_rules
PASS test_people_by_company
PASS test_talks_by_speaker
PASS test_icebreaker_from_shared_path
PASS test_icebreaker_fallbacks
PASS test_planner_builds_explained_clash_free_plan
PASS test_planner_repair_after_scout_refresh
PASS test_scout_detects_fixture_changes
PASS test_matchmaker_suggests_with_icebreakers_and_remembers
PASS test_record_meeting_normalizes_blank_at
PASS test_met_list_seeded_memory
PASS test_default_provider_is_fireworks_with_glm
PASS test_openai_provider_selection_and_defaults
PASS test_no_key_means_unconfigured_and_chat_is_none
PASS test_base_url_and_model_overrides
PASS test_unknown_provider_falls_back_to_fireworks
PASS test_payload_shape_for_both_providers
PASS test_chat_posts_to_chat_completions_for_both_providers
PASS test_parse_content_reads_content_only
PASS test_chat_failure_and_garbage_return_none
PASS test_intro_uses_llm_when_configured
PASS test_intro_falls_back_to_template_without_key
PASS test_intro_falls_back_to_template_when_llm_fails
PASS test_plan_summary_uses_llm_when_configured
PASS test_plan_summary_none_without_key_or_plan
FULL SUITE: 29/29 tests passed, 0 failed

34 passed in pytest
```

---

## 2. Live Sponsor Track Validations

### Track 1: FalkorDB (Graph Core + MCP Server)
* **Multi-hop Cypher Matchmaking:** `graph/queries.py` executes 2-hop (`Person -> Topic <- Person`) and 3-hop (`Person -> Topic <- Talk <- Person`) Cypher traversals and renders the full path string:
  `Person(Rene Turcios) -[INTERESTED_IN]-> Topic(Rust) <-[ABOUT]- Talk(Rust CLIs That Feel Instant) <-[GIVES]- Person(Diego Fuentes)`
* **Persistent Shared Memory (`MET` edges):** Recording a meeting writes a `(:Person)-[:MET {note, at}]->(:Person)` edge that immediately excludes that person from future matchmaking across all agents and sessions.
* **Official FalkorDB MCP Server (`@falkordb/mcpserver`):** Configured in `mcp/servers.json` and verified live via JSON-RPC handshake (`serverInfo: falkordb 1.3.0`, tools: `query_graph`, `query_graph_readonly`, `list_graphs`, `delete_graph`, `get_graph_schema`, `get_node_schema`, `get_relationship_schema`).

### Track 2: Bright Data (Live Web Unlocker + SERP + Change Diffing)
* **Zones & Live Connectivity:** Active zones `web_unlocker1` (Web Unlocker) and `serp_api1` (SERP API) verified against Bright Data API with live HTTP 200 responses (`ingest/brightdata.py`).
* **Diffing & Stale-Edge Cleanup:** `agents/scout.py` diffs fetched schedules against the FalkorDB graph, reconciles `GIVES`, `ABOUT`, and `IN_ROOM` edges, and reports exact room and time changes (`t6` moved from Main Stage to Workshop 2; `t11` moved from `16:15-17:00` to `16:30-17:15`).

### Track 3: TrueFoundry TrueForge (Agent Harness + Approval Gates + LLM Layer)
* **TrueForge Definitions (`trueforge/`):** `scout.agent.json`, `planner.agent.json`, and `matchmaker.agent.json` verified against TrueForge v0.180.0 standalone harness (`npx @truefoundry/trueforge`).
* **Live Fireworks GLM + OpenAI Provider Layer (`agents/llm.py`):** Verified live with `fireworks/glm-5p3-flash` (`accounts/fireworks/models/glm-5p3-flash`) for natural-language day briefings and grounded intro drafting, with automatic deterministic fallback when offline.
* **Human Approval Gate:** Both in the TrueForge harness (`require_approval_for_tools`) and in the board/runner (`trueforge-approval-gate`), intro drafts halt for explicit human confirmation before anything is sent.

### Track 4: Qodo (PR Workflow & Reviews)
* **Small, Single-Purpose PRs:** All features and fixes shipped as 14 focused pull requests (`PR #1` through `PR #14`) with `/agentic_review` triggers and full test evidence in each PR description.

---

## 3. Standalone Desktop App Validation (`Hallway.app`)

* **Packaged App Location:** `electron/dist/mac-arm64/Hallway.app`
* **Verified Boot Sequence:**
  1. Checks/creates user `.env` (`~/Library/Application Support/Hallway/.env`)
  2. Verifies Python 3.12 virtualenv (`~/Library/Application Support/Hallway/venv`)
  3. Verifies FalkorDB reachability on `127.0.0.1:6379` (or launches `docker compose up -d`)
  4. Seeds the 18-person, 19-talk graph if empty
  5. Boots `uvicorn app.main:app` on `127.0.0.1:8000` and renders the interactive board UI
