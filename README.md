# Padina Claude Code plugins

A [Claude Code](https://claude.com/claude-code) plugin marketplace. Two plugins so far: one that
gives your sessions a memory of themselves, one that repairs Hebrew/English layout typos.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
```

Then install whichever you want:

```
/plugin install agentctl-sessions@padina
/plugin install heeng-keyboard-translator@padina
```

📖 **[Full documentation is in the Wiki](https://github.com/roypadina/padina-claude-code-plugins/wiki)**

---

## Plugins

### [`agentctl-sessions`](agentctl-sessions) — sessions that remember what they were

Claude Code names a session after your first prompt and records nothing else about it. Two hundred
sessions later you cannot find the one you want. This plugin fixes that: a real name, labels, notes,
flags, a done state, reminders and due dates — stored by the
[`agentctl`](https://github.com/roypadina/agentctl) CLI and shown in its session picker.

Claude does most of it unprompted — names the session once your task is clear, labels it with the
issue key from your git branch — and handles plain requests:

> "mark this done" · "remind me in 2h" · "this is for RD-12345" · "what do I need to get back to?"

Seven slash commands, a `SessionStart` hook that hands a resumed session its own metadata back, and
a skill that teaches Claude the whole toolset.

**Requires** the `agentctl` CLI, 0.5.0+ (`brew install --cask roypadina/tap/agentctl`). The plugin
offers to install it if it is missing.

→ [Plugin README](agentctl-sessions/README.md) · [Wiki page](https://github.com/roypadina/padina-claude-code-plugins/wiki/agentctl-sessions)

### [`heeng-keyboard-translator`](heeng-keyboard-translator) — fix wrong-layout typing

You meant to type Hebrew, the layout was still English, and you got `akuo` instead of `שלום`. This
plugin spots it and offers the repair — **per word**, so the common case where only part of a
sentence is garbled works too:

| You typed | It reconstructs |
|---|---|
| `akuo` | `שלום` |
| `שלום, akuo חבר` | `שלום, שלום חבר` |
| `hello world` | unchanged — it stays quiet |

No dependencies beyond Python 3. It always asks before substituting, and never fires inside code
blocks, paths, URLs or identifiers.

→ [Plugin README](heeng-keyboard-translator/README.md) · [Wiki page](https://github.com/roypadina/padina-claude-code-plugins/wiki/heeng-keyboard-translator)

---

## Repository layout

```
.claude-plugin/marketplace.json   the marketplace manifest
agentctl-sessions/                plugin: commands/, hooks/, skills/
heeng-keyboard-translator/        plugin: skills/ (with a bundled Python translator)
```

Each plugin directory is self-contained and follows the standard Claude Code plugin layout —
`.claude-plugin/plugin.json` plus whichever of `commands/`, `hooks/`, `skills/` and `agents/` it
needs.

## Contributing

Issues and pull requests welcome. If you are adding a plugin, it needs its own directory, a
`.claude-plugin/plugin.json`, a README, and an entry in `.claude-plugin/marketplace.json`.

## License

MIT © Roy Padina
