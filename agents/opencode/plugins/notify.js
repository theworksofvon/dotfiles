/**
 * Desktop notifications for opencode, matching the Claude Code hook.
 *
 * `session.idle` fires when a turn finishes. It delegates to agent-notify,
 * which decides whether you'd actually see the output — it stays silent when
 * the terminal is frontmost and you're looking at the active tmux pane.
 *
 * Lives in ~/.config/opencode/plugins/ (symlinked from the dotfiles repo).
 */

import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

const NOTIFY = join(homedir(), ".dotfiles", "bin", "agent-notify");

export const NotifyPlugin = async ({ directory }) => {
  const project = directory ? directory.split("/").filter(Boolean).pop() : "opencode";

  return {
    event: async ({ event }) => {
      if (event?.type !== "session.idle") return;

      // agent-notify reads a hook payload on stdin; give it the same shape
      // Claude Code sends so one script serves both.
      const payload = JSON.stringify({
        hook_event_name: "Stop",
        message: `Finished in ${project}`,
      });

      await new Promise((resolve) => {
        const child = execFile(NOTIFY, [], { cwd: directory }, () => resolve());
        child.stdin?.end(payload);
        // Never let a notification failure interrupt the session.
        child.on("error", () => resolve());
      });
    },
  };
};
