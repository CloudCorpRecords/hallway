# Coordination board

Two AI agents are building Hallway at the same time today (Sat Oct 24, 2026, Patch the Conference Hackathon). This file is where they coordinate. Humans: Rene owns the repo and makes the final calls.

## Who is who

- **Tree** (Muse, remote): works through the GitHub API, opens PRs, runs the test suite against a real FalkorDB before pushing. Started the scaffold, the repo, the Qodo install, PR #1.
- **Mac session** (Muse on Rene's Mac, "Hallway Agents Review"): fresh clone at /tmp/hallway on ff4c7c9, local git, can run things on the laptop. Did the 10:47 AM agents review quoted below.

## Ground rules

1. Claim before you build: move your task to CLAIMED with your name and the time before editing files. One owner per file area at a time.
2. Small PRs with clear descriptions. Branch names: tree/<slug> or rene/<slug>. Never force-push. Never push straight to main except this coordination file and emergency fixes Rene approves.
3. Every commit gets the trailer: Signed-off-by: Rene Turcios <95189389+CloudCorpRecords@users.noreply.github.com>
4. No em dashes or en dashes anywhere (code, docs, commit messages, PR text).
5. Test before you push: run the suite in tests/ against a real FalkorDB and say the result in your PR. Smoke tests use their own graph (HALLWAY_GRAPH=hallway_smoke); never wipe the demo graph.
6. When you finish or get blocked, update this board and add a line to the work log. If you are not sure a file is free, it is not free.

## Requirements and venue wiring (the risks that are not code)

In order, per the Mac session review and the runbook in BUILD-PLAN.md:

1. Bright Data: sign up at brightdata.com/cp/start, redeem code patch50, create the zones, API key into .env (or bdata login for CLI mode).
2. OpenAI: claim the $50 credits at the venue, key from platform.openai.com/api-keys into TrueForge and .env.
3. TrueForge: npx @truefoundry/trueforge, load the agents from trueforge/, wire mcp/servers.json (FalkorDB MCP quickstart: docs.falkordb.com/genai-tools/mcpserver/quickstart).
4. Real schedule: point Scout at the real GitHub Universe schedule URL through Bright Data.
5. Demo video: under 3 minutes, public or unlisted.
6. Submission: select ALL FOUR tracks. The team locks when the project is submitted, so any team invites go first.

Build requirements:

- requirements.txt versions pinned before the demo (task below).
- Wording rule: the planner output says "best per slot", never "optimal day" (build_plan greedily re-picks per slot; see review notes).
- Demo runs from a fresh clone of this repo, not from a zip copy (history differs).

## Review findings (Mac session, 2026-10-24 10:47 AM)

- build_plan clears then greedily re-picks. Fine for the demo, but say "best per slot" not "optimal day".
- MeetingIn.at has no validation. An empty at sorts oddly in met_list.
- Add the HALLWAY_GRAPH=hallway_smoke note to the test docs so no one wipes the demo graph. (Added to rule 5 above; still wants a line in tests/ docs.)
- Biggest risk is not code, it is the venue wiring list above. Do them in that order.

## Task board

### CLAIMED

- Tree, started ~10:40 AM: PR 2 branch tree/expand-graph-smarts. Richer seed data, talk explanations, icebreakers, people_by_company, talks_by_speaker, full test suite. Areas: graph/, tests/, agents/planner.py, agents/matchmaker.py. (Also folds in: MeetingIn.at validation in graph/queries.py, best-per-slot wording in planner output.)
- Tree, queued after PR 2: PR 3 branch tree/whimsical-ui. Visual board UI plus plan add/drop endpoints and changes feed. Area: app/.
- Tree, queued after PR 3: PR 4 branch tree/docs-demo-refresh. README and DEMO.md refresh. Areas: README.md, DEMO.md.
- Done, Tree: PR #1 (trueforge-schema-pass) open. Model field and mcp_servers shapes aligned to the TrueForge docs. Qodo installed on this repo; PR #1 is waiting on a Qodo review (trigger comment posted).

### FREE to claim (suggested for the Mac session)

- Scout stale edge cleanup: when a talk moves or disappears, remove stale ABOUT/GIVES edges so the graph never keeps ghost talks. Area: agents/scout.py, ingest/. (Tree is not in these files except planner/matchmaker; scout.py is free.)
- Pin requirements.txt and note the Python version in README or a .python-version file. Area: requirements.txt. Small and safe.
- TrueForge field check, round 2: the HTTP tool entries (hallway_refresh, hallway_plan, hallway_matchmake, hallway_met) and the send_intro approval flag still have no documented shape. The workshop or the running harness can settle them. Area: trueforge/ (coordinate with PR #1 before editing; the files are in that open PR).
- FalkorDB MCP wiring test: run the FalkorDB MCP server locally and confirm a TrueForge agent can query the graph through it. No repo files needed unless config changes land in mcp/servers.json.

### DONE

- Scaffold, smoke tests 3/3, repo created and pushed, Qodo installed (free open-source plan, this repo only). Tree, morning of Oct 24.

## Work log

- 2026-10-24 ~10:52 AM PT, Tree: created this board at Rene's direction so both agents can work at the same time. Expansion PRs 2 to 4 claimed above.
