# Hallway venue runbook: 11:00 to 17:30, Patch the Conference, Oct 24 2026

Venue: Bright Data, 625 2nd St, San Francisco. Demos on stage at 17:30.
Team: Aigents xero (Rene, leader, 1 of 4 seats). Bring laptop, charger,
government photo ID (21+, checked at the door).

## Step 0. Graph database running (before anything else)

- [ ] `docker compose up -d` in this repo, FalkorDB on 6379, browser on 3000
- [ ] No Docker fallback: `redis-server --loadmodule falkordb-x64.so --port 6379`
- [ ] `python tests/test_smoke.py` prints SMOKE OK
- [ ] `python -m graph.seed` then `python -m agents.runner --noninteractive` runs clean

## Accounts and keys (the venue steps only Rene can do)

- [ ] Bright Data: sign up at https://brightdata.com/cp/start, redeem the
      venue credit code **patch50** ($50; it is the only credit code on any
      hackathon page), create Web Unlocker and SERP zones, copy the API key
      into `.env` as BRIGHTDATA_API_KEY (never commit it). Optional CLI
      path: `npx -p @brightdata/cli bdata login`, then BRIGHTDATA_MODE=cli
- [ ] OpenAI: claim the $50 credits at the venue (explained there), the key
      lives at platform.openai.com/api-keys; put it in TrueForge as a
      standard provider and in `.env` as OPENAI_API_KEY
- [ ] TrueForge: `npx @truefoundry/trueforge` (nothing to clone), open the
      `trueforge/` agent definitions, reconcile field names against
      trueforge.dev/create-agent/overview, wire the MCP servers from
      `mcp/servers.json`, confirm the Chat UI answers
- [ ] FalkorDB MCP: follow docs.falkordb.com/genai-tools/mcpserver/quickstart
      and confirm the agents can run Cypher through it; the Python client
      path stays as the fallback either way
- [ ] GitHub: create the Hallway repo, push this scaffold, from here on all
      work lands as small single-purpose PRs
- [ ] Qodo: install per docs.qodo.ai/install-qodo/github/qodo-multi-tenant,
      open the first PR and confirm the review lands; a manual review is
      triggered by commenting /agentic_review on a PR; agent skills via
      `npx skills add qodo-ai/qodo-skills/skills`

## Build window (11:00 to 14:00)

- [ ] Seed the graph with the REAL GitHub Universe schedule: set
      SCHEDULE_URL in `.env`, run Scout refresh, spot check 5 talks against
      the official schedule (title, time, room, speaker)
- [ ] Enrich the top 20 speakers via Bright Data SERP (bios into Person nodes)
- [ ] Wire TrueForge: `npx @truefoundry/trueforge`, agents from
      `trueforge/`, Bright Data and FalkorDB MCP servers as tools (configs
      in `mcp/servers.json`), approval gate live on Matchmaker's send_intro
- [ ] Polish the web page: plan, who to meet with paths, who I met
- [ ] Fix every Qodo finding on the day's PRs, keep PRs small

## Lunch and submit window (14:00 to 17:30)

- [ ] Rehearse DEMO.md end to end twice, timed, with the deterministic
      fallback mode (runner with no keys) as the safety net
- [ ] Record the demo video, under 3 minutes, public or unlisted
- [ ] Submit at wemakedevs.org/hackathons/ptc/submit with ALL FOUR tracks
      selected (FalkorDB, Bright Data, TrueForge with OpenAI, Qodo)
- [ ] Submission fields: title (Hallway), repository URL, demo video,
      the conference problem (README, "The problem it patches"), what was
      built and how it works (README), Qodo PR links in Track Details
- [ ] Team locks at submission: send any team invites before this step

## If things break

- FalkorDB down: restart the container or module server, reseed, rerun the
  smoke test. The app answers 503 with a sentence, not a crash.
- Live data down: the Bright Data adapter falls back to fixtures; the demo
  still runs. Say so on stage rather than faking freshness.
- LLM down: the runner's deterministic mode is the demo. It needs only the
  graph, by design.
