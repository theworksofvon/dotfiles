#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Git status across a directory of repos.  usage: wgit.py <root> <TITLE>"""

import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, GRY, RED, RST, WHT, header, poller, run, sh

ROOT = Path(os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/dev"))
TITLE = sys.argv[2] if len(sys.argv) > 2 else ROOT.name.upper()
TRACK = re.compile(r"^## (?:No commits yet on )?([^.\s]+)(?:\.\.\.\S+)?(?: \[(.+)\])?")


def shorten(name):
    """Costmine.Underground.Backend -> Underground-be, so 17 repos stay legible."""
    name = re.sub(r"^Costmine\.", "", name)
    name = re.sub(r"\.Backend$", "-be", name)
    name = re.sub(r"\.Frontend$", "-fe", name)
    return name.replace("Api.Gateway", "Gateway").replace("ECC-Admin", "ECC-A")


def shortbranch(b):
    """Drop the owner prefix; the ticket is the part worth reading."""
    b = re.sub(r"^[a-z]+[./]", "", b)
    m = re.search(r"(dev-\d+|DEV-\d+)", b)
    return m.group(1) if m else b


def scan():
    repos = []
    for p in sorted(ROOT.iterdir()):
        if not (p / ".git").exists():
            continue
        st = sh(["git", "status", "--porcelain", "-b"], cwd=str(p), timeout=10).splitlines()
        if not st:
            continue
        branch, ahead, behind = "?", 0, 0
        m = TRACK.match(st[0])
        if m:
            branch = m.group(1)
            for kind, n in re.findall(r"(ahead|behind) (\d+)", m.group(2) or ""):
                if kind == "ahead":
                    ahead = int(n)
                else:
                    behind = int(n)
        dirty = len(st) - 1
        ts = sh(["git", "log", "-1", "--format=%ct"], cwd=str(p), timeout=10).strip()
        repos.append(
            {
                "name": p.name,
                "branch": branch,
                "dirty": dirty,
                "ahead": ahead,
                "behind": behind,
                "when": int(ts) if ts.isdigit() else 0,
            }
        )
    repos.sort(key=lambda r: (-r["dirty"], -r["when"]))
    return repos


poll = poller(scan, 25.0, initial=[])


def ago(ts):
    if not ts:
        return "  —"
    d = time.time() - ts
    for div, unit in ((86400, "d"), (3600, "h"), (60, "m")):
        if d >= div:
            return f"{int(d // div):>3}{unit}"
    return "now"


def render(w, h, t):
    repos = poll["v"] or []
    dirty = sum(1 for r in repos if r["dirty"])
    out = [header(TITLE, w, C3, C1)]

    # Below ~40 columns the "last commit" age is the first thing to go: repo
    # name and branch are what make a row identifiable.
    wide = w >= 40
    nw = min(18, max(10, w - (21 if wide else 20)))
    bw = max(6, w - nw - (13 if wide else 10))
    for r in repos[: max(0, h - 2)]:
        dcol = AMB if r["dirty"] else G0
        acol = G4 if r["ahead"] else G0
        bcol = RED if r["behind"] else G0
        out.append(
            f"{G3}{shorten(r['name'])[:nw]:<{nw}} {G1}{shortbranch(r['branch'])[:bw]:<{bw}} "
            f"{dcol}{('+' + str(r['dirty'])) if r['dirty'] else '  ':>3}"
            f"{acol}{('↑' + str(r['ahead'])) if r['ahead'] else '  ':>3}"
            f"{bcol}{('↓' + str(r['behind'])) if r['behind'] else '  ':>3}"
            f"{G0}{ago(r['when']) if wide else ''}{RST}"
        )
    while len(out) < h - 1:
        out.append("")
    out.append(
        f"{C1}{len(repos)} repos · {(AMB if dirty else G3)}{dirty} dirty{C1} · {G0}{ROOT.name}{RST}"
    )
    return out[:h]


run(render, fps=2)
