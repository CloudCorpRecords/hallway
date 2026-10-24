"""Planner: builds the attendee's day from interest matched, clash free talks,
and repairs it when Scout reports the schedule moved underneath it.

plan_summary() is the one LLM touch: when a provider is configured
(agents/llm.py), the model writes a short natural language summary of the
plan. Without a provider, or on any call failure, it returns None and the
caller shows the plan itself, unchanged.
"""

from graph import queries
from agents import llm


def build_plan(g, person_id):
    """Pick the best talk per slot. Returns the planned talks in order,
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


def plan_summary(person_name, plan):
    """A two or three sentence summary of the plan from the configured
    LLM provider, or None when no provider is configured, the plan is
    empty, or the call fails."""
    if not plan or not llm.configured():
        return None
    lines = "; ".join(
        f"{t['starts']} {t['title']} in {t['room']}"
        + (f" ({t['why']})" if t.get("why") else "")
        for t in plan)
    messages = [
        {"role": "system",
         "content": "You brief conference attendees on their day. "
                    "Two or three short sentences. Plain words, "
                    "no invented facts."},
        {"role": "user",
         "content": (f"Brief {person_name} on their conference day. "
                     f"Their planned talks, in order: {lines}. "
                     "Mention the shape of the day, not every talk.")},
    ]
    # 600, not a tight budget: glm-5p3-flash spends reasoning tokens
    # against max_tokens before any content appears (see agents/llm.py).
    return llm.chat(messages, max_tokens=600)
