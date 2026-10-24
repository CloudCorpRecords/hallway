"""API test suite for the Hallway board endpoints (app/main.py).

Runs against a scratch graph (HALLWAY_GRAPH=hallway_api_test) so the live
demo graph is never modified.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from graph import seed  # noqa: E402

API_GRAPH = "hallway_api_test"


def _with_scratch(fn):
    prev = os.environ.get("HALLWAY_GRAPH")
    os.environ["HALLWAY_GRAPH"] = API_GRAPH
    try:
        c = TestClient(app)
        return fn(c)
    finally:
        if prev is None:
            os.environ.pop("HALLWAY_GRAPH", None)
        else:
            os.environ["HALLWAY_GRAPH"] = prev
        try:
            seed.connect(graph_name=API_GRAPH).delete()
        except Exception:
            pass


def test_api_reset_and_board_endpoints():
    def _run(c):
        # 1. Stage reset seeds and builds plan
        r = c.post("/api/demo/reset?person_id=rene")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["reset"] is True
        assert body["counts"]["people"] == 18
        assert body["planned"] == 11

        # 2. Health and talks
        h = c.get("/api/health").json()
        assert h["ok"] is True and h["graph"] == API_GRAPH
        talks = c.get("/api/talks").json()["talks"]
        assert len(talks) == 19

        # 3. Plan summary
        summary = c.get("/api/plan/rene/summary").json()
        assert summary["talk_count"] == 11
        assert summary["summary"]

        # 4. Clash refusal on add, then drop + add succeeds
        clash = c.post("/api/plan/rene/add", json={"talk_id": "t2"})
        assert clash.status_code == 409
        assert "clashes with" in clash.json()["detail"]

        drop = c.post("/api/plan/rene/drop", json={"talk_id": "t1"})
        assert drop.status_code == 200 and drop.json()["dropped"] is True

        added = c.post("/api/plan/rene/add", json={"talk_id": "t2"})
        assert added.status_code == 200 and added.json()["added"] is True

        # 5. Intro draft with approval gate
        intro = c.post("/api/intro/draft",
                       json={"person_id": "rene", "other_id": "diego-fuentes"})
        assert intro.status_code == 200, intro.text
        ibody = intro.json()
        assert "Diego" in ibody["draft"]
        assert ibody["approval"]["approved"] in (None, False)

        # 6. Company and speaker directory
        gh = c.get("/api/company/GitHub").json()
        assert {p["person_id"] for p in gh["people"]} == {
            "maya-chen", "lena-fischer"}
        sp = c.get("/api/speaker/maya-chen/talks").json()
        assert len(sp["talks"]) >= 3

        # 7. Record meeting removes Diego from matchmaking
        met_r = c.post("/api/met", json={
            "a": "rene", "b": "diego-fuentes",
            "note": "Met at the Rust booth.", "at": "10:35"
        })
        assert met_r.status_code == 200
        matches = c.get("/api/matchmake/rene").json()["matches"]
        assert all(m["person_id"] != "diego-fuentes" for m in matches)
        met_list = c.get("/api/met/rene").json()["met"]
        assert any(m["person_id"] == "diego-fuentes" for m in met_list)

    _with_scratch(_run)
