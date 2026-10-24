# Handoff log

Append-only. Either agent may append its own entries; never edit or delete earlier entries. Format per coordination/PROTOCOL.md:

```
## <date time>, <from> -> <to>: <task id>
Done: <what was done, plainly>
Evidence: <verbatim test result, PR link, or commit sha>
Next: <what happens now>
Owner now: Tree | Mac session | Rene
```

## 2026-10-24 ~11:24 AM PT, Tree -> Mac session: coordination-kit

Done: created the coordination/ folder (PROTOCOL.md, tree-status.md, mac-status.md, handoffs.md) and pointed the board at it. Both lanes are merged on main: Tree PRs #1, #5, #6, #7 and Mac session PRs #8, #9. Tree claimed the FalkorDB MCP wiring test from the board's free list and is running it now against current main (full suite, smoke, runner, then a real MCP handshake and Cypher queries through the FalkorDB MCP server, plus a keyless load check of the Bright Data MCP entry).
Evidence: COORDINATION.md board and work log through 2026-10-24 ~11:16 AM PT; this folder lands on main in the same commit as this entry.
Next: Tree posts the MCP results here and marks tree-status.md READY; Rene relays the word.
Owner now: Tree (MCP test), Rene (venue steps).

## 2026-10-24 ~11:33 AM PT, Tree -> Mac session: mcp-wiring-test

Done: re-verified current main from a fresh clone (suites, runner) and tested both MCP server entries for real. Found one real bug: mcp/servers.json declared the FalkorDB server as `uvx falkordb-mcp`, a package that does not exist on PyPI or npm. The official server is the npm package @falkordb/mcpserver; Tree ran it against the local FalkorDB and completed a full MCP handshake plus read-only Cypher queries through it. The fix is PR #10 (tree/mcp-servers-fix), one file, left open for Rene to merge. Until it merges, use `npx -y @falkordb/mcpserver@latest` with FALKORDB_HOST=localhost and FALKORDB_PORT=6379 directly. The Bright Data entry is correct as declared (package resolves at 4.1.0; keyless start fails cleanly asking for API_TOKEN, which is Rene's venue step).
Evidence: "FULL SUITE: 15/15 tests passed, 0 failed"; "SMOKE OK: 3/3 graph smoke tests passed"; MCP tools/list = query_graph, query_graph_readonly, list_graphs, delete_graph, get_graph_schema, get_node_schema, get_relationship_schema; query_graph_readonly count of Person nodes in graph hallway = 18; matchmake pattern for rene returned 10 rows (Marcus Webb and Maya Chen on MCP among them); PR https://github.com/CloudCorpRecords/hallway/pull/10.
Next: Rene merges PR #10 and does the venue steps. Mac session can treat the MCP wiring as proven and build on it. Tree is READY (see coordination/tree-status.md).
Owner now: Rene (PR #10, venue steps), Mac session (build on the wiring).

## 2026-10-24 ~11:45 AM PT, Mac session -> Tree: post-merge-reverify
Done: re-ran both suites on current main (1e60f5b, PR #10 merged) against the local FalkorDB, all green; independently re-ran the FalkorDB MCP entry from mcp/servers.json (handshake, tool list, one read-only count query), everything matches Tree's wiring evidence.
Evidence: "SMOKE OK: 3/3 graph smoke tests passed"; "FULL SUITE: 15/15 tests passed, 0 failed"; serverInfo falkordb 1.3.0 with the same 7 tools; people = 18 via query_graph_readonly.
Next: venue steps stay Rene's (Bright Data key, OpenAI credits, TrueForge run, real schedule URL, video, submission). Code and wiring are proven on two machines now.
Owner now: Rene (venue steps).

## 2026-10-24 ~11:40 AM PT, Tree -> Mac session: submission-pack-and-trueforge-run
Done: Tree wrote the WeMakeDevs submission pack and left it on Tree's machine at ~/workspace/hackathons/hallway-submission-pack.md. It holds paste-ready text for every field of the submission form: title, tagline, the problem, the build description, the Part 2 per-track paragraphs (including the verified PR link list for Qodo), and the Part 3 sponsor feedback. The pack is not in the repo, so when Rene fills the form he should ask Tree for any field text. Sponsor wiring status on Tree's side: the Bright Data signup (brightdata.com/cp/start, code patch50, zones created, API key into .env) and the Qodo enable (sign in to Qodo, turn on review for this repo) are in progress. The TrueForge venue run sequence for this Mac is at the bottom of this entry and uses only commands the repo documents.
Evidence: pack file written 2026-10-24 on Tree's machine; PR states for the pack's Qodo section re-verified through the API in this pass (PRs #1, #5, #6, #7, #8, #9, #10: state closed, merge check HTTP 204 for each one, so all seven are merged); mcp/servers.json on main names @falkordb/mcpserver after PR #10.
Next: Mac session runs the TrueForge sequence below when Rene says go. Rene submits with all four tracks selected; the team locks at submission.
Owner now: Mac session (TrueForge run), Rene (submission), Tree (Bright Data signup, Qodo enable).

TrueForge venue run sequence (Mac session):
1. Pull the latest main into the clone.
2. FalkorDB: already running on this Mac via colima, per coordination/mac-status.md. If it is ever down, the README Quickstart command is: docker compose up -d
3. Python environment, from the README Quickstart (skip if the venv from the PR #9 pass already exists): python3 -m venv .venv && source .venv/bin/activate, then pip install -r requirements.txt, then cp .env.example .env. Put the venue OpenAI key into .env and into TrueForge once Rene has claimed the $50 credits (key from platform.openai.com/api-keys).
4. Seed the graph: python -m graph.seed
5. Start the graph service the agents call as an HTTP tool: uvicorn app.main:app --port 8000
6. Start the harness: npx @truefoundry/trueforge
7. In the harness, load the three agent definitions from trueforge/ (scout.agent.json, planner.agent.json, matchmaker.agent.json) and confirm the OpenAI provider key is set. The repo documents the definition files and the start command; loading them is harness UI, so no repo command is quoted for this step.
8. Confirm mcp/servers.json resolves the FalkorDB MCP server: the falkordb entry runs npx -y @falkordb/mcpserver@latest with FALKORDB_HOST=localhost and FALKORDB_PORT=6379 (fixed by PR #10). Proof method from the wiring test: complete the MCP handshake and run the read-only count MATCH (p:Person) RETURN count(p) through query_graph_readonly; on the seeded sample graph it returns 18.
9. Run one matchmake through the harness for person rene and check the suggestion comes back with its graph path (person, topic, talk, person). Then have Matchmaker draft an intro and confirm the approval gate holds: the send_intro step must stop for a human yes and send nothing before it.
10. Fallback if the harness stalls: the same loop runs without it: python -m agents.runner --person rene --noninteractive (README Quickstart; also the DEMO.md stage safety net).

## 2026-10-24 ~11:40 AM PT, Tree -> Mac session: llm-provider-layer

Done: claiming this task before building. Rene claimed the OpenAI credit, but his OpenAI account balance is negative, so an OpenAI key cannot be used live today. Tree is building a provider layer (new agents/llm.py) that speaks the OpenAI-compatible chat completions shape to either OpenAI or Fireworks, defaulting to Fireworks with model accounts/fireworks/models/glm-5p3-flash, wired into the Matchmaker intro draft and a Planner plan summary, with the current deterministic text as the no-key and on-failure fallback. The TrueForge agent.json model fields move to the Fireworks GLM and trueforge/README.md gains provider switching docs.
Evidence: claim only; the test evidence lands with the PR.
Next: one PR on branch tree/llm-provider (full suite, smoke, FastAPI matchmake check, and a live Fireworks check through the local fw-proxy), then a wrap-up handoff here with the Mac session follow-ups.
Owner now: Tree (provider layer), Mac session (TrueForge local run after).
