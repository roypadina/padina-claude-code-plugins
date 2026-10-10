# Padina Claude Code plugins

A [Claude Code](https://claude.com/claude-code) plugin marketplace. Eight plugins so far: one that
wires Claude into the cmux terminal, one that gives your sessions a memory of themselves, one that
recaps and closes out sessions so nothing falls through the cracks, one that runs the release
checklist for my Mac apps, one that repairs Hebrew/English layout typos, one that teaches Claude the
Espanso text-expander CLI, one that researches recipes with parallel subagents, one that hands you
values through your MaccyPlus clipboard history, labelled by session.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
```

Then install whichever you want:

```
/plugin install cmux-control@padina
/plugin install agentctl-sessions@padina
/plugin install session-management@padina
/plugin install finalize-app-release@padina
/plugin install heeng-keyboard-translator@padina
/plugin install espanso-control@padina
/plugin install recipe-research@padina
/plugin install maccyplus-clipboard@padina
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

### [`session-management`](session-management) — recap mid-session, close out at the end

A long session starts things everywhere — background agents, other panes, PRs, tickets, temp files.
Two commands keep track of it:

- `/session-recap` — mid-session: done / now / next, then what's open and *how* each item runs
  (background agent, other pane or workspace, another session, a cron), what's missing, not planned,
  waiting on, and what you need to do. Ends with a `/compact` verdict from the measured context size.
- `/finish-session` — before closing: every open, un-done, un-cleaned or owed item with a proposed
  action; acts only on what you pick. Then say `close`: it marks the session done in `agentctl` and
  closes the cmux pane — only its own, never someone else's.

**Requires** nothing. `jq`, `agentctl` and cmux are used when present.

→ [Plugin README](session-management/README.md) · [Wiki page](https://github.com/roypadina/padina-claude-code-plugins/wiki/session-management)

### [`finalize-app-release`](finalize-app-release) — no forgotten release step

Shipping one of my Mac apps is twenty small steps across four repos — version, CHANGELOG, README,
wiki, Ko-fi links, GitHub release and zip, Homebrew cask, the tap's README, pushing it all, upgrading
the copy you actually run. One skill runs the whole checklist at the end of a session (or when Claude
sees the work wrapping up). A script checks the mechanical part in about ten seconds — including that
the tap and wiki really reached the server, since a failed tap push still upgrades your own Mac — and
stamps a clean result, so the next run skips the review when nothing changed.

**Requires** macOS, `gh`, Homebrew and the tap checked out locally. Written for my own repos; fork it
to point it at yours.

→ [Plugin README](finalize-app-release/README.md) · [Wiki page](https://github.com/roypadina/padina-claude-code-plugins/wiki/finalize-app-release)

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

### [`maccyplus-clipboard`](maccyplus-clipboard) — values left in your clipboard history, labelled by session

Several sessions each "copy a query to your clipboard", and by the time you get to it you can't
tell which value came from where. Each `pbcopy` also overwrites what you were copying. With this
plugin Claude adds the value to [MaccyPlus](https://github.com/roypadina/maccyplus) history instead.
The value carries a label (the session name) and a note (`DataGrip → prod`, `run in pane: ~/repo`),
and your live clipboard is not touched. Claude can also read, pin, move, copy, relabel and delete
history items.

**Requires** MaccyPlus 2.8.0+ (`brew install --cask roypadina/tap/maccyplus`), running.

→ [Plugin README](maccyplus-clipboard/README.md) · [Wiki page](https://github.com/roypadina/padina-claude-code-plugins/wiki/maccyplus-clipboard)

---

## Repository layout

```
.claude-plugin/marketplace.json   the marketplace manifest
cmux-control/                     plugin: commands/, hooks/, scripts/, skills/
agentctl-sessions/                plugin: commands/, hooks/, skills/
session-management/               plugin: commands/
finalize-app-release/             plugin: skills/ (with a bundled state script)
heeng-keyboard-translator/        plugin: skills/ (with a bundled Python translator)
espanso-control/                  plugin: commands/, scripts/, skills/
recipe-research/                  plugin: commands/, skills/
maccyplus-clipboard/              plugin: skills/
```

Each plugin directory is self-contained and follows the standard Claude Code plugin layout —
`.claude-plugin/plugin.json` plus whichever of `commands/`, `hooks/`, `skills/` and `agents/` it
needs.

## Contributing

Issues and pull requests welcome. If you are adding a plugin, it needs its own directory, a
`.claude-plugin/plugin.json`, a README, and an entry in `.claude-plugin/marketplace.json`.

## License

MIT © Roy Padina
