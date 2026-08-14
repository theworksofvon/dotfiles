#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Cipher brute-force theatre: key digits lock in one at a time."""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, G0, G1, G3, G4, RED, RST, WHT, bar, header, run

HEX = "0123456789ABCDEF"
ALGOS = ["AES-256-GCM", "RSA-4096", "SHA-512/HMAC", "ED25519", "CHACHA20", "BLOWFISH-448"]
state = {"keys": [], "n": 0}


class Key:
    def __init__(self, width):
        self.reset(width)

    def reset(self, width):
        self.n = max(8, min(24, width))
        self.target = [random.choice(HEX) for _ in range(self.n)]
        self.locked = 0
        self.algo = random.choice(ALGOS)
        self.rate = random.uniform(0.06, 0.22)
        self.done = 0

    def step(self):
        if self.locked >= self.n:
            self.done += 1
            return
        if random.random() < self.rate:
            self.locked += 1

    def text(self):
        cells = []
        for i in range(self.n):
            if i < self.locked:
                cells.append(f"{G4}{self.target[i]}")
            else:
                cells.append(f"{G0}{random.choice(HEX)}")
        return "".join(cells)


def render(w, h, t):
    kw = max(8, min(20, w - 12))
    slots = max(1, (h - 3) // 3)
    while len(state["keys"]) < slots:
        state["keys"].append(Key(kw))
    del state["keys"][slots:]

    out = [header("CIPHER.BREAK", w, AMB, G0)]
    for i, k in enumerate(state["keys"]):
        k.step()
        if k.done > 14:
            state["n"] += 1
            k.reset(kw)
        frac = k.locked / k.n
        if k.locked >= k.n:
            tag = f"{G4}◆ KEY ACQUIRED"
            keyline = f"{G4}{''.join(k.target)}"
        else:
            tag = f"{G1}{k.algo}"
            keyline = k.text()
        out.append(f"{G1}[{i:02d}] {tag}{RST}")
        out.append(f"     {keyline}{RST}")
        col = G4 if frac >= 1 else (AMB if frac > 0.6 else G3)
        out.append(f"     {bar(frac, max(4, w - 12), col)} {col}{frac * 100:3.0f}%{RST}")
    while len(out) < h - 1:
        out.append("")
    out.append(f"{G0}BROKEN {WHT}{state['n']:04d}{G0} · ENTROPY {RED}LOW{RST}")
    return out


run(render, fps=12)
