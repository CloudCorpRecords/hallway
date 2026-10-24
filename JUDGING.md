# Judging checklist

How Hallway answers each track criterion, and the on-stage proof for it.

## FalkorDB

- **Graph at the core:** Scout, Planner and Matchmaker share one FalkorDB graph. Matchmaking is a multi-hop traversal over talks, topics and people, and MET edges are memory across sessions. Proof: the who-to-meet answer shows its graph path on screen.
- **Explainable answers:** every suggestion renders the path behind it (person, topic, talk, speaker). The path is the reason, not a black box score.
- **Real problem, working demo:** attendees miss talks, talks move rooms, and the right people never meet. The demo runs live, step by step, as written in DEMO.md.

## Bright Data

- **Hard-to-get data at the core:** Scout fetches live schedule pages that are JS-heavy and bot-hostile, pages a plain script cannot reliably read. A fixture fallback covers fetch failures. Proof: a live refresh during the demo catches a room change.
- **Data quality:** fetched changes are diffed against the graph and reported as a change list (moved, added, removed), never silently overwritten.

## TrueForge with OpenAI

- **Built on TrueForge:** Scout, Planner and Matchmaker run as TrueForge agents (definitions in trueforge/), using MCP tools plus an HTTP tool into the graph service. OpenAI models do the reasoning and the drafting.
- **Human approval:** introductions stop at a requiresApproval gate. Nothing contacts a person without a human yes.

## Qodo

- **Qodo in use:** Qodo is installed on this repo and reviews pull requests through the day. Work lands in small PRs with clear descriptions.
- **Acting on feedback:** Qodo findings get fixed in follow-up commits on the same PR, with before and after noted.
- Qodo review examples: (PR links added here as reviews land)
