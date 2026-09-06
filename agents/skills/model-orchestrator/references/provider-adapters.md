# Provider adapters

This skill is provider-neutral. Model labels such as `claude`, `codex`, or `gpt` are aliases only; resolve them through `.orchestrator/config.toml` and the CLIs installed in the current environment. Three providers have working templates in [config.example.toml](../config.example.toml); `mo profiles` shows how the current config resolves each role.

## Claude Code

Template: `claude -p --output-format json --model {model} --permission-mode acceptEdits`

The packet goes in on stdin. The single JSON object that comes back carries `result` (the model's answer), `total_cost_usd`, `duration_api_ms`, `session_id`, and `usage` with input, output, and cache token counts. mo.py reads all of these, so Claude stages are recorded as `exact` cost. Add `--json-schema` when a stage must return structured findings. Use `--permission-mode plan` for planner and reviewer stages so they cannot edit files.

## Codex

Template: `codex exec --json -m {model} -s workspace-write --skip-git-repo-check -o {run_dir}/last-message.md`

The packet goes in on stdin. `--json` streams one JSONL event per line; mo.py de-duplicates by event id and sums any `usage` objects it finds. `-o` writes the final assistant message to a file inside the run directory, which is the artifact to hand to the next stage. Use `-s read-only` for planner and reviewer stages. Cost is not reported by the CLI, so Codex stages record as `estimated` when `[pricing]` has a rate card for the model and `unavailable` otherwise.

Codex model names change often. Check `codex --help` or the model picker rather than trusting a name in a document, and keep the mapping in `[models]`.

## opencode

Template: `opencode run --format json --pure -m {model}`

The packet goes in on stdin. `--format json` streams JSONL events; the `step_finish` event carries `part.tokens` (input, output, reasoning, cache) and `part.cost`, so opencode stages record as `exact`. mo.py joins the `text` parts into `last-message.md`. `--pure` skips opencode's plugins so a run is just the model. Model IDs take the form `provider/model`, for example `opencode-go/glm-5.3-flash`; `opencode models` lists what the current login can reach. This is the cheap tier for well-specified implementation; keep planning and review on a stronger model.

## Other backends

Treat any other provider, local model, agent framework, or script as an adapter with four properties: invocation method, model identifier, input/output format, and usage/cost reporting. Never expose credentials in packets. If an adapter changes files, require a diff or precise changed-file list and command log.

## User-run bridge

When no direct bridge exists, provide a copyable stage prompt containing the packet, ask the user to run it in the other tool, and request the resulting plan, diff, review, or test log. Continue from that artifact; do not fabricate completion.

## Model selection rubric

| Need | Prefer |
|---|---|
| Ambiguous requirements, architecture, migration, threat modeling | strongest available planner |
| Mechanical edits with clear acceptance tests | lower-cost implementer |
| Independent correctness and regression review | different model/provider when practical |
| Novel, security-sensitive, or failed repair | stronger implementer/reviewer and tighter human checkpoints |

Record the model identifier, reason for selection, and usage/cost if exposed. If usage is not exposed, state that it is unavailable rather than estimating it as fact.
