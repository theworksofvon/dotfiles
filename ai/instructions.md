# Working agreements

Shared by Claude Code (`~/.claude/CLAUDE.md`) and Codex (`~/.codex/AGENTS.md`),
both symlinked to this file. Applies to every project unless a repo's own
instructions override it.

## Communication

- Challenge assumptions and suggest alternatives; don't just agree.
- Lead with the outcome, then the reasoning. No preamble, no flattery.
- Report honestly: if tests fail, say so with the output. If a step was
  skipped, say that. Don't describe work as done until it's verified.

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
- `pnpm` over `npm` for Node.
- `mise` manages CLI tools and runtimes; `uv` for Python.
- Prefer `rg` and `fd` over `grep` and `find`.
- Use `rm -f` to avoid interactive prompts.

## Python

- Standalone scripts use PEP 723 inline dependencies with the
  `#!/usr/bin/env -S uv run --script` shebang. No requirements.txt.
- Format with `ruff`.

## Git

- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- `git push --force-with-lease`, never `--force`.
- Commit or push only when asked. Never post PR comments unless explicitly
  told to — review output stays in the conversation.
- Never commit secrets, `.env` files, or credentials.

## Code style

- Public methods at the top, implementation details below.
- Comments explain constraints the code can't express — not what the next
  line does, and not why a change was made.
- Test behavior, not implementation. Mock only at real boundaries: network,
  external services, slow operations.
