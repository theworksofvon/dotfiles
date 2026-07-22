#!/usr/bin/env bash
# install.sh links two kinds of file: tracked configs, and live configs the
# tool rewrites as it runs. Mixing them up is silent — a live config left
# tracked churns on every launch, and a tracked config that got gitignored
# vanishes on a fresh clone. This checks each one is linked the right way.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
fail=0

while read -r path; do
  example="${path%.*}.example.${path##*.}"
  if [ ! -e "$ROOT/$example" ]; then
    printf 'link_live %s: no %s to seed a fresh clone from\n' "$path" "$example"
    fail=1
  fi
  if ! git -C "$ROOT" check-ignore -q "$path"; then
    printf 'link_live %s: still tracked, so the tool rewriting it will churn\n' "$path"
    fail=1
  fi
done < <(rg -N '(^|;)\s*link_live\s+([^"$\s]\S*)' -o -r '$2' "$ROOT/install.sh")

while read -r path; do
  if git -C "$ROOT" check-ignore -q "$path"; then
    printf 'link %s: gitignored, so a fresh clone has nothing to link — use link_live\n' "$path"
    fail=1
  fi
done < <(rg -N '(^|;)\s*link\s+([^"$\s]\S*)' -o -r '$2' "$ROOT/install.sh")

[ "$fail" -eq 0 ]

printf 'live configs are gitignored and seeded from examples\n'
