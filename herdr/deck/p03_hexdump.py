#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Scrolling memory dump with occasional signature hits."""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, G0, G1, G3, G4, RED, RST, WHT, header, run

SIGS = [b"\x89PNG\r\n", b"MZ\x90\x00", b"\x7fELF\x02\x01", b"PK\x03\x04", b"ssh-rsa ", b"BEGIN RSA"]
state = {"addr": random.randrange(0x7F00000000, 0x7FFFFFFFFF) & ~0xF, "rows": [], "hit": -99}


def newrow(nbytes):
    data = bytearray(random.randbytes(nbytes))
    tag = None
    if random.random() < 0.06:
        s = random.choice(SIGS)[:nbytes]
        off = random.randrange(0, max(1, nbytes - len(s) + 1))
        data[off : off + len(s)] = s
        tag = (off, len(s))
    addr = state["addr"]
    state["addr"] = (addr + nbytes) & 0xFFFFFFFFFFFF
    return addr, bytes(data), tag


def render(w, h, t):
    # Widest byte count that fits "ADDR  hex...  |ascii|" in this pane.
    nb = 8
    while nb > 2 and 6 + nb * 3 + 2 + nb + 2 > w:
        nb -= 1
    rows = max(1, h - 2)
    while len(state["rows"]) < rows:
        state["rows"].append(newrow(nb))
    state["rows"] = state["rows"][-rows:]
    if len(state["rows"][0][1]) != nb:
        state["rows"] = [newrow(nb) for _ in range(rows)]

    for _ in range(random.randint(1, 2)):
        state["rows"].append(newrow(nb))
        state["rows"].pop(0)

    out = [header("MEM.DUMP", w, G3, G0)]
    for i, (addr, data, tag) in enumerate(state["rows"]):
        fade = G0 if i < 2 else (G1 if i < 4 else G3)
        hexpart = []
        for j, b in enumerate(data):
            hot = tag and tag[0] <= j < tag[0] + tag[1]
            hexpart.append(f"{AMB if hot else fade}{b:02x}")
        asc = "".join(
            (chr(b) if 32 <= b < 127 else f"{G0}·{fade}") for b in data
        )
        col = RED if tag else fade
        out.append(
            f"{col}{addr & 0xFFFFFF:06x} {' '.join(hexpart)}{fade} {G0}|{G4 if tag else fade}{asc}{G0}|{RST}"
        )
    out.append(f"{G0}SCAN {WHT}0x{state['addr'] & 0xFFFFFFFF:08x}{G0} · {G1}NO FAULT{RST}")
    return out


run(render, fps=9)
