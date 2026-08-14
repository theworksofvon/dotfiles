#!/usr/bin/env bash
# Build a 10-pane sci-fi deck in a new Herdr tab.
#   ./hackdeck.sh            build it in the background (stay where you are)
#   ./hackdeck.sh --focus    build it and jump to it
#   ./hackdeck.sh --close    tear down the deck tab
set -euo pipefail

DECK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="HACKDECK"
FOCUS="--no-focus"
[[ "${1:-}" == "--focus" ]] && FOCUS="--focus"

if [[ -z "${HERDR_ENV:-}" ]]; then
  echo "not inside a herdr pane" >&2
  exit 1
fi

WS="${HERDR_WORKSPACE_ID:-w1}"

if [[ "${1:-}" == "--close" ]]; then
  tab=$(herdr tab list --workspace "$WS" | jq -r ".result.tabs[] | select(.label==\"$LABEL\") | .tab_id" | head -1)
  [[ -n "$tab" ]] && herdr tab close "$tab" >/dev/null && echo "closed $tab" || echo "no $LABEL tab"
  exit 0
fi

root=$(herdr tab create --workspace "$WS" --label "$LABEL" --cwd "$DECK" --no-focus |
  jq -r '.result.root_pane.pane_id')

sp() { herdr pane split "$1" --direction "$2" --ratio "$3" --cwd "$DECK" --no-focus | jq -r '.result.pane.pane_id'; }

# Left column: two panels over a wide map over two short panels.
right=$(sp "$root" right 0.5)
lbot=$(sp "$root" down 0.45)
p2=$(sp "$root" right 0.5)
lbb=$(sp "$lbot" down 0.62)
p4=$(sp "$lbb" right 0.5)
# Right side: a column of three, then a column of two.
r2=$(sp "$right" right 0.5)
r1b=$(sp "$right" down 0.34)
r1c=$(sp "$r1b" down 0.5)
r2b=$(sp "$r2" down 0.5)

# No `exec`: Ctrl+C should drop to a prompt, not close the pane.
go() { herdr pane run "$1" "clear; ./$2" >/dev/null; }
go "$root" p01_matrix.py
go "$p2"   p02_telemetry.py
go "$lbot" p05_worldmap.py
go "$lbb"  p03_hexdump.py
go "$p4"   p04_cracker.py
go "$right" p06_netscan.py
go "$r1b"  p07_signal.py
go "$r1c"  p08_syslog.py
go "$r2"   p09_radar.py
go "$r2b"  p10_console.py

tab=$(herdr pane get "$root" | jq -r '.result.pane.tab_id')
[[ "$FOCUS" == "--focus" ]] && herdr tab focus "$tab" >/dev/null
echo "deck up: tab $tab (10 panes)"
