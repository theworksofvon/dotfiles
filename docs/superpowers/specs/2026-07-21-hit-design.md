# `hit` — a simple curl wrapper for hitting endpoints

**Status:** design approved 2026-07-21

## Goal

A single terminal command that makes HTTP requests less painful than raw
`curl`, for both a human at the keyboard and an AI agent. Two ways to use it:

- **Ad-hoc:** `hit get /users`, `hit post /login '{"u":"ada"}'`
- **Saved:** define a route once in config, then `hit users` knows it's a GET.

It shells out to real `curl` (so what runs _is_ a curl command), stays
zero-dependency (Node built-ins only, matching the other `bin/` tools), and
keeps every secret out of the config file.

## Non-goals (YAGNI for v1)

Response assertions / test-runner behavior, saving responses, request chaining,
auth schemes other than a bearer-style header, streaming huge downloads
(response bodies are buffered).

## Command surface

```
hit <route>                     # saved top-level route:      hit users
hit <service>/<route>           # saved route in a service:   hit surface/users
hit <service> <route>           # same, space instead of slash
hit <method> <url|path>         # ad-hoc:                      hit get /users
hit list                        # list envs, services, routes
hit auth <name> [--refresh|--clear]   # inspect/manage a cached token
hit --help
```

Any request form takes optional **trailing positionals**, order-free, each
classified by shape — no flags to remember:

- path-param values fill `{...}` placeholders in a saved route's path, in order
  (leading, non-JSON args): `hit surface/user 42` → `/users/42`
- an arg that looks like JSON (`{…}`, `[…]`) or `@file.json` → request **body**
- any other remaining arg → **token** (sent as `Authorization: Bearer <arg>`)

Examples:

```
hit post /login '{"u":"ada"}'          # ad-hoc + JSON body
hit surface/create-user '{"name":"x"}' # saved route + body
hit get /me abc123token                # ad-hoc + token
hit surface/user 42 abc123token        # path param 42 + token
```

### The few flags (long form only, rarely typed)

- `-e, --env <name>` — pick an environment (default: `default_env`)
- `--curl` — dry-run: print the exact curl command, send nothing
- `--` — everything after is passed straight to `curl`

A response status of 400+ exits non-zero by default (so a broken request never
passes silently in a script); the body still prints. Use `hit ... || true` to
ignore it — there is no `--fail`-style flag to remember.

## Disambiguation rules

Parsing `hit <args...>` (flags stripped out first, anywhere in the line):

1. First token is a subcommand (`list`, `auth`, `--help`) → handle it.
2. First token is an HTTP method (`get post put patch delete head options`,
   case-insensitive) → **ad-hoc**: `method`, `url`, then trailing positionals.
   Ad-hoc has no `{}` placeholders (the URL is written literally).
3. Otherwise → **saved**:
   - `a/b` → service `a`, route `b`
   - `a b` when `a` is a known service and `b` a route in it → service `a`, route `b`
   - single token → top-level route; error (with a suggestion) if unknown
4. Fill the route's `{...}` placeholders from leading non-JSON trailing args.
5. Classify each remaining trailing arg: JSON-shaped/`@file` → body, else token.
   More than one body or token, or a missing required placeholder → usage error.

A bare `/path` (ad-hoc or saved) resolves against the active `base`; a full
`http(s)://…` URL is used as-is.

## Config

Location: `$XDG_CONFIG_HOME/hit/requests.toml`, else `~/.config/hit/requests.toml`.
Valid TOML, comments allowed. Never contains secrets.

```toml
default_env = "local"

[env.local]
base = "http://localhost:3000"

[env.prod]
base = "https://api.example.com"

# Top-level saved routes (no service). Value is "METHOD /path".
[routes]
health = "GET /health"
users  = "GET /users"

# A service groups routes, and can set its own base and attach auth.
[services.surface]
base = "https://surface.example.com"   # optional; falls back to env base
auth = "surface"                        # every route here auto-attaches auth "surface"

[services.surface.routes]
users       = "GET /users"
user        = "GET /users/{id}"
create-user = "POST /users"

# How to obtain a token. Use EITHER command OR login/body/token.
[auth.surface]
login  = "POST /auth/login"            # request made against the service/env base
body   = '{"key":"$SURFACE_KEY"}'       # $ resolves from the shell env
token  = "data.access_token"            # dotted path into the JSON response
# command = "op read op://vault/surface/token"   # alternative: stdout is the token
# header  = "Authorization: Bearer {token}"        # optional; this is the default
# ttl     = "1h"                                    # optional proactive refresh
```

### Route value grammar

`"METHOD /path"` — split on the first whitespace into method + path template.
The path may contain `{name}` placeholders.

## Variables and secrets

`$VAR` / `${VAR}` are substituted in url/path, header values, body, query, and
the auth login body. Resolution order: **active env profile, then the shell
environment.** An unresolved variable is a hard error naming the variable — never
a silent empty string. Env-profile values may themselves reference `$VAR`, which
resolves from the shell env when the profile loads.

Secrets are therefore never written to config: a `$TOKEN` (or a login `body`
referencing `$SURFACE_KEY`) is pulled from the shell at request time.

## Auth

- A request's token comes from, in order: (1) a positional token, which
  overrides everything; (2) the auth block attached to the route's service;
  (3) nothing.
- Obtaining a token: run `command` (stdout, trimmed, is the token) **or** perform
  the `login` request and read the dotted `token` path out of its JSON response.
- The token is cached to `~/.cache/hit/<name>.token` (mode `600`) and reused.
  With `ttl` it refreshes when stale; without, it lives until a 401.
- **On a 401 for an authed request, `hit` clears the cache, re-obtains the token
  once, and retries the request one time.**
- Header default `Authorization: Bearer {token}`, overridable per auth block.
- `hit auth <name>` obtains/prints the token; `--refresh` forces a new one;
  `--clear` deletes the cache.
- v1 limitation: auth attaches via a **service**. A standalone authed route means
  either putting it under a service or passing a positional token.

## Execution and output

Builds a `curl` argv and runs it via `child_process`. To get the status code
(for 401 handling and the summary line) while still controlling output, the body
is written to a temp file and `-w '%{http_code}\t%{time_total}\t%{content_type}'`
is captured:

- A summary line goes to **stderr**: `METHOD url STATUS time`.
- The body goes to **stdout**. If the content-type is JSON **and** stdout is a
  TTY **and** `jq` is on PATH, it's pretty-printed through `jq`; otherwise raw
  bytes. Non-TTY (pipes, agents) always gets raw, uncolored output.

`--curl` builds the same argv (obtaining the auth token, since a runnable curl
must contain it) and prints it as a copy-pasteable command instead of running —
so `--curl` output is as sensitive as the request itself.

### Exit codes

- `0` — request completed with status < 400
- `22` — response status ≥ 400 (default; body still prints, `|| true` to ignore)
- `2` — usage error (bad args, unknown route, unresolved variable)
- otherwise — curl's own exit code on a transport error

## Files

Tracked in the repo:

```
bin/hit                          # the tool: one zero-dep Node executable
bin/hit.test.mjs                 # tests, built-in node:test (node --test bin/)
config/hit/requests.example.toml # starter config, seeded into ~ by install.sh
```

`bin/` is already on PATH as `~/.dotfiles/bin` (zshrc) and `install.sh` chmods
`bin/*`, so `bin/hit` needs no new symlink. `install.sh` gains one block that
seeds `~/.config/hit/requests.toml` from the example if absent (mirroring the
`~/.gitconfig.local` pattern).

Created at runtime, never tracked (secrets / user data):

```
~/.config/hit/requests.toml      # the real config
~/.cache/hit/<name>.token         # cached tokens, mode 600
```

`bin/hit` is a single file, internally sectioned (arg parse · TOML parser ·
config resolve · var/secret resolve · auth · curl builder · run+output ·
subcommands), with a `main()` guard so `hit.test.mjs` can import the pieces and
unit-test them (arg grammar, TOML parser, var resolution, curl builder) without
network. `--curl` is the integration seam; a couple of live tests run against a
throwaway Node `http` server.

## Internal TOML parser (supported subset)

Comments (`#`), `key = value`, `[table]` and nested `[a.b.c]` tables, basic
strings (`"…"` with `\n \t \" \\` escapes), literal strings (`'…'`), inline
tables (`{ k = v }`), booleans, integers. **Not** supported (errors clearly):
arrays, arrays-of-tables, multiline strings, dates, floats. The config only
needs the supported subset.
