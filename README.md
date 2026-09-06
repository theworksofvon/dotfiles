# dotfiles

macOS terminal: zsh, Starship, Ghostty, git, and coding agents.

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

|                  |                                               |                               |
| ---------------- | --------------------------------------------- | ----------------------------- |
| `ai-usage`       | every provider at once, one block each        | `--short` `--json`            |
| `claude-usage`   | limits, tokens, per-model breakdown           | `--short` `--json` `--prompt` |
| `codex-usage`    | quota and tokens from session logs            | `--short` `--json`            |
| `opencode-usage` | cost and tokens (only if installed)           | `--short` `--json`            |
| `usage-alert`    | notify past 80%, backgrounded at shell start  | `--short`                     |
| `handoff`        | move a conversation to another agent          | `--full` `--stdout` `--force` |
| `agent-rules`    | drop shared AGENTS.md into a project          |                               |
| `git-pr`         | PR number for the branch, for the status line |                               |
| `prompt-style`   | swap presets: `bridge` or `mission`           |                               |
| `cc`             | Claude as this directory's account            | `cc 2` for a specific one     |
| `gh-whoami`      | which GitHub account gh would use from here   |                               |
| `claude-whoami`  | which Claude account `cc` would launch here   |                               |

## Accounts

Work and personal are two separate logins on every tool, and all three pick the
same way — by directory. Under `~/costmine` you are work; everywhere else you
are personal. Nothing to switch, and nothing to remember before a push.

| tool     | mechanism                                                           |
| -------- | ------------------------------------------------------------------- |
| `git`    | `includeIf "gitdir:~/costmine/"` → `~/.gitconfig.work`, own SSH key |
| `gh`     | `bin/gh` picks the matching account's token per invocation          |
| `claude` | `cswap` gives each account its own `CLAUDE_CONFIG_DIR`              |

`bin/gh` is a shim on PATH rather than a shell function, so a Makefile, a git
alias, or an MCP server gets the same routing an interactive shell does. It has
to outrank the Homebrew `gh`, which is why `~/.dotfiles/bin` is prepended last
in `zshrc` — after brew and mise have had their turn.

Claude keeps one login per machine, so accounts move via
[claude-swap](https://github.com/realiti4/claude-swap) (`cswap`, installed by
mise). It hands each account its own config dir, which is what Claude hashes
into its Keychain service name — so the logins are genuinely separate and two
accounts can run at once instead of taking turns on a shared entry. `cswap map`
holds the directory rules, `cswap list` shows live usage per account. Run
`cc` and you get whichever account owns the directory you're standing in.

One-time setup on a new machine: `gh auth login --user <name>` for each GitHub
account, then `cswap add` while logged into each Claude account.

## Prompt

The Claude meter reads `🟢8pm 🟢4d` — the 5-hour block resets at 8pm, 4 days
remain on the weekly window. Colour tracks burn **rate**, not raw usage: 🟢
spending slower than the clock, 🟡 slightly ahead, 🔴 on pace to run out early.

## Guardrails

Claude and Codex are both blocked from writing outside the project without
approval, from destructive commands (recursive deletes, force pushes, history
rewrites), and from reading `.env`, SSH keys, and credentials. Pre-tool hooks
block pushes and merges to protected branches, including an implicit
`git push` issued while sitting on `main`.

Claude uses `ask`/`deny` rules; Codex uses its sandbox, which enforces rather
than prompts. opencode is configured but not covered by either.

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
- **Ghostty** — `cmd+d` and `cmd+shift+d` split, `cmd+opt+arrow` moves,
  `cmd+up`/`cmd+down` jump between prompts.

## Layout

```
setup.sh     install prerequisites, then link
install.sh   link only
agents/      shared AGENTS.md + per-agent config; each linked only if installed
bin/         usage meters, guards, notifier, status-line widgets, gh routing
test/        run any file directly; no runner
```

Configs are symlinked, so editing a live file edits this repo — commit and push,
there is no copy-back step. Replaced files are backed up to `*.bak`.

## License

MIT — see [LICENSE](LICENSE). The Claude Code approach here was inspired by
[gsong/home-directory](https://github.com/gsong/home-directory).
