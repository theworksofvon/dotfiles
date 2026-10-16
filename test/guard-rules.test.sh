#!/usr/bin/env bash
# guard-rules applies the allow and block lists in rules.json.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GUARD="$ROOT/agents/hooks/guard-rules"
pass=0; fail=0

SCRATCH=$(mktemp -d)
trap 'rm -rf "$SCRATCH"' EXIT

# The fake homes below hide mise's trust records from its node shim, so put
# the real node first.
PATH="$(dirname "$(node -e 'process.stdout.write(process.execPath)')"):$PATH"

# One fake home per auth0 login state; the guard reads the default tenant
# from ~/.config/auth0/config.json.
home_with_tenant() {
  mkdir -p "$SCRATCH/$1/.config/auth0"
  printf '{"default_tenant":"%s"}' "$2" >"$SCRATCH/$1/.config/auth0/config.json"
}
home_with_tenant stage costmine-stage.us.auth0.com
home_with_tenant prod glacierrig.us.auth0.com
mkdir -p "$SCRATCH/none"

run() {
  local want=$1 label=$2 home=$3 payload=$4 got
  echo "$payload" | HOME="$SCRATCH/$home" "$GUARD" >/dev/null 2>&1; got=$?
  if [ "$got" = "$want" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL $label: exit $got, wanted $want"; fi
}

# shell <want> <label> <home> <command>, run from the repo root
shell() {
  run "$1" "$2" "$3" "$(jq -nc --arg c "$4" --arg cwd "$ROOT" '{tool_name:"Bash",tool_input:{command:$c},cwd:$cwd}')"
}

# ── auth0 on staging ──────────────────────────────
shell 0 "list APIs"                       stage 'auth0 apis list'
shell 0 "list API scopes"                 stage 'auth0 apis scopes list abc --json'
shell 0 "ls alias on production"          prod  'auth0 client-grants ls --audience https://api.costmine.com/'
shell 0 "raw API get"                     stage 'auth0 api get "client-grants?audience=https://stage-api.costmine.com/"'
shell 0 "update an API"                   stage 'auth0 apis update abc --scopes read:a,read:b'
shell 0 "update a client grant"           stage 'auth0 client-grants update abc --scopes read:a'
shell 0 "raw API patch"                   stage "auth0 api patch resource-servers/abc --data '{}'"
shell 0 "get a test token"                stage 'auth0 test token abc -a https://stage-api.costmine.com/'
shell 0 "env prefix on a read"            stage 'AUTH0_CLI_ANALYTICS=false auth0 apis list'
shell 0 "help"                            stage 'auth0 apis update --help'
shell 2 "delete an API"                   stage 'auth0 apis delete abc'
shell 2 "raw API delete"                  stage 'auth0 api delete clients/abc --force'
shell 2 "remove a role permission"        stage 'auth0 roles permissions remove abc'
shell 2 "clear a grant's scopes"          stage 'auth0 client-grants update abc --no-scopes'
shell 2 "machine login"                   stage 'auth0 login --domain x.us.auth0.com --client-id a --client-secret b'
shell 2 "logout"                          stage 'auth0 logout costmine-stage.us.auth0.com'
shell 2 "switch tenant"                   stage 'auth0 tenants use glacierrig.us.auth0.com'
shell 2 "reveal secrets"                  stage 'auth0 apps show abc --reveal-secrets'
shell 2 "install agent skills"            stage 'auth0 agent skills install'

# ── a delete hidden in a longer command ───────────
shell 2 "delete after a read"             stage 'auth0 apis list && auth0 apis delete abc'
shell 2 "delete in a pipe"                stage 'echo y | auth0 apis delete abc'
shell 2 "delete in bash -c"               stage 'bash -c "auth0 apis delete abc"'
shell 2 "delete in a substitution"        stage 'echo $(auth0 apis delete abc)'
shell 2 "delete by full path"             stage '/opt/homebrew/bin/auth0 apis delete abc'
shell 2 "delete behind env vars"          stage 'AUTH0_CLI_ANALYTICS=false auth0 apis delete abc'
shell 0 "auth0 as an argument"            stage 'rg "auth0 apis delete" notes.txt'

# ── auth0 on any other tenant ─────────────────────
shell 0 "read on production"              prod  'auth0 apis list'
shell 2 "write on production"             prod  'auth0 apis update abc --scopes read:a'
shell 2 "write with a production flag"    stage 'auth0 apis update abc --tenant glacierrig.us.auth0.com'
shell 2 "write with a production flag ="  stage 'auth0 apis update abc --tenant=glacierrig.us.auth0.com'
shell 0 "write with a staging flag"       prod  'auth0 apis update abc --tenant costmine-stage.us.auth0.com'
shell 2 "write when not logged in"        none  'auth0 apis update abc'

# ── rules.json is locked unless rules-lock opens it ──
RULES="$ROOT/agents/hooks/rules.json"
LOCK="$ROOT/bin/rules-lock"

# tool <want> <label> <home> <tool_name> <tool_input json>
tool() {
  run "$1" "$2" "$3" "$(jq -nc --arg t "$4" --argjson i "$5" --arg cwd "$ROOT" '{tool_name:$t,tool_input:$i,cwd:$cwd}')"
}

tool 2 "Edit rules.json"                  stage Edit  "$(jq -nc --arg p "$RULES" '{file_path:$p}')"
tool 2 "opencode edit rules.json"         stage Edit  '{"filePath":"agents/hooks/rules.json"}'
tool 2 "Codex apply_patch on rules.json"  stage apply_patch '{"command":"*** Begin Patch\n*** Update File: agents/hooks/rules.json\n@@\n*** End Patch"}'
tool 0 "Edit another file"                stage Edit  "$(jq -nc --arg p "$ROOT/Brewfile" '{file_path:$p}')"
ln -s "$ROOT" "$SCRATCH/link"
tool 2 "Write through a symlink"          stage Write "$(jq -nc --arg p "$SCRATCH/link/agents/hooks/rules.json" '{file_path:$p}')"
shell 2 "sed -i on rules.json"            stage "sed -i '' s/block/allow/ agents/hooks/rules.json"
shell 2 "redirect into rules.json"        stage 'jq . /tmp/x > agents/hooks/rules.json'
shell 2 "fd redirect into rules.json"     stage 'echo {} 2>agents/hooks/rules.json'
shell 2 "mv after cd"                     stage 'cd agents/hooks && mv /tmp/x rules.json'
shell 2 "git checkout rules.json"         stage 'git checkout -- agents/hooks/rules.json'
shell 0 "cat rules.json"                  stage 'cat agents/hooks/rules.json'
shell 0 "jq rules.json"                   stage 'jq .auth0.block agents/hooks/rules.json'
shell 0 "git diff rules.json"             stage 'git diff agents/hooks/rules.json'
shell 0 "another project's rules.json"    stage 'sed -i "" s/a/b/ /tmp/other/rules.json'

# An agent can never open the lock itself.
shell 2 "run rules-lock"                  stage 'rules-lock off'
shell 2 "run rules-lock by path"          stage "$LOCK off 60"
shell 0 "rules-lock status"               stage 'rules-lock status'
shell 2 "write the state file"            stage 'echo 9999999999 > ~/.config/guard/rules-unlocked'
tool 2 "Edit the state file"              stage Write "$(jq -nc --arg p "$SCRATCH/stage/.config/guard/rules-unlocked" '{file_path:$p}')"

# The real command opens the lock for its deadline, and `on` closes it.
cp -R "$SCRATCH/stage" "$SCRATCH/open"
HOME="$SCRATCH/open" "$LOCK" off 5 >/dev/null
tool 0 "Edit rules.json while unlocked"   open  Edit  "$(jq -nc --arg p "$RULES" '{file_path:$p}')"
shell 0 "sed rules.json while unlocked"   open  "sed -i '' s/a/b/ agents/hooks/rules.json"
shell 2 "rules-lock while unlocked"       open  'rules-lock on'
shell 2 "state file while unlocked"       open  'rm ~/.config/guard/rules-unlocked'
HOME="$SCRATCH/open" "$LOCK" on >/dev/null
tool 2 "Edit rules.json after lock on"    open  Edit  "$(jq -nc --arg p "$RULES" '{file_path:$p}')"

# A deadline in the past is locked.
cp -R "$SCRATCH/stage" "$SCRATCH/expired"
mkdir -p "$SCRATCH/expired/.config/guard"
echo $(($(date +%s) - 60)) >"$SCRATCH/expired/.config/guard/rules-unlocked"
tool 2 "Edit rules.json after expiry"     expired Edit "$(jq -nc --arg p "$RULES" '{file_path:$p}')"

# ── a broken rules.json blocks, not allows ────────
mkdir -p "$SCRATCH/hooks"
cp "$GUARD" "$SCRATCH/hooks/guard-rules"
printf '{ not json' >"$SCRATCH/hooks/rules.json"
echo '{"tool_name":"Bash","tool_input":{"command":"auth0 apis list"}}' | HOME="$SCRATCH/stage" "$SCRATCH/hooks/guard-rules" >/dev/null 2>&1
if [ $? = 2 ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL broken rules.json: not blocked"; fi

echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
