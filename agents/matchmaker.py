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
from agents import llm, trueforge_adapter

PENDING = Path(__file__).parent.parent / ".runtime" / "pending_intros.json"


def suggest(g, person_id, limit=5):
    """Ranked suggestions, each with an icebreaker built from its path."""
    matches = queries.matchmake(g, person_id, limit=limit)
    for match in matches:
        match["icebreaker"] = queries.icebreaker(
            g, person_id, match["person_id"])
    return matches


def _template_intro(my_name, match):
    """The deterministic intro, grounded in the match evidence. This is
    the fallback whenever no LLM provider is configured or the call fails,
    so the demo path never depends on a network call."""
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


def _llm_intro(my_name, match):
    """The intro drafted by the configured LLM provider, or None."""
    if not llm.configured():
        return None
    first = (match["name"] or "there").split()[0]
    facts = []
    if match.get("speaking_on"):
        facts.append(f"{first} is speaking on: {match['speaking_on'][0]}.")
    if match.get("shared_topics"):
        facts.append("Shared topics: "
                     + ", ".join(match["shared_topics"]) + ".")
    icebreaker = match.get("icebreaker") or {}
    if icebreaker.get("line"):
        facts.append("Icebreaker from the graph path: "
                     + icebreaker["line"])
    messages = [
        {"role": "system",
         "content": "You draft short, warm conference intro messages. "
                    "Three sentences at most. Plain words, no hype, "
                    "no invented facts. The sender is an attendee; "
                    "when a talk is named, the other person is its "
                    "speaker, not the sender."},
        {"role": "user",
         "content": (f"Draft an intro message from {my_name} to "
                     f"{match['name']} of {match.get('company', '')}. "
                     + " ".join(facts)
                     + " End by asking if they are up for a quick "
                       "hallway chat today.")},
    ]
    # 600, not a tight budget: glm-5p3-flash spends reasoning tokens
    # against max_tokens before any content appears (see agents/llm.py).
    return llm.chat(messages, max_tokens=600)


def intro_draft_with_source(my_name, match):
    """(draft, source): the LLM draft when a provider answers, else the
    deterministic template. Source names which one produced the text,
    e.g. "llm:fireworks:accounts/fireworks/models/glm-5p3-flash" or
    "template"."""
    text = _llm_intro(my_name, match)
    if text:
        cfg = llm.config()
        return text, f"llm:{cfg['provider']}:{cfg['model']}"
    return _template_intro(my_name, match), "template"


def draft_intro(my_name, match):
    """A short intro grounded in the match evidence: LLM drafted when a
    provider is configured, deterministic template otherwise."""
    return intro_draft_with_source(my_name, match)[0]


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
