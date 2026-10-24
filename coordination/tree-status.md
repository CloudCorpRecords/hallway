# Tree status

Owner: Tree. Only Tree edits this file.
Status: READY, 2026-10-24 ~11:45 AM PT (llm-provider-layer shipped as PR #11, Fireworks GLM live-verified end to end; see Evidence).

## Now

- DONE: llm-provider-layer, PR #11 (branch tree/llm-provider, left open for Rene). agents/llm.py speaks the OpenAI-compatible chat completions shape to OpenAI or Fireworks, env selected, Fireworks GLM the default. Matchmaker intro drafts and the Planner plan summary use it with the deterministic text as fallback; the TrueForge agent.json models moved to fireworks/glm-5p3-flash and trueforge/README.md documents switching. Wrap-up handoff with the Mac session follow-ups is in coordination/handoffs.md.
- DONE: coordination kit on main (commit 16a5a59): coordination/PROTOCOL.md, tree-status.md, mac-status.md, handoffs.md, plus the pointer section at the end of COORDINATION.md.
- DONE: main re-verified from a fresh clone of d2366df (the Mac session's latest board commit): full suite and smoke green, runner end to end (details in Evidence).
- DONE with one fix: MCP wiring test. The FalkorDB entry in mcp/servers.json pointed at a package that does not exist (`uvx falkordb-mcp`; PyPI and npm both 404). The official server is `@falkordb/mcpserver` on npm. Fix is in PR #10 (branch tree/mcp-servers-fix), left open for Rene to merge. Until it merges, run the server directly: `npx -y @falkordb/mcpserver@latest` with FALKORDB_HOST=localhost and FALKORDB_PORT=6379. The Bright Data entry is correct as declared.
- Merged today, all verified by API read-back: Tree PRs #1, #5, #6, #7 and Mac session PRs #8, #9. Rene called the merges; Tree executed them.

## Lanes (Tree)

graph/, tests/, agents/llm.py, agents/runner.py, agents/planner.py, agents/matchmaker.py, trueforge/ (agent definitions and docs), app/, README.md, DEMO.md, COORDINATION.md (appends), coordination/tree-status.md, coordination/handoffs.md (appends).

## Evidence (verbatim, Tree, 2026-10-24)

- LLM provider layer (PR #11): "LLM SUITE: 14/14 tests passed, 0 failed"; "FULL SUITE: 29/29 tests passed, 0 failed" (15 graph and agent tests plus 14 mocked-transport LLM tests); "SMOKE OK: 3/3 graph smoke tests passed".
- Live Fireworks check (tests/live_llm_check.py, through fw-proxy on 127.0.0.1:8791, real API): "LIVE CHECK: OK (intro source llm:fireworks:accounts/fireworks/models/glm-5p3-flash, summary present)". The live GLM intro draft and plan summary are quoted in the PR #11 body and the wrap-up handoff.
- Runner with no env: "no LLM provider configured (deterministic mode)", draft source: template. Runner with the proxy env: provider line "fireworks / accounts/fireworks/models/glm-5p3-flash via http://127.0.0.1:8791/inference/v1", LLM plan summary printed, draft source llm:fireworks:accounts/fireworks/models/glm-5p3-flash.
- FastAPI on the new code: GET /api/health {"ok":true}; GET /api/matchmake/rene returned 5 matches, top "Diego Fuentes" score 19.
- Suites from current main against the real FalkorDB on localhost:6379: "FULL SUITE: 15/15 tests passed, 0 failed" and "SMOKE OK: 3/3 graph smoke tests passed". Runner end to end, top match "Diego Fuentes (Independent) score 19".
- MCP initialize against @falkordb/mcpserver: serverInfo name "falkordb", version "1.3.0".
- MCP tools/list: query_graph, query_graph_readonly, list_graphs, delete_graph, get_graph_schema, get_node_schema, get_relationship_schema.
- tools/call query_graph_readonly on graph hallway, MATCH (p:Person) RETURN count(p) AS people: people = 18.
- tools/call query_graph_readonly, matchmake pattern for rene (Person to Topic to Talk to Person): 10 rows, first rows Marcus Webb / MCP / Opening Keynote: Software in the Agent Era and Maya Chen / MCP / MCP in Production: Tool Servers That Scale.
- Bright Data keyless load (npx -y @brightdata/mcp, no API_TOKEN): "Error: Cannot run MCP server without API_TOKEN env", exit 1. Expected healthy failure; the API key is a venue step for Rene.
- Qodo: installed on this repo (free open-source plan). No Qodo review has landed on any PR yet despite /agentic_review trigger comments. The likely remaining step is the Qodo-side sign-in and repo enable, which is Rene's.

## Next

- Rene: merge PR #11 when ready; venue steps stay his (Bright Data key and zones with patch50, TrueForge run, real schedule URL, demo video, submission with all four tracks). OpenAI live use stays blocked until the account's negative balance is settled with OpenAI; Fireworks is the live provider meanwhile.
- Mac session: run TrueForge locally with the Fireworks GLM (the three follow-ups are spelled out in the wrap-up handoff in coordination/handoffs.md: accept-check the model string, verify the send_intro approval gate in the harness, capture the run for the submission).
