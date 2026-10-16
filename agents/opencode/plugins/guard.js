/**
 * Guardrails and format-on-write for opencode, matching the Claude Code and
 * Codex hooks.
 *
 * Both delegate to the shared scripts in ~/.dotfiles/agents/hooks, fed the
 * same payload shape Claude Code sends, so one guard list serves all three
 * harnesses. Throwing from the execute.before hook is how opencode cancels a
 * tool call; the message reaches the model.
 *
 * Written against the opencode 2 plugin API: a default export with an id and
 * setup(ctx). V1-style named exports are skipped by the v2 loader.
 *
 * Lives in ~/.config/opencode/plugins/ (symlinked from the dotfiles repo).
 */

import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { isAbsolute, join, resolve } from "node:path";

const HOOKS = join(homedir(), ".dotfiles", "agents", "hooks");

// opencode names its tools in lowercase; the hooks expect Claude's names.
const TOOL_NAMES = {
  shell: "Bash",
  edit: "Edit",
  write: "Write",
  patch: "Edit",
};

export default {
  id: "dotfiles.guard",
  async setup(ctx) {
    const directory = ctx.location.directory;

    await ctx.tool.hook("execute.before", async (event) => {
      const input = event.input ?? {};
      const cwd = input.workdir ?? directory;
      const { code, stderr } = await run(
        "guard",
        {
          hook_event_name: "PreToolUse",
          tool_name: TOOL_NAMES[event.tool] ?? event.tool,
          tool_input: input,
          cwd,
        },
        cwd,
      );
      if (code === 2) throw new Error(stderr.trim());
    });

    await ctx.tool.hook("execute.after", async (event) => {
      if (event.status !== "completed") return;
      for (const file of writtenFiles(event, directory)) {
        await run(
          "format-on-write",
          {
            hook_event_name: "PostToolUse",
            tool_name: TOOL_NAMES[event.tool],
            tool_input: { file_path: file },
            cwd: directory,
          },
          directory,
        );
      }
    });
  },
};

// Edit and write name one path; patch can touch several, listed in its text.
function writtenFiles(event, directory) {
  const input = event.input ?? {};
  let paths = [];
  if (event.tool === "edit" || event.tool === "write") paths = [input.path];
  if (event.tool === "patch") {
    paths = [
      ...String(input.patchText ?? "").matchAll(
        /^\*\*\* (?:Add|Update) File: (.+)$/gm,
      ),
    ].map((m) => m[1].trim());
  }
  return paths
    .filter((p) => typeof p === "string" && p)
    .map((p) => (isAbsolute(p) ? p : resolve(directory, p)));
}

function run(script, payload, cwd) {
  return new Promise((done) => {
    const child = execFile(
      join(HOOKS, script),
      [],
      { cwd },
      (error, _stdout, stderr) => done({ code: error?.code ?? 0, stderr }),
    );
    child.stdin?.end(JSON.stringify(payload));
    // A hook that can't start must not take the session down with it.
    child.on("error", () => done({ code: 0, stderr: "" }));
  });
}
