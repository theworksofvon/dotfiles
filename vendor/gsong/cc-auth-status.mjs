#!/usr/bin/env node

import { execSync } from "child_process";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { homedir } from "os";

const CONFIG_FILE = join(
  homedir(),
  ".config",
  "cc-auth-status",
  "accounts.json",
);
const CACHE_DIR = join(homedir(), ".cache", "cc-auth-status");
const CACHE_FILE = join(CACHE_DIR, "status.json");
const CACHE_TTL = 60_000; // 60 seconds

const flags = {
  debug: process.argv.includes("--debug"),
  forceRefresh: process.argv.includes("--force-refresh"),
};

function debug(...args) {
  if (flags.debug) console.error(...args);
}

const ANSI_COLORS = {
  black: 30,
  red: 31,
  green: 32,
  yellow: 33,
  blue: 34,
  magenta: 35,
  cyan: 36,
  white: 37,
  brightBlack: 90,
  brightRed: 91,
  brightGreen: 92,
  brightYellow: 93,
  brightBlue: 94,
  brightMagenta: 95,
  brightCyan: 96,
  brightWhite: 97,
};

function colorize(text, colorName) {
  const code = ANSI_COLORS[colorName];
  if (code == null) return text;
  return `\x1b[${code}m${text}\x1b[0m`;
}

function readCache() {
  try {
    const cache = JSON.parse(readFileSync(CACHE_FILE, "utf8"));
    if (Date.now() - cache.timestamp < CACHE_TTL) {
      debug("Cache hit");
      return cache.data;
    }
    debug("Cache expired");
    return null;
  } catch {
    return null;
  }
}

function writeCache(data) {
  try {
    mkdirSync(CACHE_DIR, { recursive: true });
    writeFileSync(CACHE_FILE, JSON.stringify({ timestamp: Date.now(), data }));
  } catch {}
}

function loadAccountMap() {
  try {
    return JSON.parse(readFileSync(CONFIG_FILE, "utf8"));
  } catch {
    debug("No accounts config found at", CONFIG_FILE);
    return {};
  }
}

function getAuthStatus() {
  try {
    // Unset ANTHROPIC_API_KEY so claude reports OAuth identity, not API key auth
    const env = { ...process.env };
    delete env.ANTHROPIC_API_KEY;
    const output = execSync("claude auth status", {
      encoding: "utf8",
      timeout: 5000,
      env,
      stdio: ["pipe", "pipe", "ignore"],
    }).trim();
    return JSON.parse(output);
  } catch (err) {
    debug("Failed to get auth status:", err.message);
    return null;
  }
}

try {
  let status = flags.forceRefresh ? null : readCache();

  if (!status) {
    status = getAuthStatus();
    if (status) writeCache(status);
  }

  if (!status || !status.loggedIn) {
    process.stdout.write("?");
    process.exit(0);
  }

  debug("Auth status:", JSON.stringify(status, null, 2));

  const accounts = loadAccountMap();
  const entry = accounts[status.orgId];
  const label = entry?.label || status.orgName || "?";
  const color = entry?.color;

  process.stdout.write(colorize(label, color));
} catch {
  process.stdout.write("?");
}
