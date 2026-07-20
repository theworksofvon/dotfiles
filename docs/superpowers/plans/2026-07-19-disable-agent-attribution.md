# Disable Agent Attribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent Claude Code, Codex, and Cursor from adding AI attribution to future commits and pull requests.

**Architecture:** Use each harness's native attribution setting to disable automatic tags, then add one shared instruction for PR surfaces without a native setting. A configuration regression test parses the tracked and live config shapes to prevent attribution from being re-enabled accidentally.

**Tech Stack:** JSON, TOML, Markdown, Python standard library (`json`, `tomllib`)

## Global Constraints

- Do not rewrite existing Git history.
- Do not add repository Git hooks that affect human-authored commits.
- Suppress AI identity, co-author, generated-by, and session-link attribution in commits, PR titles, and PR bodies.

---

### Task 1: Disable attribution across all harnesses

**Files:**

- Create: `test/agent-attribution.test.py`
- Modify: `agents/claude/settings.json`
- Modify: `agents/codex/config.example.toml`
- Modify: `agents/codex/config.toml`
- Modify: `agents/cursor/cli-config.json`
- Modify: `agents/AGENTS.md`

**Interfaces:**

- Consumes: Claude Code `attribution`, Codex `commit_attribution`, and Cursor `attribution` configuration surfaces.
- Produces: Agent configs that omit automatic attribution and a shared instruction covering generated PR text.

- [ ] **Step 1: Write the failing configuration test**

Create `test/agent-attribution.test.py`:

```python
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
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python3 test/agent-attribution.test.py
```

Expected: `KeyError: 'attribution'` for Claude, proving the native settings are not configured yet.

- [ ] **Step 3: Add the native harness settings**

In `agents/claude/settings.json`, add this top-level object after `theme`:

```json
"attribution": {
  "commit": "",
  "pr": "",
  "sessionUrl": false
},
```

In both `agents/codex/config.example.toml` and the gitignored live
`agents/codex/config.toml`, add this top-level key before the first TOML table:

```toml
commit_attribution = ""
```

In `agents/cursor/cli-config.json`, change the existing attribution values:

```json
"attribution": {
  "attributeCommitsToAgent": false,
  "attributePRsToAgent": false
}
```

- [ ] **Step 4: Add shared PR-text guidance**

Add this bullet under `## Git` in `agents/AGENTS.md`:

```markdown
- Do not add AI attribution, co-author trailers, generated-by text, or agent
  session links to commits, PR titles, or PR bodies.
```

- [ ] **Step 5: Run all configuration tests**

Run:

```bash
python3 test/agent-attribution.test.py
bash test/guard-main.test.sh
python3 test/codex-hooks.test.py
python3 test/cursor-hooks.test.py
node -e 'JSON.parse(require("fs").readFileSync("agents/claude/settings.json")); JSON.parse(require("fs").readFileSync("agents/cursor/cli-config.json"))'
git diff --check
```

Expected: every command exits `0`; attribution test prints
`Agent attribution is disabled`; guard test reports zero failures; both hook
tests report valid configs.

- [ ] **Step 6: Commit when explicitly requested**

```bash
git add agents/AGENTS.md agents/claude/settings.json \
  agents/codex/config.example.toml agents/cursor/cli-config.json \
  test/agent-attribution.test.py
git commit -m "chore: remove agent attribution from git metadata"
```
