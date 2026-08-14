#!/usr/bin/env bash
# Build the 10-pane work deck in a new Herdr tab. Same grid as hackdeck,
# every panel fed by real data.
#   ./workdeck.sh            build it in the background
#   ./workdeck.sh --focus    build it and jump to it
#   ./workdeck.sh --close    tear it down
set -euo pipefail

DECK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="WORKDECK"
FOCUS="${1:-}"

if [[ -z "${HERDR_ENV:-}" ]]; then
  echo "not inside a herdr pane" >&2
  exit 1
fi
WS="${HERDR_WORKSPACE_ID:-w1}"

if [[ "$FOCUS" == "--close" ]]; then
  tab=$(herdr tab list --workspace "$WS" | jq -r ".result.tabs[] | select(.label==\"$LABEL\") | .tab_id" | head -1)
  [[ -n "$tab" ]] && herdr tab close "$tab" >/dev/null && echo "closed $tab" || echo "no $LABEL tab"
  exit 0
fi

root=$(herdr tab create --workspace "$WS" --label "$LABEL" --cwd "$DECK" --no-focus |
  jq -r '.result.root_pane.pane_id')

sp() { herdr pane split "$1" --direction "$2" --ratio "$3" --cwd "$DECK" --no-focus | jq -r '.result.pane.pane_id'; }

right=$(sp "$root" right 0.5)
lbot=$(sp "$root" down 0.45)
p2=$(sp "$root" right 0.5)
lbb=$(sp "$lbot" down 0.62)
p4=$(sp "$lbb" right 0.5)
r2=$(sp "$right" right 0.5)
r1b=$(sp "$right" down 0.34)
r1c=$(sp "$r1b" down 0.5)
r2b=$(sp "$r2" down 0.5)

go() { herdr pane run "$1" "clear; $2" >/dev/null; }
go "$root"  "./w01_agents.py"                 # 34x21 live agent tool stream
go "$p2"    "./w02_herdr.py"                  # 33x21 session/pane/agent map
go "$lbot"  "./w03_devstudies.py"             # 67x16 ledger + sweep guard
go "$lbb"   "./wgit.py ~/dev DEV"             # 34x9  personal repos
go "$p4"    "./w05_pulse.py"                  # 33x9  pulse health
go "$right" "./w06_prci.py"                   # 33x16 open PRs + CI
go "$r1b"   "./w07_tokens.py"                 # 33x15 today's token spend
go "$r1c"   "./p02_telemetry.py"              # 33x15 host telemetry
go "$r2"    "./wgit.py ~/costmine COSTMINE"   # 33x23 the 17 work repos
go "$r2b"   "./w10_ident.py"                  # 33x23 clock + identities

tab=$(herdr pane get "$root" | jq -r '.result.pane.tab_id')
[[ "$FOCUS" == "--focus" ]] && herdr tab focus "$tab" >/dev/null
echo "workdeck up: tab $tab (10 panes)"
