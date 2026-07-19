#!/usr/bin/env node

import { execSync } from "child_process";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { homedir } from "os";

const CACHE_DIR = join(homedir(), ".cache", "cc-pr-number");
const CACHE_FILE = join(CACHE_DIR, "cache.json");
const HIT_TTL = 300_000; // 5 min — PR numbers don't change
const MISS_TTL = 60_000; // 60s — pick up newly created PRs quickly

function exec(cmd) {
  try {
    return execSync(cmd, {
      encoding: "utf8",
      timeout: 5000,
      stdio: ["pipe", "pipe", "ignore"],
    }).trim();
  } catch {
    return null;
  }
}

function readCache() {
  try {
    return JSON.parse(readFileSync(CACHE_FILE, "utf8"));
  } catch {
    return null;
  }
}

function writeCache(data) {
  try {
    mkdirSync(CACHE_DIR, { recursive: true });
    writeFileSync(CACHE_FILE, JSON.stringify(data));
  } catch {}
}

try {
  const branch = exec("git branch --show-current");
  const repo = exec("git rev-parse --show-toplevel");
  if (!branch || !repo) process.exit(0);

  const cache = readCache();
  const now = Date.now();

  if (cache && cache.branch === branch && cache.repo === repo) {
    const ttl = cache.pr ? HIT_TTL : MISS_TTL;
    if (now - cache.timestamp < ttl) {
      if (cache.pr) process.stdout.write(`| #${cache.pr} `);
      process.exit(0);
    }
  }

  const pr = exec("gh pr view --json number -q .number");

  writeCache({ branch, repo, pr: pr || null, timestamp: now });

  if (pr) process.stdout.write(`| #${pr} `);
} catch {
  // silent exit 0 on any unexpected error
}
