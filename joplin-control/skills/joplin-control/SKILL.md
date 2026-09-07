---
name: joplin-control
description: Use when reading, searching, creating or updating notes in the user's local Joplin desktop app — including notebooks, tags, attachments, bulk edits and note migrations. Covers when to use Joplin's built-in MCP tools versus its Data API, how to avoid clobbering existing note content, and how to diagnose a Joplin connection that is not working.
---

# Joplin Control

## Overview

Joplin is a desktop note app. Notes live as rows in a SQLite database inside the user's profile
(`~/.config/joplin-desktop/database.sqlite`), **not** as Markdown files you can edit on disk. Reach
them through one of two local interfaces the app itself exposes:

| | Joplin MCP tools | Joplin Data API |
|---|---|---|
| Transport | MCP, wired into this client | HTTP on `127.0.0.1:41184` |
| Best for | Everyday note work, one note at a time | Bulk, attachments, exact field control |
| Attachments | ✗ no upload/download tool | ✓ full resource endpoints |
| Pagination | handled for you | you drive `limit`/`page`/`has_more` |
| Field control | fixed set of fields | any field via `fields=` |

**Never** write to `database.sqlite` directly, and never edit files in a configured sync target.
Both bypass Joplin's change tracking, and the next sync will either lose the edit or manufacture a
conflict.

## Choosing an interface

Use **MCP tools** by default. Reach for the **Data API** when you need something MCP does not do:

- uploading or downloading an attachment (`read_image` can *view* an image, but nothing uploads one)
- more than a handful of notes in one pass, where per-note tool calls would be slow
- reading or writing a field the tools do not expose — `created_time`, `is_todo`, `todo_completed`,
  `source_url`, `latitude`, `is_conflict`
- listing the trash, or anything needing `include_deleted=1` / `include_conflicts=1`
- deleting a note (deliberately not exposed as an MCP tool in this setup)

The Data API is reached through the bundled wrapper, which finds the port and supplies the token
without ever printing it:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/joplin-api.sh" GET /notes 'limit=10&fields=id,title,updated_time'
"${CLAUDE_PLUGIN_ROOT}/scripts/joplin-api.sh" GET /search 'query=recipe&fields=id,title'
"${CLAUDE_PLUGIN_ROOT}/scripts/joplin-api.sh" POST /notes '' '{"title":"T","body":"B","parent_id":"<folder-id>"}'
```

Full endpoint and parameter detail: `references/data-api.md`.
Per-tool MCP behaviour and its gaps: `references/mcp-tools.md`.

## Before the first call in a session

Joplin's interfaces only exist while the desktop app is open, so a failure is far more often "the
app is closed" than "the request was wrong". If anything errors, run the preflight rather than
guessing:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/joplin-doctor.sh"
```

It reports, in order: app running, the real clipper port, token present, token accepted, MCP
responding, which MCP tools are actually enabled, and whether each client is wired up. It only
reports — it never changes a setting. Diagnosis per failure line: `references/troubleshooting.md`.

## Working rules

### Note IDs

Every note, notebook, tag and resource is a **32-character lowercase hex** id. Titles are not
unique and not stable — a user renames notes freely. Always carry the id once you have it, and
never re-find a note by title between a read and a write.

### Search before you create

Duplicate notes are the most common damage an agent does here, because a "create" always succeeds.
Before creating anything, search for it:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/joplin-api.sh" GET /search 'query="Weekly review"&fields=id,title,parent_id'
```

Search matches note *content* as well as titles. If a plausible match comes back, ask the user
whether to update it instead of creating a second one. The same goes for notebooks and tags — check
`list_notebooks` / `GET /folders` before `create_notebook`.

### Never blind-write a body

Passing `body` **replaces the entire body**, on both interfaces. That is how notes get destroyed.

The MCP `update_note` tool gives you three partial operations that avoid the problem entirely, and
you should reach for them first:

- `append` — add to the end
- `prepend` — insert at the start
- `replace_text` — swap one exact match; **errors if the text is missing or appears more than
  once**, so it fails loudly rather than mangling the note

These are atomic against the note's current content, so they cannot clobber an edit the user made
between your read and your write. The Data API has no equivalent — `PUT /notes/:id` is always a
full replace.

When you genuinely must rewrite a whole body:

1. read the note's current `body`
2. build the new body from what you actually read
3. write it back in one call

Never construct a `body` from what you *think* the note contains. If a read did not return the
current body, do not write. Omit every field you are not deliberately changing — omitted fields are
left alone, and that is the mechanism that protects `created_time`, tags and to-do state.

### Verify after you write

A write returns the saved object. Check it rather than trusting the call:

- after a create, confirm the returned `id` and re-read the note
- after an update, re-read and confirm the change landed and nothing else moved
- report the note title *and* id back to the user

### Pagination

List and search endpoints cap at 100 items and page silently. A response has `items` and
`has_more`; when `has_more` is `true` you have **not** seen everything. Loop `page=1,2,3…` until
`has_more` is `false`. Treating the first page as the whole result set is the classic way to
produce a confidently wrong answer about "all" of someone's notes.

### Attachments

Attachments are `resource` records. A note references one with Markdown of the form
`![title](:/<32-char-resource-id>)`. Uploading is Data API only:

```bash
curl -F 'data=@/path/to/file.pdf' -F 'props={"title":"file.pdf"}' \
  "http://127.0.0.1:$PORT/resources?token=$TOKEN"
```

Then append the `![](:/<id>)` reference into the note body — following the read-before-update rule
above. Deleting a note does not delete its resources.

### Conflicts and errors

- A sync conflict produces a **copy** of the note in a "Conflicts" notebook with `is_conflict = 1`.
  Normal listings hide these. Never resolve one by guessing — show the user both versions.
- `403` / `401` means the token is wrong or was renewed. Re-run the doctor; the bridge picks up a
  renewed token automatically, but a stale `JOPLIN_TOKEN` in the environment will override it.
- Connection refused on every port in `41184-41194` means the app is closed or the Web Clipper
  service is off.
- A `404` on a note id that used to work usually means it was trashed, not that the id was wrong —
  re-query with `include_deleted=1`.

### Credentials

The authorisation token lives in `~/.config/joplin-desktop/settings.json` as `api.token`. It grants
full read/write to every note.

- Read it through the bundled scripts. Do not `cat` the settings file, do not echo the token, and
  do not paste it into a command line where it lands in shell history or `ps`.
- It must never appear in a committed file, a client config, a note body, or a bug report.
- If it is ever exposed, renew it: Joplin > Settings > Web Clipper > **Renew token**. No client
  reconfiguration is needed — the bridge re-reads it on the next call.

### Local vs synced storage

Everything here talks to the **local desktop app only**. There is no remote Joplin API in this
setup.

- A change made through MCP or the Data API lands in the local database immediately, and reaches
  other devices only on the next sync — Joplin's default interval is 5 minutes.
- If the user has not configured a sync target, nothing leaves this machine at all.
- A sync target (WebDAV on a NAS, Joplin Server, Dropbox…) is Joplin's business, not ours. Do not
  read or write sync-target files directly to "speed things up"; that is how you corrupt a
  revision history.
- On mobile, Joplin pauses syncing when the app is backgrounded, so "it hasn't shown up on my
  phone" is usually not a bug.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/joplin-doctor.sh` | Preflight every link in the chain. `--selftest` for offline parser tests. |
| `scripts/joplin-api.sh` | Data API wrapper; keeps the token out of argv. `--check`, `--port`, `--selftest`. |
| `scripts/joplin-mcp-stdio.py` | stdio↔HTTP MCP bridge, so no client config holds the token. |
| `scripts/joplin-mcp-install.sh` | Wire both clients up. `--print` to dry-run, `--remove` to undo. |
