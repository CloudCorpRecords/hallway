"""Hallway agent runner: one entry point, three execution modes, in order:

1. TrueForge mode: if the TrueForge / truefoundry SDK is importable
   (agents/trueforge_adapter.py), the run is annotated as harness ready.
   At the venue the harness executes this same loop with MCP tools, sandbox
   and the approval gate. The graph work is identical either way.
2. Local LLM mode: if OPENAI_API_KEY is set, the openai package adds a short
   natural language summary on top of the deterministic results.
3. Deterministic demo mode (default offline): walks Scout, Planner and
   Matchmaker over the graph with no LLM at all. This is the mode that must
   never fail on stage.

Usage: python -m agents.runner [--person rene] [--noninteractive]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from graph import queries, seed  # noqa: E402
from agents import matchmaker, planner, scout, trueforge_adapter  # noqa: E402


def _person_name(g, person_id):
    res = g.query("MATCH (p:Person {id: $id}) RETURN p.name",
                  {"id": person_id})
    return res.result_set[0][0] if res.result_set else person_id


def _ensure_seeded(g):
    res = g.query("MATCH (p:Person) RETURN count(p)")
    if res.result_set and res.result_set[0][0] == 0:
        seed.seed(g)
        print("(graph was empty: seeded the sample conference)")


def _llm_summary(person, plan, matches):
    """Optional OpenAI polish. Returns None on any problem, by design."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        plan_txt = "; ".join(f"{t['starts']} {t['title']}" for t in plan[:4])
        match_txt = "; ".join(m["name"] for m in matches[:3])
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content":
                       f"In two short sentences, brief {person} on their "
                       f"conference day. Talks: {plan_txt}. People to meet: "
                       f"{match_txt}."}],
            max_tokens=120,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:  # never let polish break the demo
        print(f"(OpenAI summary skipped: {exc})")
        return None


def main():
    parser = argparse.ArgumentParser(description="Run the Hallway agents")
    parser.add_argument("--person", default="rene")
    parser.add_argument("--noninteractive", action="store_true")
    args = parser.parse_args()
    if args.noninteractive:
        os.environ["HALLWAY_NONINTERACTIVE"] = "1"

    tf = trueforge_adapter.describe()
    print(f"Agent harness: {tf['sdk'] or 'local fallback'} ({tf['note']})")

    g = seed.connect()
    _ensure_seeded(g)
    me = _person_name(g, args.person)

    print("\n== Scout: refresh conference data ==")
    report = scout.refresh(g)
    print(f"source: {report['source']} | upserted: {report['upserted']}")
    for change in report["changes"]:
        print(f"  change: {change}")

    print("\n== Planner: repair and rebuild the day ==")
    repair = planner.repair_plan(g, args.person)
    for t in repair["plan"]:
        print(f"  {t['starts']}-{t['ends']}  {t['title']}  ({t['room']})")
        if t.get("why"):
            print(f"    why: {t['why']}")
    if repair["dropped"]:
        print(f"  dropped after schedule change: {repair['dropped']}")

    print("\n== Matchmaker: who to meet, and why (the path is the reason) ==")
    matches = matchmaker.suggest(g, args.person)
    for m in matches:
        print(f"  {m['name']} ({m['company']}) score {m['score']}")
        for p in m["paths"][:1]:
            print(f"    path: {p['text']}")
        if m.get("icebreaker"):
            print(f"    icebreaker: {m['icebreaker']['line']}")

    print("\n== Memory: who I already met ==")
    for met in queries.met_list(g, args.person):
        print(f"  {met['name']} at {met['at']}: {met['note']}")

    if matches:
        draft = matchmaker.draft_intro(me, matches[0])
        verdict = matchmaker.request_approval(
            draft, noninteractive=args.noninteractive)
        print(f"\n== Intro approval ==\n  draft: {draft}")
        print(f"  verdict: {verdict}")

    summary = _llm_summary(me, repair["plan"], matches)
    if summary:
        print(f"\n== Assistant summary (OpenAI) ==\n  {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
