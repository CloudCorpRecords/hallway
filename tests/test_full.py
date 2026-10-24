"""Full test suite for the Hallway graph, agents and Scout.

Runs against a real FalkorDB at FALKORDB_URL (default redis://localhost:6379)
using scratch graphs so the demo graph is never touched.

    python tests/test_full.py     # standalone, PASS/FAIL per test + summary
    pytest tests/test_full.py     # same assertions under pytest
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from graph import queries, seed  # noqa: E402
from agents import matchmaker, planner, scout  # noqa: E402

SCRATCH = "hallway_full"
SCOUT_GRAPH = "hallway_full_scout"
REPAIR_GRAPH = "hallway_full_repair"

RENE_INTERESTS = {"MCP", "AI Agents", "Developer Tools", "Rust"}


def fresh_graph(name=SCRATCH):
    g = seed.connect(graph_name=name)
    seed.seed(g, fresh=True)
    return g


def _no_clashes(talks):
    for a in talks:
        for b in talks:
            if a["id"] < b["id"]:
                assert not (a["starts"] < b["ends"]
                            and b["starts"] < a["ends"]), \
                    f"talks clash: {a['id']} vs {b['id']}"


# ---------- seed ----------

def test_seed_is_rich_and_deterministic():
    g = seed.connect(graph_name=SCRATCH)
    counts = seed.seed(g, fresh=True)
    assert counts["people"] == len(seed.PEOPLE) >= 17, counts
    assert counts["talks"] == len(seed.TALKS) >= 18, counts
    assert counts["topics"] == 9, counts
    assert counts["meetings"] == 1, counts
    again = seed.seed(g, fresh=True)
    assert again == counts, "seeding must be deterministic"
    # at least two talks share a speaker (Maya gives three)
    assert len(queries.talks_by_speaker(g, "maya-chen")) >= 3
    # the keynote has broad appeal: it matches very different people
    for pid in ("rene", "sam-okafor", "grace-muli"):
        ids = {t["id"] for t in queries.talks_for(g, pid)}
        assert "t0" in ids, f"keynote missing from talks_for({pid})"


# ---------- matchmake ----------

def test_matchmake_ranking_and_memory_exclusion():
    g = fresh_graph()
    matches = queries.matchmake(g, "rene", limit=10)
    assert len(matches) >= 5, f"only {len(matches)} matches"
    scores = [m["score"] for m in matches]
    assert scores == sorted(scores, reverse=True), "ranking must descend"
    names = {m["name"] for m in matches}
    assert "Maya Chen" in names
    assert "Tom Alvarez" not in names, "met at breakfast: memory excludes"
    for m in matches:
        assert m["shared_topics"] or m["speaking_on"], \
            f"{m['name']} suggested with no evidence"


def test_matchmake_paths_are_real():
    g = fresh_graph()
    matches = queries.matchmake(g, "rene", limit=10)
    best = 0
    for m in matches:
        assert m["paths"], f"{m['name']} has no proving path"
        for p in m["paths"]:
            assert "Person(Rene Turcios)" in p["text"]
            best = max(best, p["hops"])
    assert best >= 3, f"longest path is {best} hops, want >= 3"


# ---------- talks_for and explanations ----------

def test_talks_for_carries_reasons():
    g = fresh_graph()
    talks = queries.talks_for(g, "rene")
    assert talks, "no talks matched"
    assert "t0" in {t["id"] for t in talks}, "keynote should match"
    for t in talks:
        assert t["topics"], f"{t['id']} has no matched topics"
        assert set(t["topics"]) <= RENE_INTERESTS, t
        assert t["reasons"], f"{t['id']} has no explanation"
        for reason in t["reasons"]:
            assert reason.startswith("matches your interest in "), reason
            assert reason.rsplit(" ", 1)[-1] or True  # shape check only
        assert {r.replace("matches your interest in ", "")
                for r in t["reasons"]} == set(t["topics"])


def test_talks_for_clash_rules():
    g = fresh_graph()
    assert queries.plan_talk(g, "rene", "t15")  # 14:00-14:45, Main Stage
    ids = {t["id"] for t in queries.talks_for(g, "rene")}
    assert "t8" not in ids, "t8 runs 14:00-14:45, clashes with planned t15"
    assert "t9" in ids, "t9 starts when t15 ends: no clash"
    assert not queries.plan_talk(g, "rene", "t8"), \
        "plan_talk must refuse a clashing talk"
    assert queries.plan_talk(g, "rene", "t15"), \
        "re-planning the same talk is not a clash"


# ---------- directory queries ----------

def test_people_by_company():
    g = fresh_graph()
    github = queries.people_by_company(g, "GitHub")
    assert {p["person_id"] for p in github} == {"maya-chen", "lena-fischer"}
    for p in github:
        assert p["handle"].startswith("@")
        assert p["kind"] in ("speaker", "attendee")
    assert queries.people_by_company(g, "No Such Company") == []


def test_talks_by_speaker():
    g = fresh_graph()
    maya = queries.talks_by_speaker(g, "maya-chen")
    assert {"t1", "t6", "t12"} <= {t["id"] for t in maya}
    starts = [t["starts"] for t in maya]
    assert starts == sorted(starts), "talks must come back in day order"
    nina = queries.talks_by_speaker(g, "nina-petrova")
    assert {t["id"] for t in nina} == {"t13", "t16"}
    assert queries.talks_by_speaker(g, "grace-muli") == [], \
        "attendees give no talks"


# ---------- icebreakers ----------

def test_icebreaker_from_shared_path():
    g = fresh_graph()
    ib = queries.icebreaker(g, "rene", "maya-chen")
    assert ib["topic"] == "MCP", ib
    assert ib["talk"] and ib["talk"]["id"] == "t1", ib
    assert "Maya" in ib["line"] and "MCP" in ib["line"]
    assert "MCP in Production" in ib["line"]
    assert queries.icebreaker(g, "rene", "maya-chen") == ib, \
        "icebreakers must be deterministic"


def test_icebreaker_fallbacks():
    g = fresh_graph()
    # shared interest, but Grace gives no talks: the topic branch
    ib = queries.icebreaker(g, "rene", "grace-muli")
    assert ib["talk"] is None and ib["topic"] == "AI Agents", ib
    assert "Grace" in ib["line"] and "AI Agents" in ib["line"]
    # nothing shared, no connecting talk: the plain fallback
    ib = queries.icebreaker(g, "ben-kowalski", "omar-haddad")
    assert ib["topic"] is None and ib["talk"] is None, ib
    assert ib["line"].startswith("Ask Omar"), ib


# ---------- planner ----------

def test_planner_builds_explained_clash_free_plan():
    g = fresh_graph()
    plan = planner.build_plan(g, "rene")
    assert len(plan) >= 8, f"plan has {len(plan)} talks"
    _no_clashes(plan)
    ids = {t["id"] for t in plan}
    assert {"t0", "t1"} <= ids
    for t in plan:
        assert t.get("why"), f"{t['id']} planned without a reason"
        assert "interest" in t["why"]


def test_planner_repair_after_scout_refresh():
    g = fresh_graph(REPAIR_GRAPH)
    before = {t["id"] for t in planner.build_plan(g, "rene")}
    report = scout.refresh(g)
    assert len(report["changes"]) == 2, report["changes"]
    repair = planner.repair_plan(g, "rene")
    after = {t["id"] for t in repair["plan"]}
    _no_clashes(repair["plan"])
    assert set(repair["kept"]) | set(repair["dropped"]) == before
    assert set(repair["kept"]) | set(repair["added"]) == after
    t6 = next(t for t in repair["plan"] if t["id"] == "t6")
    assert t6["room"] == "Workshop 2", "repair must use the moved room"


# ---------- scout ----------

def test_scout_detects_fixture_changes():
    g = fresh_graph(SCOUT_GRAPH)
    report = scout.refresh(g)
    assert report["upserted"] == 12, report
    assert len(report["changes"]) == 2, report["changes"]
    joined = " | ".join(report["changes"])
    assert "t6" in joined and "Workshop 2" in joined
    assert "t11" in joined and "16:30" in joined
    again = scout.refresh(g)
    assert again["changes"] == [], "second refresh must find nothing new"


# ---------- matchmaker agent and memory ----------

def test_matchmaker_suggests_with_icebreakers_and_remembers():
    g = fresh_graph()
    matches = matchmaker.suggest(g, "rene")
    assert matches, "no suggestions"
    for m in matches:
        assert m.get("icebreaker"), f"{m['name']} has no icebreaker"
        assert m["icebreaker"]["line"], "empty icebreaker line"
    top = matches[0]
    queries.record_meeting(g, "rene", top["person_id"],
                           "Test meeting in the hallway.", at="12:05")
    names = {m["person_id"] for m in matchmaker.suggest(g, "rene")}
    assert top["person_id"] not in names, \
        "once met, Matchmaker must stop suggesting"
    met = {m["person_id"]: m for m in queries.met_list(g, "rene")}
    assert met[top["person_id"]]["note"] == "Test meeting in the hallway."


def test_record_meeting_normalizes_blank_at():
    import re
    g = fresh_graph()
    for blank in ("", "   ", None):
        saved = queries.record_meeting(g, "rene", "diego-fuentes",
                                       "Blank timestamp check.", at=blank)
        assert re.fullmatch(r"\d{2}:\d{2}", saved["at"]), \
            f"blank at={blank!r} was not normalized, got {saved['at']!r}"
    trimmed = queries.record_meeting(g, "rene", "diego-fuentes",
                                     "Trim check.", at=" 12:40 ")
    assert trimmed["at"] == "12:40", f"at was not trimmed: {trimmed['at']!r}"
    met = queries.met_list(g, "rene")
    assert all(m["at"] for m in met), "met_list carries an empty timestamp"
    stamps = [m["at"] for m in met]
    assert stamps == sorted(stamps), "met_list is not sorted by timestamp"


def test_met_list_seeded_memory():
    g = fresh_graph()
    met = queries.met_list(g, "rene")
    assert len(met) == 1
    assert met[0]["person_id"] == "tom-alvarez"
    assert "breakfast" in met[0]["note"].lower()


TESTS = [
    test_seed_is_rich_and_deterministic,
    test_matchmake_ranking_and_memory_exclusion,
    test_matchmake_paths_are_real,
    test_talks_for_carries_reasons,
    test_talks_for_clash_rules,
    test_people_by_company,
    test_talks_by_speaker,
    test_icebreaker_from_shared_path,
    test_icebreaker_fallbacks,
    test_planner_builds_explained_clash_free_plan,
    test_planner_repair_after_scout_refresh,
    test_scout_detects_fixture_changes,
    test_matchmaker_suggests_with_icebreakers_and_remembers,
    test_record_meeting_normalizes_blank_at,
    test_met_list_seeded_memory,
]

# The LLM provider layer tests (tests/test_llm.py) are mocked-transport
# only, so they belong in the full suite: the fallback guarantees they pin
# down are part of the demo contract.
from tests.test_llm import TESTS as LLM_TESTS  # noqa: E402

TESTS = TESTS + LLM_TESTS


def main():
    passed, failed = 0, []
    for test in TESTS:
        try:
            test()
            passed += 1
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failed.append(test.__name__)
            print(f"FAIL {test.__name__}: {exc}")
    for name in (SCRATCH, SCOUT_GRAPH, REPAIR_GRAPH):
        try:
            seed.connect(graph_name=name).delete()
        except Exception:
            pass
    print(f"FULL SUITE: {passed}/{len(TESTS)} tests passed, "
          f"{len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
