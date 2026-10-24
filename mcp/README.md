# MCP servers for Hallway

Two MCP servers give the agents their hands. Config: `servers.json` in this
folder.

## FalkorDB MCP server (preferred path for agent graph access)

FalkorDB ships its own MCP server, so the TrueForge agents can run Cypher
and use the graph as memory through tools instead of through our HTTP API:
docs.falkordb.com/genai-tools/mcpserver/quickstart. The related agentic
memory landscape (Graphiti, Cognee, Mem0) is surveyed at
docs.falkordb.com/genai-tools as well; Hallway's MET and PLANNED edges are
the same idea, hand rolled for one conference.

Preference order, deliberate:

1. **FalkorDB MCP server** for the agent layer at the venue, once the
   quickstart checks out in the workshop.
2. **The Python client path** (graph/queries.py over the HTTP API) stays as
   the tested fallback. It is what the smoke tests prove, and the demo can
   fall back to it mid sentence.

A FalkorDB Cloud option exists (app.falkordb.cloud) but no credit is
offered for this hackathon, so Docker (or the module build) stays the plan.

## Bright Data MCP server

@npx @brightdata/mcp with the account API token in the environment. This is
how Scout's live fetching is exposed to the harness; the REST adapter in
ingest/brightdata.py and the bdata CLI are the other two doors to the same
account.
