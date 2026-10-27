---
name: vault-add
description: Decide where new content goes in an Obsidian vault managed by obsidian-vault-manager, name it per the vault's rules, create it, and keep the Vault Structure note and index current. Use before creating any note or folder in a managed vault ("where should this note go", "add a folder for X to the vault", "create a note about Y in my vault", "new section in the vault"), or /vault-add. Not for vaults without `_Vault/Vault Structure.md` — run vault-review (init) first.
---

# Add content to a managed vault

`VP="${CLAUDE_PLUGIN_ROOT}/scripts/vault.py"`. Structure note: `_Vault/Vault Structure.md`.

1. **Read the rules** (sections only): `sed -n '/^## Taxonomy/,/^## Rules/p' "V/_Vault/Vault Structure.md"` and `sed -n '/^## Rules/,/^## Writers/p' …`. If the note is missing → stop, run `vault-review` step 1 (init).
2. **Place it.** Area from the Taxonomy table, then the most specific existing folder in the Folder map. Check for an existing note on the same subject before creating one: `grep -il "<subject>" "V/_Vault/Index/<Folder>.md"` — extend it instead of adding a sibling.
3. **New folder only when the rule allows** (≥3 notes on one subject no folder covers, or a machine writer needing its own tree). Never for one note; never a second folder with the same meaning.
4. **Name per the vault's Naming rule** (Structure note § Naming). Still the init placeholder → derive the convention from sibling names, write it into the rule, then follow it. Language of the area.
5. **Create** the note/folder. Frontmatter: follow what sibling notes use (`head -n 8` on one of them) — at least `tags` and `updated` when siblings have them.
6. **Keep the structure current.** New folder → add its line to the Folder map (`` - `Path/` — what it holds ``) and a Taxonomy row if top-level. Then `python3 "$VP" index --vault V`; a folder gets a subject: `python3 "$VP" subject set --vault V "Path/" "…"`.
7. **Machine-written?** If a skill, script, workflow or app will keep writing here, register it now: `vault-writers`.

Say where it went and why in one line. Do not restructure anything else while adding.
