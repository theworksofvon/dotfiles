# Working agreements

Shared by Claude Code (`~/.claude/CLAUDE.md`), Codex (`~/.codex/AGENTS.md`) and
opencode (`~/.config/opencode/AGENTS.md`), all symlinked to this file. Applies
to every project unless a repo's own instructions override it.

## Navigation

Where things live. Go straight to these rather than scanning for them.

- `~/src/<org>/<repo>` — every repo on this machine. `costmine` is work
  (GlacierRIG), `theworksofvon` and `ek-labs` are personal, `vendor` is other
  people's code kept for reading, `learning` is course material.
- `~/src/theworksofvon/dotfiles` — this file and everything else that
  configures the machine. `~/dotfiles` is a symlink to it, and the entries in
  `$HOME` are symlinks into it, so edit the repo, never the symlink target.
- `~/src/theworksofvon/dotfiles/Brewfile` and `mise/config.toml` — the two
  halves of the toolchain. A tool belongs to exactly one of them; see
  "Shell and tools" below.
- `~/src/theworksofvon/vstack/skills/` — skills, shared by all three harnesses
  via symlink. Adding one means linking it into each; `skill-forge` does it.

## Communication

- Challenge assumptions and suggest alternatives; don't just agree.
- Lead with the outcome, then the reasoning. No preamble, no flattery.
- Report honestly: if tests fail, say so with the output. If a step was
  skipped, say that. Don't describe work as done until it's verified.
- Surface the decision before doing the work. When something looks dead,
  duplicated, or not worth the effort, say so and ask — don't spend the
  effort first and report it after.

## Writing standard

Write every reply in ASD-STE100 Simplified Technical English, held to its
structure and grammar rules below. Code, commands, quoted text, commit
messages, and the files you write keep their own conventions. The strict
form, with the approved dictionary, is in
`~/src/theworksofvon/vstack/skills/explain/STE100.md`.

Structure:

- One topic per paragraph, topic sentence first, six sentences at most.
- Twenty words per sentence at most in instructions, twenty-five in
  description.
- One instruction per sentence. Two only when they happen at the same time.
- Active voice, actor first: "the scheduler moves the task".
- A vertical list for a sequence of more than two steps.
- Numerals for numbers.
- A warning comes before the step it protects, as a command.
- Define a term in one short sentence the first time it appears, then use
  that exact term every time. One name per thing.
- Literal language: replace an idiom or metaphor with the fact it stands
  for.

Grammar:

- Verb forms: infinitive, imperative, simple present, simple past, future
  with "will", and the past participle as an adjective ("the closed valve").
- Rewrite an -ing verb or noun as a clause: "when you start the service",
  "the process that runs".
- Simple past for finished actions: "was sent", not "has been sent".
- Negation in full: "do not", "is not". Write every word out, with no
  contractions.
- Keep articles, demonstratives, and "that" in relative clauses: "the file
  that the job writes".
- Three nouns in a row at most: "the protocol that rebalances a consumer
  group".
- "Can" means possible, "must" means required, "will" is the future. Use
  these three in place of "may" and "might".

Before you send a reply, read it once for each check: a sentence over the
word cap, an -ing verb or noun, a passive construction, and a term used two
ways. Fix every hit.

## Before changing code

- Read the surrounding code first and match its conventions — naming, comment
  density, error handling, file layout.
- Prefer editing an existing file over creating a new one.
- Don't create documentation (`*.md`, README) unless asked.

## Verification

- Run the thing. Tests passing is not the same as the feature working.
- For anything with a runtime surface, exercise the actual path that changed.

## Shell and tools

- macOS, zsh, Homebrew at `/opt/homebrew`.
- Homebrew owns tools where one global version is always correct. mise owns
  anything whose version varies per project — language runtimes and the
  npm/pipx CLIs pinned beside them. A tool in both means PATH order silently
  picks the winner, so put it in one and only one.
- `pnpm` over `npm` for Node. `uv` for Python.
- Prefer `rg` and `fd` over `grep` and `find`.
- Prefer `hit` over `curl` for HTTP requests — it's a curl wrapper on PATH.
  `hit get <url>` works anywhere; saved routes and auth come from
  `~/.config/hit/requests.toml`. Run `hit --help` or `hit list`. Fall back to
  `curl` only when `hit` isn't installed or can't express the request.

## Destructive operations

Deleting and moving files is where the real damage happens, and it is silent.

- Never interpolate a variable into a destructive path. `rm -rf "$D"/*` with an
  empty `$D` means `rm -rf /*`. Write the path literally, or guard with
  `[ -n "$D" ]` first.
- Never suppress stderr on `rm`, `mv`, or `cp`. `2>/dev/null` on a destructive
  command hides the failure that tells you it went somewhere unintended.
- Move to a staging folder rather than deleting outright, and let the user do
  the final `rm`.
- Before deleting a repo or tree, check it for uncommitted and unpushed work,
  and confirm anything unique exists elsewhere.

## Python

- Standalone scripts use PEP 723 inline dependencies with the
  `#!/usr/bin/env -S uv run --script` shebang. No requirements.txt.
- Format with `ruff`.

## Git

- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- `git push --force-with-lease`, never `--force`.
- Commit or push only when asked. Never post PR comments unless explicitly
  told to — review output stays in the conversation.
- Do not add AI attribution, co-author trailers, generated-by text, or agent
  session links to commits, PR titles, or PR bodies.
- Never commit secrets, `.env` files, or credentials.

## Changelogs

When a repo has a `CHANGELOG.md`, updating it is part of the change — always,
without being asked. Read `agents/docs/changelogs.md` for how to match the
file's own conventions before writing an entry.

## Code style

- Public methods at the top, implementation details below.
- Comments explain constraints the code can't express — not what the next
  line does, and not why a change was made.
- Test behavior, not implementation. Mock only at real boundaries: network,
  external services, slow operations.
