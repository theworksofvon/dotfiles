#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Open PRs and latest CI conclusion for the repos currently in play.

Repos are read from repos.txt (one path per line) so the watch list can change
without touching the panel.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, GRY, MAG, RED, RST, WHT, header, poller, run, shj

HERE = Path(__file__).resolve().parent
LIST = HERE / "repos.txt"
CI = {
    "success": (G4, "✓"),
    "failure": (RED, "✗"),
    "cancelled": (GRY, "–"),
    "skipped": (GRY, "–"),
    "startup_failure": (RED, "✗"),
    None: (AMB, "◐"),
}


def watched():
    if not LIST.exists():
        return []
    out = []
    for ln in LIST.read_text().splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            p = Path(os.path.expanduser(ln))
            if (p / ".git").exists():
                out.append(p)
    return out


def collect():
    rows = []
    for repo in watched():
        prs = (
            shj(
                ["gh", "pr", "list", "--limit", "4", "--json", "number,title,isDraft,headRefName"],
                cwd=str(repo),
                timeout=20,
                default=[],
            )
            or []
        )
        runs = (
            shj(
                ["gh", "run", "list", "--limit", "1", "--json", "status,conclusion,workflowName"],
                cwd=str(repo),
                timeout=20,
                default=[],
            )
            or []
        )
        last = runs[0] if runs else {}
        rows.append(
            {
                "repo": repo.name,
                "prs": prs,
                "status": last.get("status"),
                "concl": last.get("conclusion"),
            }
        )
    return rows


poll = poller(collect, 120.0, initial=[])


def render(w, h, t):
    out = [header("PR / CI", w, MAG, G0)]
    rows = poll["v"] or []
    if not rows:
        out.append(f"{G0} {'no repos.txt' if not LIST.exists() else 'querying gh…'}{RST}")
        return out

    npr = sum(len(r["prs"]) for r in rows)
    fails = sum(1 for r in rows if r["concl"] == "failure")
    for r in rows:
        if len(out) >= h - 1:
            break
        running = r["status"] and r["status"] != "completed"
        col, mark = (AMB, "◐") if running else CI.get(r["concl"], (GRY, "·"))
        short = r["repo"].replace("Costmine.", "").replace(".Backend", "-be").replace(
            ".Frontend", "-fe"
        )
        out.append(f"{col}{mark} {C3}{short[: w - 6]:<{max(4, w - 6)}}{G0}{len(r['prs']):>2}{RST}")
        for pr in r["prs"]:
            if len(out) >= h - 1:
                break
            pcol = GRY if pr["isDraft"] else G3
            out.append(f"{G0}  #{pr['number']:<4} {pcol}{pr['title'][: max(4, w - 9)]}{RST}")
    while len(out) < h - 1:
        out.append("")
    out.append(
        f"{C1}{len(rows)} repos · {G3}{npr} open PR{C1} · "
        f"{(RED if fails else G3)}{fails} failing{RST}"
    )
    return out[:h]


run(render, fps=1)
