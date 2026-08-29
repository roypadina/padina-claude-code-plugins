# cmux-control

Makes Claude Code and the [cmux](https://cmux.com) terminal aware of each other. Your tabs get named
after the work, finished turns announce themselves in the sidebar with a line about what actually
happened, and Claude gets a skill that knows the cmux CLI properly.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install cmux-control@padina
```

## The problem

cmux gives every workspace a tab, a sidebar entry, a notification centre, a status pill and a
progress bar. Claude Code, running inside that terminal, uses none of it. You end up with eleven tabs
called `zsh`, and the only way to know a twenty-minute agent run finished is to keep looking at it.

## Features

| Feature | Mechanism | File |
|---|---|---|
| Tab + sidebar named `repo · branch` | `SessionStart` hook | `hooks/hooks.json` → `scripts/cmux-hook.sh session-start` |
| Notification when a turn finishes | `Stop` hook | `hooks/hooks.json` → `scripts/cmux-hook.sh stop` |
| Notification when a subagent finishes | `SubagentStop` hook | `hooks/hooks.json` → `scripts/cmux-hook.sh subagent-stop` |
| Sidebar progress + status pill | **skill guidance** (see below) | `skills/cmux-control/SKILL.md` |
| `/cmux-sessions` — session inventory and recovery | slash command | `commands/cmux-sessions.md` → `scripts/cmux-sessions.py` |
| The whole cmux CLI, for Claude | skill | `skills/cmux-control/SKILL.md` + `references/` |

### Tab naming

The tab and the sidebar entry both become `repo · branch` — derived from git, deterministically, not
guessed:

| Situation | Name |
|---|---|
| `~/Code/myapp` on `feature/RD-12851` | `myapp · feature/RD-12851` |
| A subdirectory of that repo | `myapp · feature/RD-12851` |
| A linked worktree at `~/wt/topic` | `myapp · wt/topic` — the **main** repo's name, not the worktree directory's |
| Detached HEAD | `myapp · @a1b2c3d` |
| Not a git repo | the directory's own name |

Branch names keep their slashes. A worktree reports the main repository via `--git-common-dir`,
because a worktree directory is usually named after its branch and you would otherwise read the
branch twice.

It also sets `hookSpecificOutput.sessionTitle`, which is a real Claude Code SessionStart field
("Set the session title"). Whether cmux mirrors that anywhere in its own UI is **unverified** — the
tab and sidebar names come from the `cmux` calls, not from that field.

**It does not fight cmux's own naming.** cmux ships an opt-in `automation.workspaceAutoNaming`
setting; its settings copy says, verbatim: *"Manual renames always win and stop auto-naming for that
workspace or tab."* A `rename-tab` counts as a manual rename, so this plugin's name stands and cmux's
AI naming stays out of the way.

### Notifications

`Stop` and `SubagentStop` — the purpose-built events, not a `PostToolUse` matcher on `Task`. Their
payloads carry `last_assistant_message`, `stop_hook_active`, `background_tasks`, and for subagents
`agent_type` and `agent_id`, so the notification can say something:

```
Claude finished
myapp · feature/RD-12851 · 2 background tasks
Fixed the null-deref in the checkout handler. Added a regression test; both suites pass.

Subagent finished · Explore
myapp · feature/RD-12851
Found 3 call sites in src/api.ts
```

The body is the closing message, whitespace-collapsed and cut to 180 characters on a codepoint
boundary.

The `Stop` hook respects `stop_hook_active` (so it never fires again on a continuation) and **never**
emits `decision: "block"`. It notifies and exits 0. It cannot keep a session running.

Set `CMUX_CONTROL_QUIET=1` to keep the tab naming and drop the notifications.

> cmux's own Claude wrapper sets `CMUX_SUPPRESS_SUBAGENT_NOTIFICATIONS=1` for its own notifier. This
> plugin deliberately does not read that variable — its semantics are undocumented, and installing
> this plugin is itself the opt-in. `CMUX_CONTROL_QUIET` is the switch that belongs to you.

### Sidebar progress — honest disclaimer

**This one is not hook-enforced.** No hook knows how far through a task Claude is, so there is
nothing to wire it to. What the plugin ships is a set of rules in the skill: use `set-progress` /
`set-status` only for genuinely long multi-step work, at most one call per completed step, and always
clear both when the work ends — including when it fails.

Claude follows guidance well but not perfectly. If you want the pill gone, ask, or run
`cmux clear-progress && cmux clear-status cmux_control`.

The plugin writes to the status key **`cmux_control`** and never touches `claude_code` — cmux's own
Claude wrapper owns that key (live value: `claude_code=Running icon=bolt.fill color=#4C8DFF`) and
writing to it would stomp the app's own state.

### `/cmux-sessions`

cmux has no detached server: when the app quits, every terminal child process dies, Claude Code
included. On relaunch cmux replays each pane's saved resume binding and most sessions come back —
most, not all. A workspace can be dropped from the restore, or a pane can come back as a bare shell.

```
/cmux-sessions                  inventory every live Claude pane, with its resume command
/cmux-sessions check            MISSING workspaces, DEAD panes, transcript warnings
/cmux-sessions restore --dry-run
/cmux-sessions restore
```

It reads cmux's own state file. Multiple Claude Code profiles are discovered rather than assumed:
`CLAUDE_CONFIG_DIR` is honoured, `~/.claude*` directories are scanned, and profiles are deduped by
**resolved** transcript path — so if you symlink `projects/` between profiles (a common way to share
transcripts across accounts) nothing is counted twice. One profile is the normal case and needs no
setup.

### The skill

One skill covering the whole cmux CLI: topology and handles, launching agents in panes, browser
automation, notifications and sidebar state, `cmux.json` layouts, and session recovery — plus four
reference files loaded on demand.

Verified against **cmux 0.64.22**, with the traps that cost real time written down: `focus-surface`
and `list-surfaces` do not exist, `--surface` resolves inside the *caller's* workspace so
cross-workspace calls need `--workspace` (the failure is a misleading
`invalid_params: Surface is not a terminal`), `close-surface` reports the surface focused *after* the
close, `list-panes` prefixes the focused row with a literal `*`, and `identify` gives you both
`.caller` and `.focused` — which are frequently different.

It also carries cmux's own guardrail about `cmux todo`, verbatim: *"this checklist belongs to the
user. Do not add, edit, complete, remove, or replace items on your own initiative."*

## Prerequisites

- **macOS** and the [cmux](https://cmux.com) app, with its CLI on PATH
  (`/Applications/cmux.app/Contents/Resources/bin/cmux`).
- **`jq`** (`brew install jq`) for the hooks. Without it the notifications lose their body text and
  the tab is named from `$PWD` instead of the payload's `cwd` — everything still works, just less
  precisely.
- **Python 3** for `/cmux-sessions` only.

Everything is guarded. Outside cmux, or without the CLI, every hook exits 0 without a sound — no
errors, no output, nothing in your transcript.

## What is enforced vs what is guidance

| | |
|---|---|
| **Hook-enforced** — happens whether or not Claude cooperates | tab + sidebar naming, turn-finished notification, subagent-finished notification |
| **Skill guidance** — Claude's judgement, usually right, not guaranteed | sidebar progress and status pills, when to use which cmux command, restraint about the user's `todo` list |
| **On request** | `/cmux-sessions` and everything else in the skill |

## Layout

```
.claude-plugin/plugin.json
hooks/hooks.json                     three hooks, each guarded on `command -v cmux`
commands/cmux-sessions.md            the /cmux-sessions slash command
scripts/cmux-hook.sh                 one entrypoint for all three hook events
scripts/cmux-sessions.py             session inventory / check / restore
scripts/selfcheck.sh                 the runnable check for both of the above
skills/cmux-control/SKILL.md         the cmux CLI, for Claude
skills/cmux-control/references/      cli-reference · agents · browser · custom-commands
```

## Checking it works

```bash
scripts/selfcheck.sh
```

Asserts the `repo · branch` derivation against real throwaway repos — plain directory, slashed
branch, subdirectory, detached HEAD, linked worktree, bare repo — then runs the session script's own
assertions. No framework; it prints a line per check.

## Credits

The idea of wiring cmux to Claude Code hooks comes from
[`hopchouinard/cmux-plugin`](https://github.com/hopchouinard/cmux-plugin) (MIT, Patrick Chouinard).
This is an independent reimplementation — no code was copied — that fixes the two things that bothered
me about the original: it names tabs with the branch as well as the repo, and its notifications say
what finished instead of "Agent finished — check results".

## License

MIT © Roy Padina
