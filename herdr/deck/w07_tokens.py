#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Today's Claude Code token spend, by project and by hour."""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, RED, RST, WHT, bar, header, poller, run

ROOT = Path.home() / ".claude" / "projects"
SPARK = "▁▂▃▄▅▆▇█"


def shortname(dirname):
    """-Users-…-dev-pulse -> pulse; the dev-study-parse tree -> dev-studies."""
    name = dirname.replace("-Users-davontaejackson-", "")
    for prefix in ("dev-", "costmine-"):
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break
    parts = name.split("-")
    return ("-".join(parts[-2:]) if len(parts) > 2 else name) or "?"


def collect():
    """Sum usage from transcripts touched today. Only reads lines that carry it."""
    midnight = (
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    )
    by_proj, by_hour = {}, [0] * 24
    tot_in = tot_out = tot_cache = 0
    for p in ROOT.rglob("*.jsonl"):
        try:
            if p.stat().st_mtime < midnight:
                continue
        except OSError:
            continue
        proj = p.parent.name
        if proj == "subagents":
            proj = p.parent.parent.parent.name
        proj = shortname(proj)
        try:
            with p.open("r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if '"output_tokens"' not in line:
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    u = (rec.get("message") or {}).get("usage") or {}
                    o = u.get("output_tokens") or 0
                    if not o:
                        continue
                    ts = rec.get("timestamp") or ""
                    try:
                        when = datetime.fromisoformat(
                            ts.replace("Z", "+00:00")
                        ).astimezone()
                    except ValueError:
                        continue
                    if when.timestamp() < midnight:
                        continue
                    by_proj[proj] = by_proj.get(proj, 0) + o
                    by_hour[when.hour] += o
                    tot_out += o
                    tot_in += u.get("input_tokens") or 0
                    tot_cache += (u.get("cache_read_input_tokens") or 0) + (
                        u.get("cache_creation_input_tokens") or 0
                    )
        except OSError:
            continue
    return {
        "proj": sorted(by_proj.items(), key=lambda kv: -kv[1]),
        "hour": by_hour,
        "in": tot_in,
        "out": tot_out,
        "cache": tot_cache,
    }


poll = poller(collect, 45.0, initial=None)


def k(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1000:
        return f"{n / 1000:.0f}k"
    return str(n)


def render(w, h, t):
    out = [header("TOKENS TODAY", w, C3, C1)]
    d = poll["v"]
    if not d:
        out.append(f"{G0} scanning transcripts…{RST}")
        return out

    out.append(f"{G1}out {G4}{k(d['out']):>5}{G1} in {G3}{k(d['in']):>4}{G1} cch {C1}{k(d['cache']):>5}{RST}")
    peak = max(d["hour"]) or 1
    now_h = time.localtime().tm_hour
    spark = "".join(
        (f"{G4}" if i == now_h else f"{G3}") + SPARK[min(7, int(v / peak * 7.99))]
        if v
        else f"{G0}▁"
        for i, v in enumerate(d["hour"])
    )
    out.append(spark + RST)
    out.append(f"{G0}0h{' ' * max(0, 20)}23h{RST}")
    out.append(f"{G0}{'─' * w}{RST}")

    top = d["proj"][: max(0, h - len(out) - 1)]
    biggest = top[0][1] if top else 1
    nw = max(8, w - 16)
    for name, n in top:
        out.append(
            f"{G3}{name[:nw]:<{nw}} {bar(n / biggest, max(3, w - nw - 9), G3)} {G4}{k(n):>5}{RST}"
        )
    while len(out) < h:
        out.append("")
    return out[:h]


run(render, fps=1)
