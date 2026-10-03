#!/usr/bin/env bash
# Read-only check that this machine matches what the repo says. Changes
# nothing; prints one line per check and exits non-zero if any failed.
#
# Four questions, in order of how silently each one breaks:
#   Links     does every file install.sh manages point into this repo?
#   Hooks     does every hook script a harness config names exist, and will
#             it run? A typo here means a guard never fires and nothing says so.
#   Configs   does each config parse? Claude and opencode ignore a settings
#             file with a syntax error rather than refusing to start.
#   Toolchain is everything in Brewfile and mise/config.toml installed?
set -uo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DOTFILES" || exit 1
fail=0

dim=$(tput dim 2>/dev/null || true); bold=$(tput bold 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)
ok()  { printf '  %s·%s %s\n' "$dim" "$reset" "$1"; }
bad() { printf '  %s!%s %s\n' "$bold" "$reset" "$1"; fail=1; }

echo "Links"
# install.sh already knows the full list and what "in place" means, so reuse
# its dry run: any "would ..." line is drift, any "missing in repo" is a link
# whose source was moved without updating the installer.
dry=$(./install.sh --dry-run 2>&1)
if drift=$(printf '%s\n' "$dry" | rg '^\s+(would |missing in repo)'); then
  bad "install.sh --dry-run wants to change something:"
  printf '%s\n' "$drift" | sed 's/^/    /'
else
  ok "every link install.sh manages is in place"
fi

echo "Hooks"
# Claude and Codex name hooks by path in their configs; opencode's plugin
# passes bare names to run(). Collect both, then check each resolves to an
# executable file.
hooks=$( {
  rg -oN --no-filename 'agents/hooks/([A-Za-z-]+)' -r '$1' \
    agents/claude/settings.example.json agents/codex/config.example.toml
  rg -oN --no-filename -U 'run\(\s*"([A-Za-z-]+)"' -r '$1' agents/opencode/plugins/*.js
} | sort -u)
for hook in $hooks; do
  if [ -x "agents/hooks/$hook" ]; then
    ok "agents/hooks/$hook"
  else
    bad "agents/hooks/$hook is named in a harness config but is missing or not executable"
  fi
done
for f in agents/hooks/*; do
  [ -x "$f" ] || bad "$f is not executable; install.sh should have chmod'd it"
done

echo "Configs"
for f in agents/claude/settings.example.json agents/opencode/opencode.json \
         config/ccstatusline/settings.json config/claude-account/accounts.example.json; do
  if jq -e . "$f" >/dev/null 2>&1; then ok "$f"; else bad "$f is not valid JSON"; fi
done
for f in agents/codex/config.example.toml mise/config.toml config/hit/requests.example.toml; do
  if python3 -c 'import sys, tomllib; tomllib.load(open(sys.argv[1], "rb"))' "$f" 2>/dev/null; then
    ok "$f"
  else
    bad "$f is not valid TOML"
  fi
done
for f in agents/opencode/plugins/*.js; do
  if node --check "$f" 2>/dev/null; then ok "$f"; else bad "$f does not parse"; fi
done

echo "Toolchain"
# --no-upgrade: outdated is fine, only absent counts as drift.
if brew bundle check --no-upgrade --file Brewfile >/dev/null 2>&1; then
  ok "Brewfile satisfied"
else
  bad "Brewfile has uninstalled entries: brew bundle check --verbose --no-upgrade"
fi
if missing=$(mise ls --missing 2>/dev/null) && [ -z "$missing" ]; then
  ok "mise/config.toml satisfied"
else
  bad "mise has uninstalled tools: mise ls --missing"
fi
# bin/gh must shadow Homebrew's gh for account routing to work (see zshrc).
if [ "$(command -v gh)" = "$HOME/.dotfiles/bin/gh" ]; then
  ok "bin/gh wins over Homebrew's gh on PATH"
else
  bad "gh resolves to $(command -v gh), not bin/gh; account routing is off"
fi

echo
if [ "$fail" = 0 ]; then
  echo "Healthy."
else
  echo "Drift found. ./install.sh fixes links; setup.sh fixes the toolchain."
  exit 1
fi
