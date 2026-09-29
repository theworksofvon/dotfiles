---
name: code-audit
description: Invoke whenever code is esoteric, over-long, deeply nested, magic-number-laden, or bunched into one function or file that should be several. Audit workflow for cutting code and complexity while holding behavior fixed; the production-code sibling of test-audit.
---

# Code Audit

One goal: less code, less complexity, same behavior. Every edit here is a
**refactor** in the strict sense: observable behavior before and after is
identical, and the test suite (plus any manual path the tests miss) proves it.
Run [`test-audit`](../test-audit/SKILL.md) on the tests that guard the code
first when they are weak; a refactor is only as safe as the proof around it.
Use the [`codebase-design`](../codebase-design/SKILL.md) vocabulary (module,
interface, seam, depth) for every restructuring decision.

## Smells

The checklist discovery hunts for. A match is a candidate, never a verdict.

- **Magic numerics**: literals with no name, unit, or source. Ask where the
  number came from; if nobody can say, it is a bug in waiting, not a
  constant.
- **Nesting**: more than two levels of `if`/`else`/loop in one function.
  Guard clauses, early returns, and lookup tables flatten most of it.
- **Long functions**: a function that needs scrolling, or whose name needs
  "and". Each "and" is a seam.
- **Bunched responsibilities**: one function or file doing parsing, deciding,
  and side-effecting together, so none can be tested or reused alone.
- **Shallow modules**: a wrapper whose interface is as wide as what it hides,
  a pass-through layer, an abstraction with one caller and one
  implementation.
- **Duplicated logic**: the same branch, transform, or validation copied with
  small drift across sites. Drift is where the bugs live.
- **Dead paths**: unreachable branches, unused parameters, flags nobody sets,
  fallbacks for callers that no longer exist, compatibility shims past their
  date.
- **Speculative generality**: hooks, options, and plugin points with no
  second user.
- **Clever code**: bit tricks, operator overloading, implicit coercions, or
  metaprogramming where a plain loop would read in one pass.
- **Comment-shaped code**: comments that narrate what the next line does
  instead of naming a constraint the code cannot express. The fix is usually
  a better name, then deleting the comment.

## Value bar

A change lands when it removes lines or nesting, and a reader new to the file
can follow the result faster than the original. "Cleaner" alone is not
enough. Extraction that adds a layer with one caller, or a helper file with
one function, adds indirection and fails the bar. Prefer deleting over
abstracting, and abstracting over rearranging.

Read before judging: the full function and file, every caller, sibling
implementations of the same idea, the tests that cover it, and the history
that explains why it looks this way. Read root and scoped `AGENTS.md` /
`CLAUDE.md` first. A weird shape often encodes a real constraint (a hot loop,
a platform quirk, a wire format); find the constraint before flattening it.

## Discovery

Read-only. Report evidence before editing. For broad scope, run parallel
discovery lanes:

- longest functions and deepest nesting (a quick script over the tree is
  fine);
- unnamed numerics and string literals repeated across files;
- files over a few hundred lines that mix concerns;
- duplicated blocks across siblings;
- exports, flags, and parameters with no non-test callers.

Prefer a few high-confidence candidates over a large speculative inventory.

## Candidate evidence

Record every field before editing. A missing field means not ready:

- exact location and current shape (LOC, nesting depth, responsibilities);
- which smells it matches and the constraint that might explain it;
- every caller and what each one relies on;
- the proof that holds behavior fixed: the test that covers it, or the
  manual path to exercise, or the characterization test to add first;
- the proposed shape and the LOC and nesting it removes;
- risk and the focused validation command.

When no test covers the candidate, write a **characterization test** first:
capture current outputs for representative inputs, including the ugly edge
cases, so the refactor has something to fail against. Route it through the
`test-audit` authoring gate; it must assert behavior, not the old
implementation.

## Edit shape

One coherent batch per module. Within it, in order:

1. **Delete** dead paths, unused parameters, shims, and speculative hooks.
2. **Name** numerics and repeated literals; one constant, one home, a source
   in its name or a one-line comment.
3. **Flatten** with guard clauses, early returns, and table lookups.
4. **Split** at the "and" seams into deep modules: small interface, all the
   logic inside. A split that yields two shallow halves is worse than the
   original; keep it together.
5. **Merge** duplicates into one implementation at the owning seam.

Prefer net-negative LOC on every batch. Preserve public interfaces unless the
batch's stated purpose is to change one, and then update every caller in the
same change. Keep names in the repo's existing style.

## Validation

1. Run the owning tests and their siblings before touching anything; a
   baseline failure is a product bug to report, not a refactor to make.
2. Rerun after each step of the edit shape, not only at the end. A green run
   after step 1 localizes any red run after step 3.
3. Exercise the real runtime path for anything the tests do not reach.
4. Run targeted formatting and the repo's changed-file gate (lint, typecheck,
   affected tests).
5. Inspect `git diff --numstat`; report LOC removed versus added, and max
   nesting before versus after.
6. Self-review the diff for behavior drift: changed defaults, reordered side
   effects, swallowed errors, altered short-circuit order.

## Landing and continuation

Commit, push, open a PR, or land only when authorized. One coherent PR per
module; after landing, refresh from main and rerun discovery for the next
batch.

## Handoff

Report:

- smells removed and the constraints that were real and kept;
- LOC and nesting before versus after;
- interfaces changed, if any, and every caller updated;
- characterization tests added and whether they went red on a deliberate
  break;
- proof actually run;
- PR and merge state;
- named follow-ups.
