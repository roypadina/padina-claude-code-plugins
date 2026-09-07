# joplin-control

Lets Claude Code and Codex read, search and write the notes in your local [Joplin](https://joplinapp.org)
desktop app — through Joplin's own built-in MCP server for note work, and its Data API for the
things MCP does not expose (attachments, bulk, exact fields). Adds `/joplin-doctor`, a preflight
that finds the real port, checks the token without printing it, and reports which MCP tools are
*actually* enabled.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install joplin-control@padina
```

Then wire the clients up (see [Setup](#setup)):

```
~/.claude/plugins/.../joplin-control/scripts/joplin-mcp-install.sh
```

## The problem

Joplin keeps notes as rows in SQLite, not as Markdown files an agent can open. It ships two local
interfaces instead — an MCP server and a REST Data API — and getting an agent onto them has three
sharp edges:

1. **Three separate switches.** The Web Clipper service, `Enable MCP server`, and each individual
   tool all default to off, in three different settings panes. Miss the last one and the server
   connects fine and exposes nothing.
2. **The token has to live somewhere.** The endpoint is
   `http://127.0.0.1:PORT/mcp?token=<128-hex>`. Pasting that URL into a client config writes a
   full-access credential into `~/.claude.json` — mode **644** on a default install, readable by
   any local user — and breaks every time the token is renewed.
3. **Writes are silent and total.** Joplin never prompts before an agent write, and passing `body`
   replaces the entire note. An agent that guesses at a note's contents destroys them.

## Features

| Feature | Mechanism | File |
|---|---|---|
| When to use MCP vs the Data API, and how not to destroy a note | skill | `skills/joplin-control/SKILL.md` |
| Every Data API endpoint, parameter and pagination gotcha | skill reference | `skills/joplin-control/references/data-api.md` |
| The real MCP tool schemas, read from a live server | skill reference | `skills/joplin-control/references/mcp-tools.md` |
| Failure-by-failure diagnosis | skill reference | `skills/joplin-control/references/troubleshooting.md` |
| `/joplin-doctor` — app, port, token, API, MCP, tools, clients | slash command | `commands/joplin-doctor.md` → `scripts/joplin-doctor.sh` |
| Data API wrapper that keeps the token out of `argv` | script | `scripts/joplin-api.sh` |
| stdio↔HTTP MCP bridge, so no client config holds the token | script | `scripts/joplin-mcp-stdio.py` |
| One-shot wiring for Claude Code (all profiles) and Codex | script | `scripts/joplin-mcp-install.sh` |

### Why a bridge instead of the documented URL

Joplin's docs tell you to point a client at `http://127.0.0.1:PORT/mcp?token=YOUR_TOKEN` (via
`npx mcp-remote` for Claude Desktop). Both clients here speak streamable HTTP natively, so that
would work — and it is still the wrong thing to do, for two reasons:

- **The secret ends up in client config.** `~/.claude.json` is mode 644 on a default install.
  `mcp-remote` is no better: the token goes in `argv`, visible to `ps` for every local user.
- **It breaks on renewal.** Renewing the token in Joplin means editing every client config.

`scripts/joplin-mcp-stdio.py` is ~40 lines of stdlib Python that speaks MCP stdio to the client and
resolves the port and token from Joplin's own profile *on every call*. No client config contains
the token, a renewal needs no reconfiguration, and a non-default port is discovered rather than
hard-coded. It stays this small because Joplin's `/mcp` is a single-shot JSON-RPC POST — no SSE, no
sessions, no server-initiated messages.

### `/joplin-doctor`

Checks the chain in dependency order, each check degrading independently:

- Joplin desktop actually running — both interfaces die with the app
- which port the clipper service really landed on (Joplin walks 41184 → 41194)
- an `api.token` exists — reported as `<128 chars, sha256:1a2b3c4d>`, never the token itself
- the Data API accepts that token
- the MCP server answers `initialize`
- **which tools are genuinely enabled**, from a live `tools/list` — applied state, not documentation
- whether each client is wired up

It warns separately when write-capable tools are on, and again when `delete_note` is on, because
Joplin does not confirm agent writes.

It **only reports and advises** — it never enables a setting, renews a token, edits a client config
or touches a note.

Every script has a `--selftest` that runs its parsers against canned input offline, with no Joplin
and no network.

## Setup

Joplin, once — the plugin deliberately cannot do this for you, since these are your notes:

1. **Settings > Web Clipper** > *Enable Web Clipper Service*. (The browser extension is not needed.)
2. **Settings > AI** > tick *Enable MCP server*. Leave *Enable AI features* alone — that is Joplin's
   own chat panel and is unrelated.
3. **Settings > Tools** > tick the tools to allow, then **Apply**. Everything defaults to off, and
   nothing persists until Apply.

A read/write set that excludes destructive operations: searching, reading, listing notebooks,
listing tags, creating notes, updating notes, editing tags, creating notebooks — with *trashing
notes* left off.

Then, once:

```bash
scripts/joplin-mcp-install.sh --print   # see exactly what it will do
scripts/joplin-mcp-install.sh
```

It registers the bridge as an MCP server named `joplin` in every Claude Code profile it finds — the
default one plus `~/.claude-work2` and `~/.claude3` if they exist, since MCP config is per-profile
and a partial install makes them diverge silently — and in Codex, and symlinks the skill into
`~/.codex/skills/` so both clients share one copy. `--remove` undoes all of it.

Restrict it with `JOPLIN_CLAUDE_PROFILES`, e.g. `JOPLIN_CLAUDE_PROFILES=default` to touch only the
default profile and leave work profiles without access to your personal notes.

One trap worth knowing, since the script exists partly to avoid it: the default profile must be
addressed by leaving `CLAUDE_CONFIG_DIR` **unset**. Setting it to `~/.claude` does not select the
default profile — it redirects writes to `~/.claude/.claude.json`, a different file that the
default profile never reads, so the server lands somewhere Claude Code will not look.

**Restart any running Claude Code or Codex session** — MCP servers are connected at startup.

## Prerequisites

- **macOS** with [Joplin](https://joplinapp.org) desktop installed (`brew install --cask joplin`);
  verified against **3.7.16**. The MCP server is a 3.7-era feature.
- `python3` (system Python is fine) and `curl`.
- Claude Code and/or Codex CLI. Neither is required for the other.

## Scope and limits

- **Local only.** Everything talks to the desktop app on `127.0.0.1`. There is no remote Joplin API
  here, and nothing is exposed to the network.
- **Sync is Joplin's job.** Writes land in the local database immediately and reach other devices on
  Joplin's own sync cycle. Nothing here reads or writes a sync target directly — that is how you
  corrupt a revision history.
- **The plugin never enables a tool for you.** Which tools an agent gets is entirely your choice in
  Joplin's own settings, where everything starts off. `/joplin-doctor` reports the applied set and
  warns whenever write tools — and separately `delete_note` — are on, since Joplin does not confirm
  agent writes.
- Verified against Joplin 3.7.16. The MCP tool set is young; re-run `/joplin-doctor` after a Joplin
  upgrade, since it reads the live tool list rather than trusting this README.

## License

MIT
