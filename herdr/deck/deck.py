"""Shared plumbing for the panel scripts: framebuffer loop, ANSI-safe clipping, palette."""

import json
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

# 256-colour phosphor palette.
G0 = "\x1b[38;5;22m"
G1 = "\x1b[38;5;28m"
G2 = "\x1b[38;5;40m"
G3 = "\x1b[38;5;46m"
G4 = "\x1b[38;5;120m"
C0 = "\x1b[38;5;23m"
C1 = "\x1b[38;5;30m"
C2 = "\x1b[38;5;44m"
C3 = "\x1b[38;5;51m"
AMB = "\x1b[38;5;214m"
RED = "\x1b[38;5;196m"
MAG = "\x1b[38;5;171m"
WHT = "\x1b[38;5;231m"
GRY = "\x1b[38;5;240m"
BLD = "\x1b[1m"
DIM = "\x1b[2m"
RST = "\x1b[0m"

_ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")

BOX_H = "─"


def size():
    s = shutil.get_terminal_size((80, 24))
    return s.columns, s.lines


def vlen(s):
    return len(_ANSI.sub("", s))


def clip(s, w):
    """Truncate to w visible columns, keeping escape sequences intact."""
    if vlen(s) <= w:
        return s
    out = []
    seen = 0
    i = 0
    while i < len(s) and seen < w:
        m = _ANSI.match(s, i)
        if m:
            out.append(m.group())
            i = m.end()
            continue
        out.append(s[i])
        seen += 1
        i += 1
    return "".join(out)


def pad(s, w):
    n = vlen(s)
    return s + " " * (w - n) if n < w else clip(s, w)


def header(title, w, c=G3, accent=G0):
    """Title bar: reverse-video label followed by a rule."""
    label = f"{c}{BLD} {title} {RST}"
    rule = BOX_H * max(0, w - vlen(label) - 1)
    return f"{label}{accent}{rule}{RST}"


def bar(frac, w, on=G3, off=G0, ch="█", offch="─"):
    frac = 0.0 if frac < 0 else (1.0 if frac > 1 else frac)
    n = int(round(frac * w))
    return f"{on}{ch * n}{off}{offch * (w - n)}{RST}"


def rule(w, c=G0, ch=BOX_H):
    return f"{c}{ch * w}{RST}"


def stamp(t=None):
    lt = time.localtime(t)
    return time.strftime("%H:%M:%S", lt)


def hexs(n, upper=True):
    s = "".join(random.choice("0123456789ABCDEF") for _ in range(n))
    return s if upper else s.lower()


def sh(cmd, cwd=None, timeout=15):
    """Run a command, return stdout ('' on any failure). Never raises."""
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd
        ).stdout
    except Exception:
        return ""


def shj(cmd, cwd=None, timeout=15, default=None):
    try:
        return json.loads(sh(cmd, cwd, timeout) or "null") or default
    except Exception:
        return default


def poller(fn, interval, initial=None):
    """Keep slow work (git, gh, sqlite) off the render loop.

    Returns a dict whose "v" holds the latest successful result.
    """
    box = {"v": initial, "err": None, "at": 0.0, "runs": 0}

    def loop():
        while True:
            try:
                box["v"] = fn()
                box["err"] = None
            except Exception as e:
                box["err"] = f"{type(e).__name__}: {e}"[:60]
            box["at"] = time.time()
            box["runs"] += 1
            time.sleep(interval)

    threading.Thread(target=loop, daemon=True).start()
    return box


def age(box):
    """Human 'last refreshed' marker for a poller box."""
    if not box["at"]:
        return "…"
    d = int(time.time() - box["at"])
    return f"{d}s" if d < 90 else f"{d // 60}m"


def run(render, fps=10):
    """Drive render(w, h, t) -> [lines] as a flicker-free full-pane framebuffer."""

    def restore(*_):
        sys.stdout.write("\x1b[?25h" + RST + "\n")
        sys.stdout.flush()
        os._exit(0)

    signal.signal(signal.SIGINT, restore)
    signal.signal(signal.SIGTERM, restore)
    signal.signal(signal.SIGHUP, restore)
    sys.stdout.write("\x1b[?25l\x1b[2J")
    delay = 1.0 / fps
    t0 = time.time()
    try:
        while True:
            w, h = size()
            lines = render(w, h, time.time() - t0)
            out = ["\x1b[H"]
            for i in range(h):
                out.append(clip(lines[i], w) if i < len(lines) else "")
                out.append(RST + "\x1b[K")
                if i < h - 1:
                    out.append("\r\n")
            sys.stdout.write("".join(out))
            sys.stdout.flush()
            time.sleep(delay)
    except (KeyboardInterrupt, BrokenPipeError):
        restore()
