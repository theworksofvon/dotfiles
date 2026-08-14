#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Intrusion-detection log: severity-coloured event stream."""

import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, RED, RST, WHT, header, run

# Kept terse on purpose: these panes run ~33 columns, and a line that clips
# mid-word reads as a rendering bug rather than as a log.
SUBSYS = ["krnl", "authd", "ipsec", "fw", "sshd", "dns", "audit", "cryptd", "netd"]
INFO = [
    "session open uid={uid}",
    "route tbl +{n}",
    "peer ok {ip}",
    "cache flush {n}ms",
    "keepalive {d}",
    "cert ok depth={d}",
    "hb ack {n}",
]
WARN = [
    "retransmit {d}x",
    "clock skew {d}s",
    "rate limit {ip}",
    "unknown SNI",
    "entropy low {n}b",
]
CRIT = [
    "AUTH FAIL uid={uid}",
    "PORT SCAN {ip}",
    "PRIV ESC pid={n}",
    "SIG MATCH {h}",
    "HIJACK {ip}",
]
state = {"log": [], "crit": 0, "warn": 0, "seq": 0}


def ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def fill(tpl):
    return tpl.format(
        uid=random.randint(0, 1999),
        n=random.randint(2, 9999),
        d=random.randint(1, 9),
        ip=ip(),
        h="".join(random.choice("0123456789abcdef") for _ in range(8)),
    )


def emit():
    r = random.random()
    if r < 0.10:
        state["crit"] += 1
        return RED, "CRIT", fill(random.choice(CRIT))
    if r < 0.30:
        state["warn"] += 1
        return AMB, "WARN", fill(random.choice(WARN))
    return G1, "INFO", fill(random.choice(INFO))


def render(w, h, t):
    if random.random() < 0.6:
        col, lvl, msg = emit()
        state["seq"] += 1
        sub = random.choice(SUBSYS)
        ts = time.strftime("%H:%M:%S")
        # Drop the subsystem rather than let the message clip.
        if len(ts) + 6 + len(sub) + 2 + len(msg) > w:
            sub = ""
        tag = f"{C1}{sub}: " if sub else ""
        state["log"].append(f"{G0}{ts} {col}{lvl} {tag}{col}{msg}")
    del state["log"][: max(0, len(state["log"]) - 80)]

    out = [header("IDS.LOG", w, G3, G0)]
    rows = max(1, h - 3)
    for line in state["log"][-rows:]:
        out.append(line)
    while len(out) < h - 2:
        out.append("")
    out.append(f"{G0}{'─' * w}{RST}")
    hot = state["crit"] % 7 < 3
    out.append(
        f"{C1}EVT {WHT}{state['seq']:05d} {AMB}W{state['warn']:03d} "
        f"{RED}C{state['crit']:03d} {(RED if hot else AMB)}{'ELEVATED' if hot else 'GUARDED'}{RST}"
    )
    return out


run(render, fps=8)
