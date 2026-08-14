#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Live host telemetry: real load, memory, disk, uptime — bars and sparklines."""

import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import AMB, C1, C3, G0, G1, G2, G3, G4, RED, RST, WHT, bar, header, run

SPARK = "▁▂▃▄▅▆▇█"
NCPU = os.cpu_count() or 8
state = {
    "t": 0.0,
    "mem": 0.0,
    "cpu": 0.0,
    "hist": [],
    "boot": 0,
    "disk": 0.0,
    "procs": 0,
}


def sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return ""


def sample():
    """Refresh the slow syscalls at most twice a second."""
    now = time.time()
    if now - state["t"] < 2.0:
        return
    state["t"] = now

    out = sh(["vm_stat"])
    pages = {}
    for line in out.splitlines()[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            pages[k.strip()] = int(v.strip().rstrip("."))
    free = pages.get("Pages free", 0) + pages.get("Pages speculative", 0)
    total_pages = sum(
        pages.get(k, 0)
        for k in (
            "Pages free",
            "Pages active",
            "Pages inactive",
            "Pages speculative",
            "Pages wired down",
            "Pages occupied by compressor",
        )
    )
    if total_pages:
        state["mem"] = 1.0 - free / total_pages

    if not state["boot"]:
        bt = sh(["sysctl", "-n", "kern.boottime"])
        if "sec = " in bt:
            state["boot"] = int(bt.split("sec = ")[1].split(",")[0])

    st = os.statvfs("/")
    state["disk"] = 1.0 - (st.f_bavail / st.f_blocks if st.f_blocks else 0)

    state["procs"] = max(0, len(sh(["ps", "-A", "-o", "pid="]).splitlines()))


def uptime():
    if not state["boot"]:
        return "--:--:--"
    s = int(time.time() - state["boot"])
    return f"{s // 86400}d {s % 86400 // 3600:02d}h {s % 3600 // 60:02d}m"


def render(w, h, t):
    sample()
    l1, l5, l15 = os.getloadavg()
    cpu = min(1.0, l1 / NCPU)
    state["hist"].append(cpu)
    del state["hist"][: max(0, len(state["hist"]) - 200)]

    bw = max(6, w - 14)
    out = [header("SYS.TELEMETRY", w, C3, C1)]

    def gauge(name, frac, txt):
        col = G3 if frac < 0.7 else (AMB if frac < 0.9 else RED)
        return f"{G1}{name:<5}{RST}{bar(frac, bw, col)} {col}{txt:>5}{RST}"

    out.append(gauge("CPU", cpu, f"{cpu * 100:.0f}%"))
    out.append(gauge("MEM", state["mem"], f"{state['mem'] * 100:.0f}%"))
    out.append(gauge("DISK", state["disk"], f"{state['disk'] * 100:.0f}%"))
    out.append("")

    spk = "".join(SPARK[min(7, int(v * 7.999))] for v in state["hist"][-(w - 2) :])
    out.append(f"{G0}LOAD 60s{RST}")
    out.append(f"{G4}{spk}{RST}")
    out.append("")
    out.append(f"{G1}LOADAVG {G3}{l1:5.2f}{G2} {l5:5.2f}{G1} {l15:5.2f}{RST}")
    out.append(f"{G1}CORES   {G3}{NCPU:<6}{G1}PROCS {G3}{state['procs']}{RST}")
    out.append(f"{G1}UPTIME  {G3}{uptime()}{RST}")
    out.append("")

    # Per-core activity ribbon, jittered around the real 1-min load.
    out.append(f"{G0}CORE ARRAY{RST}")
    row = []
    for i in range(NCPU):
        v = min(
            0.999, max(0.0, cpu + 0.35 * (((t * 3.1 + i * 1.7) % 2) - 1) * (0.4 + cpu))
        )
        col = G1 if v < 0.4 else (G3 if v < 0.75 else AMB)
        row.append(f"{col}{SPARK[int(v * 7.999)]}")
        if len(row) % 16 == 0:
            out.append("".join(row) + RST)
            row = []
    if row:
        out.append("".join(row) + RST)

    while len(out) < h - 1:
        out.append("")
    out.append(f"{C1}HOST {WHT}{os.uname().nodename[: w - 12]}{RST}")
    return out


run(render, fps=6)
