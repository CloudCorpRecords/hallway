"""The money queries: every answer comes back with the graph path that proves it.

Each function takes a FalkorDB graph object (see graph/seed.py connect()).
Matchmaking runs two traversals and merges them in Python:

1. Shared interests:  me -INTERESTED_IN-> Topic <-INTERESTED_IN- other
2. Speaking on my interests (the 3 hop path):
   me -INTERESTED_IN-> Topic <-ABOUT- Talk <-GIVES- other

People already connected to me by a MET edge are never suggested again:
that is the memory doing its job.
"""

from datetime import datetime


# ---------- path helpers ----------

def _node_label(node):
    props = getattr(node, "properties", {}) or {}
    labels = getattr(node, "labels", []) or []
    name = props.get("name") or props.get("title") or props.get("id") or "?"
    label = labels[0] if labels else "Node"
    return f"{label}({name})"


def _path_parts(path):
    """Return (nodes, edges) from a FalkorDB Path object, defensively."""
    nodes = getattr(path, "nodes", None)
    edges = getattr(path, "edges", None)
    if callable(nodes):
        nodes = nodes()
    if callable(edges):
        edges = edges()
    return list(nodes or []), list(edges or [])


def render_path(path):
    """Render a path as readable text, e.g.
    Person(Rene Turcios) -[INTERESTED_IN]-> Topic(MCP) <-[ABOUT]- Talk(...) <-[GIVES]- Person(Maya Chen)
    """
    nodes, edges = _path_parts(path)
    if not nodes:
        return str(path)
    if not edges:
        return _node_label(nodes[0])
    by_id = {getattr(n, "id", i): n for i, n in enumerate(nodes)}
    current = nodes[0]
    out = [_node_label(current)]
    remaining = list(nodes[1:])
    for edge in edges:
        src = getattr(edge, "src_node", None)
        dst = getattr(edge, "dest_node", None)
        rel = getattr(edge, "relation", "REL")
        cur_id = getattr(current, "id", None)
        nxt = None
        forward = True
        if src is not None and dst is not None and cur_id is not None:
            if src == cur_id and dst in by_id:
                nxt, forward = by_id[dst], True
            elif dst == cur_id and src in by_id:
                nxt, forward = by_id[src], False
        if nxt is None:
            if not remaining:
                break
            nxt = remaining.pop(0)
        else:
            if nxt in remaining:
                remaining.remove(nxt)
        out.append(f"-[{rel}]->" if forward else f"<-[{rel}]-")
        out.append(_node_label(nxt))
        current = nxt
    return " ".join(out)


def path_hops(path):
    _, edges = _path_parts(path)
    return len(edges)


def _props(node):
    return dict(getattr(node, "properties", {}) or {})


# ---------- (a) matchmaking ----------

def matchmake(g, person_id, limit=5):
    """People to meet, ranked, each with reasons and graph paths.

    Returns a list of dicts: {person_id, name, company, score,
    shared_topics, speaking_on, paths: [{text, hops}]}.
    """
    found = {}

    def entry(pid, props):
        if pid not in found:
            found[pid] = {
                "person_id": pid,
                "name": props.get("name"),
                "company": props.get("company"),
                "score": 0,
                "shared_topics": [],
                "speaking_on": [],
                "paths": [],
            }
        return found[pid]

    # 1. Shared interests, 2 hop path through a Topic.
    res = g.query(
        "MATCH p = (me:Person {id: $pid})-[:INTERESTED_IN]->(t:Topic)"
        "<-[:INTERESTED_IN]-(other:Person) "
        "WHERE other.id <> $pid AND NOT (me)-[:MET]-(other) "
        "RETURN other, t.name, p",
        {"pid": person_id},
    )
    for other, topic, path in res.result_set:
        props = _props(other)
        e = entry(props["id"], props)
        if topic not in e["shared_topics"]:
            e["shared_topics"].append(topic)
            e["score"] += 2
        e["paths"].append({"text": render_path(path), "hops": path_hops(path)})

    # 2. Speaking on my interests, 3 hop path through Topic and Talk.
    res = g.query(
        "MATCH p = (me:Person {id: $pid})-[:INTERESTED_IN]->(t:Topic)"
        "<-[:ABOUT]-(talk:Talk)<-[:GIVES]-(other:Person) "
        "WHERE other.id <> $pid AND NOT (me)-[:MET]-(other) "
        "RETURN other, t.name, talk.title, p",
        {"pid": person_id},
    )
    for other, topic, talk_title, path in res.result_set:
        props = _props(other)
        e = entry(props["id"], props)
        tag = f"{talk_title} ({topic})"
        if tag not in e["speaking_on"]:
            e["speaking_on"].append(tag)
            e["score"] += 3
        e["paths"].append({"text": render_path(path), "hops": path_hops(path)})

    ranked = sorted(found.values(), key=lambda e: (-e["score"], e["name"] or ""))
    for e in ranked:
        seen = set()
        unique_paths = []
        for p in e["paths"]:
            if p["text"] not in seen:
                seen.add(p["text"])
                unique_paths.append(p)
        e["paths"] = sorted(unique_paths, key=lambda p: -p["hops"])
    return ranked[:limit]


# ---------- (b) talks for a person, clash free ----------

def planned_talks(g, person_id):
    res = g.query(
        "MATCH (:Person {id: $pid})-[:PLANNED]->(t:Talk) "
        "RETURN t.id, t.starts, t.ends",
        {"pid": person_id},
    )
    return [{"id": r[0], "starts": r[1], "ends": r[2]} for r in res.result_set]


def _clashes(starts, ends, picks, ignore_id=None):
    for p in picks:
        if ignore_id is not None and p["id"] == ignore_id:
            continue
        if starts < p["ends"] and p["starts"] < ends:
            return p
    return None


def talks_for(g, person_id):
    """Talks matching my interests that do not clash with my PLANNED picks.

    Interest matching and speaker/room lookup run in Cypher; the overlap
    check runs here so it is easy to audit. A talk already PLANNED is kept
    (flagged planned=True) and never counts as its own clash.
    """
    res = g.query(
        "MATCH (:Person {id: $pid})-[:INTERESTED_IN]->(t:Topic)<-[:ABOUT]-(talk:Talk)"
        "-[:IN_ROOM]->(r:Room) "
        "OPTIONAL MATCH (sp:Person)-[:GIVES]->(talk) "
        "RETURN talk, r.name, collect(DISTINCT t.name), collect(DISTINCT sp.name)",
        {"pid": person_id},
    )
    picks = planned_talks(g, person_id)
    pick_ids = {p["id"] for p in picks}
    out = []
    seen = set()
    for talk, room, topics, speakers in res.result_set:
        props = _props(talk)
        if props["id"] in seen:
            continue
        seen.add(props["id"])
        planned = props["id"] in pick_ids
        clash = _clashes(props["starts"], props["ends"], picks,
                          ignore_id=props["id"])
        if clash is not None:
            continue
        out.append({
            "id": props["id"],
            "title": props["title"],
            "starts": props["starts"],
            "ends": props["ends"],
            "room": room,
            "topics": sorted(t for t in topics if t),
            "speakers": sorted(s for s in speakers if s),
            "planned": planned,
        })
    out.sort(key=lambda t: (t["starts"], t["title"]))
    return out


def plan_talk(g, person_id, talk_id):
    """Write a PLANNED edge. Returns False if it would clash."""
    res = g.query("MATCH (t:Talk {id: $tid}) RETURN t.starts, t.ends",
                  {"tid": talk_id})
    if not res.result_set:
        return False
    starts, ends = res.result_set[0]
    picks = planned_talks(g, person_id)
    if _clashes(starts, ends, picks, ignore_id=talk_id) is not None:
        return False
    g.query(
        "MATCH (p:Person {id: $pid}), (t:Talk {id: $tid}) "
        "MERGE (p)-[r:PLANNED]->(t) SET r.added_at = $at",
        {"pid": person_id, "tid": talk_id,
         "at": datetime.now().strftime("%H:%M")},
    )
    return True


def clear_plan(g, person_id):
    g.query(
        "MATCH (:Person {id: $pid})-[r:PLANNED]->(:Talk) DELETE r",
        {"pid": person_id},
    )


# ---------- (c) and (d) memory: who I met, and recording a meeting ----------

def met_list(g, person_id):
    """Everyone this person has a MET edge with, oldest first."""
    res = g.query(
        "MATCH (:Person {id: $pid})-[m:MET]-(other:Person) "
        "RETURN other, m.note, m.at ORDER BY m.at",
        {"pid": person_id},
    )
    out = []
    for other, note, at in res.result_set:
        props = _props(other)
        out.append({"person_id": props.get("id"), "name": props.get("name"),
                    "company": props.get("company"), "note": note, "at": at})
    out.sort(key=lambda m: m["at"] or "")
    return out


def record_meeting(g, a_id, b_id, note, at=None):
    """Write memory: a and b met. Replaces any previous MET edge between them."""
    at = at or datetime.now().strftime("%H:%M")
    g.query(
        "MATCH (a:Person {id: $a})-[old:MET]-(b:Person {id: $b}) DELETE old",
        {"a": a_id, "b": b_id},
    )
    g.query(
        "MATCH (a:Person {id: $a}), (b:Person {id: $b}) "
        "CREATE (a)-[:MET {note: $note, at: $at}]->(b)",
        {"a": a_id, "b": b_id, "note": note, "at": at},
    )
    return {"a": a_id, "b": b_id, "note": note, "at": at}
