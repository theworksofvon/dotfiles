#!/usr/bin/env bash
# Bootstrap a machine from zero: install prerequisites, then symlink configs.
#
# Idempotent — every step checks before acting, so re-running is a no-op that
# just reports what's already in place. Safe to run on a fresh machine or an
# existing one.
#
#   ./setup.sh              install prerequisites, then link configs
#   ./setup.sh --no-install only link configs (skip package installation)
#   ./setup.sh --dry-run    print what would happen, change nothing
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=false
DO_INSTALL=true

for arg in "$@"; do
  case "$arg" in
    --dry-run)    DRY_RUN=true ;;
    --no-install) DO_INSTALL=false ;;
    -h|--help)    sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 1 ;;
  esac
done

# ── output helpers ────────────────────────────────
bold=$(tput bold 2>/dev/null || true); dim=$(tput dim 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)
step() { echo "${bold}==>${reset} $*"; }
ok()   { echo "  ${dim}·${reset} $*"; }
act()  { echo "  ${bold}+${reset} $*"; }
warn() { echo "  ${bold}!${reset} $*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }
run() {
  if $DRY_RUN; then echo "  ${dim}would run:${reset} $*"; else "$@"; fi
}

# ── platform detection ────────────────────────────
OS="$(uname -s)"
ARCH="$(uname -m)"
case "$OS" in
  Darwin) IS_MAC=true ;;
  Linux)  IS_MAC=false ;;
  *) echo "Unsupported OS: $OS" >&2; exit 1 ;;
esac

if $IS_MAC; then
  [ "$ARCH" = "arm64" ] && BREW_PREFIX=/opt/homebrew || BREW_PREFIX=/usr/local
else
  BREW_PREFIX=/home/linuxbrew/.linuxbrew
fi

step "Platform: $OS/$ARCH (brew prefix: $BREW_PREFIX)"

if [ "$DOTFILES" != "$HOME/dotfiles" ]; then
  warn "repo is at $DOTFILES, but configs reference \$HOME/dotfiles."
  warn "Clone to ~/dotfiles, or update the paths in claude/settings.json"
  warn "and starship/bridge.toml."
fi

# ── prerequisites ─────────────────────────────────
if $DO_INSTALL; then
  step "Homebrew"
  if have brew; then
    ok "already installed ($(brew --version | head -1))"
  else
    act "installing Homebrew"
    run /bin/bash -c \
      "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi
  # Make brew available to the rest of this script even on a fresh install.
  [ -x "$BREW_PREFIX/bin/brew" ] && eval "$("$BREW_PREFIX/bin/brew" shellenv)"

  brew_formula() {
    if brew list --formula "$1" >/dev/null 2>&1; then ok "$1"
    else act "installing $1"; run brew install "$1"; fi
  }
  # Casks: an app installed outside Homebrew still counts as present, so check
  # for the .app bundle too rather than reinstalling over it.
  brew_cask() {
    local cask="$1" app="${2:-}"
    if brew list --cask "$cask" >/dev/null 2>&1; then ok "$cask"
    elif [ -n "$app" ] && [ -d "/Applications/$app" ]; then ok "$cask (installed outside Homebrew)"
    else act "installing $cask"; run brew install --cask "$cask"; fi
  }

  step "CLI tools"
  for f in starship mise jq git; do
    have brew && brew_formula "$f" || warn "brew unavailable, skipping $f"
  done

  step "Apps and fonts"
  if $IS_MAC; then
    brew_cask ghostty Ghostty.app
    brew_cask font-jetbrains-mono-nerd-font
  else
    ok "skipped (casks are macOS-only)"
  fi

  step "oh-my-zsh"
  if [ -d "$HOME/.oh-my-zsh" ]; then
    ok "already installed"
  else
    act "installing oh-my-zsh"
    run sh -c \
      "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" \
      "" --unattended
  fi
else
  step "Skipping prerequisite installation (--no-install)"
fi

# ── link configs ──────────────────────────────────
step "Linking configs"
if $DRY_RUN; then
  "$DOTFILES/install.sh" --dry-run
else
  "$DOTFILES/install.sh"
fi

# ── mise-managed tools ────────────────────────────
# Runs after linking, since mise reads the config we just symlinked.
step "mise tools (prettier, sqlfluff)"
if have mise; then
  run mise install
  $DRY_RUN || ok "installed per mise/config.toml"
else
  warn "mise not found — skipping. Re-run setup.sh after installing it."
fi

step "ruff (Python formatting)"
if have ruff; then
  ok "already installed ($(ruff --version))"
elif have mise; then
  act "installing ruff via mise"
  run mise use -g "pipx:ruff@latest"
else
  warn "skipped — needs mise or 'brew install ruff'"
fi

# ── done ──────────────────────────────────────────
echo
if $DRY_RUN; then
  step "Dry run complete — nothing was changed."
else
  step "Setup complete."
  cat <<'EOF'

  Restart your terminal, then verify:
    starship prompt          # should show the Claude usage meter
    mise ls                  # prettier, sqlfluff, ruff
    prompt-style mission     # switch prompts

  Anything already present was left alone — re-run this script any time.
EOF
fi
