/**
 * Desktop notifications for opencode, matching the Claude Code hook.
 *
 * `session.execution.succeeded` fires when a turn finishes; it replaced v1's
 * `session.idle`. It delegates to agent-notify, which decides whether you'd
 * actually see the output — it stays silent when the terminal is frontmost and
 * you're looking at the active tmux pane.
 *
 * Written against the opencode 2 plugin API: a default export with an id and
 * setup(ctx). V1-style named exports are skipped by the v2 loader.
 *
 * Lives in ~/.config/opencode/plugins/ (symlinked from the dotfiles repo).
 */

import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

const NOTIFY = join(homedir(), ".dotfiles", "agents", "hooks", "agent-notify");

export default {
  id: "dotfiles.notify",
  setup(ctx) {
    const directory = ctx.location.directory;
    const project = directory
      ? directory.split("/").filter(Boolean).pop()
      : "opencode";
    const controller = new AbortController();

    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({
          signal: controller.signal,
        })) {
          if (event?.type === "session.execution.succeeded")
            await notify(project, directory);
        }
      } catch {
        // The stream ends with an abort when the plugin unloads.
      }
    })();

    return () => controller.abort();
  },
};

function notify(project, directory) {
  // agent-notify reads a hook payload on stdin; give it the same shape
  // Claude Code sends so one script serves both.
  const payload = JSON.stringify({
    hook_event_name: "Stop",
    message: `Finished in ${project}`,
  });

  return new Promise((done) => {
    const child = execFile(NOTIFY, [], { cwd: directory }, () => done());
    child.stdin?.end(payload);
    // Never let a notification failure interrupt the session.
    child.on("error", () => done());
  });
}
