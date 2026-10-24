# Judging checklist

How Hallway answers each track criterion, and the on-stage proof for it.

## FalkorDB

- **Graph at the core:** Scout, Planner and Matchmaker share one FalkorDB graph. Matchmaking is a multi-hop traversal over talks, topics and people, and MET edges are memory across sessions. Proof: the who-to-meet answer shows its graph path on screen.
- **Explainable answers:** every suggestion renders the path behind it (person, topic, talk, speaker). The path is the reason, not a black box score.
- **Real problem, working demo:** attendees miss talks, talks move rooms, and the right people never meet. The demo runs live, step by step, as written in DEMO.md.

## Bright Data

- **Hard-to-get data at the core:** Scout fetches live schedule pages that are JS-heavy and bot-hostile, pages a plain script cannot reliably read. A fixture fallback covers fetch failures. Proof: a live refresh during the demo catches a room change.
- **Data quality:** fetched changes are diffed against the graph and reported as a change list (moved, added, removed), never silently overwritten.

## TrueForge

- **Built on TrueForge:** Scout, Planner and Matchmaker run as TrueForge agents (definitions in `trueforge/`), using MCP tools (`@falkordb/mcpserver` and `@brightdata/mcp` in `mcp/servers.json`) plus HTTP tools into the graph service. Fireworks GLM (`fireworks/glm-5p3-flash`) and OpenAI models do the reasoning, day briefing, and intro drafting (`agents/llm.py`).
- **Human approval:** introductions stop at a `requiresApproval` gate (`trueforge-approval-gate`), visible both in the TrueForge harness, the CLI runner, and directly on the board UI when clicking **Draft intro (approval gate)**. Nothing contacts a person without a human yes.

## Qodo

- **Qodo in use:** Qodo is installed on this repo and triggered across pull requests through the day. Work lands in small, single-purpose PRs with clear descriptions and test evidence:
  - PR #1 (`tree/trueforge-schema-pass`): TrueForge agent definitions and schema pass
  - PR #5 (`tree/expand-graph-smarts`): Richer seed data, talk explanations, icebreakers, full test suite
  - PR #6 (`tree/whimsical-ui`): Visual board UI, plan add/drop clash refusal, Scout changes feed
  - PR #7 (`tree/docs-demo-refresh`): README and DEMO stage script
  - PR #8 (`rene/scout-stale-edges`): Scout stale edge cleanup and feed-missing reconciliation
  - PR #9 (`rene/pin-requirements`): Pinned `requirements.txt` and `.python-version`
  - PR #10 (`tree/mcp-servers-fix`): Official `@falkordb/mcpserver` MCP wiring fix
  - PR #11 (`tree/llm-provider`): Multi-provider LLM layer (Fireworks GLM + OpenAI) with deterministic fallback
  - PR #12 (`rene/serp-query-encode`): URL-encoding fix for live Bright Data SERP queries
  - PR #13 (`rene/demo-env-fix`): Auto-load `.env` in `graph/seed.py` for fresh shells

## Bonus: Standalone Desktop App (`electron/`)

- **Zero-terminal experience for non-devs:** `Hallway.app` (`electron/`) wraps Docker Compose FalkorDB, Python virtualenv provisioning, graph seeding, and the FastAPI board server into a native macOS app with a friendly boot checklist and plain-English error recovery.

