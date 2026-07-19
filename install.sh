#!/usr/bin/env bash
# Symlinks these dotfiles into place. Existing real files are backed up to *.bak.
#
# Symlinks (rather than copies) mean editing the live config edits the repo —
# no copy-back step before committing.
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# link <source-in-repo> <target-in-home>
link() {
  local src="$DOTFILES/$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    cp "$dst" "$dst.bak"
    echo "  backed up $dst -> $dst.bak"
  fi
  ln -sfn "$src" "$dst"
  echo "  $dst -> $src"
}

echo "Shell..."
link zsh/zshrc "$HOME/.zshrc"

echo "Git..."
link git/gitconfig "$HOME/.gitconfig"

echo "Starship..."
link starship/bridge.toml  "$HOME/.config/starship/bridge.toml"
link starship/mission.toml "$HOME/.config/starship/mission.toml"
# Active prompt is a symlink to a preset; `prompt-style` re-points it.
if [ ! -L "$HOME/.config/starship.toml" ]; then
  [ -e "$HOME/.config/starship.toml" ] && cp "$HOME/.config/starship.toml" "$HOME/.config/starship.toml.bak"
  ln -sfn "$HOME/.config/starship/bridge.toml" "$HOME/.config/starship.toml"
  echo "  active prompt -> bridge"
fi

echo "Ghostty..."
link ghostty/config "$HOME/.config/ghostty/config"

echo "mise..."
link mise/config.toml "$HOME/.config/mise/config.toml"

echo "Claude Code..."
link claude/settings.json "$HOME/.claude/settings.json"

chmod +x "$DOTFILES"/vendor/gsong/*.mjs

cat <<'EOF'

✔ Done. Prerequisites on this machine:

  brew install starship mise jq
  brew install --cask font-jetbrains-mono-nerd-font ghostty
  mise install                      # prettier + sqlfluff, per mise/config.toml

  Python formatting uses ruff:  mise use -g pipx:ruff   (or brew install ruff)

Then fully restart your terminal.
EOF
