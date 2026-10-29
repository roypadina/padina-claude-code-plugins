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
| Start a shell that runs a command, with no `.zshrc` race | skill recipe (`create-session --input … --start`) | same |
| Start an agent session, message it, read and wait on it | skill recipe, routes to Ghostex's `ghostex-agents` skill | same |
| Type into, read, wait on, rename, sleep, close, restore sessions | skill | same |
| Notifications, hooks and the status line Ghostex installs | skill | same |
| Every CLI command with a risk class (read / state / UI / destructive / network) | reference, loaded on demand | `skills/ghostex-control/references/cli-reference.md` |
| Routing to the skills Ghostex bundles in the app | skill | `SKILL.md` § 7 |

No hooks, no scripts, no commands: the plugin is knowledge only.

### Safety rules the skill enforces

Read before acting; change only sessions Claude created (by global ref) or the one the user names
exactly; never `all`; never focus, open, attach or switch projects unless asked; never type into a
session a person or another agent is using; leave Ghostex's hooks, status line wrapper and settings
files alone; never restart the app or gxserver to fix a delivery problem.

### Why `create-session --input` and not "wait for the prompt, then type"

The skill's main recipe hands the command to Ghostex instead of typing it. In zsh, Ghostex `eval`s
that text once from the login shell's first `precmd` — after `.zshrc`, instant prompts and
framework update questions are done — so nothing can swallow the first characters, aliases work,
and `claude "$(< prompt.md)"` passes a long prompt with no quoting trouble. Typing into a fresh
shell is still documented, with a prompt wait, for when it is the only option.

### Works with Ghostex's own skills

Ghostex bundles skills in `/Applications/Ghostex.app/Contents/Resources/CLI/skills/`
(`ghostex-cli`, `ghostex-agents`, `ghostex-orchestrator`, `ghostex-help`, browser and computer use,
the board, visuals, and more). This plugin does not copy them. Its skill is the one Claude loads
automatically; it carries the traps and the safety rules, and tells Claude which bundled skill file
to read when a task goes deeper (multi-agent runs, coordinators, settings, browsers).

## Verified vs unverified

Checked against Ghostex 10.40.0: the CLI help, the bundled skills, read-only commands on a live
install, and the gxserver source on GitHub. Behaviour that would need a mutating live run is marked
**[unverified]** in the skill:

- whether `create-session --start` and `agents create` leave the user's focus where it was;
- the exact `create-session` result fields beyond the session's project and id;
- how multi-line `send-text` lands in a shell;
- whether a Claude Code session started in Ghostex can reach its parent with Claude Code's own
  cross-session messaging (inside Ghostex, `ghostex agents send` is the verified channel).

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
