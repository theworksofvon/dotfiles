#!/usr/bin/env bash
# Symlinks these dotfiles into place. Existing real files are backed up to *.bak.
#
# Symlinks (rather than copies) mean editing the live config edits the repo —
# no copy-back step. Idempotent: re-running relinks without re-backing up.
#
#   ./install.sh            link everything
#   ./install.sh --dry-run  print what would change, do nothing
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=false
[ "${1:-}" = "--dry-run" ] && DRY_RUN=true

dim=$(tput dim 2>/dev/null || true); reset=$(tput sgr0 2>/dev/null || true)
bold=$(tput bold 2>/dev/null || true)

# link <path-in-repo> <target-in-home>
link() {
  local src="$DOTFILES/$1" dst="$2" pretty="~${2#"$HOME"}"

  if [ ! -e "$src" ]; then
    echo "  missing in repo, skipped: $1" >&2
    return
  fi

  # Already pointing where we want it — nothing to do.
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "  ${dim}·${reset} $pretty"
    return
  fi

  if $DRY_RUN; then
    [ -e "$dst" ] && [ ! -L "$dst" ] && echo "  would back up $pretty -> $pretty.bak"
    echo "  would link $pretty -> $1"
    return
  fi

  mkdir -p "$(dirname "$dst")"
  # Back up only real files; never clobber an existing backup.
  if [ -e "$dst" ] && [ ! -L "$dst" ] && [ ! -e "$dst.bak" ]; then
    cp "$dst" "$dst.bak"
    echo "  backed up $pretty -> $pretty.bak"
  fi
  ln -sfn "$src" "$dst"
  echo "  + $pretty -> $1"
}

# link_live <path-in-repo> <target-in-home>
#
# Same as link, but for configs their tool rewrites as it runs. Tracking one of
# those turns every plugin install or model change into repo churn carrying
# absolute paths from whichever machine wrote it, so the live file is gitignored
# and seeded from a tracked .example sibling instead.
link_live() {
  local live="$1" example="${1%.*}.example.${1##*.}"

  if [ ! -e "$DOTFILES/$example" ]; then
    echo "  ${bold}!${reset} $live needs $example to seed from" >&2
    return 1
  fi

  # The mistake this helper exists to catch. Left tracked, the file looks fine
  # until the tool rewrites it and the diff lands in an unrelated commit.
  if git -C "$DOTFILES" rev-parse --is-inside-work-tree >/dev/null 2>&1 &&
     ! git -C "$DOTFILES" check-ignore -q "$live"; then
    echo "  ${bold}!${reset} $live is a live config but git still tracks it." >&2
    echo "    Add it to .gitignore, then: git rm --cached $live" >&2
    return 1
  fi

  [ -e "$DOTFILES/$live" ] || $DRY_RUN || cp "$DOTFILES/$example" "$DOTFILES/$live"
  link "$live" "$2"
}

# Config files can't compute their own location, so they reference
# ~/.dotfiles/bin/... — a stable symlink to wherever this repo was cloned.
# That's what lets the repo live anywhere instead of only in ~/dotfiles.
if [ "$DOTFILES" != "$HOME/.dotfiles" ]; then
  if $DRY_RUN; then
    echo "Root"; echo "  would link ~/.dotfiles -> $DOTFILES"
  else
    ln -sfn "$DOTFILES" "$HOME/.dotfiles"
    echo "Root"; echo "  ~/.dotfiles -> $DOTFILES"
  fi
fi

echo "Shell"      ; link zsh/zshrc          "$HOME/.zshrc"
echo "Git"
link git/gitconfig        "$HOME/.gitconfig"
link git/gitignore_global "$HOME/.gitignore_global"
# Identity is untracked, so a fork doesn't inherit someone else's name.
if [ ! -e "$HOME/.gitconfig.local" ] && ! $DRY_RUN; then
  cp "$DOTFILES/git/gitconfig.local.example" "$HOME/.gitconfig.local"
  echo "  created ~/.gitconfig.local — set your name and email there"
fi
echo "tmux"       ; link tmux/tmux.conf     "$HOME/.tmux.conf"
echo "Ghostty"    ; link ghostty/config     "$HOME/.config/ghostty/config"
echo "Neovim"     ; link nvim               "$HOME/.config/nvim"
echo "mise"       ; link mise/config.toml   "$HOME/.config/mise/config.toml"
# gh's config.yml holds preferences and aliases only — credentials live in
# hosts.yml, which is deliberately not tracked.
echo "gh"         ; link config/gh/config.yml "$HOME/.config/gh/config.yml"
# ── coding agents ─────────────────────────────────
# Each agent is configured only if it's actually installed, so this works with
# one of them, two, or all three. agents/AGENTS.md is the single source of
# instructions; each tool reads it under the name it expects.
echo "Agents"

if [ -d "$HOME/.claude" ] || command -v claude >/dev/null 2>&1; then
  link agents/AGENTS.md          "$HOME/.claude/CLAUDE.md"
  link_live agents/claude/settings.json "$HOME/.claude/settings.json"
  link config/ccstatusline/settings.json "$HOME/.config/ccstatusline/settings.json"
  # Account labels hold a personal org ID, so the live file stays out of git for
  # privacy rather than churn; claude-account falls back to the email prefix.
  link_live config/claude-account/accounts.json "$HOME/.config/claude-account/accounts.json"
else
  echo "  ${dim}·${reset} Claude Code not installed, skipped"
fi

if [ -d "$HOME/.codex" ] || command -v codex >/dev/null 2>&1; then
  link agents/AGENTS.md "$HOME/.codex/AGENTS.md"
  link_live agents/codex/config.toml "$HOME/.codex/config.toml"
else
  echo "  ${dim}·${reset} Codex not installed, skipped"
fi

if [ -d "$HOME/.opencode" ] || [ -d "$HOME/.config/opencode" ] || command -v opencode >/dev/null 2>&1; then
  # opencode reads global rules from ~/.config/opencode/AGENTS.md, so unlike
  # Cursor it needs no per-project step.
  link agents/AGENTS.md              "$HOME/.config/opencode/AGENTS.md"
  link agents/opencode/opencode.json "$HOME/.config/opencode/opencode.json"
  link agents/opencode/plugins/notify.js "$HOME/.config/opencode/plugins/notify.js"
else
  echo "  ${dim}·${reset} opencode not installed, skipped"
fi

if [ -d "$HOME/.cursor" ] || command -v cursor-agent >/dev/null 2>&1; then
  link agents/cursor/cli-config.json "$HOME/.cursor/cli-config.json"
  link agents/cursor/hooks.json      "$HOME/.cursor/hooks.json"
  link agents/cursor/mcp.json        "$HOME/.cursor/mcp.json"
  # Cursor has no global instructions file — User Rules are UI-only and
  # AGENTS.md is read per-project. `agent-rules` drops it into a project.
  echo "  ${dim}·${reset} Cursor: run 'agent-rules' in a project for AGENTS.md"
else
  echo "  ${dim}·${reset} Cursor not installed, skipped"
fi

echo "Starship"
link starship/bridge.toml  "$HOME/.config/starship/bridge.toml"
link starship/mission.toml "$HOME/.config/starship/mission.toml"
# The active prompt is a symlink to whichever preset is selected;
# `prompt-style` re-points it. Only set a default if unset.
if [ ! -L "$HOME/.config/starship.toml" ]; then
  if $DRY_RUN; then
    echo "  would set active prompt -> bridge"
  else
    [ -e "$HOME/.config/starship.toml" ] && [ ! -e "$HOME/.config/starship.toml.bak" ] \
      && cp "$HOME/.config/starship.toml" "$HOME/.config/starship.toml.bak"
    ln -sfn "$HOME/.config/starship/bridge.toml" "$HOME/.config/starship.toml"
    echo "  + active prompt -> bridge"
  fi
else
  echo "  ${dim}·${reset} active prompt -> $(basename "$(readlink "$HOME/.config/starship.toml")" .toml)"
fi

$DRY_RUN || chmod +x "$DOTFILES"/bin/*

echo
if $DRY_RUN; then
  echo "Dry run — nothing changed."
else
  echo "Linked. Run ./setup.sh to also install prerequisites."
fi
