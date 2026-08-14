#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Herdr session map: workspaces, tabs, panes and agent lifecycle states."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, GRY, MAG, RED, RST, WHT, header, poller, run, shj

STATE_COL = {
    "working": AMB,
    "idle": G4,
    "done": G4,
    "blocked": RED,
    "unknown": GRY,
}
SELF = os.environ.get("HERDR_PANE_ID", "")


def snapshot():
    ws = (shj(["herdr", "workspace", "list"], default={}) or {}).get("result", {}).get(
        "workspaces", []
    )
    rows = []
    for w in ws:
        wid = w["workspace_id"]
        tabs = (shj(["herdr", "tab", "list", "--workspace", wid], default={}) or {}).get(
            "result", {}
        ).get("tabs", [])
        panes = (shj(["herdr", "pane", "list", "--workspace", wid], default={}) or {}).get(
            "result", {}
        ).get("panes", [])
        rows.append((w, tabs, panes))
    return rows


poll = poller(snapshot, 2.5, initial=[])


def render(w, h, t):
    out = [header("HERDR SESSION", w, C3, C1)]
    data = poll["v"] or []
    npanes = sum(len(p) for _, _, p in data)
    nagents = sum(1 for _, _, ps in data for p in ps if p.get("agent"))

    for ws, tabs, panes in data:
        star = "●" if ws.get("focused") else "○"
        out.append(f"{C3}{star} {ws['workspace_id']} {WHT}{(ws.get('label') or '')[:14]}{RST}")
        for tab in tabs:
            tid = tab["tab_id"]
            mine = [p for p in panes if p.get("tab_id") == tid]
            mark = "▸" if tab.get("focused") else " "
            out.append(
                f"{G0} {mark}{C1}{tid} {G1}{(tab.get('label') or '—')[:11]:<11}"
                f"{G0}{len(mine)}p{RST}"
            )
            for p in mine:
                agent = p.get("agent")
                st = p.get("agent_status", "unknown")
                col = STATE_COL.get(st, GRY)
                here = f"{G4}◀" if p["pane_id"] == SELF else " "
                name = (agent or os.path.basename(p.get("foreground_cwd", "")) or "sh")[:11]
                dot = "◉" if agent else "·"
                out.append(
                    f"{G0}   {col}{dot} {name:<11}{G0}{p['pane_id'][-3:]:>4} "
                    f"{col}{(st[:4] if agent else ''):<4}{here}{RST}"
                )
    while len(out) < h - 1:
        out.append("")
    out.append(f"{C1}PANES {WHT}{npanes:>2}{C1} · AGENTS {G4}{nagents}{C1} · {G0}herdr{RST}")
    return out[:h]


run(render, fps=3)
