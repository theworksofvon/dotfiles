#!/usr/bin/env node

import { execSync } from "child_process";
import { basename } from "path";
import { parseArgs as nodeParseArgs } from "util";

/**
 * Send macOS notification for Claude Code events
 * Reads event JSON from stdin and dispatches based on hook_event_name
 * Only sends if not in tmux or tmux pane is inactive
 */

const readStdin = async () => {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString();
};

const isInTmux = () => {
  return !!process.env.TMUX;
};

const isActiveTmuxPane = (() => {
  let cached;
  return () => {
    if (cached !== undefined) return cached;
    if (!isInTmux()) return (cached = false);
    try {
      const tmuxPane = process.env.TMUX_PANE;
      if (!tmuxPane) return (cached = false);
      const result = execSync(
        `tmux display-message -pt "${tmuxPane}" '#{pane_active} #{window_active}'`,
        {
          encoding: "utf8",
          stdio: ["pipe", "pipe", "ignore"],
        },
      ).trim();
      // Both pane and window must be active
      return (cached = result === "1 1");
    } catch (error) {
      return (cached = false);
    }
  };
})();

const isGhosttyFrontmost = (() => {
  let cached;
  return () => {
    if (cached !== undefined) return cached;
    try {
      const result = execSync(
        `osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true'`,
        {
          encoding: "utf8",
          stdio: ["pipe", "pipe", "ignore"],
        },
      ).trim();
      return (cached = result === "ghostty");
    } catch (error) {
      return (cached = false);
    }
  };
})();

/**
 * Notification Decision Logic:
 *
 *   Should we send a notification?
 *
 *   ├─ Is --force flag set?
 *   │  ├─ YES → ✓ NOTIFY
 *   │  └─ NO → Continue...
 *   │
 *   ├─ Is Ghostty the frontmost app?
 *   │  ├─ NO (Ghostty is in background) → ✓ NOTIFY (user is in another app)
 *   │  └─ YES (Ghostty is frontmost) → Continue...
 *   │
 *   └─ Are we in tmux?
 *      ├─ NO → ✓ NOTIFY
 *      └─ YES → Is this pane active AND window active?
 *         ├─ YES (both active) → ✗ DON'T NOTIFY (user is watching)
 *         └─ NO (either inactive) → ✓ NOTIFY
 */
const shouldNotify = (force = false) => {
  // Force flag overrides all checks
  if (force) {
    return true;
  }
  // If Ghostty is not the frontmost app, always notify (user is in another app)
  if (!isGhosttyFrontmost()) {
    return true;
  }
  // Ghostty is frontmost, use tmux logic:
  // Don't notify if we're in the active tmux pane (user is actively watching)
  if (isActiveTmuxPane()) {
    return false;
  }
  return true;
};

const getDirectoryInfo = () => {
  const pwd = process.cwd();
  const parts = pwd.split("/").filter(Boolean);
  const lastTwo = parts.slice(-2).join("/");
  const current = basename(pwd);

  return { lastTwo, current };
};

const sendNotification = ({
  title,
  subtitle,
  message,
  sound = "default",
  force = false,
}) => {
  if (!shouldNotify(force)) {
    return;
  }

  const escapeAppleScript = (str) => {
    return str.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  };

  const appleScript = `display notification "${escapeAppleScript(message)}" with title "${escapeAppleScript(title)}" subtitle "${escapeAppleScript(subtitle)}" sound name "${sound}"`;

  try {
    execSync(`osascript -e '${appleScript.replace(/'/g, "'\\''")}'`, {
      stdio: "ignore",
      shell: true,
    });
  } catch (error) {
    console.error("Failed to send notification:", error.message);
  }
};

// Parse command line arguments using Node.js built-in parseArgs
const parseArgs = () => {
  const { values } = nodeParseArgs({
    options: {
      debug: { type: "boolean" },
      force: { type: "boolean" },
      message: { type: "string" },
      subtitle: { type: "string" },
      title: { type: "string" },
      sound: { type: "string" },
    },
    strict: false, // Allow unknown options for forward compatibility
  });
  return values;
};

const getNotificationConfig = (eventData) => {
  const { lastTwo, current } = getDirectoryInfo();

  switch (eventData.hook_event_name) {
    case "Notification":
      return {
        title: "CC: Input Required",
        subtitle: current,
        message: eventData.message || "Input required",
        sound: "Ping",
      };

    case "Stop":
      return {
        title: "CC: Done",
        subtitle: current,
        message: `Task completed: ${lastTwo}`,
        sound: "Glass",
      };

    default:
      return {
        title: "Claude Code",
        subtitle: current,
        message: eventData.message || `Event: ${eventData.hook_event_name}`,
        sound: "default",
      };
  }
};

const main = async () => {
  const options = parseArgs();
  const { lastTwo, current } = getDirectoryInfo();

  // Try to read event JSON from stdin
  let eventData = null;
  let stdinData = "";

  try {
    stdinData = await readStdin();
    if (stdinData.trim()) {
      eventData = JSON.parse(stdinData);
    }
  } catch (error) {
    // Not JSON or no stdin, fall back to CLI args
  }

  const inTmux = isInTmux();
  const activePane = isActiveTmuxPane();
  const ghosttyFrontmost = isGhosttyFrontmost();

  if (options.debug) {
    console.log("Debug info:");
    console.log("  TMUX:", process.env.TMUX);
    console.log("  TMUX_PANE:", process.env.TMUX_PANE);
    if (inTmux && process.env.TMUX_PANE) {
      try {
        const status = execSync(
          `tmux display-message -pt "${process.env.TMUX_PANE}" '#{pane_active} #{window_active}'`,
          { encoding: "utf8", stdio: ["pipe", "pipe", "ignore"] },
        ).trim();
        const [paneActive, windowActive] = status.split(" ");
        console.log("  pane_active:", paneActive);
        console.log("  window_active:", windowActive);
      } catch (e) {}
    }
    console.log("  isInTmux:", inTmux);
    console.log("  isActiveTmuxPane:", activePane);
    console.log("  isGhosttyFrontmost:", ghosttyFrontmost);
    console.log("  shouldNotify:", shouldNotify(options.force));
    console.log("  force:", options.force);
    console.log("  eventData:", eventData);
  }

  let title, subtitle, message, sound, force;

  // If we have event data with hook_event_name, use that
  if (eventData && eventData.hook_event_name) {
    const config = getNotificationConfig(eventData);
    title = config.title;
    subtitle = config.subtitle;
    message = config.message;
    sound = config.sound;
    force = options.force || false; // Allow --force flag to override
  } else {
    // Fall back to CLI args for backward compatibility
    message = (options.message || "")
      .replace("{{dir}}", lastTwo)
      .replace("{{basename}}", current);

    subtitle = (options.subtitle || current)
      .replace("{{dir}}", lastTwo)
      .replace("{{basename}}", current);

    title = options.title || "Claude Code";
    sound = options.sound || "default";
    force = options.force;
  }

  sendNotification({
    title,
    subtitle,
    message,
    sound,
    force,
  });
};

main();
