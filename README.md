# dotfiles

My macOS terminal and development setup: a [Starship](https://starship.rs/)
prompt with swappable presets, [Ghostty](https://ghostty.org/), zsh, git, and a
[Claude Code](https://claude.com/claude-code) configuration that surfaces usage
limits in the prompt and formats every file it writes.

## What's here

```
zsh/zshrc            # shell: oh-my-zsh, nvm, bun, mise, starship
git/gitconfig        # identity + histogram diffs, zdiff3, rerere, sane rebase
starship/
  bridge.toml        # "bridge"  — horizontal command-console prompt (default)
  mission.toml       # "mission" — vertical mission-control checklist
ghostty/config       # JetBrainsMono Nerd Font Mono, tokyonight
mise/config.toml     # CLI tools + 7-day minimum release age
claude/settings.json # Claude Code hooks, status line, formatters
vendor/gsong/        # two scripts borrowed from another repo — see its README
install.sh           # symlinks everything into place
```

## Install on a new machine

```sh
git clone https://github.com/theworksofvon/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

`install.sh` creates **symlinks**, so editing a live config edits this repo —
there is no copy-back step. Any existing real file is backed up to `*.bak`
first.

### Prerequisites

```sh
brew install starship mise jq
brew install --cask font-jetbrains-mono-nerd-font ghostty
mise install    # prettier + sqlfluff
```

## Switch prompt presets

```sh
prompt-style bridge     # horizontal console (default)
prompt-style mission    # vertical checklist
```

The active prompt (`~/.config/starship.toml`) is a symlink; `prompt-style`
re-points it. Press Enter after switching — no restart needed.

## Claude Code setup

**Usage meter in the prompt.** The `[custom.claude]` Starship module shows
`🟢8pm 🟢4d` — the 5-hour block resets at 8pm, and 4 days remain in the 7-day
window. The circle tracks _burn rate_, not raw usage: 🟢 under 1.0 (spending
slower than the clock), 🟡 up to 1.3, 🔴 above 1.3 (on pace to run out early).
Reads a 5-minute cache, ~25ms per prompt.

**Notifications.** A Stop/Notification hook fires a macOS notification only when
Ghostty isn't frontmost or the tmux pane isn't active — quiet while you're
watching, audible when you've walked away.

**Formatting.** A `PostToolUse` hook formats every file Claude writes, by
extension: `ruff` for Python, `sqlfluff` for SQL, `prettier` for
JS/TS/JSON/CSS/HTML/Markdown/YAML.

## Supply-chain note

`mise/config.toml` sets `minimum_release_age = "7d"`, so mise refuses to install
any release less than a week old — long enough for a compromised package to be
caught and yanked upstream. For Node projects the equivalent is
`minimum-release-age=10080` in a project `.npmrc` (pnpm 10.16+).

## Credits

`vendor/gsong/` contains two Claude Code scripts from
[gsong/home-directory](https://github.com/gsong/home-directory). See
[`vendor/gsong/README.md`](vendor/gsong/README.md) for details and license
status.
