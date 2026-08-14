#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Live tool-use stream tailed from every active Claude Code transcript."""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, MAG, RED, RST, WHT, header, poller, run

ROOT = Path.home() / ".claude" / "projects"
HOT = 900  # only tail transcripts touched in the last 15 minutes

TOOLCOL = {
    "Bash": AMB,
    "Edit": G4,
    "Write": G4,
    "Read": G3,
    "Grep": C1,
    "Glob": C1,
    "Task": MAG,
    "Agent": MAG,
    "Skill": MAG,
    "WebFetch": C3,
    "WebSearch": C3,
}
state = {"offsets": {}, "events": []}


def label(path):
    """Project directory -> short name: dev-pulse becomes pulse, and the
    dev-study-parse tree collapses to dev-studies."""
    name = path.parent.name
    if name == "subagents":
        name = path.parent.parent.parent.name
    name = name.replace("-Users-davontaejackson-", "")
    for prefix in ("dev-", "costmine-"):
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break
    parts = name.split("-")
    if len(parts) > 2:
        name = "-".join(parts[-2:])
    return name[:12] or "?"


def localtime(ts):
    """Transcript stamps are UTC; the wall clock next to this pane is not."""
    try:
        return (
            datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%H:%M:%S")
        )
    except ValueError:
        return "--:--:--"


def detail(name, inp):
    if not isinstance(inp, dict):
        return ""
    if name == "Bash":
        return (inp.get("command") or "").split("\n")[0]
    for k in ("file_path", "path", "notebook_path"):
        if inp.get(k):
            return os.path.basename(inp[k])
    for k in ("pattern", "description", "skill", "query", "url", "prompt"):
        if inp.get(k):
            return str(inp[k])
    return ""


def scan():
    """Read only what has been appended since the last pass."""
    now = time.time()
    fresh = []
    for p in ROOT.rglob("*.jsonl"):
        try:
            st = p.stat()
        except OSError:
            continue
        if now - st.st_mtime > HOT:
            continue
        key = str(p)
        prev = state["offsets"].get(key)
        if prev is None:
            # First sighting: start at the end so we stream, not replay.
            state["offsets"][key] = st.st_size
            continue
        if st.st_size <= prev:
            state["offsets"][key] = min(prev, st.st_size)
            continue
        try:
            with p.open("rb") as fh:
                fh.seek(prev)
                blob = fh.read(st.st_size - prev)
            state["offsets"][key] = st.st_size
        except OSError:
            continue
        for raw in blob.decode("utf-8", "replace").splitlines():
            if '"tool_use"' not in raw and '"type":"user"' not in raw:
                continue
            try:
                rec = json.loads(raw)
            except ValueError:
                continue
            ts = localtime(rec.get("timestamp") or "")
            proj = label(p)
            msg = rec.get("message") or {}
            if rec.get("type") == "assistant":
                for c in msg.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        fresh.append((ts, proj, c.get("name", "?"), detail(c.get("name"), c.get("input"))))
            elif rec.get("type") == "user" and isinstance(msg.get("content"), str):
                fresh.append((ts, proj, "▸PROMPT", msg["content"].split("\n")[0]))
    # Only the poller thread mutates the buffer; render is read-only.
    state["events"].extend(fresh)
    del state["events"][: max(0, len(state["events"]) - 200)]
    return len(state["events"])


poll = poller(scan, 2.0, initial=0)


def render(w, h, t):
    out = [header("AGENT ACTIVITY", w, MAG, G0)]
    rows = max(1, h - 2)
    for ts, proj, tool, det in state["events"][-rows:]:
        col = TOOLCOL.get(tool, WHT if tool.startswith("▸") else G1)
        head = f"{G0}{ts[3:]} {C1}{proj[:9]:<9} {col}{tool[:8]}"
        used = 6 + 10 + min(8, len(tool))
        out.append(f"{head} {G0}{det[: max(0, w - used - 2)]}{RST}")
    while len(out) < h:
        out.append("")
    return out[:h]


run(render, fps=4)
