# dotfiles

macOS terminal setup: zsh, Starship, Ghostty, git, and Claude Code.

## Install

```sh
git clone https://github.com/theworksofvon/dotfiles.git ~/dotfiles
cd ~/dotfiles && ./setup.sh
```

Installs anything missing (Homebrew, starship, mise, jq, Ghostty, the Nerd Font,
oh-my-zsh), then symlinks the configs. **Idempotent** — it checks before
installing, so re-running is safe and only fills in gaps.

```sh
./setup.sh --dry-run      # show what would happen
./setup.sh --no-install   # link configs only
./install.sh              # link configs only (same thing, no prereq checks)
```

Restart your terminal when it finishes.

Clone anywhere — `install.sh` links `~/.dotfiles` to wherever it lives, and
configs reference that. Your git identity goes in `~/.gitconfig.local`, which
setup creates and never tracks, so a fork doesn't commit as me.

## What you get

**Prompt** — Starship with a live Claude usage meter: `🟢8pm 🟢4d` means your
5-hour block resets at 8pm and 4 days remain on the weekly window. The circle
tracks burn rate, not raw usage — 🟢 spending slower than the clock, 🟡 slightly
ahead, 🔴 on pace to run out early.

Two presets, swappable instantly:

```sh
prompt-style bridge     # horizontal console (default)
prompt-style mission    # vertical checklist
```

**Claude Code** — notifications that only fire when you're _not_ looking at the
terminal, and a hook that auto-formats every file Claude writes (ruff for
Python, sqlfluff for SQL, prettier for web files). Missing formatters are
skipped, not errors.

**Git** — histogram diffs, `zdiff3` conflict markers, and rerere, which
remembers how you resolved a conflict and replays it next time. Rebase
autosquashes and autostashes; push sets upstream automatically.

**tmux** — mainly for persistence: `C-b d` detaches, `tmux a` reattaches, and
long-running work survives closing the terminal. Default `C-b` prefix so any
cheatsheet applies. `C-b |` and `C-b -` split, `C-b hjkl` moves between panes,
`y` in copy mode yanks to the system clipboard. Styled to match the prompt.

**Shell** — oh-my-zsh with nvm, bun, and mise. Also a Claude account switcher
(`claude-personal`, `claude-cm`) that swaps logins via the Keychain, since macOS
only stores one set of credentials at a time.

**Supply chain** — mise refuses any release less than 7 days old, long enough for
a bad package to be caught upstream. Node projects want
`minimum-release-age=10080` in `.npmrc` (pnpm 10.16+).

## Guardrails

Claude, Codex, and Cursor are each restricted from writing outside the project
without approval, and from destructive commands — recursive deletes, force
pushes, history rewrites — plus reads of `.env`, SSH keys, and credentials.
Pre-tool hooks also block agent pushes and merges to protected branches,
including implicit `git push` commands issued while checked out on `main`.

Claude uses `ask`/`deny` rules; Codex and Cursor use their sandboxes, which
enforce it rather than prompting. opencode is supported but not covered.

## Layout

```
setup.sh     install prerequisites, then link
install.sh   link only
agents/      shared AGENTS.md + per-agent config (claude, codex,
             cursor, opencode); each linked only if installed
bin/         usage meters, notifier, status-line widgets
zsh/ git/ tmux/ nvim/ starship/ ghostty/ mise/ claude/
```

Configs are symlinked, so editing a live file edits this repo. Commit and push;
there's no copy-back step. Replaced files are backed up to `*.bak`.

## Commands

```sh
ai-usage        every provider at once
claude-usage    limits, token counts, per-model breakdown
codex-usage     quota and tokens from Codex session logs
opencode-usage  cost and tokens (optional; only if opencode is installed)
usage-alert     notify past 80%; runs backgrounded at shell start
handoff         move a conversation to another agent
agent-rules     drop shared AGENTS.md into a project
```

Each takes `--short` and `--json`; `claude-usage` also takes `--prompt`.

## License

MIT — see [LICENSE](LICENSE). The Claude Code approach here was inspired by
[gsong/home-directory](https://github.com/gsong/home-directory), which is worth
reading if you're building something similar.
