"""Integrity tests for the seed conference data (graph/seed.py).

The graph tests (test_smoke, test_full, test_api) prove the seeded data
behaves once it is in FalkorDB, but they need a live database. The data
itself is plain Python constants, and most seed breakage is a data typo:
a talk naming a speaker who does not exist, an interest pointing at a
topic that is not in TOPICS, two talks sharing an id, a talk that ends
before it starts, a meeting between people who are not seeded. Those
break the demo just as hard and can be caught offline in milliseconds.

    pytest tests/test_seed_data.py     # no FalkorDB needed
"""

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from graph import seed  # noqa: E402

PEOPLE_IDS = {p[0] for p in seed.PEOPLE}
TALK_IDS = [t[0] for t in seed.TALKS]


def test_counts_match_what_the_api_suite_expects():
    # tests/test_api.py asserts 18 people and 19 talks over HTTP; pin the
    # constants here so a seed edit fails fast and offline first.
    assert len(seed.PEOPLE) == 18
    assert len(seed.TALKS) == 19
    assert len(seed.TOPICS) == 9
    assert seed.MEETINGS, "the seeded breakfast memory must exist"


def test_ids_are_unique():
    assert len(PEOPLE_IDS) == len(seed.PEOPLE), "duplicate person id"
    assert len(set(TALK_IDS)) == len(TALK_IDS), "duplicate talk id"
    assert len(set(seed.TOPICS)) == len(seed.TOPICS), "duplicate topic"
    assert len(set(seed.ROOMS)) == len(seed.ROOMS), "duplicate room"


def test_people_rows_are_well_formed():
    for pid, name, kind, company, handle in seed.PEOPLE:
        assert pid and name and company, f"blank field in person {pid}"
        assert kind in ("speaker", "attendee"), f"{pid}: bad kind {kind}"
        assert handle.startswith("@"), f"{pid}: handle {handle} lacks @"


def test_interests_reference_real_people_and_topics():
    for pid, topic, weight in seed.INTERESTS:
        assert pid in PEOPLE_IDS, f"interest for unknown person {pid}"
        assert topic in seed.TOPICS, f"interest in unknown topic {topic}"
        assert 1 <= weight <= 3, f"weight {weight} outside 1 to 3"
    pairs = [(p, t) for p, t, _ in seed.INTERESTS]
    assert len(pairs) == len(set(pairs)), "duplicate interest edge"


def test_talks_reference_real_speakers_topics_and_rooms():
    for tid, title, starts, ends, room, speakers, topics, blurb in seed.TALKS:
        assert title and blurb, f"talk {tid} missing title or blurb"
        assert room in seed.ROOMS, f"talk {tid} in unknown room {room}"
        assert speakers, f"talk {tid} has no speakers"
        for speaker in speakers:
            assert speaker in PEOPLE_IDS, f"talk {tid}: unknown {speaker}"
        assert topics, f"talk {tid} has no topics"
        for topic in topics:
            assert topic in seed.TOPICS, f"talk {tid}: unknown topic {topic}"


def test_talk_times_are_sane_hhmm_and_end_after_they_start():
    for tid, _title, starts, ends, _room, _s, _t, _b in seed.TALKS:
        for value in (starts, ends):
            hours, minutes = value.split(":")
            assert 0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59, \
                f"talk {tid}: bad time {value}"
        assert starts < ends, f"talk {tid} ends at {ends}, starts {starts}"


def test_every_speaker_actually_speaks_somewhere():
    speaking = {s for t in seed.TALKS for s in t[5]}
    speakers = {p[0] for p in seed.PEOPLE if p[2] == "speaker"}
    assert speakers <= speaking, \
        f"speakers with no talk: {sorted(speakers - speaking)}"
    # And nobody listed as an attendee is billed as a speaker.
    attendees = {p[0] for p in seed.PEOPLE if p[2] == "attendee"}
    assert not (attendees & speaking), \
        f"attendees giving talks: {sorted(attendees & speaking)}"


def test_meetings_reference_real_people_and_are_not_self_meetings():
    for a, b, note, at in seed.MEETINGS:
        assert a in PEOPLE_IDS and b in PEOPLE_IDS, f"meeting {a}/{b}"
        assert a != b, "a person cannot have a seeded meeting with themselves"
        assert note.strip(), "meeting note is the memory; it cannot be blank"
        hours, minutes = at.split(":")
        assert 0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59


def test_rene_is_seeded_with_the_demo_interests():
    rene = {topic for pid, topic, _w in seed.INTERESTS if pid == "rene"}
    assert rene == {"MCP", "AI Agents", "Developer Tools", "Rust"}
    # The smoke suite relies on Tom Alvarez being already met by Rene.
    assert ("rene", "tom-alvarez") in {(a, b) for a, b, _n, _t in seed.MEETINGS}


def test_topics_and_rooms_are_all_used():
    used_topics = {t for talk in seed.TALKS for t in talk[6]}
    used_topics |= {topic for _p, topic, _w in seed.INTERESTS}
    assert used_topics == set(seed.TOPICS), \
        f"unused topics: {sorted(set(seed.TOPICS) - used_topics)}"
    used_rooms = {talk[4] for talk in seed.TALKS}
    assert used_rooms == set(seed.ROOMS), \
        f"unused rooms: {sorted(set(seed.ROOMS) - used_rooms)}"


def test_no_two_talks_share_a_slot_and_room_unless_they_are_a_panel():
    # Same room, same start: only acceptable for multi speaker panels,
    # which this seed does not schedule in parallel. A clash here means
    # a typo in a time or a room.
    slots = Counter((t[2], t[4]) for t in seed.TALKS)
    clashes = {slot: n for slot, n in slots.items() if n > 1}
    assert not clashes, f"parallel talks in one room: {clashes}"
