# Joplin Data API reference

Verified against **Joplin 3.7.16** (desktop, macOS) on 2026-09-07. Official docs:
<https://joplinapp.org/help/api/references/rest_api/>

## Connection

- Base URL `http://127.0.0.1:<port>`. Default port **41184**; if it is taken Joplin walks up to
  **41194**, so discover the port rather than hard-coding it.
- `GET /ping` returns the literal string `JoplinClipperServer`. This is the only endpoint that does
  not need a token, which makes it the right probe for "is this port Joplin".
- Every other request needs `?token=<api.token>`. The token is a 128-char lowercase hex string in
  `~/.config/joplin-desktop/settings.json`.
- The service only listens on localhost, and only while the desktop app is running.

Use `scripts/joplin-api.sh` rather than raw curl — it discovers the port, injects the token via
`curl --config -` so the secret never enters argv, and returns the raw JSON.

## Objects and endpoints

All ids are 32-character lowercase hex.

### Notes

| Method | Path | Notes |
|---|---|---|
| `GET` | `/notes` | paginated list |
| `GET` | `/notes/:id` | single note |
| `GET` | `/notes/:id/tags` | tags on the note |
| `GET` | `/notes/:id/resources` | attachments on the note |
| `POST` | `/notes` | create |
| `PUT` | `/notes/:id` | update — **replaces** the fields you send |
| `DELETE` | `/notes/:id` | to trash; `?permanent=1` to destroy |

Create takes `title`, `body` (Markdown) or `body_html`, and `parent_id` (the notebook). Omitting
`parent_id` drops the note in the default notebook.

```json
{ "title": "Weekly review", "body": "## Done\n- ...", "parent_id": "0123456789abcdef0123456789abcdef" }
```

Fields worth knowing beyond the obvious: `is_todo`, `todo_completed`, `todo_due`, `source_url`,
`created_time`, `user_updated_time`, `is_conflict`, `markup_language` (1 = Markdown, 2 = HTML).

`created_time` and `updated_time` are Unix milliseconds, not seconds.

### Folders (notebooks)

`GET /folders`, `GET /folders/:id`, `GET /folders/:id/notes`, `POST /folders`, `PUT /folders/:id`,
`DELETE /folders/:id`. Nest by setting `parent_id` to another folder id. `GET /folders?as_tree=1`
returns the hierarchy in one call.

### Tags

`GET /tags`, `GET /tags/:id`, `GET /tags/:id/notes`, `POST /tags`, `PUT /tags/:id`,
`DELETE /tags/:id`. Attach with `POST /tags/:id/notes` and a body of `{"id": "<note-id>"}`; detach
with `DELETE /tags/:id/notes/:note_id`. Tag titles are lowercased by Joplin.

### Resources (attachments)

`GET /resources`, `GET /resources/:id`, `GET /resources/:id/file` (the bytes),
`GET /resources/:id/notes`, `PUT /resources/:id`.

Upload is `POST /resources` as `multipart/form-data` with two parts — `data` (the file) and `props`
(a JSON string of metadata):

```bash
curl -F 'data=@report.pdf' -F 'props={"title":"report.pdf"}' \
  "http://127.0.0.1:41184/resources?token=$TOKEN"
```

Reference it from a note body as `[report.pdf](:/<resource-id>)`, or `![alt](:/<id>)` for an image.
Deleting a note leaves its resources behind.

### Search

`GET /search?query=<q>` searches note titles **and** bodies using Joplin's search syntax
(`tag:work`, `notebook:Recipes`, `title:foo`, `-excluded`, `"exact phrase"`, `*` wildcard).

`type=` switches the searched entity: `note` (default), `folder`, `tag`.

## Query parameters

| Param | Meaning |
|---|---|
| `fields=id,title,body` | return only these — always set it, bodies are large |
| `limit=100` | page size, **100 is the maximum** |
| `page=1` | 1-indexed |
| `order_by=updated_time` | sort field |
| `order_dir=ASC` \| `DESC` | sort direction |
| `include_deleted=1` | include trashed items |
| `include_conflicts=1` | include conflict copies |
| `permanent=1` | on `DELETE`, skip the trash |

## Pagination

```json
{ "items": [ … ], "has_more": true }
```

`has_more: true` means there is at least one more page. Loop until it is `false`:

```bash
page=1
while :; do
  out=$(scripts/joplin-api.sh GET /notes "limit=100&page=$page&fields=id,title")
  echo "$out" | python3 -c 'import json,sys; [print(i["id"], i["title"]) for i in json.load(sys.stdin)["items"]]'
  [ "$(echo "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["has_more"])')" = True ] || break
  page=$((page+1))
done
```

## Errors

| Status | Meaning |
|---|---|
| `403` | bad or renewed token |
| `404` | no such id — or the item is in the trash; retry with `include_deleted=1` |
| `500` | usually a malformed body, e.g. a `parent_id` that does not exist |
| connection refused | app closed, or Web Clipper service off |

## Gotchas

- `PUT` replaces the fields it receives. There is no append. Read, rebuild, write.
- A `PUT` with no `parent_id` does not move the note; a `PUT` *with* a wrong `parent_id` silently
  moves it to another notebook.
- `GET /notes` excludes conflicts and trash by default — "all notes" is not all rows.
- Times are milliseconds. Passing seconds dates a note to 1970.
