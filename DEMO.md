# Hallway demo script (stage, about 3 minutes)

Setup before going on: FalkorDB running, graph seeded, app open at
http://localhost:8000, terminal open with the runner. Person field: rene.
Interests on the record: MCP, AI agents, developer tools, Rust.

## Step 1. The matchmaking question, with the path lit (FalkorDB)

Ask out loud: "I build MCP tooling. Who should I meet this afternoon, and why
should I believe you?"

Click Load. Under "Who to meet", point at the top match and read the path:

    Person(Rene Turcios) -[INTERESTED_IN]-> Topic(MCP) <-[ABOUT]-
    Talk(MCP in Production: Tool Servers That Scale) <-[GIVES]- Person(Maya Chen)

Say: "Three hops. Me, to my topic, to her talk, to her. The path is not a
debug view, it is the answer. Every suggestion Hallway makes can be audited
like this."

## Step 2. Memory recall (FalkorDB MET edges)

Ask: "Who have I already met today?" The "Who I already met" card answers:
Tom Alvarez, breakfast, MCP gateways. Say: "Tom never appears in my
suggestions, even though he scores well on my topics. Memory is an edge in
the graph, so every agent sees it, and it survives after I close the laptop."

Live beat if there is time: record a meeting with Maya from the API, reload,
and watch her leave the suggestion list.

## Step 3. The schedule moves, the plan repairs itself (Bright Data + Planner)

Click "Scout: refresh data". The status line reports the changes Scout
pulled through Bright Data: talk t6 moved from Main Stage to Workshop 2,
talk t11 moved from 16:15 to 16:30. Click "Rebuild my plan" (or run the
runner, which does Scout then Planner). Say: "Conferences change under you.
Hallway notices, replans, and tells you what it cost, instead of sending you
to the wrong room."

## Step 4. The intro that stops for a human (TrueForge approvals)

Run the runner (or show the approval card). Matchmaker drafts an intro to
the top match, grounded in the shared topic, and it stops at the approval
gate. Nothing is sent. Approve it on stage. Say: "Agents that message people
on your behalf should ask first. The gate is part of the harness, not a
checkbox we remembered to add."

## Step 5. The Qodo trail (Qodo)

Show the repo pull requests: small, single purpose, each reviewed by Qodo.
Open one finding and its fix commit. Say: "Everything you just saw shipped
through pull requests an AI reviewer read first, including the fix it asked
for. That is the whole day, in the open."

Close: "Hallway. Your conference, run by agents that share one memory, and
every answer comes with its path."
