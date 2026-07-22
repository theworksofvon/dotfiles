#!/usr/bin/env python3
import pathlib
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent

for name in ("config.toml", "config.example.toml"):
    path = ROOT / "agents" / "codex" / name
    with path.open("rb") as file:
        config = tomllib.load(file)

    features = config["features"]
    assert features.get("hooks") is True, f"{path}: hooks feature is not enabled"
    assert "codex_hooks" not in features, (
        f"{path}: deprecated codex_hooks feature is set"
    )

    groups = config["hooks"]["PreToolUse"]
    bash_groups = [group for group in groups if group["matcher"] == "^Bash$"]
    assert len(bash_groups) == 1, f"{path}: expected one exact Bash hook group"

    handlers = bash_groups[0]["hooks"]
    assert len(handlers) == 1, f"{path}: expected one Bash hook handler"
    assert handlers[0]["type"] == "command"
    assert handlers[0]["command"] == "$HOME/.dotfiles/bin/guard-main"

print("Codex hook config is valid")
