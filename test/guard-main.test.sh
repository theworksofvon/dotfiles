#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
GUARD="$ROOT/bin/guard-main"
PASS=0
FAIL=0

expect_status() {
  local expected=$1
  local command=$2
  local actual=0

  "$GUARD" --test "$command" >/dev/null 2>&1 || actual=$?
  if [[ $actual -eq $expected ]]; then
    PASS=$((PASS + 1))
  else
    printf 'FAIL: %q returned %d, expected %d\n' "$command" "$actual" "$expected" >&2
    FAIL=$((FAIL + 1))
  fi
}

expect_payload_status() {
  local expected=$1
  local payload=$2
  local actual=0

  (cd / && printf '%s' "$payload" | "$GUARD") >/dev/null 2>&1 || actual=$?
  if [[ $actual -eq $expected ]]; then
    PASS=$((PASS + 1))
  else
    printf 'FAIL: payload returned %d, expected %d\n' "$actual" "$expected" >&2
    FAIL=$((FAIL + 1))
  fi
}

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

git -C "$tmp" init -q -b main
git -C "$tmp" config user.name "Guard Test"
git -C "$tmp" config user.email "guard@example.invalid"
git -C "$tmp" commit --allow-empty -qm init

cd "$tmp"

expect_status 2 "git push"
expect_status 2 "git push origin HEAD:main"
expect_status 2 "git push origin feature:refs/heads/main"
expect_status 0 "git push origin main:backup"
expect_status 0 "git status"
expect_status 0 "echo 'git push'"

git switch -qc feature

expect_status 0 "git push"
expect_status 2 "git push origin HEAD:main"
expect_status 2 "git push origin feature:refs/heads/main"
expect_status 0 "git push origin feature"
expect_status 0 "git merge main"

git switch -q main
expect_payload_status 2 "{\"command\":\"git push\",\"cwd\":\"$tmp\"}"

printf '%d passed, %d failed\n' "$PASS" "$FAIL"
((FAIL == 0))
