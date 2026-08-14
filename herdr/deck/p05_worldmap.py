#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Global threat map: coarse continent mask, live attack vectors, node lock-ons."""

import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G3, G4, RED, RST, WHT, header, run

# Land mask as column spans on a 64x16 equirectangular grid (lon -180..180, lat 80..-56).
MW, MH = 64, 16
LAND = {
    0: [(11, 25), (26, 31), (37, 62)],
    1: [(9, 25), (27, 31), (36, 62)],
    2: [(8, 24), (33, 40), (41, 62)],
    3: [(8, 23), (32, 45), (46, 60)],
    4: [(9, 22), (31, 44), (47, 58)],
    5: [(10, 20), (30, 36), (38, 42), (44, 56)],
    6: [(13, 19), (31, 40), (43, 54)],
    7: [(16, 20), (31, 41), (45, 52)],
    8: [(18, 22), (32, 40), (46, 50)],
    9: [(19, 24), (33, 39), (47, 51)],
    10: [(19, 24), (33, 38), (50, 52)],
    11: [(20, 24), (34, 38), (52, 58)],
    12: [(20, 23), (34, 37), (51, 58)],
    13: [(20, 23), (35, 37), (53, 57)],
    14: [(20, 22), (56, 58)],
    15: [],
}

NODES = [
    ("NYC", 40.7, -74.0),
    ("LON", 51.5, -0.1),
    ("MOW", 55.7, 37.6),
    ("BJS", 39.9, 116.4),
    ("TYO", 35.6, 139.7),
    ("SYD", -33.8, 151.2),
    ("GRU", -23.5, -46.6),
    ("JNB", -26.2, 28.0),
    ("DXB", 25.2, 55.2),
    ("SFO", 37.7, -122.4),
    ("BOM", 19.0, 72.8),
    ("BER", 52.5, 13.4),
    ("SIN", 1.3, 103.8),
    ("YYZ", 43.6, -79.3),
    ("REY", 64.1, -21.9),
]
VERBS = ["EXFIL", "PROBE", "INJECT", "RELAY", "SPOOF", "TUNNEL", "HARVEST"]

state = {"vectors": [], "log": [], "hits": 0, "blocked": 0}


def landmask(w, h):
    grid = [[False] * w for _ in range(h)]
    for y in range(h):
        my = min(MH - 1, int(y * MH / h))
        for a, b in LAND[my]:
            for mx in range(a, b):
                x = int(mx * w / MW)
                if 0 <= x < w:
                    grid[y][x] = True
    return grid


def project(lat, lon, w, h):
    x = int((lon + 180) / 360 * w)
    y = int((80 - lat) / 136 * h)
    return max(0, min(w - 1, x)), max(0, min(h - 1, y))


def line(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return pts
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def spawn(w, h):
    a, b = random.sample(NODES, 2)
    p0 = project(a[1], a[2], w, h)
    p1 = project(b[1], b[2], w, h)
    hostile = random.random() < 0.5
    state["vectors"].append(
        {"pts": line(*p0, *p1), "i": 0.0, "spd": random.uniform(1.4, 4.0), "hot": hostile,
         "src": a[0], "dst": b[0], "age": 0}
    )
    verb = random.choice(VERBS)
    if hostile:
        state["hits"] += 1
        state["log"].append(f"{RED}▲ {verb} {a[0]}→{b[0]} BLOCKED")
        state["blocked"] += 1
    else:
        state["log"].append(f"{G1}· {verb} {a[0]}→{b[0]} ok")
    del state["log"][:-3]


def render(w, h, t):
    mh = max(4, h - 2)
    mw = w
    grid = landmask(mw, mh)
    cells = [[None] * mw for _ in range(mh)]

    for y in range(mh):
        for x in range(mw):
            cells[y][x] = (G0, "▒") if grid[y][x] else (f"\x1b[38;5;17m", "·")

    if random.random() < 0.10 and len(state["vectors"]) < 7:
        spawn(mw, mh)

    for v in state["vectors"]:
        v["i"] += v["spd"]
        n = int(min(v["i"], len(v["pts"])))
        col = RED if v["hot"] else C1
        for j, (x, y) in enumerate(v["pts"][:n]):
            fresh = j > n - 6
            cells[y][x] = ((WHT if fresh and v["hot"] else (C3 if fresh else col)), "•" if fresh else "─")
        if n >= len(v["pts"]):
            v["age"] += 1
            x, y = v["pts"][-1]
            cells[y][x] = ((RED, "◉") if v["hot"] and v["age"] % 4 < 2 else (G4, "◎"))
    state["vectors"] = [v for v in state["vectors"] if v["age"] < 26]

    for name, lat, lon in NODES:
        x, y = project(lat, lon, mw, mh)
        if cells[y][x][1] in ("▒", "·"):
            cells[y][x] = (G3, "▪")

    out = [header("GLOBAL THREAT MAP ∷ LIVE", w, C3, C1)]
    for y in range(mh):
        line_s = []
        cur = None
        for x in range(mw):
            c, ch = cells[y][x]
            if c != cur:
                line_s.append(c)
                cur = c
            line_s.append(ch)
        out.append("".join(line_s) + RST)

    tail = " ".join(state["log"][-2:]) if state["log"] else ""
    left = f"{C1}NODES {WHT}{len(NODES)}{C1} · VECTORS {WHT}{len(state['vectors'])}{C1} · BLOCKED {RED}{state['blocked']:04d}{RST}"
    out.append(f"{left}  {tail}{RST}")
    return out


run(render, fps=10)
