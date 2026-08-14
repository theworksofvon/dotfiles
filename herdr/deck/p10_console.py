#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Master console: block clock, link status, session readout."""

import math
import os
import random
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, RED, RST, WHT, bar, header, run

FONT = {
    "0": ["█████", "█   █", "█   █", "█   █", "█████"],
    "1": ["   ██", "    █", "    █", "    █", "    █"],
    "2": ["█████", "    █", "█████", "█    ", "█████"],
    "3": ["█████", "    █", "█████", "    █", "█████"],
    "4": ["█   █", "█   █", "█████", "    █", "    █"],
    "5": ["█████", "█    ", "█████", "    █", "█████"],
    "6": ["█████", "█    ", "█████", "█   █", "█████"],
    "7": ["█████", "    █", "    █", "    █", "    █"],
    "8": ["█████", "█   █", "█████", "█   █", "█████"],
    "9": ["█████", "█   █", "█████", "    █", "█████"],
    ":": [" ", "█", " ", "█", " "],
    " ": [" ", " ", " ", " ", " "],
}
state = {"ip": "", "t": 0.0, "user": os.environ.get("USER", "operator")}


def localip():
    if time.time() - state["t"] > 30 or not state["ip"]:
        state["t"] = time.time()
        try:
            out = subprocess.run(
                ["ipconfig", "getifaddr", "en0"], capture_output=True, text=True, timeout=2
            ).stdout.strip()
            state["ip"] = out or "0.0.0.0"
        except Exception:
            state["ip"] = "0.0.0.0"
    return state["ip"]


def big(text, col):
    rows = ["", "", "", "", ""]
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for i in range(5):
            rows[i] += glyph[i] + " "
    return [f"{col}{r}{RST}" for r in rows]


def render(w, h, t):
    now = time.localtime()
    out = [header("CONSOLE", w, C3, C1)]
    out.append("")
    out += big(time.strftime("%H:%M", now), G4)
    out.append("")
    out.append(f"{G1}  {time.strftime('%a %d %b %Y', now)}  {G3}:{time.strftime('%S', now)}{RST}")
    out.append(f"{G0}{'─' * w}{RST}")

    blink = int(t * 2) % 2 == 0
    link = f"{G4}◉ SECURE" if blink else f"{G3}◎ SECURE"
    out.append(f"{C1}LINK   {link}{RST}")
    out.append(f"{C1}NODE   {WHT}{os.uname().nodename.split('.')[0][: w - 8]}{RST}")
    out.append(f"{C1}ADDR   {G3}{localip()}{RST}")
    out.append(f"{C1}USER   {G3}{state['user']}{RST}")
    out.append(f"{C1}SHELL  {G3}{os.path.basename(os.environ.get('SHELL', 'zsh'))}{RST}")
    out.append(f"{C1}SESS   {G3}{os.environ.get('HERDR_WORKSPACE_ID', 'w?')}·herdr{RST}")
    out.append(f"{G0}{'─' * w}{RST}")

    bw = max(5, w - 11)
    for name, phase, speed in (("PWR", 0.0, 0.7), ("ICE", 2.0, 1.1), ("VPN", 4.0, 0.5)):
        v = 0.55 + 0.42 * math.sin(t * speed + phase)
        col = G3 if v > 0.4 else AMB
        out.append(f"{G1}{name} {bar(min(0.99, v), bw, col)}{RST}")

    out.append(f"{G0}{'─' * w}{RST}")
    lat = 43.6532 + 0.001 * math.sin(t * 0.3)
    lon = -79.3832 + 0.001 * math.cos(t * 0.3)
    out.append(f"{C1}GEO {G3}{lat:8.4f}N {lon:9.4f}W{RST}")
    out.append(f"{C1}TRK {G3}{'█' * (int(t * 3) % max(2, w - 6))}{RST}")

    while len(out) < h - 1:
        out.append("")
    msg = "ALL SYSTEMS NOMINAL" if int(t) % 12 < 8 else "TRACE IN PROGRESS…"
    col = G4 if int(t) % 12 < 8 else AMB
    out.append(f"{col}{msg.center(w)[:w]}{RST}")
    return out


run(render, fps=8)
