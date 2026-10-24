"""Live LLM check. NOT part of the default suite.

Runs the real intro-draft and plan-summary paths for the top match through
the local Fireworks credential proxy (fw-proxy.py on 127.0.0.1:8791), so
no real key ever sits in the environment: FIREWORKS_API_KEY=proxy and
FIREWORKS_BASE_URL=http://127.0.0.1:8791/inference/v1. The model is
accounts/fireworks/models/glm-5p3-flash. Start the proxy first:

    python3 ~/workspace/custom-connectors/custom.fireworks/bin/fw-proxy.py

Then:

    python tests/live_llm_check.py [--person rene]

Uses its own scratch graph (hallway_livecheck) and deletes it afterwards.
Exits 0 only when the LLM actually answered both calls; a deterministic
fallback result is reported and exits 1, because the point of this script
is proving the live path, not the fallback.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("HALLWAY_LLM_PROVIDER", "fireworks")
os.environ.setdefault("FIREWORKS_API_KEY", "proxy")
os.environ.setdefault("FIREWORKS_BASE_URL",
                      "http://127.0.0.1:8791/inference/v1")

from graph import seed  # noqa: E402
from agents import llm, matchmaker, planner  # noqa: E402

SCRATCH = "hallway_livecheck"


def person_name(g, person_id):
    res = g.query("MATCH (p:Person {id: $id}) RETURN p.name",
                  {"id": person_id})
    return res.result_set[0][0] if res.result_set else person_id


def main():
    parser = argparse.ArgumentParser(description="Live LLM check")
    parser.add_argument("--person", default="rene")
    args = parser.parse_args()

    print(f"provider: {llm.describe()}")
    if not llm.configured():
        print("LIVE CHECK FAILED: no provider configured")
        return 1

    g = seed.connect(graph_name=SCRATCH)
    try:
        seed.seed(g, fresh=True)
        me = person_name(g, args.person)
        matches = matchmaker.suggest(g, args.person)
        if not matches:
            print("LIVE CHECK FAILED: no matches to draft for")
            return 1
        top = matches[0]
        print(f"top match: {top['name']} ({top['company']}) "
              f"score {top['score']}")

        template = matchmaker._template_intro(me, top)
        print(f"\ndeterministic template draft:\n  {template}")

        draft, source = matchmaker.intro_draft_with_source(me, top)
        print(f"\nintro draft (source: {source}):\n  {draft}")

        plan = planner.build_plan(g, args.person)
        summary = planner.plan_summary(me, plan)
        print(f"\nplan summary:\n  {summary}")

        ok = source.startswith("llm:fireworks:") and bool(summary)
        print(f"\nLIVE CHECK: {'OK' if ok else 'FAILED'} "
              f"(intro source {source}, summary "
              f"{'present' if summary else 'missing'})")
        return 0 if ok else 1
    finally:
        try:
            g.delete()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
