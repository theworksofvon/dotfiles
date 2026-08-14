#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Live socket table from netstat, rendered as a packet trace."""

import os
import random
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, RED, RST, WHT, header, run

state = {"t": 0.0, "conns": [], "log": [], "bytes": 0}
# tcp4 only: IPv6 remotes are far too wide for a 33-column pane.
ROW = re.compile(r"^tcp4\s+\d+\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)")


def poll():
    now = time.time()
    if now - state["t"] < 4.0:
        return
    state["t"] = now
    try:
        out = subprocess.run(
            ["netstat", "-an", "-p", "tcp"], capture_output=True, text=True, timeout=4
        ).stdout
    except Exception:
        return
    conns = []
    for line in out.splitlines():
        m = ROW.match(line)
        if not m:
            continue
        local, remote, st = m.groups()
        if (
            st in ("ESTABLISHED", "SYN_SENT", "CLOSE_WAIT", "TIME_WAIT")
            and remote != "*.*"
        ):
            conns.append((local, remote, st))
    if conns:
        state["conns"] = conns


def render(w, h, t):
    poll()
    if state["conns"] and random.random() < 0.55:
        _, remote, st = random.choice(state["conns"])
        n = random.randint(40, 9000)
        state["bytes"] += n
        col = {
            "ESTABLISHED": G3,
            "SYN_SENT": AMB,
            "TIME_WAIT": G0,
            "CLOSE_WAIT": G1,
        }.get(st, G1)
        flag = random.choice(["PSH", "ACK", "SYN", "FIN", "RST"])
        # netstat prints host.port; show host:port trimmed from the left so the
        # port and the low octets — the interesting end — always survive.
        host, _, port = remote.rpartition(".")
        aw = max(9, w - 17)
        addr = f"{host}:{port}"[-aw:]
        state["log"].append(
            f"{G0}{time.strftime('%M:%S')} {col}{addr:<{aw}} {C1}{flag} {G4}{n:>4}B{RST}"
        )
    del state["log"][: max(0, len(state["log"]) - 64)]

    out = [header("NET.TRACE", w, C3, C1)]
    rows = max(1, h - 3)
    for line in state["log"][-rows:]:
        out.append(line)
    while len(out) < h - 2:
        out.append("")
    mb = state["bytes"] / 1048576
    out.append(f"{G0}{'─' * w}{RST}")
    out.append(
        f"{C1}SOCK {WHT}{len(state['conns']):>3}{C1} · RX {G4}{mb:6.2f}M{C1} · {G3}en0{RST}"
    )
    return out


run(render, fps=8)
