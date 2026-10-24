"""Planner: builds the attendee's day from interest matched, clash free talks,
and repairs it when Scout reports the schedule moved underneath it.
"""

from graph import queries


def build_plan(g, person_id):
    """Pick the best talk in every slot. Returns the planned talks in order,
    each carrying its why: the interest reasons Planner picked it."""
    queries.clear_plan(g, person_id)
    for talk in queries.talks_for(g, person_id):
        queries.plan_talk(g, person_id, talk["id"])
    planned_ids = {p["id"] for p in queries.planned_talks(g, person_id)}
    plan = [t for t in queries.talks_for(g, person_id)
            if t["id"] in planned_ids]
    for talk in plan:
        reasons = talk.get("reasons") or [
            f"matches your interest in {name}" for name in talk["topics"]]
        talk["why"] = "; ".join(reasons)
    return plan


def repair_plan(g, person_id):
    """Rebuild after a schedule change. Reports what the repair cost."""
    before = {p["id"] for p in queries.planned_talks(g, person_id)}
    after_talks = build_plan(g, person_id)
    after = {t["id"] for t in after_talks}
    return {
        "plan": after_talks,
        "kept": sorted(before & after),
        "dropped": sorted(before - after),
        "added": sorted(after - before),
    }
