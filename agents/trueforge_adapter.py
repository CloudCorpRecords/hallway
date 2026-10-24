"""TrueForge adapter (Track 3): detect the harness, never hard-depend on it.

Recon, updated from the hackathon Resources page (2026-10-24):
- TrueForge is TrueFoundry's open source agent harness, TypeScript first,
  with a built in Chat UI. It starts with one command, nothing to clone:
  `npx @truefoundry/trueforge`. Docs: trueforge.dev/quickstart,
  trueforge.dev/create-agent/overview, trueforge.dev/mcp-servers.
  Example agent.json files: github.com/truefoundry/trueforge,
  tree examples/agent-cookbook/examples.
- Hallway's structure follows from that: the agent definitions live in
  trueforge/*.agent.json (Scout, Planner, Matchmaker), and the Python
  FalkorDB graph service in this repo sits behind them as tools, over the
  HTTP API in app/main.py and the FalkorDB MCP server (see mcp/).
- The Python agents in this folder are the deterministic fallback loop:
  same graph, same queries, no harness required. That fallback is what
  gets smoke tested, so the demo never depends on the harness being up.

This module keeps a runtime probe for a Python side module for completeness
and reports the launch path. available() refers to the probe only; the
runner treats the harness as venue configured either way.
"""

import importlib

_CANDIDATES = ("trueforge", "truefoundry")
_detected = "unset"


def detect():
    global _detected
    if _detected != "unset":
        return _detected
    for name in _CANDIDATES:
        try:
            module = importlib.import_module(name)
        except ImportError:
            continue
        _detected = (name, module)
        return _detected
    _detected = (None, None)
    return _detected


def available():
    return detect()[0] is not None


def describe():
    name, module = detect()
    if name is None:
        return {"sdk": None,
                "note": "No TrueForge/truefoundry module importable. "
                        "Local fallback loop is active. Install at the venue "
                        "per the TrueForge workshop."}
    return {"sdk": name,
            "version": getattr(module, "__version__", "unknown"),
            "note": "Python side module detected. The primary harness is "
                    "TypeScript: npx @truefoundry/trueforge with the "
                    "agent definitions in trueforge/."}
