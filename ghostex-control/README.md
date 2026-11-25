# ghostex-control

Teaches Claude Code to drive [Ghostex](https://ghostex.dev), the macOS workspace that runs every
coding agent in its own persistent terminal session, through its `ghostex` / `gx` CLI — safely.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install ghostex-control@padina
```

## The problem

Ghostex ships a large CLI (well over a hundred verbs) and a set of agent skills of its own. Those
skills are help-first by design ("read `ghostex --help`, then act"), and all but the coordinator
playbook are marked `disable-model-invocation`, so Claude never loads them on its own. Left to the
help text alone, Claude reaches for the obvious verbs and hits the traps:

- `ghostex terminal` looks like "open a terminal" but creates a record that is **not started** —
  every `send-text` / `read-text` against it fails — and for an unknown folder it **adds a sidebar
  project** as a side effect.
- `send-message` run from an agent session **appends a multi-line sender block** to the text, which
  a plain shell then tries to execute; and a first argument that matches no session is silently
  taken as an **agent id**.
- Titles match by case-insensitive substring and numeric aliases come from whichever session last
  printed `gx sessions`, so `gx kill 4` or `gx kill build` can close somebody else's session.
- `kill`, `sleep` and `wake` accept `all`.

## Features

| Feature | Mechanism | File |
|---|---|---|
| Find yourself: environment, `agents whoami`, global refs | skill | `skills/ghostex-control/SKILL.md` |
| Start a shell that runs a command (bare `create-session --start`, prompt wait, `send-text`) | skill recipe | same |
| Start an agent session (`agents create`), message it, read and wait on it, close it | skill recipe, routes to `ghostex agents guide` | same |
| Type into, read, wait on, rename, sleep, close, restore sessions | skill | same |
| Notifications, hooks and the status line Ghostex installs | skill | same |
| Answer keyboard-shortcut questions from the live hotkey list (your rebinds included) | skill (`ghostex settings hotkeys list`) | same |
| Every CLI command with a risk class (read / state / UI / destructive / network) | reference, loaded on demand | `skills/ghostex-control/references/cli-reference.md` |
| Routing to the guides Ghostex prints (`ghostex <area> guide`) | skill | `SKILL.md` § 7 |

No hooks, no scripts, no commands: the plugin is knowledge only.

### Safety rules the skill enforces

Read before acting; change only sessions Claude created (by global ref) or the one the user names
exactly; never `all`; never focus, open, attach or switch projects unless asked; never type into a
session a person or another agent is using; leave Ghostex's hooks, status line wrapper and settings
files alone; never restart the app or gxserver to fix a delivery problem.

### Ghostex 12: agents launch agents with `agents create`

Since Ghostex 12.0.0, `create-session --input '<cmd>'` run from an agent session is refused ("Only
your own devices can supply a raw launch plan or startup command."). The skill launches agents with
Ghostex's own `ghostex agents create` (configured launcher, account, approvals and hooks, folder
pre-trusted) and uses a bare `create-session --start` plus a prompt wait and `send-text` only for plain
shell work, never to type an agent launcher around the refusal.

### Works with Ghostex's own guides

Ghostex 12 no longer bundles skills; it prints guides that always match the installed version
(`ghostex agent-guide`, `ghostex agents guide`, `ghostex coordinator guide`, `ghostex help guide`,
`ghostex visual guide`, `ghostex board guide`, `ghostex secret guide`). This plugin does not copy
them. Its skill is the one Claude loads automatically; it carries the traps and the safety rules, and
tells Claude which guide to read when a task goes deeper (multi-agent runs, coordinators, settings,
browsers, secrets).

## Verified vs unverified

Checked against Ghostex 12.0.0 (2026-11-25; first written against 10.40.0): the CLI help, the built-in
guides, read-only commands and an `agents create` → `agents close` round trip on a live install, and the gxserver source on GitHub. Behaviour that would need a mutating live run is marked
**[unverified]** in the skill:

- whether `agents create` leaves the user's focus where it was (`create-session --start` does);
- how multi-line `send-text` lands in a shell.

## Prerequisites

- **macOS** and the [Ghostex](https://ghostex.dev) app (`brew install --cask ghostex`), which puts
  `ghostex` and `gx` on PATH.
- **`jq`** for the recipes that pick fields out of the CLI's JSON.

## Layout

```
.claude-plugin/plugin.json
skills/ghostex-control/SKILL.md                  the skill
skills/ghostex-control/references/cli-reference.md   every command, grouped, with a risk class
```

## License

MIT © Roy Padina
