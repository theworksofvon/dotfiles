#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""dev-studies ledger: sweep state, tree lock, run history, extraction outcomes.

Every database handle is opened read-only. The ledger is written by paid sweeps;
this panel must never be the reason one fails.
"""

import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import (
    AMB,
    C1,
    C3,
    G0,
    G1,
    G3,
    G4,
    GRY,
    RED,
    RST,
    WHT,
    bar,
    header,
    poller,
    run,
    sh,
)

REPO = Path.home() / "costmine" / "dev-study-parse" / "dev-studies"
LEDGER = REPO / "data" / "ledger.db"
INDEX = REPO / "data" / "index.db"


def q(db, sql, args=()):
    if not db.exists():
        return []
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=2.0)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def collect():
    docs = dict(q(INDEX, "select doc, name from documents"))
    runs = q(
        LEDGER,
        "select run_id, kind, doc, started_at from runs order by started_at desc limit 12",
    )
    outcomes = {}
    for run_id, *_ in runs[:1]:
        outcomes = dict(
            q(
                LEDGER,
                "select outcome, count(*) from field_results where run_id=? group by outcome",
                (run_id,),
            )
        )
    totals = q(
        LEDGER,
        "select count(*), coalesce(sum(seconds),0), coalesce(sum(images),0) from llm_calls",
    )
    allout = dict(q(LEDGER, "select outcome, count(*) from field_results group by outcome"))

    # A sweep is any live `dev-studies extract`; the tree is locked while one runs.
    ps = sh(["pgrep", "-fl", "dev-studies extract"], timeout=3)
    sweeping = bool([ln for ln in ps.splitlines() if "pgrep" not in ln])
    dirty = len([ln for ln in sh(["git", "status", "--porcelain"], cwd=str(REPO)).splitlines() if ln])
    branch = sh(["git", "branch", "--show-current"], cwd=str(REPO)).strip()
    return {
        "docs": docs,
        "runs": runs,
        "outcomes": outcomes,
        "totals": totals[0] if totals else (0, 0, 0),
        "allout": allout,
        "sweeping": sweeping,
        "dirty": dirty,
        "branch": branch,
    }


poll = poller(collect, 5.0, initial=None)


def render(w, h, t):
    out = [header("DEV-STUDIES LEDGER", w, C3, C1)]
    d = poll["v"]
    if not d:
        out.append(f"{G0}  reading ledger…{RST}")
        return out

    # Status banner: the thing worth glancing at from across the room.
    if d["sweeping"]:
        blink = int(t * 2) % 2 == 0
        col = RED if blink else AMB
        msg = "◉ SWEEP RUNNING — DO NOT WRITE TO THE TREE"
        if d["dirty"]:
            msg = f"◉ SWEEP RUNNING — TREE DIRTY ({d['dirty']} files)"
    else:
        col, msg = G4, "○ IDLE — tree is yours"
    out.append(f"{col}{msg[:w]}{RST}")
    out.append(
        f"{G0}branch {G3}{d['branch'][:28]:<28}{G0}dirty {(AMB if d['dirty'] else G1)}{d['dirty']:<4}"
        f"{G0}docs {G3}{len(d['docs'])}{RST}"
    )
    out.append(f"{G0}{'─' * w}{RST}")

    found = d["allout"].get("found", 0)
    miss = d["allout"].get("not_found", 0)
    err = d["allout"].get("error", 0)
    tot = max(1, found + miss + err)
    bw = max(8, w - 34)
    out.append(
        f"{G1}FIELDS  {bar(found / tot, bw, G3)} {G3}{found} found{G0}/"
        f"{AMB}{miss} miss{G0}/{RED}{err} err{RST}"
    )
    calls, secs, imgs = d["totals"]
    out.append(
        f"{G1}LLM     {WHT}{calls:>5}{G1} calls  {WHT}{secs / 3600:>5.1f}{G1} h  "
        f"{WHT}{imgs:>5}{G1} images{RST}"
    )
    out.append(f"{G0}{'─' * w}{RST}")

    rows = max(1, h - len(out) - 1)
    for run_id, kind, doc, started in d["runs"][:rows]:
        name = d["docs"].get(doc, doc)[:26]
        kcol = G4 if kind == "extract" else C1
        out.append(
            f"{G0}{started[5:16]} {kcol}{kind[:7]:<7} {G3}{name:<26}"
            f"{G0}{run_id[-6:]}{RST}"
        )
    while len(out) < h:
        out.append("")
    return out[:h]


run(render, fps=4)
