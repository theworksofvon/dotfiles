# Disable Agent Attribution

## Goal

Prevent Claude Code, Codex, and Cursor from adding AI identity, co-author,
generated-by, or session-link attribution to future commits and pull requests.
Do not rewrite existing Git history.

## Design

Use each harness's native configuration wherever it exists:

- Claude Code: set `attribution.commit` and `attribution.pr` to empty strings,
  and set `attribution.sessionUrl` to `false`.
- Codex: set the top-level `commit_attribution` value to an empty string.
- Cursor: set `attributeCommitsToAgent` and `attributePRsToAgent` to `false`.

Add a matching rule to the shared `agents/AGENTS.md` instructing every harness
not to append AI attribution to commit messages, PR titles, or PR bodies. This
provides coverage where a harness has no dedicated setting, particularly Codex
pull request text.

Do not add a Git hook. Repository-level rejection would affect humans and other
tools, while the requirement applies specifically to agent harnesses.

## Verification

Add a small configuration test that parses all three harness configs and checks
the native settings. Verify the shared instruction contains an explicit
prohibition, then run the existing test suite and config syntax checks.
