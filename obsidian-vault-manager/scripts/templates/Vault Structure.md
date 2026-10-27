---
type: vault-structure
tags: [vault-structure]
last_review_sha:
last_review_date:
---

# Vault Structure — {{VAULT_NAME}}

The map and the rules of this vault. Agents and humans: read this before adding, moving or renaming anything. Maintained with the `obsidian-vault-manager` plugin (skills `vault-review`, `vault-add`, `vault-writers`, `vault-update-refs`); the mechanical parts are checked by `vault.py check`.

Root index for fast search: [[Index]] (regenerate with `vault.py index`). Config: `_Vault/vault-manager.json` (consumer search roots, collapsed folders).

## Taxonomy

Top-level areas, one row each. Every note belongs to exactly one area.

| Folder | Area | What belongs here | What does not | Owner |
|---|---|---|---|---|
| `Example/` | personal · technical · work · infra · setup | … | … | human / machine (writer name) |

## Folder map

One line per folder (to depth {{DEPTH}}; deeper only where it matters): what it holds, structure-wise, not its content. Fixed format, parsed by `vault.py check`: `` - `Path/` — what it holds ``.

{{FOLDER_MAP}}

## Rules

### Where new content goes
1. Pick the area in Taxonomy, then the most specific folder in the Folder map. An existing folder always wins over a new one.
2. One subject = one note. Extend an existing note before creating a sibling.
3. Machine-owned folders (Owner = machine) are never edited by hand — change the writer instead.
4. Added a note or folder → `vault.py index` (and a Folder map line for a new folder).

### Naming
- Folders: Title Case with spaces, no abbreviations, no typos — fix them when found.
- Notes: (describe: this vault's convention, derived from the existing names — e.g. `<Subject> — <qualifier>.md`, series codes `XY-01 <Part>.md`, ordered `1. `, hubs `00 <Name>.md`; list the folders that keep another scheme and why).
- Language: the language of the area's existing notes.

### When a new folder is justified
- Three or more notes on one subject that no existing folder covers, or a machine writer that needs its own tree.
- Never for a single note; never a second folder with the same meaning as an existing one.
- Creating one: `vault-add` → Folder map line (+ Taxonomy row if top-level) → `vault.py index`.

### Moves and renames
Only through `vault-review` or `vault-update-refs`: `vault.py move OLD NEW` (history-preserving, fixes in-vault links), then `vault.py refs rewrite OLD NEW --apply` for everything outside the vault, then the Writers registry rows, then `vault.py index`. A move without that follow-up leaves broken links and stale writers.

## Writers registry

Every workflow, script, skill, plugin, app, cron or hook that writes to or reads a fixed path in this vault. When a path moves, every row touching it is updated in the same change. A new writer registers itself (`vault-writers`) in the same change that creates it.

| Writer | Kind | Source | Vault paths | Access | Notes |
|---|---|---|---|---|---|

Kind: skill · command · plugin · script · app · cron · hook · workflow. Source: the code's path (`~/…`), never an installed cache copy. Vault paths: comma-separated, each in backticks, folders end with `/` (`vault.py move` / `refs rewrite` update backticked paths in this note; prose is not touched). Access: read · write · read/write.

## Consumers (reference search roots)

Where references to vault paths live outside the vault: `_Vault/vault-manager.json` → `consumers.roots` (rewritten by `vault.py refs rewrite --apply`), `consumers.report_only` (installed copies and shared repos: reported only — fix at the source or by PR, then reinstall) and `consumers.needles` (how the vault is named outside, when not `<parent>/<name>`). Keep the list current when a new place starts referencing the vault.

## Review log

Last review: frontmatter `last_review_sha` / `last_review_date` (written by `vault.py mark`); `vault.py changes` diffs from there. One line per review, newest first.

- {{DATE}} — initialised by `vault.py init`.
