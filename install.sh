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

echo "Shell"      ; link zsh/zshrc          "$HOME/.zshrc"
echo "Git"
link git/gitconfig        "$HOME/.gitconfig"
link git/gitignore_global "$HOME/.gitignore_global"
echo "tmux"       ; link tmux/tmux.conf     "$HOME/.tmux.conf"
echo "Ghostty"    ; link ghostty/config     "$HOME/.config/ghostty/config"
echo "Neovim"     ; link nvim               "$HOME/.config/nvim"
echo "mise"       ; link mise/config.toml   "$HOME/.config/mise/config.toml"
echo "Claude Code"
link claude/settings.json "$HOME/.claude/settings.json"
link config/ccstatusline/settings.json  "$HOME/.config/ccstatusline/settings.json"
link config/cc-auth-status/accounts.json "$HOME/.config/cc-auth-status/accounts.json"

# One instructions file, two agents: Claude reads CLAUDE.md, Codex reads
# AGENTS.md. Both point at the same source so they can't drift apart.
echo "Agent instructions"
link ai/instructions.md "$HOME/.claude/CLAUDE.md"
link ai/instructions.md "$HOME/.codex/AGENTS.md"

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

$DRY_RUN || chmod +x "$DOTFILES"/vendor/gsong/*.mjs "$DOTFILES"/bin/*

echo
if $DRY_RUN; then
  echo "Dry run — nothing changed."
else
  echo "Linked. Run ./setup.sh to also install prerequisites."
fi
