# dotfiles

macOS terminal: zsh, Starship, Ghostty, tmux, git, and coding agents.

## Install

```sh
git clone https://github.com/theworksofvon/dotfiles.git ~/dotfiles
cd ~/dotfiles && ./setup.sh     # --dry-run to preview, --no-install to link only
```

Installs what's missing (Homebrew, starship, mise, jq, Ghostty, the Nerd Font,
oh-my-zsh), then symlinks the configs. Re-running only fills gaps. Restart the
terminal afterwards.

Clone anywhere: `install.sh` points `~/.dotfiles` at wherever this lives, and
configs reference that. Git identity goes in `~/.gitconfig.local`, untracked.

**Skills are not in this repo.** `model-orchestrator` and `pr-reviewer` live in
[agent-workflows](https://github.com/theworksofvon/agent-workflows); run
`pnpm skills:install` there to link them into `~/.claude` and `~/.codex`.

## Commands

|                                 |                                               |                               |
| ------------------------------- | --------------------------------------------- | ----------------------------- |
| `ai-usage`                      | every provider at once, one block each        | `--short` `--json`            |
| `claude-usage`                  | limits, tokens, per-model breakdown           | `--short` `--json` `--prompt` |
| `codex-usage`                   | quota and tokens from session logs            | `--short` `--json`            |
| `opencode-usage`                | cost and tokens (only if installed)           | `--short` `--json`            |
| `usage-alert`                   | notify past 80%, backgrounded at shell start  | `--short`                     |
| `handoff`                       | move a conversation to another agent          | `--full` `--stdout` `--force` |
| `agent-rules`                   | drop shared AGENTS.md into a project          |                               |
| `git-pr`                        | PR number for the branch, for the status line |                               |
| `prompt-style`                  | swap presets: `bridge` or `mission`           |                               |
| `claude-personal` / `claude-cm` | swap Claude logins via Keychain               |                               |

## Prompt

The Claude meter reads `🟢8pm 🟢4d` — the 5-hour block resets at 8pm, 4 days
remain on the weekly window. Colour tracks burn **rate**, not raw usage: 🟢
spending slower than the clock, 🟡 slightly ahead, 🔴 on pace to run out early.

## Guardrails

Claude, Codex, and Cursor are each blocked from writing outside the project
without approval, from destructive commands (recursive deletes, force pushes,
history rewrites), and from reading `.env`, SSH keys, and credentials. Pre-tool
hooks block pushes and merges to protected branches, including an implicit
`git push` issued while sitting on `main`.

Claude uses `ask`/`deny` rules; Codex and Cursor use their sandboxes, which
enforce rather than prompt. opencode is installed but not covered.

## Things worth remembering

- **Live configs** — Claude Code and Codex rewrite their own settings as they
  run, so those files are gitignored and seeded from a `*.example.*` sibling.
  `link_live` in `install.sh` fails the install if one is left tracked.
- **Supply chain** — mise refuses any release under 7 days old, long enough for
  a bad package to be caught upstream. Node projects want
  `minimum-release-age=10080` in `.npmrc` (pnpm 10.16+).
- **Claude hooks** — every file it writes gets formatted (ruff, sqlfluff,
  prettier; missing ones skipped). Notifications fire only when the terminal
  isn't focused.
- **git** — rerere replays how you resolved a conflict last time. Histogram
  diffs, `zdiff3` markers, rebase autosquash and autostash, push sets upstream.
- **tmux** — `C-b |` and `C-b -` split, `C-b hjkl` moves, `y` yanks to the
  system clipboard.

## Layout

```
setup.sh     install prerequisites, then link
install.sh   link only
agents/      shared AGENTS.md + per-agent config; each linked only if installed
bin/         usage meters, guards, notifier, status-line widgets
test/        run any file directly; no runner
```

Configs are symlinked, so editing a live file edits this repo — commit and push,
there is no copy-back step. Replaced files are backed up to `*.bak`.

## License

MIT — see [LICENSE](LICENSE). The Claude Code approach here was inspired by
[gsong/home-directory](https://github.com/gsong/home-directory).
