# Padina Claude Code plugins

A [Claude Code](https://claude.com/claude-code) plugin marketplace. Five plugins so far: one that
wires Claude into the cmux terminal, one that gives your sessions a memory of themselves, one that
repairs Hebrew/English layout typos, one that teaches Claude the Espanso text-expander CLI, one that
researches recipes with parallel subagents.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
```

Then install whichever you want:

```
/plugin install cmux-control@padina
/plugin install agentctl-sessions@padina
/plugin install heeng-keyboard-translator@padina
/plugin install espanso-control@padina
/plugin install recipe-research@padina
```

📖 **[Full documentation is in the Wiki](https://github.com/roypadina/padina-claude-code-plugins/wiki)**

---

## Plugins

### [`cmux-control`](cmux-control) — Claude Code, wired into cmux

You run Claude inside [cmux](https://cmux.com), and cmux has a notification centre and a progress bar
that Claude never touches. So there is no way to know a twenty-minute agent run finished except to
keep looking at it.

This plugin closes that gap. `Stop` and `SubagentStop` hooks push a notification that says what
actually finished, subtitled with the repo and branch it finished in — the real branch, slashes and
all, the main repo's name from inside a worktree, the sha on a detached HEAD:

```
Subagent finished · Explore
myapp · feature/RD-12851
Found 3 call sites in src/api.ts
```

Plus `/cmux-sessions` — an inventory of every Claude pane across cmux with its resume command, and a
`check`/`restore` pair for the workspaces that don't come back after a restart — and a skill that
teaches Claude the cmux CLI properly, verified against 0.64.22, traps and all.

**Requires** macOS, the cmux app with its CLI on PATH, and `jq` for the hooks. Every hook is guarded:
outside cmux they exit silently.

→ [Plugin README](cmux-control/README.md) · [Wiki page](https://github.com/roypadina/padina-claude-code-plugins/wiki/cmux-control)

### [`agentctl-sessions`](agentctl-sessions) — sessions that remember what they were

Claude Code names a session after your first prompt and records nothing else about it. Two hundred
sessions later you cannot find the one you want. This plugin fixes that: a real name, labels, notes,
flags, a done state, reminders and due dates — stored by the
[`agentctl`](https://github.com/roypadina/agentctl) CLI and shown in its session picker.

Claude does most of it unprompted — names the session once your task is clear, labels it with the
issue key from your git branch — and handles plain requests:

> "mark this done" · "remind me in 2h" · "this is for RD-12345" · "what do I need to get back to?"

Nine slash commands, a `SessionStart` hook that hands a resumed session its own metadata back, and
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

### [`espanso-control`](espanso-control) — the Espanso CLI, for Claude

[Espanso](https://espanso.org) is a text expander configured entirely through YAML, driven by a CLI
whose subcommands have shifted across 2.x releases. A binary being installed says nothing about
whether the daemon is running, registered to survive a reboot, or has the macOS Accessibility
permission it silently requires — expansions just don't fire, with no error anywhere.

This plugin teaches Claude the CLI properly (verified against 2.4.0) and adds `/espanso-doctor` — six
checks that each degrade independently: PATH, installed version vs. latest stable, daemon actually
running, service registration, config path, and Accessibility permission (reported as
**unverifiable**, not guessed — querying `TCC.db` from an unprivileged shell returns zero rows
whether or not the grant is real, so a script that claimed otherwise would be wrong exactly when it
mattered). It only reports and advises — never restarts, registers, or edits anything.

**Requires** macOS and [Espanso](https://espanso.org) (`brew install --cask espanso`) with
Accessibility permission granted by hand.

→ [Plugin README](espanso-control/README.md) · [Wiki page](https://github.com/roypadina/padina-claude-code-plugins/wiki/espanso-control)

### [`recipe-research`](recipe-research) — a restaurant-level recipe, not one blogger's opinion

"Find me a recipe" gets you one source. This plugin fans three subagents out in parallel — classic
recipes (sourced, exact quantities), food science (why the good version works), pro-chef technique
(named chefs, restaurant practice, UNVERIFIED claims flagged rather than asserted) — then makes the
actual editorial call on where they disagree, instead of averaging opinions.

The output is a linked note tree under `<cuisine>/<dish>/`: a synthesized recipe, three summaries,
three raw research files. **Obsidian is optional** — off by default (plain relative Markdown links,
readable anywhere), or turn on `vaultMode` for `[[wiki-links]]` and frontmatter tags. Output folder
and language are configurable too (`/plugin configure recipe-research`).

→ [Plugin README](recipe-research/README.md) · [Wiki page](https://github.com/roypadina/padina-claude-code-plugins/wiki/recipe-research)

---

## Repository layout

```
.claude-plugin/marketplace.json   the marketplace manifest
cmux-control/                     plugin: commands/, hooks/, scripts/, skills/
agentctl-sessions/                plugin: commands/, hooks/, skills/
heeng-keyboard-translator/        plugin: skills/ (with a bundled Python translator)
espanso-control/                  plugin: commands/, scripts/, skills/
recipe-research/                  plugin: commands/, skills/
```

Each plugin directory is self-contained and follows the standard Claude Code plugin layout —
`.claude-plugin/plugin.json` plus whichever of `commands/`, `hooks/`, `skills/` and `agents/` it
needs.

## Contributing

Issues and pull requests welcome. If you are adding a plugin, it needs its own directory, a
`.claude-plugin/plugin.json`, a README, and an entry in `.claude-plugin/marketplace.json`.

## License

MIT © Roy Padina
