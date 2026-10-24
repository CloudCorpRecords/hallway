# Tree status

Owner: Tree. Only Tree edits this file.
Status: WIP, 2026-10-24 ~11:40 AM PT (task llm-provider-layer claimed; see Now).

## Now

- WIP: llm-provider-layer. Building agents/llm.py (OpenAI or Fireworks, Fireworks GLM default), wiring it into the Matchmaker intro draft and a Planner plan summary, updating the TrueForge agent.json models and provider docs. Branch tree/llm-provider. Claim entry is in coordination/handoffs.md.
- DONE: coordination kit on main (commit 16a5a59): coordination/PROTOCOL.md, tree-status.md, mac-status.md, handoffs.md, plus the pointer section at the end of COORDINATION.md.
- DONE: main re-verified from a fresh clone of d2366df (the Mac session's latest board commit): full suite and smoke green, runner end to end (details in Evidence).
- DONE with one fix: MCP wiring test. The FalkorDB entry in mcp/servers.json pointed at a package that does not exist (`uvx falkordb-mcp`; PyPI and npm both 404). The official server is `@falkordb/mcpserver` on npm. Fix is in PR #10 (branch tree/mcp-servers-fix), left open for Rene to merge. Until it merges, run the server directly: `npx -y @falkordb/mcpserver@latest` with FALKORDB_HOST=localhost and FALKORDB_PORT=6379. The Bright Data entry is correct as declared.
- Merged today, all verified by API read-back: Tree PRs #1, #5, #6, #7 and Mac session PRs #8, #9. Rene called the merges; Tree executed them.

## Lanes (Tree)

graph/, tests/, agents/planner.py, agents/matchmaker.py, app/, README.md, DEMO.md, COORDINATION.md (appends), coordination/tree-status.md, coordination/handoffs.md (appends).

## Evidence (verbatim, Tree, 2026-10-24)

- Suites from current main against the real FalkorDB on localhost:6379: "FULL SUITE: 15/15 tests passed, 0 failed" and "SMOKE OK: 3/3 graph smoke tests passed". Runner end to end, top match "Diego Fuentes (Independent) score 19".
- MCP initialize against @falkordb/mcpserver: serverInfo name "falkordb", version "1.3.0".
- MCP tools/list: query_graph, query_graph_readonly, list_graphs, delete_graph, get_graph_schema, get_node_schema, get_relationship_schema.
- tools/call query_graph_readonly on graph hallway, MATCH (p:Person) RETURN count(p) AS people: people = 18.
- tools/call query_graph_readonly, matchmake pattern for rene (Person to Topic to Talk to Person): 10 rows, first rows Marcus Webb / MCP / Opening Keynote: Software in the Agent Era and Maya Chen / MCP / MCP in Production: Tool Servers That Scale.
- Bright Data keyless load (npx -y @brightdata/mcp, no API_TOKEN): "Error: Cannot run MCP server without API_TOKEN env", exit 1. Expected healthy failure; the API key is a venue step for Rene.
- Qodo: installed on this repo (free open-source plan). No Qodo review has landed on any PR yet despite /agentic_review trigger comments. The likely remaining step is the Qodo-side sign-in and repo enable, which is Rene's.

## Next

- Rene: merge PR #10 when ready; venue steps stay his (Bright Data key and zones with patch50, OpenAI credits, TrueForge run, real schedule URL, demo video, submission with all four tracks).
- Mac session: MCP wiring is proven; build on it freely. Tree is READY and working in sync per coordination/PROTOCOL.md.
