# Joplin MCP tools reference

Captured from a live `tools/list` against **Joplin 3.7.16** on 2026-09-07 — this is what the app
actually returns, not what the docs describe. Official page:
<https://joplinapp.org/help/apps/ai_mcp/>

Server identifies as `joplin-mcp` `1.0.0`, protocol `2025-06-18`.

## Enabling

Three separate switches, all required:

1. **Settings > Web Clipper** > Enable Web Clipper Service — the MCP endpoint is served by the
   clipper's HTTP server, so MCP cannot work without it.
2. **Settings > AI** > "Enable MCP server".
3. **Settings > Tools** > tick each tool individually.

Every tool defaults to **off** (verified in the app bundle: `ai.tool.*.enabled` all default
`false`, except `ai.tool.edit_current.enabled`, which is the in-app chat panel and does not apply
to MCP). Settings only persist when you click **Apply** — toggling a checkbox changes the running
app immediately but is lost on restart if you close the dialog without applying.

`tools/list` returns only the enabled tools, so it is an accurate readout of what an agent can
actually do. `scripts/joplin-doctor.sh` prints exactly that list.

## The tools

`*` marks a required argument.

| Tool | Arguments | What it does |
|---|---|---|
| `search_notes` | `query*`, `limit` | Keyword search over titles and bodies. Returns id, title, notebook id, `updated_time` and a **snippet anchored on the match** — often enough to answer without a `read_note`. |
| `semantic_search_notes` | `query*`, `notebook_id`, `tag_id`, `relevance` | Meaning-based search over the local embeddings index. Returns ranked *chunks*, not whole notes. Errors unless embeddings are enabled in Settings > AI. |
| `read_note` | `id*`, `offset`, `max_chars` | One note: title, Markdown body, notebook name, tags, timestamps. Page long bodies with `offset`/`max_chars`. |
| `list_notebooks` | — | Flat list of id, title, `parent_id`. Rebuild the tree yourself. |
| `list_tags` | — | Tags that have at least one note attached. |
| `create_note` | `title*`, `body`, `notebook_id`, `is_todo` | Returns the new note id. Without `notebook_id` it lands in the default notebook. |
| `update_note` | `id*`, `title`, `body`, `append`, `prepend`, `replace_text`, `notebook_id`, `todo_completed` | Only the fields you pass change. See below — the partial ops matter. |
| `delete_note` | `id*` | Moves to trash, recoverable. Off by default in this setup. |
| `manage_tags` | `note_id*`, `add`, `remove` | Tags by **title**. Unknown titles in `add` are created. |
| `create_notebook` | `title*`, `parent_id` | Nest with `parent_id`. |
| `read_image` | `id*`, `resolution` | Returns image bytes for an image attachment so it can be described. View only — there is no upload tool. |

## `update_note` — prefer the partial operations

This is the single most important detail. `update_note` accepts, in order of preference:

- **`append`** — add text to the end of the body
- **`prepend`** — insert text at the start of the body
- **`replace_text`** — swap one exact match of `find` for `replace`; **errors if the text is
  missing or occurs more than once**, which makes it fail loudly instead of corrupting the note
- `body` — replace the entire body

Use `append`/`prepend`/`replace_text` whenever they fit. They are atomic against the note's current
content, so they cannot clobber an edit the user made between your read and your write. Reserve
full `body` for a genuine rewrite, and only ever build that body from a body you just read.

Note that the Data API's `PUT /notes/:id` has **no** equivalent — there, `body` is always a full
replace. The partial operations exist only on the MCP tool.

## What MCP cannot do

Fall back to the Data API (`references/data-api.md`) for any of these:

- upload or download an attachment — `read_image` only views images
- fields the tools do not expose: `created_time`, `source_url`, `todo_due`, `is_conflict`,
  geolocation
- listing the trash or conflict copies
- permanent deletion
- bulk work — anything past a handful of notes is faster in one paginated API call

## Behaviour to be aware of

- **No per-action confirmation.** Joplin does not prompt when an agent writes. A `create_note` or
  `update_note` lands immediately. Treat every write as committed the moment it is called.
- **Localhost only.** The server binds `127.0.0.1`; nothing is exposed to the network.
- **Content leaves the machine via the client, not Joplin.** Anything the tools return is sent to
  whichever model the calling client uses.
- The endpoint is a single-shot JSON-RPC POST — no SSE stream, no sessions, no server-initiated
  messages. That is why a ~40-line stdio bridge is enough to front it.
