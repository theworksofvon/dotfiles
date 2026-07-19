#!/usr/bin/env python3
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

with (ROOT / "agents" / "cursor" / "hooks.json").open() as file:
    config = json.load(file)

hooks = config["hooks"]["beforeShellExecution"]
assert len(hooks) == 1, "expected one beforeShellExecution hook"
hook = hooks[0]
assert hook["command"] == "$HOME/.dotfiles/bin/guard-main"
assert hook["matcher"] == r"\bgit\s+(push|merge)\b|\bgh\s+pr\s+merge\b"
assert hook["failClosed"] is True

install = (ROOT / "install.sh").read_text()
assert 'link agents/cursor/hooks.json      "$HOME/.cursor/hooks.json"' in install, (
    "install.sh does not link Cursor hooks"
)

print("Cursor hook config is valid")
