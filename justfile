# Verification for this repo. `just` lists recipes; `just check` runs them all.
# Nothing here changes the machine: install.sh and setup.sh do that.

set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list --unsorted

# lint, tests, then doctor — run before committing
check: lint test doctor

# shellcheck every bash and sh script
lint:
    shellcheck -S warning $(rg -l '^#!.*\b(ba)?sh\b' install.sh setup.sh doctor.sh bin agents/hooks test)

# the shell tests in test/ and the node tests in bin/
test:
    #!/usr/bin/env bash
    set -uo pipefail
    fail=0
    for t in test/*.test.sh; do
      if out=$(bash "$t" 2>&1); then printf '  · %s\n' "$t"
      else printf '  ! %s\n%s\n' "$t" "$out"; fail=1; fi
    done
    node --test bin/*.test.mjs >/dev/null 2>&1 && printf '  · bin/*.test.mjs\n' || { printf '  ! bin/*.test.mjs\n'; node --test bin/*.test.mjs; fail=1; }
    exit $fail

# is this machine in the state the repo describes? read-only
doctor:
    ./doctor.sh
