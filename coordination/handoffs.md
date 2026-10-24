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

---

## 2026-10-24 ~11:50 AM PT, Tree -> Mac session and Rene: qodo-signin-blocked-on-qodo-side

Done: attempted the Qodo-side setup from Tree's browser. GitHub authorization for Qodo.ai (account CloudCorpRecords) SUCCEEDED after the authorize button's disabled state cleared. Qodo's own sign-in callback then failed three times across two routes with the same error: app.qodo.ai/error, internal_status_code=FALLBACK, Trace ID 5a57125f-8b90-4552-a9ee-4192fbad5226. No Qodo session was created, no workspace exists, no settings were changed, and hallway is NOT enabled in Qodo's UI. This is a Qodo-side failure after successful GitHub authorization, not a credential problem; repeating the same sign-in loop is not expected to change it.
Evidence: browser run 11:34 to 11:50 AM PT, three attempts (two via app.qodo.ai/signin?product_source=login, one via app.qodo.ai/signin), identical FALLBACK error and trace ID each time; direct visit to app.qodo.ai afterward redirected back to sign-in, confirming no session.
Next: Rene, try signing in to Qodo once in your own browser on the Mac (different route may clear it); if the same FALLBACK error appears, it is a Qodo outage and the support path is the trace ID above. The Qodo GitHub App stays installed on this repo and /agentic_review triggers are posted on PRs #1, #5, #6, #7 and #11; if reviews ever arrive, the fix flow is the one already on the board. Do not let this block the demo: the Qodo track story is install plus small PRs plus triggers, with this outage noted honestly.
Owner now: Rene (one local sign-in try), then Qodo support if it persists.

## 2026-10-24 ~12:00 PM PT, Mac session -> Rene: brightdata-key-wireup
Done: stored Rene's Bright Data API key in /tmp/hallway/.env only (gitignored, status clean) and proved it with the smallest live calls. The key is valid; the default zone names do not exist on the account.
Evidence: SERP call -> HTTP 400 zone "serp_api1" not found; Web Unlocker call -> HTTP 400 zone "web_unlocker1" not found. No code changed; fixtures still drive the demo.
Next: Rene creates zones named web_unlocker1 and serp_api1 in the Bright Data dashboard (or sends the real zone names plus the real SCHEDULE_URL), then the Mac session finishes the live wiring.
Owner now: Rene (zones, schedule URL).

---

## 2026-10-24 ~12:05 PM PT, Tree -> Mac session and Rene: brightdata-zones-blocked-on-token-permissions

Done: at Rene's direction ("do what it asked"), Tree built the custom.brightdata connector helper (bin/bd.py in the custom connectors folder, modeled on the Fireworks helper) and called the Bright Data API with the registered key. The key authenticates through the connector: GET /zone/get_active_zones returned HTTP 200 with an empty list, matching the Mac session's finding that the account has no zones. Tree then attempted to create the two zones the config expects, web_unlocker1 (Web Unlocker, type unblocker) and serp_api1, using the documented POST /zone shape.
Evidence: the create call returned HTTP 403, "Your API key lacks the required permissions for this action", pointing at the token permission settings (brightdata.com/cp/setting/users). A follow-up zone list confirmed nothing was created. The connector doc (custom.brightdata/CONNECTOR.md) now records the verified read, the refused create with its exact payload shape, and the untested /request operation.
Next, Rene's call, either one unblocks everything: (1) create the two zones in the Bright Data dashboard with exactly the names web_unlocker1 (Web Unlocker) and serp_api1 (SERP API), zero code changes, the Mac .env already points at them; or (2) widen the API token's permissions at brightdata.com/cp/setting/users and tell Tree, and Tree creates both zones through the API and verifies them with one live call each. After zones exist, set SCHEDULE_URL in the Mac .env to the real schedule page, https://githubuniverse.com/schedule, and Scout can go live. Until then the demo is unaffected: the adapter keeps serving fixtures.
Owner now: Rene (dashboard or token permissions).

---

## 2026-10-24 ~12:16 PM PT, Tree -> Mac session: brightdata-zones-live

Done: both zones now exist on the account. Rene signed in to the Bright Data dashboard himself in Tree's browser, the browser created web_unlocker1 (Web Unlocker) and serp_api1 (SERP API) with default settings, and the dashboard lists both as Active. No payment information was entered and no plan changed.
Evidence: Tree verified independently through the API after creation. The zone list now returns web_unlocker1 with type unblocker and serp_api1 with type serp. One live Web Unlocker request for the real Universe schedule page returned HTTP 200 with the real page HTML, so the unlocker path works end to end against the site a plain fetch could not read.
Next, Mac session: point SCHEDULE_URL in the Mac .env at the real schedule page, https://githubuniverse.com/schedule, and run Scout live against it. Expect parser adjustments against the real page markup; ingest/ is your lane. The token permission limit from the previous entry no longer matters now that the zones exist.
Owner now: Mac session (live Scout run).

## 2026-10-24 ~12:40 PM PT, Mac session -> Rene: live-scout-run
Done: ran Scout live as far as the real web allows. The guessed schedule path is a soft 404, the real catalog is a login-walled attendee portal the unlocker cannot read, and no public agenda URL exists. Fixed one genuine adapter bug on the way (PR #12, SERP query encoding). Demo graph untouched, fixtures still drive it.
Evidence: "__NEXT_DATA__" {"page":"/404"} on /schedule; portal catalog 335KB with zero session data or API URLs; PR https://github.com/CloudCorpRecords/hallway/pull/12.
Next: Rene pastes a public agenda URL or attendee-portal credentials, and the Mac session writes the real parser and runs the first live refresh on a scratch graph. Without that, Scout stays on fixtures by design.
Owner now: Rene (agenda URL or portal access).

## 2026-10-24 ~1:00 PM PT, Mac session -> Rene and Tree: live-scout-run-blocked
Done: exhausted the public routes to a real Universe agenda. The schedule-launch blog post links only the login-walled portal; a live per-session URL returns the identical chrome-only shell (498 visible chars, zero session data). No public agenda or speaker-list page exists via two more SERP sweeps. Reverted .env SCHEDULE_URL to the placeholder with the findings noted. PR #12 (SERP encoding fix) left open for Tree to merge.
Evidence: session page 335360 bytes, visible text is nav only; PR https://github.com/CloudCorpRecords/hallway/pull/12.
Next: live Scout needs attendee-portal access (login or an authenticated export) pasted by Rene, or a public agenda URL if one appears. Until then fixtures stand and the demo is unaffected. Tree: please merge PR #12 at will, it is verified and tiny.
Owner now: Rene (portal access or agenda URL), Tree (PR #12 merge).

---

## 2026-10-24 ~12:28 PM PT, Tree -> Mac session: pr12-merged-and-schedule-finding-accepted

Done: PR #12 (Ingest: URL-encode SERP queries) is merged by Tree. Merge commit 108f6170f358fec1d10a86b8d67af4503d879a91, read back on main. Tree verified the diff before merging: one file, ingest/brightdata.py, quote_plus on the search query, exactly the fix your live run proved out.
Accepted, your schedule finding: the /schedule URL Tree supplied is a soft-404 on the public site and no public Universe agenda exists; the catalog is behind the attendee portal. Tree's earlier live fetch returned HTTP 200 on that URL but the content was the soft-404 shell, and Tree has corrected that claim to Rene directly. Agreed with your call to write no parser against unfetchable markup. Fixtures stand for the demo.
Submission pack: Tree rewrote the Bright Data paragraph to this exact state (zones live, both paths exercised at the venue, your PR #12 catch credited, the portal limit stated plainly, demo graph seeded) and added PR #12 to the Qodo section list. No action needed from you on the pack.
Still open and waiting on Rene, unchanged: PR #11 (the LLM provider layer) is still open; the merge call is his.
Owner now: Rene (PR #11 call, demo video, submission). Mac session: TrueForge run per the earlier handoff when ready.
