#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Falling-glyph rain."""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import G0, G1, G2, G4, RST, WHT, header, run

GLYPHS = "ｦｧｨｩｪｫｬｭｮｯｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜ0123456789$+-*/=<>#%&@"
TRAIL = [WHT, G4, G2, G2, G1, G1, G1, G0, G0, G0]

state = {"w": 0, "drops": []}


class Drop:
    __slots__ = ("y", "speed", "len", "chars")

    def __init__(self, h):
        self.reset(h, seed=True)

    def reset(self, h, seed=False):
        self.y = random.uniform(-h, 0) if seed else random.uniform(-12, -1)
        self.speed = random.uniform(0.35, 1.6)
        self.len = random.randint(4, max(5, h - 2))
        self.chars = [random.choice(GLYPHS) for _ in range(self.len + 2)]


def render(w, h, t):
    top = 1
    rows = h - top
    if rows < 2:
        return [header("MATRIX", w)]
    if state["w"] != w:
        state["w"] = w
        state["drops"] = [Drop(rows) for _ in range(w)]

    grid = [[" "] * w for _ in range(rows)]
    colr = [[None] * w for _ in range(rows)]

    for x, d in enumerate(state["drops"]):
        d.y += d.speed
        if random.random() < 0.25:
            d.chars[random.randrange(len(d.chars))] = random.choice(GLYPHS)
        head = int(d.y)
        for i in range(d.len):
            y = head - i
            if 0 <= y < rows:
                grid[y][x] = d.chars[i % len(d.chars)]
                shade = TRAIL[min(int(i / max(1, d.len) * len(TRAIL)), len(TRAIL) - 1)]
                colr[y][x] = shade
        if head - d.len > rows:
            d.reset(rows)

    out = [header("MATRIX ∷ STREAM", w)]
    for y in range(rows):
        line = []
        cur = None
        for x in range(w):
            c = colr[y][x]
            if c and c != cur:
                line.append(c)
                cur = c
            line.append(grid[y][x] if c else " ")
        out.append("".join(line) + RST)
    return out


run(render, fps=14)
