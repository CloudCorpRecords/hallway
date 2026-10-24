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
from agents import planner, scout  # noqa: E402

app = FastAPI(title="Hallway")
STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


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


@app.get("/api/matchmake/{person_id}")
def matchmake(person_id: str):
    def _run():
        g = graph()
        return {"matches": queries.matchmake(g, person_id)}
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


@app.post("/api/scout/refresh")
def refresh():
    def _run():
        g = graph()
        return scout.refresh(g)
    return guard(_run)
