# Hallway graph schema (FalkorDB)

One graph holds the whole conference: talks, people, topics, rooms, and the
attendee's own memory. Three agents (Scout, Planner, Matchmaker) read and write
the same graph, which is what makes their state shared instead of siloed.

## Nodes

- `Person` {id, name, kind, company, handle}
  - kind is `attendee` or `speaker`. Speakers are people who give talks; the
    speaker role is expressed with the GIVES edge, not a separate node type.
  - id is a stable slug, e.g. `maya-chen`, `rene`.
- `Talk` {id, title, starts, ends, blurb}
  - starts / ends are zero padded 24h strings `HH:MM` on a single conference
    day, so lexicographic order is chronological order.
- `Topic` {name}  e.g. MCP, AI Agents, Rust, Developer Tools, Open Source.
- `Room` {name}   e.g. Main Stage, Workshop 1.
- `Company` {name}

## Edges

- `GIVES`        Person -> Talk        (speaker gives a talk)
- `ABOUT`        Talk -> Topic          (talk is about a topic)
- `IN_ROOM`      Talk -> Room           (talk happens in a room)
- `INTERESTED_IN` Person -> Topic {weight}  (attendee interest, weight 1 to 3)
- `WORKS_AT`     Person -> Company
- `MET`          Person -> Person {note, at}
  - The memory edge. Written when two people actually meet; Matchmaker never
    suggests someone already connected by a MET edge. `at` is `HH:MM`.
- `PLANNED`      Person -> Talk {added_at}
  - The attendee's picked schedule. Planner writes these and checks new picks
    against existing ones for time clashes.

## Why a graph and not tables

The core questions are traversals, not lookups:

- Who should I meet? Person -> Topic <- Person (shared interests), and
  Person -> Topic <- Talk <- Person (people speaking on my interests). Both
  are multi-hop, and the path itself is the explanation shown to the user.
- What can I still attend? Talks on my topics, minus anything whose time range
  overlaps a PLANNED talk.
- Who have I already met? A direct read of MET edges, shared across sessions
  because it lives in the graph, not in one agent's memory.
