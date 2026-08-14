#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Rotating sweep radar with decaying contacts."""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, RED, RST, WHT, header, run

state = {"blips": [], "angle": 0.0, "id": 0}
TAGS = ["UNK", "FRND", "HOST", "GHOST", "DRONE"]


def render(w, h, t):
    out = [header("RADAR", w, G3, G0)]
    body = max(5, h - 4)
    cx, cy = (w - 1) / 2, (body - 1) / 2
    rx, ry = cx, cy  # chars are ~2:1, so x-radius in cells is 2x the visual radius

    state["angle"] = (state["angle"] + 0.22) % (2 * math.pi)
    a = state["angle"]

    if random.random() < 0.06 and len(state["blips"]) < 9:
        state["id"] += 1
        state["blips"].append(
            {
                "a": random.uniform(0, 2 * math.pi),
                "r": random.uniform(0.15, 0.95),
                "life": 0,
                "tag": random.choice(TAGS),
                "id": state["id"],
                "da": random.uniform(-0.02, 0.02),
            }
        )
    for b in state["blips"]:
        b["life"] += 1
        b["a"] += b["da"]
    state["blips"] = [b for b in state["blips"] if b["life"] < 240]

    grid = [[(G0, " ")] * w for _ in range(body)]
    grid = [[(G0, " ") for _ in range(w)] for _ in range(body)]

    # Range rings.
    for ring in (0.33, 0.66, 1.0):
        steps = int(2 * math.pi * max(rx, ry) * ring) + 24
        for i in range(steps):
            th = 2 * math.pi * i / steps
            x = int(round(cx + math.cos(th) * rx * ring))
            y = int(round(cy + math.sin(th) * ry * ring))
            if 0 <= x < w and 0 <= y < body:
                grid[y][x] = (G0, "·")
    # Cross-hairs.
    for x in range(w):
        if grid[int(cy)][x][1] == " ":
            grid[int(cy)][x] = (G0, "─")
    for y in range(body):
        if grid[y][int(cx)][1] == " ":
            grid[y][int(cx)] = (G0, "│")

    # Sweep with a fading tail.
    for k in range(22):
        th = a - k * 0.055
        shade = G4 if k < 2 else (G3 if k < 6 else (G1 if k < 12 else G0))
        for step in range(1, int(max(rx, ry) * 2) + 1):
            f = step / (max(rx, ry) * 2)
            x = int(round(cx + math.cos(th) * rx * f))
            y = int(round(cy + math.sin(th) * ry * f))
            if 0 <= x < w and 0 <= y < body:
                grid[y][x] = (shade, "░" if k > 5 else "▒")

    # Contacts brighten when the beam passes them.
    for b in state["blips"]:
        x = int(round(cx + math.cos(b["a"]) * rx * b["r"]))
        y = int(round(cy + math.sin(b["a"]) * ry * b["r"]))
        if not (0 <= x < w and 0 <= y < body):
            continue
        d = abs(((b["a"] - a + math.pi) % (2 * math.pi)) - math.pi)
        if d < 0.25:
            grid[y][x] = (WHT, "◉")
        elif b["life"] < 120:
            grid[y][x] = ((RED if b["tag"] == "HOST" else G3), "◆")
        else:
            grid[y][x] = (G1, "◇")

    for y in range(body):
        row = []
        cur = None
        for x in range(w):
            c, ch = grid[y][x]
            if c != cur:
                row.append(c)
                cur = c
            row.append(ch)
        out.append("".join(row) + RST)

    out.append(f"{G0}{'─' * w}{RST}")
    hostiles = sum(1 for b in state["blips"] if b["tag"] == "HOST")
    out.append(
        f"{G1}BRG {G3}{math.degrees(a):05.1f}°{G1} CTC {G3}{len(state['blips']):02d}{G1} "
        f"HOS {(RED if hostiles else G3)}{hostiles:02d}{RST}"
    )
    return out


run(render, fps=13)
