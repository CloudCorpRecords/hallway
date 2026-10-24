"""Smoke tests for the Hallway graph layer.

Runs against a real FalkorDB at FALKORDB_URL (default redis://localhost:6379)
using a scratch graph so the demo graph is never touched.

    python tests/test_smoke.py     # standalone, prints results
    pytest tests/test_smoke.py     # same assertions under pytest
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from graph import queries, seed  # noqa: E402

SCRATCH = "hallway_smoke"


def fresh_graph():
    g = seed.connect(graph_name=SCRATCH)
    seed.seed(g, fresh=True)
    return g


def test_matchmake_returns_a_three_hop_path():
    g = fresh_graph()
    matches = queries.matchmake(g, "rene")
    assert matches, "matchmake returned nobody"
    best = max(p["hops"] for m in matches for p in m["paths"])
    assert best >= 3, f"longest matchmaking path is {best} hops, want >= 3"
    names = {m["name"] for m in matches}
    assert "Tom Alvarez" not in names, "already met Tom, memory must exclude him"


def test_talks_for_is_clash_free_against_plan():
    g = fresh_graph()
    assert queries.plan_talk(g, "rene", "t1")  # 09:30-10:15, Main Stage
    talks = queries.talks_for(g, "rene")
    ids = {t["id"] for t in talks}
    assert "t2" not in ids, "t2 runs 09:30-10:15 and must clash with planned t1"
    assert "t3" in ids, "t3 at 10:30 is interest matched and clash free"
    picks = queries.planned_talks(g, "rene")
    for a in picks:
        for b in picks:
            if a["id"] < b["id"]:
                assert not (a["starts"] < b["ends"] and b["starts"] < a["ends"]), \
                    f"planned talks clash: {a} vs {b}"


def test_meeting_memory_round_trip():
    g = fresh_graph()
    before = {m["person_id"] for m in queries.met_list(g, "rene")}
    assert "tom-alvarez" in before  # seeded breakfast memory
    queries.record_meeting(g, "rene", "maya-chen",
                           "Met after her MCP talk. Swapped notes on tool "
                           "server auth.", at="10:20")
    after = {m["person_id"]: m for m in queries.met_list(g, "rene")}
    assert "maya-chen" in after
    assert "tool server auth" in after["maya-chen"]["note"]
    names = {m["name"] for m in queries.matchmake(g, "rene")}
    assert "Maya Chen" not in names, "once met, Matchmaker must stop suggesting"


def main():
    tests = [test_matchmake_returns_a_three_hop_path,
             test_talks_for_is_clash_free_against_plan,
             test_meeting_memory_round_trip]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("SMOKE OK: 3/3 graph smoke tests passed")


if __name__ == "__main__":
    main()
