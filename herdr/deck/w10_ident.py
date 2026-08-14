#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Console: clock, and which identity is active where.

Personal and work accounts share this machine, so which git/gh identity a
directory resolves to is worth showing rather than remembering.
"""

import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, GRY, RED, RST, WHT, header, poller, run, sh

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
CONTEXTS = [("dev", Path.home() / "dev" / "pulse"), ("work", Path.home() / "costmine" / "core")]


def collect():
    auth = sh(["gh", "auth", "status"], timeout=12)
    accounts = re.findall(r"Logged in to \S+ account (\S+)", auth)
    active = ""
    for block in auth.split("github.com")[1:]:
        m = re.search(r"account (\S+)", block)
        if m and "Active account: true" in block:
            active = m.group(1)
    ids = []
    for label, path in CONTEXTS:
        if path.exists():
            email = sh(["git", "config", "user.email"], cwd=str(path), timeout=6).strip()
            ids.append((label, email))
    boot = sh(["sysctl", "-n", "kern.boottime"], timeout=5)
    m = re.search(r"sec = (\d+)", boot)
    return {
        "accounts": accounts,
        "active": active,
        "ids": ids,
        "boot": int(m.group(1)) if m else 0,
    }


poll = poller(collect, 60.0, initial=None)


def big(text, col):
    rows = ["", "", "", "", ""]
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for i in range(5):
            rows[i] += glyph[i] + " "
    return [f"{col}{r}{RST}" for r in rows]


def render(w, h, t):
    now = time.localtime()
    out = [header("CONSOLE", w, C3, C1), ""]
    out += big(time.strftime("%H:%M", now), G4)
    out.append("")
    out.append(f"{G1}  {time.strftime('%a %d %b %Y', now)}  {G3}:{time.strftime('%S', now)}{RST}")
    out.append(f"{G0}{'─' * w}{RST}")

    d = poll["v"]
    if d:
        for name in d["accounts"]:
            live = name == d["active"]
            out.append(
                f"{(G4 if live else G0)}{'◉' if live else '○'} {(WHT if live else GRY)}{name[: w - 3]}{RST}"
            )
        out.append("")
        for label, email in d["ids"]:
            out.append(f"{C1}{label:<5}{G3}{email[: w - 6]}{RST}")
        out.append(f"{G0}{'─' * w}{RST}")
        if d["boot"]:
            s = int(time.time() - d["boot"])
            out.append(f"{C1}UP    {G3}{s // 86400}d {s % 86400 // 3600:02d}h {s % 3600 // 60:02d}m{RST}")
    out.append(f"{C1}HOST  {G3}{os.uname().nodename.split('.')[0][: w - 6]}{RST}")
    out.append(f"{C1}SESS  {G3}{os.environ.get('HERDR_WORKSPACE_ID', 'w?')}·herdr{RST}")

    while len(out) < h:
        out.append("")
    return out[:h]


run(render, fps=4)
