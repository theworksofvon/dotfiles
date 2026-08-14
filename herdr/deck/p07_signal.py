#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Oscilloscope trace over a spectrum analyser."""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, RED, RST, WHT, header, run

SPARK = "▁▂▃▄▅▆▇█"
state = {"bins": [], "peak": [], "carrier": 2.4}


def wave(x, t):
    return (
        0.55 * math.sin(x * 0.32 + t * 2.6)
        + 0.28 * math.sin(x * 0.11 - t * 1.3)
        + 0.14 * math.sin(x * 0.9 + t * 5.1)
        + 0.06 * random.uniform(-1, 1)
    )


def render(w, h, t):
    out = [header("SIGNAL ∷ 2.4GHz", w, C3, C1)]
    scope_h = max(3, (h - 4) * 2 // 3)
    spec_h = max(2, h - 3 - scope_h)

    # Oscilloscope: braille-free, one glyph per column band.
    grid = [[" "] * w for _ in range(scope_h)]
    prev = None
    for x in range(w):
        v = wave(x, t)
        y = max(0, min(scope_h - 1, int((1 - v) / 2 * (scope_h - 1))))
        # Bridge the gap to the previous sample so the trace stays continuous
        # instead of breaking into dashes on steep slopes.
        if prev is not None and abs(y - prev) > 1:
            step = 1 if y > prev else -1
            for yy in range(prev + step, y, step):
                grid[yy][x] = "│"
        grid[y][x] = "●" if x % 7 == int(t * 9) % 7 else "─"
        prev = y
    mid = scope_h // 2
    for y in range(scope_h):
        row = []
        for x in range(w):
            ch = grid[y][x]
            if ch == " ":
                row.append(f"{G0}{'┄' if y == mid and x % 2 == 0 else ' '}")
            elif ch == "●":
                row.append(f"{WHT}●")
            elif ch == "│":
                row.append(f"{G1}│")
            else:
                row.append(f"{G3}─")
        out.append("".join(row) + RST)

    # Spectrum bars with decaying peak hold.
    n = w
    if len(state["bins"]) != n:
        state["bins"] = [0.0] * n
        state["peak"] = [0.0] * n
    for i in range(n):
        f = i / max(1, n - 1)
        env = math.exp(-((f - 0.28) ** 2) / 0.02) + 0.7 * math.exp(-((f - 0.72) ** 2) / 0.05)
        v = min(1.0, env * (0.55 + 0.45 * abs(math.sin(t * 1.7 + i * 0.4))) + random.uniform(0, 0.12))
        state["bins"][i] = max(v, state["bins"][i] * 0.72)
        state["peak"][i] = max(state["bins"][i], state["peak"][i] - 0.02)

    for row in range(spec_h):
        lo = 1 - (row + 1) / spec_h
        line = []
        for i in range(n):
            v = state["bins"][i]
            cell = (v - lo) * spec_h
            if cell >= 1:
                col = G3 if lo < 0.45 else (AMB if lo < 0.75 else RED)
                line.append(f"{col}█")
            elif cell > 0:
                col = G1 if lo < 0.45 else AMB
                line.append(f"{col}{SPARK[max(0, min(7, int(cell * 8)))]}")
            elif abs(state["peak"][i] - lo) < 1.0 / spec_h:
                line.append(f"{C1}·")
            else:
                line.append(" ")
        out.append("".join(line) + RST)

    lock = "LOCKED" if int(t) % 11 else "SEEKING"
    out.append(
        f"{C1}CARR {G4}2.412GHz{C1} · SNR {G3}{18 + 6 * math.sin(t):.1f}dB{C1} · "
        f"{(G4 if lock == 'LOCKED' else AMB)}{lock}{RST}"
    )
    return out


run(render, fps=14)
