"""Offline tests for the Bright Data adapter (ingest/brightdata.py).

The adapter's contract is that Hallway runs before any Bright Data
account exists: with no BRIGHTDATA_API_KEY every call must be answered
by the bundled fixtures, and Scout's schedule refresh must come back as
normalized talk dicts. These tests pin that contract, plus the parsing
fallbacks used when a live response is not the expected JSON shape.
No network: the HTTP layer is monkeypatched where a key is set.

    pytest tests/test_brightdata.py    # no network, no API key needed
"""

import contextlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ingest import brightdata  # noqa: E402

BD_ENV_KEYS = ("BRIGHTDATA_API_KEY", "BRIGHTDATA_MODE",
               "BRIGHTDATA_ZONE_WEB_UNLOCKER", "BRIGHTDATA_ZONE_SERP",
               "SCHEDULE_URL")


@contextlib.contextmanager
def bd_env(**values):
    saved = {k: os.environ.get(k) for k in BD_ENV_KEYS}
    for k in BD_ENV_KEYS:
        os.environ.pop(k, None)
    os.environ.update(values)
    try:
        yield
    finally:
        for k in BD_ENV_KEYS:
            if saved[k] is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = saved[k]


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


@contextlib.contextmanager
def fake_post(text, record=None):
    original = brightdata.requests.post

    def _post(url, headers=None, json=None, timeout=None):
        if record is not None:
            record.update({"url": url, "headers": headers,
                           "json": json, "timeout": timeout})
        return FakeResponse(text)

    brightdata.requests.post = _post
    try:
        yield
    finally:
        brightdata.requests.post = original


# --------------------------------------------------------------- fixtures --

def test_fetch_url_without_a_key_returns_the_schedule_fixture():
    with bd_env():
        raw = brightdata.fetch_url("https://example.com/whatever")
    fixture = json.loads(
        (brightdata.FIXTURES / "schedule_page.json").read_text())
    assert json.loads(raw) == fixture


def test_search_without_a_key_returns_the_fixture_with_the_query():
    with bd_env():
        result = brightdata.search("hallway conference schedule")
    assert result["query"] == "hallway conference schedule"
    assert result["results"], "fixture search results must not be empty"
    first = result["results"][0]
    assert {"title", "url", "snippet"} <= set(first)


def test_fetch_schedule_offline_returns_normalized_talks():
    with bd_env():
        talks, meta = brightdata.fetch_schedule()
    assert talks, "fixture schedule must yield talks"
    assert meta["fetched_via"] in ("fixture", "live", "fixture-fallback")
    for talk in talks:
        assert talk["id"], "talks without an id are dropped upstream"
        assert set(talk) == {"id", "title", "starts", "ends", "room",
                             "speaker_ids", "topics", "blurb"}
        assert isinstance(talk["speaker_ids"], list)
        assert isinstance(talk["topics"], list)


def test_fetch_schedule_contains_the_two_demo_changes():
    # The fixture deliberately differs from the seed (see the module
    # docstring): t6 moved rooms and t11 moved time, which is what drives
    # the Scout refresh and Planner repair demo.
    with bd_env():
        talks, _meta = brightdata.fetch_schedule()
    by_id = {t["id"]: t for t in talks}
    # Seed values (graph/seed.py): t6 is in Main Stage, t11 starts 16:15.
    # The fixture must differ on exactly these, or the repair demo is gone.
    assert by_id["t6"]["room"] != "Main Stage", "t6 must move rooms"
    assert by_id["t11"]["starts"] != "16:15", "t11 must move time"


# ------------------------------------------------------------ normalization --

def test_normalize_talk_fills_defaults_and_dedupes():
    talk = brightdata._normalize_talk(
        {"id": "x1", "speaker_ids": ["a", "a", "b"], "topics": None})
    assert talk == {"id": "x1", "title": "", "starts": "", "ends": "",
                    "room": "Main Stage", "speaker_ids": ["a", "b"],
                    "topics": [], "blurb": ""}


def test_normalize_talk_keeps_an_explicit_room():
    talk = brightdata._normalize_talk({"id": "x2", "room": "Workshop 2"})
    assert talk["room"] == "Workshop 2"


# ---------------------------------------------------------------- live path --

def test_search_with_a_key_parses_organic_results():
    record = {}
    payload = json.dumps({"organic": [{"title": "T", "url": "https://x",
                                       "snippet": "S"}]})
    with bd_env(BRIGHTDATA_API_KEY="test-key"):
        with fake_post(payload, record):
            result = brightdata.search("agent conferences")
    assert result["fetched_via"] == "brightdata-serp"
    assert result["results"][0]["title"] == "T"
    assert record["headers"]["Authorization"] == "Bearer test-key"
    assert record["json"]["zone"] == "serp_api1"


def test_search_with_a_key_survives_non_json_responses():
    with bd_env(BRIGHTDATA_API_KEY="test-key"):
        with fake_post("<html>not json</html>"):
            result = brightdata.search("agent conferences")
    assert result["fetched_via"] == "brightdata-serp-raw"
    assert result["results"] == []
    assert result["raw"].startswith("<html>")


def test_fetch_url_with_a_key_posts_to_the_web_unlocker_zone():
    record = {}
    with bd_env(BRIGHTDATA_API_KEY="test-key"):
        with fake_post("page body", record):
            body = brightdata.fetch_url("https://example.com/schedule")
    assert body == "page body"
    assert record["json"] == {"zone": "web_unlocker1",
                               "url": "https://example.com/schedule",
                               "format": "raw"}


def test_fetch_schedule_falls_back_when_the_live_body_is_not_json():
    with bd_env(BRIGHTDATA_API_KEY="test-key"):
        with fake_post("502 Bad Gateway"):
            talks, meta = brightdata.fetch_schedule()
    assert talks, "the fixture fallback must still produce talks"
    assert meta["fetched_via"] == "fixture-fallback"


def test_mcp_config_snippet_uses_the_configured_zones():
    with bd_env(BRIGHTDATA_ZONE_WEB_UNLOCKER="zone-w",
                BRIGHTDATA_ZONE_SERP="zone-s"):
        snippet = brightdata.mcp_config_snippet()
    server = snippet["mcpServers"]["brightdata"]
    assert server["command"] == "npx"
    assert server["env"]["WEB_UNLOCKER_ZONE"] == "zone-w"
    assert server["env"]["SERP_ZONE"] == "zone-s"
    assert server["env"]["API_TOKEN"] == "$BRIGHTDATA_API_KEY"
