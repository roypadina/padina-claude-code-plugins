# Joplin troubleshooting

Run `scripts/joplin-doctor.sh` first. It walks the chain in dependency order and each line below
maps to one of its checks. Fix the first failing line before looking at anything after it.

## `fail  Joplin desktop is not running`

The Data API and the MCP server are served by the desktop app's own process. Nothing works while
it is closed, and neither interface starts it. Open Joplin.

Note this also means an agent's writes are impossible while the user has quit the app — that is a
normal state, not a broken install.

## `fail  no Web Clipper service on ports 41184-41194`

The app is open but the HTTP server is off. Joplin > **Settings > Web Clipper** > *Enable Web
Clipper Service*. The page then shows `Status: Started on port <port>`.

The browser extension is **not** needed — the service and the extension are separate things, and
this integration only uses the service.

If it is enabled but nothing answers, another app may hold the port; Joplin walks 41184 → 41194, so
check the port shown on that settings page rather than assuming 41184.

## `fail  no api.token in .../settings.json`

The token is created when the clipper service is first enabled. If the key is absent, the service
has never been on. Enable it, then re-run the doctor.

## `fail  Data API rejected the token`

The token was renewed, or a stale one is being forced. In order:

1. Check for an override: `echo "${JOPLIN_TOKEN:+JOPLIN_TOKEN is set}"`. If set, it wins over the
   real token — unset it.
2. Otherwise renew it: Joplin > Settings > Web Clipper > **Renew token**.

No client reconfiguration is needed after a renewal — the stdio bridge and `joplin-api.sh` both
read the token at call time.

## `fail  MCP endpoint /mcp gave no response`

The clipper service is up but MCP is off. Joplin > **Settings > AI** > tick *Enable MCP server*,
then **Apply**.

Applying matters: ticking the box changes the running app immediately, but the setting is only
written to `settings.json` on Apply. Skip it and MCP silently reverts on the next restart.

You do **not** need "Enable AI features" — that switch is for Joplin's own in-app chat panel and an
external LLM provider. MCP is independent of it.

## `warn  MCP exposes no tools`

Joplin > **Settings > Tools**, tick the tools to allow, then Apply. Everything defaults to off.

A reasonable read/write set that excludes destructive operations:

- ✓ searching notes, reading notes, listing notebooks, listing tags
- ✓ creating notes, updating notes, editing tags on notes, creating notebooks
- ✗ trashing notes — an agent can then trash without confirmation
- ✗ semantic search — needs the embeddings index built in Settings > AI
- ✗ reading images — read-only and harmless, enable if you want image description

`tools/list` reflects the applied state, so the doctor's tool line is the ground truth about what
an agent can do.

## `warn  <client> has no 'joplin' MCP server`

Run `scripts/joplin-mcp-install.sh`. Use `--print` first to see exactly what it will run.

## The server is configured but the client does not see it

MCP servers are connected when a session **starts**. An already-running Claude Code or Codex
session will not pick up a newly added server. Quit and reopen it.

Verify from outside the session:

```bash
claude mcp get joplin
codex mcp get joplin
```

## Writes succeed but nothing changes on another device

That is sync, not this integration. Writes land in the local database immediately and travel on
Joplin's own sync cycle (default every 5 minutes). On mobile, Joplin pauses syncing while the app
is backgrounded, so bring it to the foreground before concluding anything is wrong.

Never "fix" this by editing files in the sync target directly.

## A note came back with `is_conflict: 1`

Two devices edited the same note between syncs. Joplin keeps both: the loser becomes a copy in a
`Conflicts` notebook. These are hidden from normal listings — pass `include_conflicts=1` to see
them. Show the user both versions and let them choose; never merge silently.
