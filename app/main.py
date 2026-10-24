"""Hallway web app: a thin FastAPI layer over the graph queries and agents.

Run: uvicorn app.main:app --reload --port 8000
If FalkorDB is unreachable the API answers 503 with a plain message and the
page still loads, so the failure mode on stage is a sentence, not a stack.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from graph import queries, seed  # noqa: E402
from agents import matchmaker, planner, scout  # noqa: E402

app = FastAPI(title="Hallway")
STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")

# The last Scout refresh, for the changes feed the board polls. Refreshing
# through the API updates it; before the first refresh it is simply empty.
LAST_REFRESH = {"source": None, "upserted": 0, "changes": []}


def graph():
    try:
        return seed.connect()
    except Exception as exc:
        raise HTTPException(status_code=503,
                            detail=f"FalkorDB unreachable: {exc}")


def guard(fn):
    try:
        return fn()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503,
                            detail=f"Graph query failed: {exc}")


class MeetingIn(BaseModel):
    a: str
    b: str
    note: str
    at: str | None = None


class PlanChangeIn(BaseModel):
    talk_id: str


class IntroDraftIn(BaseModel):
    person_id: str
    other_id: str


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    def _check():
        g = graph()
        g.query("RETURN 1")
        return {"ok": True, "graph": os.environ.get("HALLWAY_GRAPH", "hallway")}
    return guard(_check)


@app.get("/api/talks")
def talks():
    """Every talk in the day, for the board timeline."""
    def _run():
        g = graph()
        res = g.query(
            "MATCH (t:Talk)-[:IN_ROOM]->(r:Room) "
            "OPTIONAL MATCH (t)-[:ABOUT]->(tp:Topic) "
            "OPTIONAL MATCH (sp:Person)-[:GIVES]->(t) "
            "RETURN t.id, t.title, t.starts, t.ends, r.name, t.blurb, "
            "collect(DISTINCT tp.name), collect(DISTINCT sp.name) "
            "ORDER BY t.starts, t.title")
        out = []
        for tid, title, starts, ends, room, blurb, topics, speakers \
                in res.result_set:
            out.append({
                "id": tid, "title": title, "starts": starts, "ends": ends,
                "room": room, "blurb": blurb,
                "topics": sorted(t for t in topics if t),
                "speakers": sorted(s for s in speakers if s),
            })
        return {"talks": out}
    return guard(_run)


@app.get("/api/plan/{person_id}")
def plan(person_id: str):
    def _run():
        g = graph()
        return {"talks": queries.talks_for(g, person_id),
                "planned": queries.planned_talks(g, person_id)}
    return guard(_run)


@app.post("/api/plan/{person_id}/rebuild")
def rebuild(person_id: str):
    def _run():
        g = graph()
        return {"plan": planner.build_plan(g, person_id)}
    return guard(_run)


@app.get("/api/plan/{person_id}/summary")
def plan_summary_ep(person_id: str):
    """Natural language briefing of the attendee's planned day."""
    def _run():
        g = graph()
        res = g.query(
            "MATCH (p:Person {id: $pid}) RETURN p.name", {"pid": person_id})
        name = res.result_set[0][0] if res.result_set else person_id
        planned_ids = {p["id"] for p in queries.planned_talks(g, person_id)}
        current_plan = [t for t in queries.talks_for(g, person_id)
                        if t["id"] in planned_ids]
        for t in current_plan:
            reasons = t.get("reasons") or [
                f"matches your interest in {tp}" for tp in t["topics"]]
            t["why"] = "; ".join(reasons)
        summary = planner.plan_summary(name, current_plan)
        if not summary and current_plan:
            first, last = current_plan[0], current_plan[-1]
            summary = (f"{name}, you have {len(current_plan)} clash-free "
                       f"talks planned today, starting at {first['starts']} "
                       f"with \"{first['title']}\" ({first['room']}) and "
                       f"wrapping up at {last['starts']} with "
                       f"\"{last['title']}\" ({last['room']}).")
            source = "template"
        else:
            from agents import llm
            cfg = llm.config()
            source = f"llm:{cfg['provider']}:{cfg['model']}" if summary else "empty"
        return {"person_id": person_id, "name": name,
                "summary": summary or "", "source": source,
                "talk_count": len(current_plan)}
    return guard(_run)


def _talk_row(g, talk_id):
    res = g.query(
        "MATCH (t:Talk {id: $tid}) RETURN t.title, t.starts, t.ends",
        {"tid": talk_id})
    if not res.result_set:
        return None
    title, starts, ends = res.result_set[0]
    return {"id": talk_id, "title": title, "starts": starts, "ends": ends}


@app.post("/api/plan/{person_id}/add")
def plan_add(person_id: str, change: PlanChangeIn):
    """Add a talk to the plan. Refuses, in plain words, when it clashes."""
    def _run():
        g = graph()
        talk = _talk_row(g, change.talk_id)
        if talk is None:
            raise HTTPException(status_code=404,
                                detail=f"No talk with id {change.talk_id}")
        for pick in queries.planned_talks(g, person_id):
            if pick["id"] == change.talk_id:
                return {"added": True, "talk_id": change.talk_id,
                        "note": "already in your plan"}
            if talk["starts"] < pick["ends"] and \
                    pick["starts"] < talk["ends"]:
                other = _talk_row(g, pick["id"]) or pick
                raise HTTPException(
                    status_code=409,
                    detail=(f"That clashes with {other['title']} "
                            f"({pick['starts']}-{pick['ends']}), which is "
                            f"already in your plan. Drop that one first "
                            f"if you would rather swap."))
        if not queries.plan_talk(g, person_id, change.talk_id):
            raise HTTPException(status_code=409,
                                detail="That talk clashes with your plan.")
        return {"added": True, "talk_id": change.talk_id}
    return guard(_run)


@app.post("/api/plan/{person_id}/drop")
def plan_drop(person_id: str, change: PlanChangeIn):
    """Remove a talk from the plan."""
    def _run():
        g = graph()
        res = g.query(
            "MATCH (:Person {id: $pid})-[r:PLANNED]->(t:Talk {id: $tid}) "
            "RETURN count(r)", {"pid": person_id, "tid": change.talk_id})
        existed = bool(res.result_set and res.result_set[0][0])
        g.query(
            "MATCH (:Person {id: $pid})-[r:PLANNED]->(t:Talk {id: $tid}) "
            "DELETE r", {"pid": person_id, "tid": change.talk_id})
        return {"dropped": existed, "talk_id": change.talk_id}
    return guard(_run)


@app.get("/api/matchmake/{person_id}")
def matchmake_ep(person_id: str):
    def _run():
        g = graph()
        return {"matches": matchmaker.suggest(g, person_id)}
    return guard(_run)


@app.post("/api/intro/draft")
def intro_draft_ep(req: IntroDraftIn):
    """Draft an intro grounded in graph evidence and park it at the human
    approval gate before anything is sent."""
    def _run():
        g = graph()
        res = g.query(
            "MATCH (p:Person {id: $pid}) RETURN p.name",
            {"pid": req.person_id})
        my_name = res.result_set[0][0] if res.result_set else req.person_id
        matches = matchmaker.suggest(g, req.person_id, limit=25)
        target = next((m for m in matches if m["person_id"] == req.other_id),
                      None)
        if target is None:
            res_o = g.query(
                "MATCH (p:Person {id: $oid}) RETURN p.name, p.company",
                {"oid": req.other_id})
            if not res_o.result_set:
                raise HTTPException(
                    status_code=404,
                    detail=f"No person with id {req.other_id}")
            oname, ocomp = res_o.result_set[0]
            target = {
                "person_id": req.other_id, "name": oname, "company": ocomp,
                "shared_topics": [], "speaking_on": [],
                "icebreaker": queries.icebreaker(g, req.person_id, req.other_id),
            }
        draft, source = matchmaker.intro_draft_with_source(my_name, target)
        verdict = matchmaker.request_approval(draft, noninteractive=True)
        return {
            "person_id": req.person_id,
            "other_id": req.other_id,
            "recipient": target.get("name"),
            "draft": draft,
            "source": source,
            "approval": verdict,
        }
    return guard(_run)


@app.get("/api/met/{person_id}")
def met(person_id: str):
    def _run():
        g = graph()
        return {"met": queries.met_list(g, person_id)}
    return guard(_run)


@app.post("/api/met")
def record(meeting: MeetingIn):
    def _run():
        g = graph()
        return queries.record_meeting(g, meeting.a, meeting.b,
                                      meeting.note, meeting.at)
    return guard(_run)


@app.get("/api/company/{company}")
def company_directory(company: str):
    """Everyone who works at a given company in the conference graph."""
    def _run():
        g = graph()
        return {"company": company,
                "people": queries.people_by_company(g, company)}
    return guard(_run)


@app.get("/api/speaker/{person_id}/talks")
def speaker_talks(person_id: str):
    """Talks a speaker gives, in day order."""
    def _run():
        g = graph()
        return {"person_id": person_id,
                "talks": queries.talks_by_speaker(g, person_id)}
    return guard(_run)


@app.post("/api/scout/refresh")
def refresh():
    def _run():
        g = graph()
        report = scout.refresh(g)
        LAST_REFRESH.update(report)
        return report
    return guard(_run)


@app.post("/api/demo/reset")
def demo_reset(person_id: str = "rene"):
    """Reset the graph to fresh stage-start state and rebuild the plan."""
    def _run():
        g = graph()
        counts = seed.seed(g, fresh=True)
        built = planner.build_plan(g, person_id)
        LAST_REFRESH.update({"source": None, "upserted": 0, "changes": []})
        return {"reset": True, "counts": counts, "planned": len(built)}
    return guard(_run)


@app.get("/api/changes")
def changes():
    """The last Scout refresh: what moved, in plain lines."""
    return dict(LAST_REFRESH)

