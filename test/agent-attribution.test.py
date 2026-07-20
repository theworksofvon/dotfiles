#!/usr/bin/env python3
import json
import pathlib
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent

with (ROOT / "agents" / "claude" / "settings.json").open() as file:
    claude = json.load(file)

assert claude["attribution"] == {
    "commit": "",
    "pr": "",
    "sessionUrl": False,
}

for name in ("config.toml", "config.example.toml"):
    path = ROOT / "agents" / "codex" / name
    with path.open("rb") as file:
        codex = tomllib.load(file)
    assert codex["commit_attribution"] == "", f"{path}: attribution is enabled"

with (ROOT / "agents" / "cursor" / "cli-config.json").open() as file:
    cursor = json.load(file)

assert cursor["attribution"] == {
    "attributeCommitsToAgent": False,
    "attributePRsToAgent": False,
}

instructions = (ROOT / "agents" / "AGENTS.md").read_text()
assert "Do not add AI attribution" in instructions

print("Agent attribution is disabled")
