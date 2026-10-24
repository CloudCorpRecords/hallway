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

## 2026-10-24 ~11:45 AM PT, Tree -> Mac session: llm-provider-layer-shipped

Done: the LLM provider layer shipped as PR #11 on branch tree/llm-provider, left open for Rene to merge. New agents/llm.py speaks the OpenAI-compatible chat completions shape to OpenAI or Fireworks, selected by env (HALLWAY_LLM_PROVIDER, default fireworks), model accounts/fireworks/models/glm-5p3-flash on Fireworks and gpt-4o on OpenAI, keys and base URLs overridable by env. The Matchmaker intro draft (the message that stops at the approval gate) is LLM drafted when a provider is configured and falls back to the deterministic template otherwise, and the draft carries its source so the two are never confused. Planner gained plan_summary(). The runner uses the layer instead of the old openai-package path and prints the provider line and the draft source; with no env set its behavior is unchanged. The three TrueForge agent.json model fields now read fireworks/glm-5p3-flash, and trueforge/README.md documents provider switching. One real bug found by testing live: glm-5p3-flash spends reasoning tokens against max_tokens, so a 160 token budget returned content=None and the intro silently fell back while the summary succeeded. Both call budgets are now 600 and the reason is documented in agents/llm.py.
Evidence: "LLM SUITE: 14/14 tests passed, 0 failed"; "FULL SUITE: 29/29 tests passed, 0 failed"; "SMOKE OK: 3/3 graph smoke tests passed"; live check through the fw-proxy against the real Fireworks API: "LIVE CHECK: OK (intro source llm:fireworks:accounts/fireworks/models/glm-5p3-flash, summary present)"; the live intro draft for the top match (Diego Fuentes), verbatim model output: "Hi Diego, I'm Rene Turcios and I'll be at the conference too. I saw you're giving "Rust CLIs That Feel Instant" at 09:30 in Workshop 1 — Rust and developer tools are both big interests of mine, so I'd love to hear about it. Are you up for a quick hallway chat today?"; FastAPI GET /api/matchmake/rene returned 5 matches, top Diego Fuentes score 19; PR https://github.com/CloudCorpRecords/hallway/pull/11.
Next: FOR THE MAC SESSION, in order. (1) Run TrueForge locally (npx @truefoundry/trueforge) with the three definitions in trueforge/ and the FalkorDB MCP server from mcp/servers.json, provider Fireworks and the GLM model, and confirm the harness accepts the agent.json model string fireworks/glm-5p3-flash. TrueForge documents the provider/model form generically; if the harness wants a different Fireworks form, fix it in one small PR and log the accepted string here. (2) Verify the send_intro approval gate fires inside TrueForge: draft an intro through the harness and confirm nothing is sent before a human yes. (3) Capture the run output (the matchmake with its graph path, the gated draft) for the submission. The earlier TrueForge venue sequence in this log still applies for the graph service steps (seed, uvicorn on 8000); only the provider changes: Fireworks, not the venue OpenAI key. Also: the submission pack Tree wrote (on Tree's machine, see the entry above) describes Track 3 in OpenAI terms; its TrueForge paragraph needs its tense updated to Fireworks once PR #11 merges, and Rene should ask Tree for the updated text before pasting.
Owner now: Rene (merge PR #11, venue steps), Mac session (TrueForge local run).

BLOCKED note (OpenAI): OpenAI live calls are blocked by the account's negative balance (Rene's report, 2026-10-24). The $50 venue credit was claimed but the balance state refuses API use until Rene settles it with OpenAI. The provider layer supports OpenAI fully (selection, payload, parsing are unit-tested with a mocked transport), but it is live-verified only on Fireworks. Do not burn venue time debugging OpenAI 429 or billing responses; they are expected until the balance is fixed.
