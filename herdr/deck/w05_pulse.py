#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Pulse: local server health, hook coverage, and the tail of its log."""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, RED, RST, WHT, header, poller, run, sh

LOG = Path.home() / ".pulse" / "logs" / "server.log"


def collect():
    txt = sh(["pulse", "status"], timeout=10)
    running = bool(re.search(r"Running\s*:\s*yes", txt))
    hooks = re.findall(r"(\d+)/(\d+) hooks installed", txt)
    agents = re.findall(r"- ([A-Za-z ]+): (connected|not connected)", txt)
    tail = []
    if LOG.exists():
        try:
            with LOG.open("rb") as fh:
                fh.seek(max(0, LOG.stat().st_size - 4000))
                tail = fh.read().decode("utf-8", "replace").splitlines()[-12:]
        except OSError:
            pass
    return {"running": running, "hooks": hooks, "agents": agents, "tail": tail}


poll = poller(collect, 8.0, initial=None)


def render(w, h, t):
    out = [header("PULSE", w, C3, C1)]
    d = poll["v"]
    if not d:
        out.append(f"{G0} querying…{RST}")
        return out

    dot = f"{G4}◉ UP" if d["running"] else f"{RED}○ DOWN"
    out.append(f"{C1}server {dot}{RST}")
    # Pair each agent with its own hook count rather than running them together.
    for i, (name, status) in enumerate(d["agents"][:3]):
        got, want = d["hooks"][i] if i < len(d["hooks"]) else ("?", "?")
        ok = status == "connected" and got == want
        col = G4 if ok else AMB
        out.append(
            f"{col}{'◉' if ok else '○'} {C3}{name.strip()[:11]:<12}{col}{got}/{want} hooks{RST}"
        )
    for ln in d["tail"][-(h - len(out) - 1) :]:
        col = RED if re.search(r"error|ERROR", ln) else G0
        out.append(f"{col}{ln.strip()[:w]}{RST}")
    if not d["running"]:
        while len(out) < h - 1:
            out.append("")
        out.append(f"{AMB}`pulse up` to start collecting{RST}")
    return out[:h]


run(render, fps=2)
