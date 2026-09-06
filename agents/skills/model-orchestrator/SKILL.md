---
name: model-orchestrator
description: Orchestrate long-running software tasks across multiple AI coding agents or model backends by assigning planning, implementation, review, testing, and repair roles; use when a user wants Claude, Codex, or other models to collaborate with explicit handoffs, model-cost tradeoffs, and durable progress artifacts.
---

# Model Orchestrator

## Purpose

This skill is the portable orchestration layer for a controlled software task:

`discover → plan → approve → implement → test → review → repair → verify`

Roles are `planner`, `implementer`, and `reviewer`. A **profile** fixes which model alias plays each role; `.orchestrator/config.toml` ships three: `claude` (Claude models only), `openai` (Codex models only), and `mixed` (any provider, including opencode's cheap tier). Aliases map to a concrete model and provider command. Model names live only in that file; [config.example.toml](config.example.toml) is the starting point. Never hardcode a model in a prompt or packet.

Pick the profile from what the user said: "just use Claude" or "keep it in my Anthropic quota" means `claude`; "OpenAI only" or "Codex" means `openai`; otherwise `mixed`, which is the default. Run `mo profiles` first and report the resolved models before delegating anything.

When shell access exists, invoke `scripts/mo.py run-stage --role <role> [--profile <name>]` for every delegated stage; pass `--model <alias>` or `--provider` only to override the profile. It records the invocation, timing, normalized usage, cost provenance, raw output, and checkpoint, and copies the model's final answer to `{run_dir}/last-message.md`. The utility is also available as `mo profiles`, `mo usage`, `mo report TASK-123`, `mo export`, and `mo dashboard`; it uses only the Python standard library. If the harness cannot execute a CLI, use the manual handoff protocol and preserve the packet instead.

## Operating rules

- Treat the repository, branch, uncommitted changes, tool availability, and user constraints as shared state. Inspect them before assigning work.
- Keep role boundaries explicit. A planner produces a plan; an implementer changes files; a reviewer diagnoses against acceptance criteria.
- Prefer a strong model for ambiguous architecture, a lower-cost model for well-specified mechanical implementation, and a different provider for review so the reviewer starts with fresh context. Escalate quality-sensitive work rather than optimizing cost blindly.
- Pass compact, durable artifacts between stages. Include task statement, repository facts, acceptance criteria, decisions, changed files, commands run, failures, and open questions.
- Do not send secrets, credentials, private prompts, or unnecessary repository contents to another backend.
- The user remains the authority for scope changes, destructive operations, external messages, deployments, and merges. Ask before those actions.
- Run tests and inspect the diff after implementation and after every repair cycle. A review approval is not a substitute for verification.
- Keep implementation and review in separate contexts; never review a change using the same context that authored it. In `mixed` that means a different provider. In a single-provider profile it means a different model, which is weaker independence; say so in the completion report.
- Never claim exact tokens or cost unless the provider reported them. Label values `exact`, `estimated` (rate-card calculation), or `unavailable` separately.
- Pause only at risk-based approval gates: scope or architecture changes, destructive operations, external messages/deployments/merges, budget overruns, or repeated repair disagreement.

## Select the workflow

For a small, local, well-defined change, use one capable agent and a lightweight review. For a long-running or high-risk task, use the full pipeline. Parallelize only independent discovery or review work; serialize edits to avoid conflicting changes.

Before starting, identify the planner, implementer, reviewer, repair policy, and budget or cost ceiling if known. If `.orchestrator/config.toml` is missing, copy [config.example.toml](config.example.toml) into place and tell the user which models it resolved to. If the user names only a provider, resolve the concrete model from that file and report the resolution. Never infer that “Codex” or “Claude” means one fixed model.

## Standard pipeline

### 1. Discover

Inspect the repository and task context. Establish the baseline branch/status, relevant files, existing tests, and available model interfaces. Record facts, not guesses. If the task is underspecified, ask only the question that blocks safe planning; otherwise state assumptions in the packet.

### 2. Plan

Give the planner only necessary context and ask for the goal/non-goals, current-state findings, proposed design, ordered file-level steps, acceptance criteria, test strategy, risks, rollback notes, and unresolved questions. Do not modify product code in this stage.

### 3. Approve and hand off

Present a concise plan summary, assumptions, selected models, and expected cost/quality tradeoff. Wait for approval when the plan changes scope, architecture, public interfaces, data, or external state. Then create an implementer packet using [handoff-protocol.md](references/handoff-protocol.md).

### 4. Implement

Instruct the implementer to follow the approved plan, inspect before editing, make the smallest coherent change, preserve unrelated user work, and report every changed file and command. A lower-cost implementer is appropriate only when the plan and acceptance criteria are concrete.

### 5. Test

Run the narrowest relevant checks first, then broader checks proportional to risk. Capture exact commands and results. Distinguish “not run,” “blocked,” and “failed.”

### 6. Review

Give the reviewer the approved plan, acceptance criteria, diff, test results, and relevant context—not private reasoning. Ask for findings ranked by severity, with file/line evidence and concrete fixes. Require checks for correctness, regressions, security/privacy, maintainability, tests, and scope drift.

### 7. Repair and verify

Hand actionable findings and needed context to the implementer, or send design-level issues back to the planner. Re-run tests and an independent review when changes are material. Limit repair cycles and surface repeated disagreement to the user.

## Provider and model handoffs

Use the provider-specific mechanism that is actually available: a local CLI, connected model tools, an API wrapper, or a user-run handoff. Translate the same packet into that mechanism rather than coupling the workflow to one provider. Read [provider-adapters.md](references/provider-adapters.md) for the working `claude -p` and `codex exec` templates, what each reports back, and the user-run fallback. Provider templates live under `[providers]` and model aliases under `[models]` in `.orchestrator/config.toml`; packets arrive on stdin and `{task_id}`, `{run_id}`, `{stage}`, `{model}`, `{input_file}`, and `{run_dir}` are substituted, shell-quoted, into the command.

The helper lives at `model-orchestrator/scripts/mo.py`. A project using the skill may copy or expose it as `mo`; raw provider commands are an adapter/debugging detail and should not be part of normal user instructions. Its append-only ledger and run artifacts are normally ignored by git. A checkpoint permits an interrupted stage to be resumed with the same run ID; successful resumed stages are not invoked twice.

For a Claude-led workflow, Claude may own discovery/planning and delegate implementation or review to callable Codex/model interfaces. For a Codex-led workflow, Codex may delegate planning or review to Claude/another backend when configured. Preserve the same packet schema in both directions and keep authority with the user.

## Completion report

End with selected roles/models and why; completed stages; files changed; test/review outcome; remaining risks; exact/estimated/unavailable usage and cost; and the next user decision, if any. Do not claim cross-model execution occurred unless it actually did.
