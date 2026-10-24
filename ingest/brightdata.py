"""Bright Data adapter (Track 2): live public web data without the fight.

Two operations, both backed by the Bright Data API when BRIGHTDATA_API_KEY
is set, and both transparently backed by bundled fixtures when it is not, so
the whole system runs before any account exists:

- fetch_url(url): Web Unlocker. Returns the page body as text.
- search(query): SERP API. Returns a list of {title, url, snippet}.
- fetch_schedule(): the conference schedule as parsed talk dicts. Live
  conference pages differ; at the venue this is where the real schedule URL
  and its JSON shape get wired in. Until then the fixture schedule (with two
  deliberate changes vs the seed: t6 moved rooms, t11 moved time) drives the
  Scout refresh and Planner repair demo.

The MCP configuration for the Bright Data MCP server lives in
mcp_config_snippet() and in docs; the agent layer can call the same data
through MCP at the venue.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import requests

FIXTURES = Path(__file__).parent / "fixtures"
API_URL = "https://api.brightdata.com/request"
SIGNUP_URL = "https://brightdata.com/cp/start"


def _key():
    return os.environ.get("BRIGHTDATA_API_KEY", "").strip()


def _zone(name, default):
    return os.environ.get(name, default)


def _post(zone, url, fmt="raw"):
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {_key()}",
                 "Content-Type": "application/json"},
        json={"zone": zone, "url": url, "format": fmt},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def fetch_url_cli(url):
    """Fetch via the Bright Data CLI (bdata), a first class path per the
    hackathon Resources page: npx -p @brightdata/cli bdata login, then
    bdata scrape <url>. Raises on any problem so callers can fall back."""
    exe = shutil.which("bdata")
    if not exe:
        raise RuntimeError("bdata CLI not on PATH")
    out = subprocess.run([exe, "scrape", url], capture_output=True,
                         text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"bdata scrape failed: {out.stderr[:200]}")
    return out.stdout


def fetch_url(url):
    """Web Unlocker fetch. BRIGHTDATA_MODE=cli tries the bdata CLI first.
    Falls back to the schedule fixture offline."""
    if os.environ.get("BRIGHTDATA_MODE") == "cli":
        try:
            return fetch_url_cli(url)
        except Exception:
            pass  # fall through to API or fixture
    if _key():
        return _post(_zone("BRIGHTDATA_ZONE_WEB_UNLOCKER", "web_unlocker1"), url)
    fixture = FIXTURES / "schedule_page.json"
    return fixture.read_text()


def search(query):
    """SERP API search. Falls back to the search fixture offline."""
    if _key():
        raw = _post(_zone("BRIGHTDATA_ZONE_SERP", "serp_api1"),
                    f"https://www.google.com/search?q={query}")
        try:
            data = json.loads(raw)
            results = data.get("organic", data.get("results", []))
            return {"query": query, "fetched_via": "brightdata-serp",
                    "results": results}
        except (ValueError, AttributeError):
            return {"query": query, "fetched_via": "brightdata-serp-raw",
                    "results": [], "raw": raw[:2000]}
    data = json.loads((FIXTURES / "search_results.json").read_text())
    data["query"] = query
    return data


def fetch_schedule():
    """Return (talks, meta). talks are dicts shaped like graph/seed TALKS."""
    url = os.environ.get("SCHEDULE_URL",
                         "https://example.com/conference/schedule")
    raw = fetch_url(url)
    try:
        data = json.loads(raw)
        return data["talks"], {"source": data.get("source", url),
                               "fetched_via": data.get("fetched_via", "live")}
    except (ValueError, KeyError):
        data = json.loads((FIXTURES / "schedule_page.json").read_text())
        return data["talks"], {"source": data.get("source", url),
                               "fetched_via": "fixture-fallback"}


def mcp_config_snippet():
    """Bright Data MCP server config for the agent layer (venue reference)."""
    return {
        "mcpServers": {
            "brightdata": {
                "command": "npx",
                "args": ["-y", "@brightdata/mcp"],
                "env": {
                    "API_TOKEN": "$BRIGHTDATA_API_KEY",
                    "WEB_UNLOCKER_ZONE": _zone(
                        "BRIGHTDATA_ZONE_WEB_UNLOCKER", "web_unlocker1"),
                    "SERP_ZONE": _zone("BRIGHTDATA_ZONE_SERP", "serp_api1"),
                },
            }
        }
    }
