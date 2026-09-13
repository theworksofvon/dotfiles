---
name: system-audit
description: Sweep the machine for drift — repos with unpushed or uncommitted work, duplicate clones, and a toolchain that no longer matches its manifests. Use when the user asks to check, audit, tidy, or clean up their system, repos, dotfiles, brew, or mise; or before any large reorganisation.
---

Report what has drifted. Do not fix anything until the user has seen the report
and said which parts to act on.

## Why this exists

This machine once carried an 18GB copy of a dead user account, three divergent
copies of the same untracked project, and seven tools installed by both
Homebrew and mise with PATH order silently picking the winner. Every one of
those was invisible until someone looked. This is the looking.

## 1. Work at risk

The only irreversible loss is work that exists in exactly one place. Check it
first, and never propose deleting anything until this section is clean.

```bash
for d in ~/src/*/*/; do
  [ -d "$d/.git" ] || continue
  dirty=$(git -C "$d" status --porcelain | wc -l | tr -d ' ')
  unpushed=$(git -C "$d" log --branches --not --remotes --oneline | wc -l | tr -d ' ')
  stash=$(git -C "$d" stash list | wc -l | tr -d ' ')
  [ "$dirty$unpushed$stash" = "000" ] && continue
  printf "%-46s dirty=%-4s unpushed=%-4s stash=%s\n" "${d#$HOME/src/}" "$dirty" "$unpushed" "$stash"
done
```

Report untracked projects too — a directory with source files and no `.git` is
work that one `rm` destroys:

```bash
fd -t d -d 3 . ~/src --min-depth 2 | while read -r d; do
  [ -d "$d/.git" ] && continue
  fd -t f -d 2 -e ts -e tsx -e py -e cs -e go . "$d" -E node_modules -E .venv 2>/dev/null \
    | head -1 | grep -q . && echo "untracked project: ${d#$HOME/src/}"
done
```

## 2. Duplicate clones

The same repo checked out twice diverges silently. Group by remote:

```bash
for d in ~/src/*/*/; do
  [ -d "$d/.git" ] || continue
  printf "%s\t%s\n" "$(git -C "$d" remote get-url origin 2>/dev/null)" "${d#$HOME/src/}"
done | sort | awk -F'\t' 'NF==2 && $1!=""{c[$1]=c[$1]" "$2; n[$1]++} END{for(r in n) if(n[r]>1) print r":"c[r]}'
```

For each duplicate, before recommending which to drop: confirm every unpushed
commit in the candidate exists in the keeper (`git -C keeper cat-file -e <sha>`),
and diff the source excluding build artifacts. Two clones at the same HEAD can
still hold different uncommitted work.

## 3. Toolchain drift

A tool in both Homebrew and mise means PATH order decides, and it changes
without warning. Find the overlap:

```bash
comm -12 <(brew leaves | sort) <(mise ls --json | jq -r 'keys[]' | sed 's|.*:||' | sort)
```

Find the Brewfile drift in both directions:

```bash
cd ~/src/theworksofvon/dotfiles
comm -3 <(brew leaves | sort) <(rg -o '^brew "([^"]+)"' -r '$1' Brewfile | sed 's|.*/||' | sort)
comm -3 <(brew list --cask | sort) <(rg -o '^cask "([^"]+)"' -r '$1' Brewfile | sed 's|.*/||' | sort)
```

Empty output from both means the manifest matches the machine.

## 4. Broken symlinks

`$HOME` is a symlink farm into the dotfiles repo. A stale link fails silently:

```bash
find ~ -maxdepth 3 -type l ! -exec test -e {} \; -print 2>/dev/null
```

Every path printed is broken. Report it — a broken `~/.claude/CLAUDE.md` means
the agent has been running with no steering file at all.

## Reporting

Lead with what is at risk, then what is merely untidy. Give counts, not
inventories — "6 repos hold unpushed work" then the list, not a wall of clean
repos. Name the specific fix for each finding and let the user choose.

When the user approves deletions, follow the destructive-operations rules in
`AGENTS.md`: stage to a folder, never interpolate a variable into a path, never
suppress stderr.
