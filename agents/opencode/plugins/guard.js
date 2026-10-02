/**
 * Guardrails and format-on-write for opencode, matching the Claude Code and
 * Codex hooks.
 *
 * Both delegate to the shared scripts in ~/.dotfiles/agents/hooks, fed the
 * same payload shape Claude Code sends, so one guard list serves all three
 * harnesses. Throwing from tool.execute.before is how opencode cancels a tool
 * call; the message reaches the model.
 *
 * Lives in ~/.config/opencode/plugins/ (symlinked from the dotfiles repo).
 */

import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

const HOOKS = join(homedir(), ".dotfiles", "agents", "hooks");

// opencode names its tools in lowercase; the hooks expect Claude's names.
const TOOL_NAMES = { bash: "Bash", edit: "Edit", write: "Write" };

function run(script, payload, cwd) {
  return new Promise((resolve) => {
    const child = execFile(
      join(HOOKS, script),
      [],
      { cwd },
      (error, _stdout, stderr) => resolve({ code: error?.code ?? 0, stderr }),
    );
    child.stdin?.end(JSON.stringify(payload));
    // A hook that can't start must not take the session down with it.
    child.on("error", () => resolve({ code: 0, stderr: "" }));
  });
}

export const GuardPlugin = async ({ directory }) => ({
  "tool.execute.before": async (input, output) => {
    const { code, stderr } = await run(
      "guard",
      {
        hook_event_name: "PreToolUse",
        tool_name: TOOL_NAMES[input.tool] ?? input.tool,
        tool_input: output.args,
        cwd: directory,
      },
      directory,
    );
    if (code === 2) throw new Error(stderr.trim());
  },

  "tool.execute.after": async (input) => {
    if (input.tool !== "edit" && input.tool !== "write") return;
    await run(
      "format-on-write",
      {
        hook_event_name: "PostToolUse",
        tool_name: TOOL_NAMES[input.tool],
        tool_input: input.args,
        cwd: directory,
      },
      directory,
    );
  },
});
