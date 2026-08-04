// Tests for hit. Run: node --test bin/
//
// Unit tests import the pieces directly (the TOML parser, arg grammar, var
// resolution, curl builder). A live block boots a throwaway http server and
// drives the real `hit` executable end to end.

import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { execFileSync, execFile } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
const HIT = join(HERE, "hit");
const { parseToml, resolveVars, planRequest, buildCurlArgs, parseFlags } =
  await import(HIT);

// ── TOML parser ──────────────────────────────────────────────────────────────

test("parseToml: tables, nested tables, strings, inline tables", () => {
  const c = parseToml(`
    default_env = "local"
    [env.local]
    base = "http://localhost:3000"
    [services.surface.routes]
    user = "GET /users/{id}"
    [auth.surface]
    body = '{"key":"$K"}'
    header = { name = "X" }
  `);
  assert.equal(c.default_env, "local");
  assert.equal(c.env.local.base, "http://localhost:3000");
  assert.equal(c.services.surface.routes.user, "GET /users/{id}");
  assert.equal(c.auth.surface.body, '{"key":"$K"}');
  assert.deepEqual(c.auth.surface.header, { name: "X" });
});

test("parseToml: comments are stripped, but not inside strings", () => {
  const c = parseToml(`
    a = "x" # trailing comment
    b = "value # with hash"
  `);
  assert.equal(c.a, "x");
  assert.equal(c.b, "value # with hash");
});

test("parseToml: rejects arrays", () => {
  assert.throws(() => parseToml("a = [1, 2]"), /arrays are not supported/);
});

// ── variables ────────────────────────────────────────────────────────────────

test("resolveVars: profile first, then env", () => {
  process.env.HIT_TEST_SHELLVAR = "shell";
  assert.equal(resolveVars("$A/${B}", { A: "profile", B: "b" }), "profile/b");
  assert.equal(resolveVars("$HIT_TEST_SHELLVAR", {}), "shell");
});

// ── arg grammar ──────────────────────────────────────────────────────────────

const CONFIG = {
  _env: "local",
  env: { local: { base: "http://h" } },
  routes: { users: "GET /users" },
  services: {
    surface: {
      base: "http://s",
      auth: "surface",
      routes: { user: "GET /users/{id}", make: "POST /users" },
    },
  },
};

test("planRequest: ad-hoc method + path uses env base", () => {
  const p = planRequest(["get", "/users"], CONFIG);
  assert.equal(p.method, "GET");
  assert.equal(p.url, "http://h/users");
});

test("planRequest: full URL is used as-is", () => {
  assert.equal(
    planRequest(["get", "https://x.com/y"], CONFIG).url,
    "https://x.com/y",
  );
});

test("planRequest: saved top-level route knows its method", () => {
  const p = planRequest(["users"], CONFIG);
  assert.equal(p.method, "GET");
  assert.equal(p.url, "http://h/users");
});

test("planRequest: service/route and space form agree", () => {
  const a = planRequest(["surface/user", "42"], CONFIG);
  const b = planRequest(["surface", "user", "42"], CONFIG);
  assert.equal(a.url, "http://s/users/42");
  assert.deepEqual(a, b);
  assert.equal(a.authName, "surface");
});

test("planRequest: JSON trailing arg is body, bare arg is token", () => {
  const p = planRequest(["post", "/x", '{"a":1}', "tok123"], CONFIG);
  assert.equal(p.body, '{"a":1}');
  assert.equal(p.token, "tok123");
});

test("planRequest: path param fills before body/token classification", () => {
  const p = planRequest(["surface/user", "42", "tok"], CONFIG);
  assert.equal(p.url, "http://s/users/42");
  assert.equal(p.token, "tok");
  assert.equal(p.body, undefined);
});

// ── curl builder ─────────────────────────────────────────────────────────────

test("buildCurlArgs: method, headers, body, url", () => {
  const args = buildCurlArgs({
    method: "POST",
    url: "http://h/x",
    headers: [["Authorization", "Bearer t"]],
    body: '{"a":1}',
  });
  assert.deepEqual(args, [
    "-sS",
    "-X",
    "POST",
    "-H",
    "Authorization: Bearer t",
    "--data-raw",
    '{"a":1}',
    "http://h/x",
  ]);
});

test("parseFlags: splits flags, positionals, and -- passthrough", () => {
  const { flags, rest, extra } = parseFlags([
    "-e",
    "prod",
    "get",
    "/x",
    "--",
    "--insecure",
  ]);
  assert.equal(flags.env, "prod");
  assert.deepEqual(rest, ["get", "/x"]);
  assert.deepEqual(extra, ["--insecure"]);
});

// ── live end-to-end against a throwaway server ───────────────────────────────

test("live: real requests through the hit executable", async (t) => {
  const seen = [];
  const server = createServer((req, res) => {
    let body = "";
    req.on("data", (d) => (body += d));
    req.on("end", () => {
      seen.push({
        method: req.method,
        url: req.url,
        auth: req.headers.authorization,
        body,
      });
      if (req.url === "/auth/login") {
        res.setHeader("content-type", "application/json");
        return res.end(
          JSON.stringify({ data: { access_token: "LIVE-TOKEN" } }),
        );
      }
      if (
        req.headers.authorization === "Bearer LIVE-TOKEN" ||
        !req.url.startsWith("/secure")
      ) {
        res.setHeader("content-type", "application/json");
        return res.end(JSON.stringify({ ok: true, url: req.url }));
      }
      res.statusCode = 401;
      res.end(JSON.stringify({ error: "unauthorized" }));
    });
  });
  await new Promise((r) => server.listen(0, r));
  const port = server.address().port;
  const base = `http://127.0.0.1:${port}`;

  const configText = `
default_env = "test"
[env.test]
base = "${base}"
[routes]
ping = "GET /ping"
[services.svc]
base = "${base}"
auth = "svc"
[services.svc.routes]
secret = "GET /secure/data"
[auth.svc]
login = "POST /auth/login"
body = '{"k":"x"}'
token = "data.access_token"
`;
  const dir = mkdtempSync(join(tmpdir(), "hit-test-"));
  mkdirSync(join(dir, "hit"), { recursive: true });
  writeFileSync(join(dir, "hit", "requests.toml"), configText);
  const env = { ...process.env, XDG_CONFIG_HOME: dir, XDG_CACHE_HOME: dir };
  // async so the in-process server can answer while a `hit` child runs
  const execFileP = promisify(execFile);
  const run = async (args) =>
    (await execFileP(HIT, args, { encoding: "utf8", env })).stdout;

  t.after(() => server.close());

  // ad-hoc GET
  assert.match(await run(["get", "/ping"]), /"ok":true/);
  assert.equal(seen.at(-1).url, "/ping");

  // saved route
  await run(["ping"]);
  assert.equal(seen.at(-1).url, "/ping");

  // POST with JSON body
  await run(["post", "/echo", '{"hello":"world"}']);
  assert.equal(seen.at(-1).method, "POST");
  assert.equal(seen.at(-1).body, '{"hello":"world"}');

  // authed route: logs in, then hits /secure with the bearer token
  const out = await run(["svc/secret"]);
  assert.match(out, /"ok":true/);
  assert.equal(seen.at(-1).auth, "Bearer LIVE-TOKEN");
  assert.ok(seen.some((s) => s.url === "/auth/login"));

  // --curl prints a command, sends nothing
  const before = seen.length;
  const curlOut = await run(["--curl", "get", "/ping"]);
  assert.match(curlOut, /^curl /);
  assert.equal(seen.length, before);
});
