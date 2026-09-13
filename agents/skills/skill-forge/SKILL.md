---
name: skill-forge
description: Create, move, or remove a skill and wire it into every harness at once. Use when the user wants a new skill, wants an existing one installed for Codex or opencode too, or asks why a skill shows up in one agent but not another.
---

A skill lives in one place and is symlinked into three. Getting the plumbing
right is mechanical; getting the writing right is not. This skill covers the
plumbing and hands the writing to `writing-for-agents`.

## The layout

```
~/src/theworksofvon/dotfiles/agents/skills/<name>/SKILL.md   ← the only real copy
~/.claude/skills/<name>            → symlink
~/.codex/skills/<name>             → symlink
~/.config/opencode/skills/<name>   → symlink
```

A skill that exists in the repo but is missing a symlink is invisible to that
harness. This is the usual cause of "it works in Claude but not Codex".

## Creating one

1. **Write it first.** Read `writing-for-agents` and follow it — that skill
   owns how the document should read. Do not skip this step and hand-roll
   prose; the frontmatter `description` is what decides whether the skill ever
   fires, and it has rules.

2. **Place it** at `agents/skills/<name>/SKILL.md`. Use a kebab-case directory
   name matching the frontmatter `name`.

3. **Link it into all three harnesses:**

```bash
D=~/src/theworksofvon/dotfiles/agents/skills
NAME=<name>
for t in ~/.claude/skills ~/.codex/skills ~/.config/opencode/skills; do
  mkdir -p "$t"
  ln -sfn "$D/$NAME" "$t/$NAME"
done
```

4. **Verify all three resolve:**

```bash
for t in ~/.claude/skills ~/.codex/skills ~/.config/opencode/skills; do
  printf "%-38s %s\n" "$t/$NAME" "$([ -e "$t/$NAME" ] && echo OK || echo BROKEN)"
done
```

5. **Commit the repo.** The symlinks are machine state; the skill is not. Only
   the `agents/skills/` directory belongs in git.

## Removing one

Remove the symlinks first, then the source — the reverse order leaves three
broken links that fail silently:

```bash
NAME=<name>
for t in ~/.claude/skills ~/.codex/skills ~/.config/opencode/skills; do
  rm -f "$t/$NAME"
done
rm -rf ~/src/theworksofvon/dotfiles/agents/skills/"$NAME"
```

## Vendored skills

`agents/skills/UPSTREAM` records which skills came from someone else's repo and
at what commit. When adding a vendored skill, add a line there. When one has
been edited locally, say so in that file — otherwise the next sync silently
overwrites the local change.

## Auditing the wiring

To find skills that are not linked everywhere:

```bash
D=~/src/theworksofvon/dotfiles/agents/skills
for s in "$D"/*/; do
  n=$(basename "$s")
  missing=""
  for t in ~/.claude/skills ~/.codex/skills ~/.config/opencode/skills; do
    [ -e "$t/$n" ] || missing="$missing $(basename $(dirname $t))"
  done
  [ -n "$missing" ] && echo "$n missing from:$missing"
done
```
