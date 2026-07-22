#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

REPO="$TEST_DIR/repo"
TEST_HOME="$TEST_DIR/home"
FAKE_BIN="$TEST_DIR/bin"
mkdir -p "$REPO" "$TEST_HOME/.codex/sessions/2026/07/21" "$FAKE_BIN"
git -C "$REPO" init -q

SESSION="$TEST_HOME/.codex/sessions/2026/07/21/session.jsonl"
printf '{"payload":{"cwd":"%s"}}\n{"payload":{"type":"user_message","message":"Keep working"}}\n' "$REPO" >"$SESSION"
printf 'personal notes\n' >"$REPO/HANDOFF.md"

cat >"$FAKE_BIN/claude" <<EOF
#!/usr/bin/env bash
touch "$TEST_DIR/summarizer-ran"
printf '## Goal\nUnexpected summary\n'
EOF
chmod +x "$FAKE_BIN/claude"

status=0
output=$(cd "$REPO" && HOME="$TEST_HOME" PATH="$FAKE_BIN:$PATH" node "$ROOT/bin/handoff" 2>&1) || status=$?

[[ $status -eq 1 ]]
[[ $output == *"already exists and wasn't written by handoff"* ]]
[[ ! -e "$TEST_DIR/summarizer-ran" ]]
[[ $(cat "$REPO/HANDOFF.md") == "personal notes" ]]

printf 'handoff checks for an existing file before summarizing\n'
