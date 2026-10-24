"""Scout: keeps conference data in the graph fresh.

Scout pulls the schedule through the Bright Data adapter (live at the venue,
fixtures offline), upserts talks, speakers, topics and rooms, and reports
exactly what changed: a talk that moved rooms or times shows up as a change
line, which is what triggers Planner's repair step in the demo.
"""

from ingest import brightdata


def _snapshot(g):
    res = g.query(
        "MATCH (t:Talk)-[:IN_ROOM]->(r:Room) RETURN t.id, t.starts, t.ends, r.name"
    )
    return {row[0]: (row[1], row[2], row[3]) for row in res.result_set}


def _upsert_talk(g, talk):
    g.query(
        "MERGE (t:Talk {id: $id}) SET t.title = $title, t.starts = $starts, "
        "t.ends = $ends, t.blurb = $blurb",
        {"id": talk["id"], "title": talk["title"], "starts": talk["starts"],
         "ends": talk["ends"], "blurb": talk.get("blurb", "")},
    )
    g.query("MATCH (t:Talk {id: $id})-[r:IN_ROOM]->(:Room) DELETE r",
            {"id": talk["id"]})
    g.query(
        "MATCH (t:Talk {id: $id}), (r:Room {name: $room}) "
        "MERGE (t)-[:IN_ROOM]->(r)",
        {"id": talk["id"], "room": talk["room"]},
    )
    for speaker_id in talk.get("speaker_ids", []):
        g.query(
            "MATCH (p:Person {id: $pid}), (t:Talk {id: $tid}) "
            "MERGE (p)-[:GIVES]->(t)",
            {"pid": speaker_id, "tid": talk["id"]},
        )
    for topic in talk.get("topics", []):
        g.query("MERGE (:Topic {name: $name})", {"name": topic})
        g.query(
            "MATCH (t:Talk {id: $id}), (tp:Topic {name: $topic}) "
            "MERGE (t)-[:ABOUT]->(tp)",
            {"id": talk["id"], "topic": topic},
        )


def refresh(g):
    """Fetch the schedule and upsert it. Returns a change report dict."""
    before = _snapshot(g)
    talks, meta = brightdata.fetch_schedule()
    for talk in talks:
        _upsert_talk(g, talk)
    after = _snapshot(g)

    changes = []
    for tid, (starts, ends, room) in sorted(after.items()):
        if tid not in before:
            changes.append(f"new talk {tid} at {starts} in {room}")
        elif before[tid] != (starts, ends, room):
            b = before[tid]
            changes.append(
                f"{tid} changed: {b[0]}-{b[1]} in {b[2]} -> "
                f"{starts}-{ends} in {room}")
    return {"source": meta, "upserted": len(talks), "changes": changes}
