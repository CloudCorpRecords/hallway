"""Matchmaker: suggests who to meet, shows the graph path as the reason,
remembers who was already met, and drafts intros that stop at a human
approval gate before anything is sent.

Approval is an adapter (see agents/trueforge_adapter.py):
- TrueForge present: the draft is parked as a pending approval for the
  harness approval gate (recorded in .runtime/pending_intros.json).
- Otherwise, interactive: a console y/n prompt.
- Non-interactive (HALLWAY_NONINTERACTIVE=1 or --noninteractive): never
  blocks, never sends, reports the draft as awaiting approval.
"""

import json
import os
from pathlib import Path

from graph import queries
from agents import trueforge_adapter

PENDING = Path(__file__).parent.parent / ".runtime" / "pending_intros.json"


def suggest(g, person_id, limit=5):
    """Ranked suggestions, each with an icebreaker built from its path."""
    matches = queries.matchmake(g, person_id, limit=limit)
    for match in matches:
        match["icebreaker"] = queries.icebreaker(
            g, person_id, match["person_id"])
    return matches


def draft_intro(my_name, match):
    """A short intro grounded in the match evidence. Deterministic on purpose:
    the LLM polish step, when a key exists, happens in the runner."""
    first = (match["name"] or "there").split()[0]
    if match.get("speaking_on"):
        reason = f"You are speaking on {match['speaking_on'][0]}, which is "
        reason += "right in the middle of what I am building."
    elif match.get("shared_topics"):
        reason = f"We are both here for {match['shared_topics'][0]}."
    else:
        reason = "Your work looks close to what I am building."
    return (f"Hi {first}, I am {my_name}. {reason} "
            f"Would you be up for a quick hallway chat today?")


def request_approval(draft, noninteractive=False):
    """Returns {approved: True/False/None, channel: str}. None means pending."""
    if trueforge_adapter.available():
        PENDING.parent.mkdir(parents=True, exist_ok=True)
        parked = []
        if PENDING.exists():
            parked = json.loads(PENDING.read_text())
        parked.append({"draft": draft, "status": "pending"})
        PENDING.write_text(json.dumps(parked, indent=2))
        return {"approved": None, "channel": "trueforge-approval-gate"}
    if noninteractive or os.environ.get("HALLWAY_NONINTERACTIVE"):
        return {"approved": False, "channel": "console-skipped-noninteractive"}
    try:
        answer = input(f"\nSend this intro? [y/N]\n{draft}\n> ").strip().lower()
    except EOFError:
        return {"approved": False, "channel": "console-eof"}
    return {"approved": answer == "y", "channel": "console"}
