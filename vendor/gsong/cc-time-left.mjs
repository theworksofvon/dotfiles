#!/usr/bin/env node

/**
 * Claude Code Usage API - Time Left Calculator
 *
 * This script queries the Anthropic API to get the exact end time of the current
 * 5-hour usage block for Claude Code when using a Claude subscription (OAuth).
 *
 * Caching:
 * - Results are cached for 5 minutes in ~/.cache/cc-time-left/usage-data.json
 * - Multiple script instances share the same cache
 * - Use --force-refresh to bypass cache and fetch fresh data
 * - Use --debug to see cache hit/miss information
 *
 * API Details:
 * - Endpoint: https://api.anthropic.com/api/oauth/usage
 * - Authentication: OAuth Bearer token from macOS Keychain
 * - Required Headers:
 *   - Authorization: Bearer <oauth_token>
 *   - Content-Type: application/json
 *   - User-Agent: claude-code/2.0.25
 *   - anthropic-beta: oauth-2025-04-20 (CRITICAL - enables OAuth on this endpoint)
 *
 * API Response Structure:
 * {
 *   "five_hour": {
 *     "utilization": <number 0-100>,      // Percentage of 5-hour limit used
 *     "resets_at": "<ISO 8601 timestamp>" // When current block ends
 *   },
 *   "seven_day": {
 *     "utilization": <number 0-100>,      // Percentage of 7-day limit used
 *     "resets_at": "<ISO 8601 timestamp>" // When 7-day window resets
 *   },
 *   "seven_day_oauth_apps": null,         // OAuth apps usage (if applicable)
 *   "seven_day_opus": {
 *     "utilization": <number 0-100>,      // Opus-specific usage
 *     "resets_at": "<ISO 8601 timestamp>" // Opus limit reset time (null if unlimited)
 *   }
 * }
 *
 * Keychain Storage:
 * - Service: "Claude Code-credentials"
 * - Account: Current macOS username
 * - Location: ~/Library/Keychains/login.keychain-db
 * - Data: JSON with claudeAiOauth.accessToken
 */

import { execSync } from "child_process";
import { homedir } from "os";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";

// Configuration
const CONFIG = {
  API_ENDPOINT: "https://api.anthropic.com/api/oauth/usage",
  USER_AGENT: "claude-code/2.0.25",
  ANTHROPIC_BETA: "oauth-2025-04-20",
  KEYCHAIN_SERVICE: "Claude Code-credentials",
  CACHE_TTL_MS: 5 * 60 * 1000, // 5 minutes
};

// Period durations in milliseconds
const PERIOD_DURATION = {
  FIVE_HOUR: 5 * 60 * 60 * 1000,
  SEVEN_DAY: 7 * 24 * 60 * 60 * 1000,
};

// Cache configuration
const CACHE_DIR = join(homedir(), ".cache", "cc-time-left");
const CACHE_FILE = join(CACHE_DIR, "usage-data.json");

// Visual indicators
const INDICATORS = {
  SAFE: "🟢",
  WARNING: "🟡",
  DANGER: "🔴",
};

// Parse command-line flags
const flags = {
  debug: process.argv.includes("--debug"),
  forceRefresh: process.argv.includes("--force-refresh"),
  help: process.argv.includes("--help") || process.argv.includes("-h"),
};

/**
 * Debug logging helper
 * @param {...any} args - Arguments to log
 */
function debug(...args) {
  if (flags.debug) {
    console.error(...args);
  }
}

/**
 * Shows help text
 */
function showHelp() {
  console.log(`Usage: cc-time-left.mjs [options]

Displays Claude Code usage limits and reset times.

Options:
  --debug           Show detailed debug information
  --force-refresh   Skip cache and fetch fresh data
  --help, -h        Show this help message

Output format:
  [5hr indicator][reset time] [7day indicator][time remaining]
  Uses – as placeholder when a period has no active data.

  Indicators:
    🟢 Safe - on track or below quota
    🟡 Warning - using quota faster than time
    🔴 Danger - likely to exceed quota`);
  process.exit(0);
}

/**
 * Validates API response structure
 * @param {Object} data - API response data
 * @returns {boolean} True if valid
 */
function validateUsageData(data) {
  if (!data || typeof data !== "object") return false;
  if (!data.five_hour || typeof data.five_hour.utilization !== "number")
    return false;
  // Allow null resets_at when no active block (utilization is 0)
  return true;
}

/**
 * Reads cached usage data if valid
 * @returns {Object|null} Cached usage data or null if expired/missing
 */
function readCache() {
  try {
    const cacheData = JSON.parse(readFileSync(CACHE_FILE, "utf-8"));
    const now = Date.now();

    // Check if cache is still valid (within TTL)
    if (now - cacheData.timestamp < CONFIG.CACHE_TTL_MS) {
      debug(
        `Using cached data (age: ${Math.round((now - cacheData.timestamp) / 1000)}s)`,
      );
      return cacheData.data;
    }

    debug("Cache expired, fetching fresh data");
    return null;
  } catch (error) {
    debug("Failed to read cache:", error.message);
    return null;
  }
}

/**
 * Writes usage data to cache
 * @param {Object} data - Usage data to cache
 */
function writeCache(data) {
  try {
    mkdirSync(CACHE_DIR, { recursive: true });
    const cacheData = {
      timestamp: Date.now(),
      data: data,
    };
    writeFileSync(CACHE_FILE, JSON.stringify(cacheData, null, 2), "utf-8");
    debug("Cache updated");
  } catch (error) {
    debug("Failed to write cache:", error.message);
  }
}

/**
 * Retrieves OAuth token from macOS Keychain
 * Note: Uses execSync for simplicity since keychain access is fast and synchronous by nature
 * @returns {string|null} OAuth access token or null if not found
 */
function getOAuthTokenFromKeychain() {
  try {
    // Query macOS keychain for Claude Code credentials
    const keychainData = execSync(
      `security find-generic-password -a "$USER" -s "${CONFIG.KEYCHAIN_SERVICE}" -w`,
      { encoding: "utf-8" },
    ).trim();

    if (!keychainData) {
      return null;
    }

    // Parse the JSON stored in keychain
    const credentials = JSON.parse(keychainData);

    // Extract the OAuth access token
    return credentials?.claudeAiOauth?.accessToken || null;
  } catch (error) {
    debug("Failed to retrieve token from keychain:", error.message);
    return null;
  }
}

/**
 * Fetches usage data from Anthropic API
 * @param {string} accessToken - OAuth access token
 * @returns {Promise<Object|null>} Usage data or null on error
 */
async function fetchUsageData(accessToken) {
  try {
    const response = await fetch(CONFIG.API_ENDPOINT, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
        "User-Agent": CONFIG.USER_AGENT,
        "anthropic-beta": CONFIG.ANTHROPIC_BETA,
      },
    });

    if (!response.ok) {
      debug(`API request failed: ${response.status} ${response.statusText}`);
      if (flags.debug) {
        const errorBody = await response.text();
        debug("Error response:", errorBody);
      }
      return null;
    }

    const data = await response.json();

    // Debug: show full API response
    if (flags.debug) {
      debug("API Response:");
      debug(JSON.stringify(data, null, 2));
    }

    return data;
  } catch (error) {
    debug("Failed to fetch usage data:", error.message);
    return null;
  }
}

/**
 * Formats a timestamp as local time, rounded to nearest hour (e.g., "4pm")
 * @param {string} isoTimestamp - ISO 8601 timestamp
 * @returns {string} Formatted time string
 */
function formatTime(isoTimestamp) {
  const date = new Date(isoTimestamp);
  const minutes = date.getMinutes();
  let hours = date.getHours();

  // Round up if 30 minutes or more
  if (minutes >= 30) {
    hours = (hours + 1) % 24;
  }

  const ampm = hours >= 12 ? "pm" : "am";
  const displayHours = hours % 12 || 12;
  return `${displayHours}${ampm}`;
}

/**
 * Calculates time remaining until timestamp and formats as "Xd" or "Xh"
 * @param {string} isoTimestamp - ISO 8601 timestamp
 * @returns {string} Formatted time remaining (e.g., "2d", "6h")
 */
function formatTimeRemaining(isoTimestamp) {
  const now = Date.now();
  const resetTime = new Date(isoTimestamp).getTime();
  const msRemaining = resetTime - now;

  if (msRemaining <= 0) {
    return "0h";
  }

  const hoursRemaining = Math.floor(msRemaining / (1000 * 60 * 60));

  if (hoursRemaining >= 24) {
    const daysRemaining = Math.floor(hoursRemaining / 24);
    return `${daysRemaining}d`;
  } else if (hoursRemaining > 0) {
    return `${hoursRemaining}h`;
  } else {
    // Less than 1 hour - show minutes
    const minutesRemaining = Math.floor(msRemaining / (1000 * 60));
    return `${minutesRemaining}m`;
  }
}

/**
 * Formats milliseconds as "Xd", "X.Xh", or "Xm"
 * @param {number} msRemaining - Milliseconds remaining
 * @returns {string} Formatted time (e.g., "2d", "1.5h", "45m")
 */
function formatMsRemaining(msRemaining) {
  if (msRemaining <= 0) {
    return "0m";
  }

  const hoursRemaining = msRemaining / (1000 * 60 * 60);

  if (hoursRemaining >= 24) {
    const daysRemaining = Math.floor(hoursRemaining / 24);
    return `${daysRemaining}d`;
  } else if (hoursRemaining >= 1) {
    return `${hoursRemaining.toFixed(1)}h`;
  } else {
    const minutesRemaining = Math.floor(msRemaining / (1000 * 60));
    return `${minutesRemaining}m`;
  }
}

/**
 * Calculates time until tokens are exhausted based on current burn rate
 * @param {number} utilization - Percentage used (0-100)
 * @param {string} resetsAt - ISO 8601 timestamp when period resets
 * @param {number} periodDurationMs - Total period duration in milliseconds
 * @returns {number|null} Milliseconds until exhaustion, or null if not applicable
 */
function calculateTimeUntilExhausted(utilization, resetsAt, periodDurationMs) {
  const now = Date.now();
  const resetTime = new Date(resetsAt).getTime();
  const startTime = resetTime - periodDurationMs;
  const timeElapsed = now - startTime;

  // If we haven't used anything yet, can't calculate
  if (utilization === 0 || timeElapsed <= 0) {
    return null;
  }

  const remainingPercent = 100 - utilization;

  // Already exhausted
  if (remainingPercent <= 0) {
    return 0;
  }

  // Calculate burn rate: percentage per millisecond
  const burnRatePerMs = utilization / timeElapsed;

  // Calculate time until exhaustion
  const msUntilExhausted = remainingPercent / burnRatePerMs;

  return msUntilExhausted;
}

/**
 * Gets visual indicator based on burn rate (usage vs time elapsed)
 * @param {number} utilization - Percentage of limit used (0-100)
 * @param {string} resetsAt - ISO 8601 timestamp when period resets
 * @param {number} periodDurationMs - Total period duration in milliseconds
 * @returns {string} Emoji indicator
 */
function getIndicatorForBurnRate(utilization, resetsAt, periodDurationMs) {
  const now = Date.now();
  const resetTime = new Date(resetsAt).getTime();
  const startTime = resetTime - periodDurationMs;
  const timeElapsed = now - startTime;

  // Calculate percentage of time elapsed
  const timeElapsedPercent = (timeElapsed / periodDurationMs) * 100;

  // Edge case: too early in the period to judge (< 10% time OR < 15% usage)
  if (timeElapsedPercent < 10 && utilization < 15) {
    return INDICATORS.SAFE;
  }

  // Calculate burn ratio: how fast we're using quota vs how fast time is passing
  const burnRatio = utilization / timeElapsedPercent;

  // Thresholds based on burn rate
  if (burnRatio < 1.0) {
    // Using at or below the rate of time passing (on track or better)
    return INDICATORS.SAFE;
  } else if (burnRatio < 1.3) {
    // Using 0-30% faster than time (might exceed)
    return INDICATORS.WARNING;
  } else {
    // Using 30%+ faster than time (likely to exceed)
    return INDICATORS.DANGER;
  }
}

/**
 * Analyzes and logs detailed burn rate information for debugging
 * @param {Object} usageData - Full usage data from API
 */
function analyzeBurnRate(usageData) {
  debug("\n--- Usage Summary ---");

  // 5-hour block analysis
  const now = Date.now();
  const fiveHourData = usageData.five_hour;

  if (fiveHourData && fiveHourData.resets_at) {
    const fiveHourResetTime = new Date(fiveHourData.resets_at).getTime();
    const fiveHourStartTime = fiveHourResetTime - PERIOD_DURATION.FIVE_HOUR;
    const fiveHourElapsed =
      ((now - fiveHourStartTime) / PERIOD_DURATION.FIVE_HOUR) * 100;
    const fiveHourBurnRatio = fiveHourData.utilization / fiveHourElapsed;

    let fiveHourMsg =
      `5-hour block: ${fiveHourData.utilization.toFixed(1)}% used, ${fiveHourElapsed.toFixed(1)}% elapsed, ` +
      `burn ratio: ${fiveHourBurnRatio.toFixed(2)}x, resets at ${fiveHourData.resets_at}`;

    if (fiveHourBurnRatio >= 1.3) {
      const msUntilExhausted = calculateTimeUntilExhausted(
        fiveHourData.utilization,
        fiveHourData.resets_at,
        PERIOD_DURATION.FIVE_HOUR,
      );
      if (msUntilExhausted !== null) {
        const exhaustionTime = formatMsRemaining(msUntilExhausted);
        fiveHourMsg += ` → projected exhaustion in ${exhaustionTime}`;
      }
    }

    debug(fiveHourMsg);
  } else {
    debug("5-hour block: no active block");
  }

  // 7-day usage analysis
  if (usageData.seven_day) {
    const sevenDayResetTime = new Date(usageData.seven_day.resets_at).getTime();
    const sevenDayStartTime = sevenDayResetTime - PERIOD_DURATION.SEVEN_DAY;
    const sevenDayElapsed =
      ((now - sevenDayStartTime) / PERIOD_DURATION.SEVEN_DAY) * 100;
    const sevenDayBurnRatio = usageData.seven_day.utilization / sevenDayElapsed;

    let sevenDayMsg =
      `7-day usage: ${usageData.seven_day.utilization.toFixed(1)}% used, ${sevenDayElapsed.toFixed(1)}% elapsed, ` +
      `burn ratio: ${sevenDayBurnRatio.toFixed(2)}x, resets at ${usageData.seven_day.resets_at}`;

    // Add exhaustion projection if burning too fast
    if (sevenDayBurnRatio >= 1.3) {
      const msUntilExhausted = calculateTimeUntilExhausted(
        usageData.seven_day.utilization,
        usageData.seven_day.resets_at,
        PERIOD_DURATION.SEVEN_DAY,
      );
      if (msUntilExhausted !== null) {
        const exhaustionTime = formatMsRemaining(msUntilExhausted);
        sevenDayMsg += ` → projected exhaustion in ${exhaustionTime}`;
      }
    }

    debug(sevenDayMsg);
  }

  // Opus usage
  if (usageData.seven_day_opus) {
    debug(
      `7-day Opus: ${usageData.seven_day_opus.utilization}% used, resets at ${usageData.seven_day_opus.resets_at || "unlimited"}`,
    );
  }
}

/**
 * Gets cached data with status information
 * @returns {{valid: boolean, data: Object|null}} Cache result with validity flag
 */
function getCachedData() {
  if (flags.forceRefresh) {
    debug("Force refresh requested, skipping cache");
    return { valid: false, data: null };
  }

  const data = readCache();
  return { valid: !!data, data };
}

// Main execution
if (flags.help) {
  showHelp();
}

// Step 1: Try to get cached data
const cache = getCachedData();
let usageData = cache.data;

// Step 2: If no valid cache, fetch from API
if (!cache.valid) {
  const accessToken = getOAuthTokenFromKeychain();

  if (!accessToken) {
    console.error("Error: No OAuth token found in keychain.");
    console.error("Please ensure you're logged into Claude Code.");
    process.exit(1);
  }

  debug("OAuth token found, fetching usage data...");

  usageData = await fetchUsageData(accessToken);

  if (!usageData) {
    console.error("Error: Failed to fetch usage data from API.");
    console.error("Please check your network connection and try again.");
    process.exit(1);
  }

  // Step 3: Validate API response
  if (!validateUsageData(usageData)) {
    console.error("Error: Invalid usage data received from API.");
    process.exit(1);
  }

  // Step 4: Cache the fresh data
  writeCache(usageData);
}

// Build display segment for a usage period
function buildSegmentDisplay(periodData, periodDurationMs, formatTimeFn) {
  if (!periodData || !periodData.resets_at) return "\u2013";

  const timeStr = formatTimeFn(periodData.resets_at);
  const indicator = getIndicatorForBurnRate(
    periodData.utilization,
    periodData.resets_at,
    periodDurationMs,
  );

  if (indicator === INDICATORS.DANGER) {
    const msUntilExhausted = calculateTimeUntilExhausted(
      periodData.utilization,
      periodData.resets_at,
      periodDurationMs,
    );
    if (msUntilExhausted !== null) {
      return `${indicator}${formatMsRemaining(msUntilExhausted)}/${timeStr}`;
    }
  }

  return `${indicator}${timeStr}`;
}

const fiveHourDisplay = buildSegmentDisplay(
  usageData.five_hour,
  PERIOD_DURATION.FIVE_HOUR,
  formatTime,
);
const sevenDayDisplay = buildSegmentDisplay(
  usageData.seven_day,
  PERIOD_DURATION.SEVEN_DAY,
  formatTimeRemaining,
);

console.log(`${fiveHourDisplay} ${sevenDayDisplay}`);

// Debug: show additional info with burn rate analysis
if (flags.debug) {
  analyzeBurnRate(usageData);
}
