# obsidian-vault-manager

A Claude Code plugin that keeps any Obsidian vault's structure under control — for humans and for the agents that write into it.

What it maintains in the vault:

- `_Vault/Vault Structure.md` — taxonomy (which top-level folder holds which area: personal, technical, work, infra, setup…), a folder map, rules for new content and naming, a **Writers registry** (every skill / script / plugin / app / cron that reads or writes a fixed vault path, with its source location), and the **last-review marker** (git sha + date; snapshot fallback for non-git vaults).
- `Index.md` + `_Vault/Index/<Folder>.md` — regenerable index of every folder and note with tags and a one-line subject (auto-derived; agent overrides live in `_Vault/subjects.json`). Machine-written bulk folders collapse to one line.
- `_Vault/vault-manager.json` — per-vault config: where references to the vault live outside it (`consumers.roots`, `report_only`), collapsed folders, alternative vault names.

## Skills

| Skill | Purpose |
|---|---|
| `vault-review` | Full workflow: init if unmanaged → what changed since the last review → evaluate taxonomy → propose moves with cost → apply approved moves safely → regenerate index → mark review. |
| `vault-add` | Where a new note/folder goes, how to name it, then keep structure note + index current. |
| `vault-writers` | Register / audit writers of the vault; row format and the "same change" rule. |
| `vault-update-refs` | After moves or renames (by agent or human): fix outside references, in-vault links, registry, index. |

## Script

`scripts/vault.py` (python3, stdlib only; needs `grep`; `git` optional — a non-git vault uses a snapshot diff). `python3 scripts/vault.py --help`.

```
init · tree · changes · index · subject set|missing · refs scan [--bare OLD] · refs rewrite OLD NEW [--bare --only ids] · move · check · mark · selfcheck
```

Safety: never touches `.git`, `.obsidian`, dot-folders; inside the vault writes `_Vault/`, `Index.md` and — on moves — the notes' links and path text; outside the vault writes only on `refs rewrite --apply`, on the configured roots (full-path references unsupervised, bare mentions only by confirmed hit id). Moves use `git mv` when the path is tracked, handle case-only renames, remove emptied folders, remap config and subjects. Never commits.

Test: `python3 scripts/vault.py selfcheck`.

## Install

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install obsidian-vault-manager@padina
```

Development: `claude --plugin-dir /path/to/obsidian-vault-manager`.

## Vault config example

```json
{
  "index": {"collapse": ["Archive/Exports"], "depth": 2, "split_kb": 20},
  "consumers": {
    "roots": ["~/.claude/CLAUDE.md", "~/.claude/skills", "~/.claude/projects/*/memory", "~/.claude/settings.json", "~/projects/*/CLAUDE.md", "~/bin"],
    "report_only": ["~/.claude/plugins/cache"],
    "needles": ["Obsidian/MyVault"]
  }
}
```

`needles` defaults to `<parent>/<vault name>` (plus `~/<name>` when the vault sits in HOME); set it when the vault is referenced under another name (`Obsidian MyVault/…`). It is a literal list: a copy of the vault carrying the same config scans for the original's name. `report_only` roots (installed plugin caches, shared repos that need a PR) are scanned by every `refs` mode and listed, never written. Bare mode also matches `<vault name>/Path` forms.
