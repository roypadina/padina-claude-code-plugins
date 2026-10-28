# Padina Claude Code plugins

[![Website](https://img.shields.io/badge/website-apps.roypadina-2F62E6)](https://apps.roypadina.synology.me/)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-support-F16061?logo=ko-fi&logoColor=white)](https://ko-fi.com/roypadina)

A [Claude Code](https://claude.com/claude-code) plugin marketplace. Small plugins for a terminal-heavy Claude Code workflow: cmux integration, session memory, recaps and close-out, the release checklist for my Mac apps, Hebrew/English layout repair, Espanso control, recipe research with parallel subagents, a MaccyPlus clipboard bridge, and native macOS UI/UX design rules.

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
/plugin install mac-design@padina
```

📖 **[Full documentation is in the Wiki](https://github.com/roypadina/padina-claude-code-plugins/wiki)**

## At a glance

| Plugin | What it does | Needs | Works with |
|---|---|---|---|
| [`cmux-control`](cmux-control) | Notifications, progress and a session inventory for Claude inside cmux | macOS, cmux CLI, `jq`, Python 3 | cmux |
| [`agentctl-sessions`](agentctl-sessions) | Name, label, flag, remind and close out sessions | `agentctl` 0.5.0+ | agentctl |
| [`session-management`](session-management) | `/session-recap`, `/resume-all`, `/finish-session` | nothing (`jq` for the pane close) | cmux, agentctl (optional) |
| [`finalize-app-release`](finalize-app-release) | Release checklist for Roy's own Mac apps, not a general tool | macOS, `gh`, Homebrew, the tap checked out | the roypadina tap |
| [`heeng-keyboard-translator`](heeng-keyboard-translator) | Repairs Hebrew/English wrong-layout typing, per word | Python 3 | any OS |
| [`espanso-control`](espanso-control) | Teaches Claude the Espanso CLI, plus `/espanso-doctor` | macOS, Espanso | Espanso |
| [`recipe-research`](recipe-research) | Restaurant-level recipes from three parallel subagents | nothing (Obsidian optional) | any OS |
| [`maccyplus-clipboard`](maccyplus-clipboard) | Leaves labelled values in MaccyPlus history | macOS, MaccyPlus 2.8.0+ | MaccyPlus |
| [`agents-session-hopper`](agents-session-hopper) | Claude steers AgentsSessionHopper: account, usage, switch, hold, resume after a move | macOS, AgentsSessionHopper 0.1.8+ | AgentsSessionHopper |
| [`obsidian-vault-manager`](obsidian-vault-manager) | Structure note, index, safe restructuring and reference updates for any Obsidian vault | Python 3 (git optional) | Obsidian |
| [`mac-design`](mac-design) | Design, build and review native macOS UI (SwiftUI + AppKit) to Apple quality, with a ranked-fix audit mode | nothing (`curl`, `jq`, `rg` for live checks and audits) | macOS 14–27 apps |

Minimum Claude Code version: not pinned. The plugins use only commands, skills, hooks and agents, so any
release with plugin marketplaces works.

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

### [`agents-session-hopper`](agents-session-hopper) — your Claude accounts, one conversation

[AgentsSessionHopper](https://github.com/roypadina/AgentsSessionHopper) keeps your own Claude accounts
side by side and continues the same conversation on another one near a usage limit. This skill tells
Claude how: which account the session is on, usage left, `switch` / `hold`, ending its turn so a move
lands cleanly, and picking the work back up when a moved session resumes.

> "which account am I on?" · "switch to work" · "stay on this account"

**Requires** AgentsSessionHopper 0.1.8+ (`brew install --cask roypadina/tap/agents-session-hopper`).
Install the plugin in every profile; the app's setup can do it for you.

→ [Plugin README](agents-session-hopper/README.md) · [Wiki page](https://github.com/roypadina/padina-claude-code-plugins/wiki/agents-session-hopper)

### [`session-management`](session-management) — recap mid-session, close out at the end

A long session starts things everywhere — background agents, other panes, PRs, tickets, temp files.
Two commands keep track of it:

- `/session-recap` — mid-session: done / now / next, then what's open and *how* each item runs
  (background agent, other pane or workspace, another session, a cron), what's missing, not planned,
  waiting on, and what you need to do.
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

### [`obsidian-vault-manager`](obsidian-vault-manager) — keep a vault's structure under control

Vaults drift: folders sorted two ways at once, typos in folder names, notes nobody can place, and
scripts or skills that write to a fixed path and break silently when a folder moves. This plugin
gives a vault a `_Vault/Vault Structure.md` note (taxonomy, folder map, rules for new content, a
**writers registry** of everything that reads or writes a fixed path, and a last-review marker), a
regenerable root `Index.md`, and a review workflow that proposes moves with their real cost, applies
them history-preserving, and rewrites every outside reference and in-vault link they break.

Four skills: `vault-review` (init + full review), `vault-add` (where new content goes),
`vault-writers` (register a writer), `vault-update-refs` (after any move, by an agent or a human).
Works on git and non-git vaults; one stdlib Python script does the mechanical parts.

→ [Plugin README](obsidian-vault-manager/README.md)

### [`mac-design`](mac-design) — Mac apps that feel like Apple built them

Claude knows SwiftUI, but left alone it writes iOS-flavoured Mac apps: 44 pt buttons, a gear in the
toolbar, glass on every card, a menu bar with half the commands missing. This skill gives it the Mac
rulebook — 243 checkable rules with IDs, severities, version gates and sources, from Liquid Glass and
toolbars to menu-bar apps, permission flows, accessibility and Icon Composer icons — plus topic
references with type-checked SwiftUI/AppKit code. Three modes: **Design** (a plan before any view
code), **Build** (rules and version gates while coding) and **Review** (an audit of your code or
screenshots that returns one ranked fix list). A bundled script prints Apple's current HIG page, so
rules can be checked against the source. Built on [BAMA](https://github.com/daveebbelaar/bama)'s design
skills (MIT).

→ [Plugin README](mac-design/README.md)

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
agents-session-hopper/            plugin: skills/
obsidian-vault-manager/           plugin: scripts/, skills/
mac-design/                       plugin: skills/ (with references and a HIG fetch script)
```

Each plugin directory is self-contained and follows the standard Claude Code plugin layout —
`.claude-plugin/plugin.json` plus whichever of `commands/`, `hooks/`, `skills/` and `agents/` it
needs.

## Contributing

Issues and pull requests welcome. If you are adding a plugin, it needs its own directory, a
`.claude-plugin/plugin.json`, a README, and an entry in `.claude-plugin/marketplace.json`. CI checks
the manifests (valid JSON, required fields, every plugin listed).

## More Mac apps by Roy

Free, open-source Mac menu-bar apps and terminal tools, all on one site: **[apps.roypadina.synology.me](https://apps.roypadina.synology.me/)**.

- [agentctl](https://apps.roypadina.synology.me/apps/agentctl/) — Find and resume any Claude Code or Codex session from one terminal menu.
- [Agents Monitor](https://apps.roypadina.synology.me/apps/agents-monitor/) — See your Claude Code and Codex usage limits before you hit them.
- [claude-jam](https://apps.roypadina.synology.me/apps/claude-jam/) — Share one real Claude Code session with other humans.
- [MaccyPlus](https://apps.roypadina.synology.me/apps/maccyplus/) — Maccy, plus automation: rules, hotkeys, plugins and a CLI for AI agents.

## Support

Free and open source, built in my spare time. If a plugin saves you time, a coffee keeps the next one coming.

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/roypadina)

## License

MIT © Roy Padina
