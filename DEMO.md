# Hallway demo script (stage, under 3 minutes of talking)

Setup before going on: FalkorDB running, graph seeded fresh
(`python -m graph.seed`), app running (`uvicorn app.main:app --port 8000`),
the board open at http://localhost:8000, a terminal open as backup.
Person field: rene. Interests on the record: MCP, AI agents, developer
tools, Rust. Timings are cumulative; the whole talk track is about 2:40.

## Step 1. Who to meet, and the trail proves it (FalkorDB) 0:00 to 0:40

Click **Load my day**. In the Who to meet panel, point at the top card
(right now Diego Fuentes) and trace the breadcrumb trail with a finger:
You, Rust, Rust CLIs That Feel Instant, Diego Fuentes. Then click
"show the graph path" on that card.

Say: "Every suggestion comes with its trail. Me, to my topic, to his talk,
to him. Three hops through the graph, on screen. The path is not a debug
view, it is the reason, and you can audit every card here the same way."

Point at the amber ice breaker box under the trail.

Say: "It even hands me the first sentence, built from that same path: ask
Diego about his Rust CLI talk at 9:30 in Workshop 1, because we are both
into developer tools."

## Step 2. Memory: the graph remembers who you met (FalkorDB) 0:40 to 1:10

Point at the Who I already met panel: Tom Alvarez, breakfast, MCP
gateways.

Say: "Tom scores well on my topics, and he is nowhere in my suggestions,
because we met at breakfast and Hallway wrote it into the graph as a MET
edge. Every agent shares that memory, and it survives closing the laptop."

Live beat, if the room is with you: record a meeting with the top
suggestion from the terminal
(`curl -X POST localhost:8000/api/met -H 'Content-Type: application/json' -d '{"a":"rene","b":"diego-fuentes","note":"Met in the hallway, swapped Rust CLI notes.","at":"10:24"}'`),
click **Load my day** again, and watch that card leave the list while the
name appears in the met panel.

## Step 3. Edit the plan, and get refused politely (Planner) 1:10 to 1:50

On the timeline, the planned talks glow green. Click **Add** on a talk
that runs at the same time as a planned one (Rust CLIs That Feel Instant
at 9:30 while MCP in Production is planned).

Say: "I want both 9:30 talks. Watch what happens." The red notice appears,
naming the clash and the talk already in the plan.

Say: "No silent failure, no double booking. It tells me exactly which talk
is in the way." Click **Drop** on the planned talk, then **Add** again:
the card turns green with its in-your-plan tag. Point at the italic why
line on any card.

Say: "And every pick says why it is there: the interests it matched."

## Step 4. The schedule moves, Scout catches it, plan repairs
(Bright Data + Planner) 1:50 to 2:30

Click **Scout: check for changes**. The yellow Scout banner appears:
talk t6 moved from Main Stage to Workshop 2, talk t11 moved from 16:15
to 16:30.

Say: "Conferences change under you. Scout pulls the live schedule through
Bright Data, diffs it against the graph, and reports exactly what moved,
in plain lines." Click **Rebuild my plan**.

Say: "Planner rebuilds the day against the new times, still clash free,
still with a reason on every talk. No being sent to the wrong room."

## Step 5. The intro that asks first, and the paper trail
(TrueForge + Qodo) 2:30 to 2:55

In the terminal run `python -m agents.runner --person rene
--noninteractive` and scroll to the intro at the end: Matchmaker's draft
to the top match, stopped at the approval gate, verdict printed, nothing
sent.

Say: "Agents that message people on your behalf should ask first. Under
TrueForge that gate is the harness approval step, not a checkbox."

Show the repo pull request list: small, single-purpose PRs (schema pass,
graph expansion, the board, these docs), each one reviewed by Qodo, its
findings fixed in follow-up commits.

Say: "Everything you just saw shipped through pull requests an AI
reviewer read first."

Close: "Hallway. Your conference, run by agents that share one memory,
and every answer comes with its path."
