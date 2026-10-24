"""Focused test for .env auto-loading.

graph.seed is the shared import point for the web app, the runner and
the seed CLI. Importing it must load the project .env so venue keys
and the FalkorDB URL from the README Quickstart reach the process
without manual exports. Runs in a subprocess with a scrubbed
environment so the parent shell cannot mask a miss.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHILD = (
    "import graph.seed, os; "
    "print(os.environ.get('HALLWAY_GRAPH','')); "
    "print(os.environ.get('FALKORDB_URL',''))"
)


def test_seed_loads_dotenv_from_project_root():
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("SKIP .env missing at project root; README Quickstart creates it")
        return
    env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}
    proc = subprocess.run(
        [sys.executable, "-c", CHILD],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr[-500:]
    graph_name, falkordb_url = proc.stdout.strip().splitlines()
    assert graph_name == "hallway"
    assert falkordb_url.startswith("redis://localhost:6379"), proc.stdout
