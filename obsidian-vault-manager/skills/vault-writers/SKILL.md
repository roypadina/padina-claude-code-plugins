---
name: vault-writers
description: Register, update, remove or audit the "writers" of an Obsidian vault — every skill, command, plugin, script, app, cron, hook or workflow that writes to or reads a fixed vault path — in the Writers registry of `_Vault/Vault Structure.md` (obsidian-vault-manager). Use whenever something is created or changed that touches a vault path ("this skill writes to the vault", "register the writer", "which scripts write to my vault", "audit vault writers", "the vault path in X changed"), after a restructure, or /vault-writers.
---

# Writers registry

`VP="${CLAUDE_PLUGIN_ROOT}/scripts/vault.py"`. The registry lives in `## Writers registry` of `_Vault/Vault Structure.md`. Purpose: when a path moves, every program touching it is known and updated in the same change.

## Row format

```
| Writer | Kind | Source | Vault paths | Access | Notes |
| journal-sync | script | ~/bin/journal-sync.py | `Journal/Daily/`, `Journal/Index.md` | write | runs nightly |
```

- **Kind**: skill · command · plugin · script · app · cron · hook · workflow.
- **Source**: the code's path, never an installed cache copy. If the path is configured elsewhere (plugin `pluginConfigs` in settings files, an env var, a constant in a script), add that file too: `~/Code/x/skills/y/SKILL.md; path in ~/.claude/settings.json pluginConfigs`.
- **Vault paths**: comma-separated, each in backticks, folders end with `/`. `vault.py move` / `refs rewrite` rewrite backticked paths in this note automatically; prose is not touched.
- **Access**: read · write · read/write.

## Register (same change as the writer)

1. Fill the row; one row per writer, not per path.
2. If the Source directory is not under any `consumers.roots` in `_Vault/vault-manager.json`, add it — otherwise the next restructure cannot find it.
3. `python3 "$VP" check --vault V` → `writers registry: … 0 problems`. A `writers vs sources` line lists vault paths the row's Source never mentions: drift (the code still holds the old path → fix it) or a path passed as an argument / composed at runtime (say so in Notes).
4. A writer that stops existing → delete its row in the same change.

## Discover existing writers

`python3 "$VP" refs scan --vault V` lists every outside file that mentions a vault path (`[ok]` current, `[STALE]` the path is gone, `[partial]` the prefix exists but the rest does not — a template or a moved subfolder). `python3 "$VP" refs scan --vault V --bare "Folder" --anywhere` finds files that use a bare vault-relative path without naming the vault (scripts, comments). Read each hit's context (`sed -n 'N,Mp' file`) to decide Kind and Access; rows for things that only *mention* the vault in prose are not needed — register what runs. Prefer full `~/<vault>/<path>` forms in anything you write: full paths are rewritten unsupervised, bare ones need a per-hit check.

## When a path moves

Update the rows that list it (the script already rewrote the backticked paths — verify), then fix the Source code via `vault-update-refs`. The row's Notes field says what to re-test.
