#!/usr/bin/env bash
# The dispatcher routes a payload to the right guards and relays a block.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GUARD="$ROOT/agents/hooks/guard"
pass=0; fail=0

check() {
  local want=$1 label=$2 payload=$3 got
  echo "$payload" | "$GUARD" >/dev/null 2>&1; got=$?
  if [ "$got" = "$want" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL $label: exit $got, wanted $want"; fi
}

# The org name is assembled so the test file itself doesn't trip the guard
# when an agent runs it from a shell.
ORG="Glacier""RIG"

check 2 "push to main is blocked"      '{"tool_name":"Bash","tool_input":{"command":"git push origin main"}}'
check 2 "fork bomb is blocked"         '{"tool_name":"Bash","tool_input":{"command":":(){ :|:& };:"}}'
check 2 "org admin write is blocked"   '{"tool_name":"Bash","tool_input":{"command":"gh repo create '"$ORG"'/x"}}'
check 2 "github mcp merge is blocked"  '{"tool_name":"mcp__github__merge_pull_request","tool_input":{"owner":"'"$ORG"'","repo":"x","pullNumber":1}}'
check 0 "ordinary command passes"      '{"tool_name":"Bash","tool_input":{"command":"git status"}}'
check 0 "unrelated tool is ignored"    '{"tool_name":"Read","tool_input":{"file_path":"/etc/hosts"}}'
check 0 "garbage payload passes"       'not json'

echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
