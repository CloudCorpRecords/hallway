# Mac session status

Owner: the Mac session (Muse on Rene's Mac, "Hallway Agents Review"). Only the Mac session edits this file.
Seeded by Tree on 2026-10-24 ~11:24 AM PT from the COORDINATION.md board, so both status files exist from the start. The Mac session maintains it from here; Tree will not edit it again.

## Now (as last reported on the board)

- DONE: PR #8 (rene/scout-stale-edges) merged. Scout stale edge cleanup: _upsert_talk reconciles GIVES and ABOUT edges, refresh reports feed-missing talks as kept, seen-in-feed tracking so seed-only talks stay quiet.
- DONE: PR #9 (rene/pin-requirements) merged. requirements.txt pinned, .python-version added (3.12).
- Board entry 2026-10-24 ~11:16 AM PT: main green after the merges (smoke 3/3, full 15/15, runner end to end clean). Demo graph reseeded after the scout work.

## Lanes (Mac session)

agents/scout.py, ingest/, requirements.txt, .python-version.

## Claims

Task: brightdata-key-wireup
Owner: Mac session
Branch: main (no code edits; .env is gitignored, coordination files only)
Areas: .env (local only, never committed), ingest/ (read-only diagnosis)
Status: READY
Started: 2026-10-24 ~11:55 AM PT
Finished: 2026-10-24 ~12:00 PM PT

Job: Rene handed over a live Bright Data API key after Tree's signup stalled. Store it gitignored-only and prove the smallest live call.

Evidence:
- Key stored in /tmp/hallway/.env as BRIGHTDATA_API_KEY; git status clean, .env check-ignored.
- Key is valid (authenticated responses, not auth errors). One minimal SERP call and one minimal Web Unlocker call each returned HTTP 400 zone not found for the default names serp_api1 and web_unlocker1. No repo code changed; the adapter already falls back to fixtures, so the demo is unaffected.
- BLOCKED on zone names: the account has no zones called web_unlocker1 or serp_api1. Rene either creates zones with exactly those names in the Bright Data dashboard or sends the real zone names and the Mac session drops them into .env (BRIGHTDATA_ZONE_WEB_UNLOCKER, BRIGHTDATA_ZONE_SERP). Still also needs the real SCHEDULE_URL before Scout can refresh live.

## Claims

Task: post-merge-reverify
Owner: Mac session
Branch: main (verification only, no code edits; coordination files only)
Areas: none (read-only suite run plus coordination/ appends)
Status: WIP
Started: 2026-10-24 ~11:40 AM PT

Job: re-run smoke plus full suite on current main (1e60f5b, post PR #10) against the local FalkorDB, and independently corroborate the FalkorDB MCP server entry (handshake plus one read-only query) from this Mac. Kit received and Tree READY confirmed via coordination/tree-status.md and handoffs.md entries of ~11:24 and ~11:33 AM PT.

## Results

Task: post-merge-reverify
Owner: Mac session
Status: READY
Finished: 2026-10-24 ~11:45 AM PT

Evidence:
- Suites on current main against local FalkorDB (docker compose, colima): "SMOKE OK: 3/3 graph smoke tests passed" and "FULL SUITE: 15/15 tests passed, 0 failed".
- MCP handshake with the merged mcp/servers.json FalkorDB entry (npx -y @falkordb/mcpserver@latest, FALKORDB_HOST=localhost, FALKORDB_PORT=6379): serverInfo name "falkordb", version "1.3.0"; tools/list = query_graph, query_graph_readonly, list_graphs, delete_graph, get_graph_schema, get_node_schema, get_relationship_schema.
- tools/call query_graph_readonly on graph hallway, MATCH (p:Person) RETURN count(p) AS people: people = 18.

Matches Tree's wiring evidence row for row. TrueForge can use the checked-in entry as-is; no fallback command needed now that PR #10 is merged.

## How to update this file

Follow coordination/PROTOCOL.md: keep the claim format, use the status vocabulary, and never mark READY or DONE without the verbatim test result or a link to it.
