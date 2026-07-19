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

> Clone to `~/dotfiles` — a few configs reference that path. Setup warns if you
> don't.

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

**Shell** — oh-my-zsh with nvm, bun, and mise. Also a Claude account switcher
(`claude-personal`, `claude-cm`) that swaps logins via the Keychain, since macOS
only stores one set of credentials at a time.

**Supply chain** — mise refuses any release less than 7 days old, long enough for
a bad package to be caught upstream. Node projects want
`minimum-release-age=10080` in `.npmrc` (pnpm 10.16+).

## Layout

```
setup.sh     install prerequisites, then link
install.sh   link only
zsh/ git/ starship/ ghostty/ mise/ claude/
vendor/      borrowed scripts — see vendor/gsong/README.md
```

Configs are symlinked, so editing a live file edits this repo. Commit and push;
there's no copy-back step. Replaced files are backed up to `*.bak`.

## Credits

`vendor/gsong/` holds two Claude Code scripts from
[gsong/home-directory](https://github.com/gsong/home-directory) — the usage
meter and the notification hook. See
[`vendor/gsong/README.md`](vendor/gsong/README.md) for license status.
