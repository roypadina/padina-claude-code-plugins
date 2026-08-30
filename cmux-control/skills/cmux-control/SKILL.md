---
name: cmux-control
description: This skill should be used when the user asks to "open a cmux pane", "split cmux", "new cmux workspace", "run claude in cmux", "run an agent in cmux", "control cmux", "send to cmux pane", "cmux notify", "show progress in the sidebar", "cmux browser", "open url in cmux", "claude-teams", "omc / omx / omo", "list my cmux sessions", "restore my cmux workspaces", "a pane came back empty after a cmux restart", "use cmux for X", or mentions the cmux.com app, manaflow-ai/cmux, or wants programmatic control of the cmux macOS terminal (workspaces, panes, surfaces, browser, notifications, agent launching, session recovery).
---

# cmux Control

Control the cmux macOS terminal (cmux.com, `manaflow-ai/cmux`) via its CLI / Unix-socket API: open
panes, split surfaces, launch coding agents inside panes, drive the embedded browser, push
notifications and progress into the sidebar, inspect topology, and recover Claude Code sessions that
did not survive a restart.

Verified against **cmux 0.64.22**. `cmux <command> --help` is always the authority — check it before
you trust anything below.

## Self-Update Rule (READ FIRST)

**This skill is a living document. Keep it accurate.**

After every cmux task — especially failures, surprises, or workarounds — update the skill before
reporting back to the user:

1. **A command failed in a way the skill didn't predict** → add it to "Pitfalls" with the wrong way,
   the right way, and the misleading error message **verbatim**.
2. **The CLI surface changed** (new flag, removed command, renamed action) → patch
   `references/cli-reference.md`.
3. **A pattern worked unexpectedly well** → one terse line in the relevant section.
4. **An assumption turned out wrong** → fix it in place; never append a contradictory note.

Edit `SKILL.md` and `references/*.md` directly. Do not create new files for transient learnings, and
do not accumulate `examples/` or one-off scripts — the skill is knowledge, not a recipe book.

Quote the verbatim error string when documenting a failure mode — future agents grep for it.

## Prerequisites

- macOS, cmux installed at `/Applications/cmux.app`.
- CLI on PATH: `/Applications/cmux.app/Contents/Resources/bin/cmux`.
- The cmux app must be running for socket commands. `cmux <path>` launches it.

```bash
cmux ping
cmux identify --json
```

## Topology Model

Nesting: **Window → Workspace → Pane → Surface (terminal | browser | simulator | agent-session)**.

| Term | Meaning |
|---|---|
| Window | Native macOS window |
| Workspace | Sidebar entry, holds panes |
| Pane | Split region inside a workspace |
| Surface | Tab inside a pane. Also addressable as `tab:<n>` by the tab commands |

**Handles**: refs (`window:1`, `workspace:2`, `pane:3`, `surface:4`, `tab:5`), UUIDs, or a numeric
index. Output defaults to refs; `--id-format uuids|both` adds UUIDs. `--json` where supported.

Inside any cmux terminal, `CMUX_WORKSPACE_ID`, `CMUX_SURFACE_ID` and `CMUX_TAB_ID` are exported and
used as the defaults for `--workspace` / `--surface` / `--tab`.

## Decision Tree

| Goal | Command |
|---|---|
| Know where this shell is | `cmux identify --json` |
| See the full tree | `cmux tree --all` |
| New empty workspace | `cmux workspace create --name X --cwd /path` |
| New workspace running a command | `cmux workspace create --cwd /path --command "claude"` |
| Split the current pane | `cmux new-split right` (or `left`/`up`/`down`) |
| New terminal tab in the current pane | `cmux new-surface --type terminal` |
| New browser surface | `cmux new-pane --type browser --url https://…` or `cmux browser open URL` |
| Send text to a surface | `cmux send --surface surface:N "claude\n"` |
| Read what is on screen | `cmux read-screen --surface surface:N --lines 200` |
| Stream live events | `cmux events --no-heartbeat` |
| Notify the user | `cmux notify --title "Done" --body "lint + test passed"` |
| Show progress in the sidebar | `cmux set-progress 0.42 --label "tests"` |
| Flash a pane to grab attention | `cmux trigger-flash --surface surface:N` |
| Show a diff in a browser split | `cmux diff --branch` |
| Reopen the previous app session | `cmux restore-session` |
| Find sessions that did not come back | `/cmux-sessions check` |

`workspace create|list|close|rename|select` is the canonical form. The flat legacy verbs
(`new-workspace`, `list-workspaces`, `close-workspace`, `rename-workspace`, `select-workspace`) keep
working indefinitely and print a one-time deprecation hint to **stderr**; `CMUX_QUIET=1` silences it.
The `OK <ref>` payload still goes to stdout, so `awk '{print $2}'` parsing is unaffected.

## What this plugin adds

### Tab and workspace naming — NOT this plugin's job

This plugin does **not** rename tabs or workspaces. It did before 0.2.0, from a `SessionStart` hook;
that was removed because a `rename-tab` / `workspace-action rename` counts as a *manual* rename and
permanently stops cmux's own naming for that workspace. Verbatim from cmux's settings copy for the
opt-in `automation.workspaceAutoNaming` setting:

> "When enabled, cmux summarizes supported agent sessions into short workspace and tab names using
> each agent's own binary, refreshed as the topic shifts. **Manual renames always win and stop
> auto-naming for that workspace or tab.** Uses your agent account for the short summarization calls."

So names belong to the user. **Do not rename a tab or workspace on your own initiative** — same rule
as `cmux todo`. When the user asks for it:

```bash
cmux rename-tab "release prep"                                    # horizontal tab
cmux workspace-action --action rename --title "release prep"      # sidebar entry
```

### Completion notifications (automatic, hook-enforced)

`Stop` and `SubagentStop` hooks push a notification naming what finished and summarising the closing
message. Nothing to invoke. `CMUX_CONTROL_QUIET=1` in the environment suppresses them.

Note: cmux's own Claude wrapper sets `CMUX_SUPPRESS_SUBAGENT_NOTIFICATIONS=1` for its own notifier.
This plugin does not read that variable — its semantics are undocumented, and installing this plugin
is itself the opt-in. Use `CMUX_CONTROL_QUIET` to turn the plugin's notifications off.

### Sidebar progress (your judgement, not a hook)

**No hook can measure how far through a task you are — this part is up to you.** During a long,
multi-step job the user asked for, keep the sidebar honest:

```bash
cmux set-progress 0.4 --label "3/7 services migrated"
cmux set-status cmux_control "migrating" --icon hammer --color "#ff9500" --priority 50
# …when the work ends, always:
cmux clear-progress
cmux clear-status cmux_control
```

**Restraint rules — a progress bar that updates every few seconds is worse than none:**

1. Only for work with **five or more steps** that will run for **more than a couple of minutes**.
   Never for a single command, a quick edit, or a question.
2. **At most one call per completed step**, and never more than about one a minute.
3. Always `clear-progress` **and** `clear-status cmux_control` when the work ends — including when
   it fails or the user interrupts. A stale pill is a bug.
4. **Use the key `cmux_control` and nothing else.** cmux's own Claude wrapper owns the key
   `claude_code` (observed live: `claude_code=Running icon=bolt.fill color=#4C8DFF`). Never write to
   it and never clear it — you would be stomping the app's own state.
5. Progress and status are per-workspace. Pass `--workspace "$CMUX_WORKSPACE_ID"` explicitly from a
   script, or you may land on whichever workspace happens to be focused.

### Session inventory — `/cmux-sessions`

cmux has no detached server: when the app quits, every terminal child process dies, Claude Code
included. On relaunch, cmux's wrapper replays each pane's stored `resumeBinding` and runs
`claude --resume <session-id> --permission-mode <captured-mode>`, so most sessions come back on their
own. Conversation state is restored from the on-disk transcript; any in-flight turn at quit time is
lost. (The captured `--permission-mode` overrides `settings.json` `defaultMode` on a resumed session.)

Most, not all. A workspace can be dropped from the restore, or a pane can come back as a bare shell.
`/cmux-sessions` wraps cmux's own state file to fix that:

```bash
SESSIONS="${CLAUDE_PLUGIN_ROOT}/scripts/cmux-sessions.py"

python3 "$SESSIONS" list                # inventory of every live Claude pane + resume command
python3 "$SESSIONS" list --json
python3 "$SESSIONS" check               # MISSING workspaces, DEAD panes, transcript warnings
python3 "$SESSIONS" restore --dry-run   # print the cmux commands without running them
python3 "$SESSIONS" restore --match "QA env"
```

**Always dry-run `restore` first and show the user the commands** — it creates workspaces and types
into existing panes.

Source of truth, if you would rather read it by hand:

```
~/Library/Application Support/cmux/session-com.cmuxterm.app.json           # current
~/Library/Application Support/cmux/session-com.cmuxterm.app-previous.json  # the launch before
```

**After a bad restart, reach for `-previous.json`** — the current file is rewritten to match whatever
actually came up, so a workspace that failed to restore may exist only in the previous one.

A resume command is `[CLAUDE_CONFIG_DIR=<dir>] claude --resume <id> --permission-mode <mode>`. The
env prefix is the part people forget: a session launched under a non-default `CLAUDE_CONFIG_DIR` is a
**different account**, and resuming it under the default profile fails with
`No conversation found with session ID`.

## Core Workflow — Open a Pane and Run an Agent

Always **identify first**, then act on a returned ref. Never assume.

```bash
CTX=$(cmux identify --json)
WS=$(echo "$CTX" | jq -r .caller.workspace_ref)

NEW=$(cmux --json new-split right --workspace "$WS" | jq -r '.surface_ref // .surface')

cmux send --workspace "$WS" --surface "$NEW" "claude"
cmux send-key --workspace "$WS" --surface "$NEW" enter
```

`identify` returns both `.caller` (this shell) and `.focused` (whatever the user is looking at) —
**they are frequently different**. When scripting, you almost always want `.caller`.

Faster equivalent, with the command pre-baked:

```bash
cmux workspace create --name "claude bug-fix" --cwd ~/Code/foo --command "claude"
```

For multi-agent orchestration, prefer cmux's native teammate mode: `cmux claude-teams`,
`cmux codex-teams`, `cmux omc`, `cmux omx`, `cmux omo`. See `references/agents.md`.

## Browser Automation

```bash
SURF=$(cmux --json browser open https://example.com | jq -r '.surface_ref // .surface')
cmux browser "$SURF" wait --load-state complete --timeout-ms 15000
cmux browser "$SURF" snapshot --interactive          # numbered refs (e1, e2, …)
cmux browser "$SURF" fill e1 "hello"
cmux browser "$SURF" click e2 --snapshot-after
cmux browser "$SURF" screenshot --out /tmp/page.png
```

Stable loop: **navigate → `get url` → `wait` → `snapshot --interactive` → act on a ref →
re-snapshot**. Refs are per-snapshot and go stale after any DOM change.

When `snapshot --interactive` returns `js_error`, fall back to `get text body` / `get html body`.

See `references/browser.md`.

## The workspace checklist — `cmux todo`

`cmux todo <add|list|check|uncheck|start|edit|rm|clear|set|open>` drives the per-workspace checklist
shown in the sidebar.

> **cmux's own guardrail, quoted from `cmux todo --help`:** "this checklist belongs to the user. Do
> not add, edit, complete, remove, or replace items on your own initiative — only manage it when the
> user explicitly asks you to. Use your own internal task tracking for your plans."

Follow that. `cmux todo list` to read is always fine; every mutating subcommand needs the user to have
asked for it.

## Sending Input — Pitfalls

- `cmux send` types text but does **not** press Enter. Append `\n` (or `\r`) inside the string, or
  follow with `cmux send-key … enter`.
- `send-key` accepts `enter`, `tab`, `escape`, `backspace`, `delete`, `up`, `down`, `left`, `right`,
  plus printable keys.
- Without `--surface`, `send` targets `CMUX_SURFACE_ID` — **the caller's own pane**, which is almost
  never what you want when scripting.

### CRITICAL: cross-workspace surface targeting

`--surface <ref>` resolves **inside `$CMUX_WORKSPACE_ID`** (the caller's workspace) by default. When
scripting a freshly-created workspace you **must** pass `--workspace <NEW_WS>` to every `send`,
`send-key`, `read-screen` and `close-surface`, or the lookup fails with the misleading error
`invalid_params: Surface is not a terminal`.

```bash
# WRONG — looks surface:15 up in the caller's workspace:
cmux send --surface surface:15 "claude"
# RIGHT:
cmux send --workspace workspace:7 --surface surface:15 "claude"
```

### `focus-surface` does not exist

`cmux focus-surface` → `Error: Unknown command 'focus-surface'. Run 'cmux --help' for the full
command list.` Focus the surface's **pane** instead: `cmux focus-pane --pane <pane-ref> --workspace
<WS>`. Usually unnecessary — `new-split --surface <S>` already takes the source surface.

`cmux list-surfaces` does not exist either. The command that lists surfaces is **`list-panels`**
("List surfaces (panels) in a workspace"); `list-panes` lists split regions, and
`list-pane-surfaces` lists the surfaces of one pane.

### Output formats — JSON vs `OK <ref>`

Not every command honours `--json`. Mutating topology commands return a plain `OK <ref>` line; read
commands return JSON.

| Command | Output |
|---|---|
| `new-workspace`/`workspace create`, `close-workspace`, `close-surface`, `focus-pane`, `select-workspace`, `notify`, `send`, `send-key`, `rename-tab` | `OK <ref> [workspace:N]` — plain text |
| `new-split`, `new-pane`, `new-surface`, `list-pane-surfaces`, `list-workspaces`, `list-panes`, `list-panels`, `identify`, `capabilities`, `tree` (with `--json`) | JSON |

```bash
WS=$(cmux workspace create --name "x" --cwd /tmp | awk '/^OK /{print $2}')
S2=$(cmux --json new-split right --workspace "$WS" --surface "$S1" | jq -r .surface_ref)
```

`close-surface` gotcha: its `OK <ref>` names the surface that **received focus after the close**, not
the one that was closed (observed: `close-surface --surface surface:30` → `OK surface:31`). Verify
with `list-panels` if in doubt.

`list-panes` / `list-pane-surfaces` prefix the focused row with a literal `* ` marker
(`* pane:24 …`). Naive `awk '{print $1}'` grabs the `*` and you get
`Error: Invalid surface handle: *`. Parse with `grep -oE 'pane:[0-9]+'` instead.

## Safety Rules

1. **Identify first.** `cmux identify --json` before acting, so you know which pane is the caller.
2. **Stay scoped.** Operate inside the caller's workspace unless asked to span workspaces. Pass
   `--focus false` / `--no-focus` when creating background work so you do not steal focus.
3. **Don't kill what you didn't create.** Never `close-surface` / `close-workspace` a pane the user
   opened — other agent sessions may be live inside it.
4. **Clean up.** Ask before closing helper panes you spawned; the user may still want the output.
5. **Reads first.** `read-screen --surface surface:N --lines 200` before assuming agent state.
6. **Refs are runtime.** `surface:7` is reassigned on every relaunch. UUIDs are stable — use
   `--id-format uuids` when persisting anything.
7. **The user's checklist is the user's.** See `cmux todo` above.

## Pane Sizing & GUI Keybindings

No incremental grow/shrink keyboard shortcut ships. Built-in sizing binds:

| Action | Keys |
|---|---|
| Toggle pane zoom | `⌘⇧↩` |
| Equalize split sizes | `⌃⌘=` |
| Focus pane left/right/up/down | `⌥⌘←/→/↑/↓` |
| Split right / down | `⌘D` / `⌘⇧D` |

Precise resize is a mouse-drag on the split edge, or
`cmux resize-pane --pane <ref> (-L|-R|-U|-D) [--amount <n>]`.

**Terminal lines run to the far right edge.** There is no terminal content-width / soft-wrap setting
in cmux — `markdown.maxWidth` and `fileEditor.wordWrap` apply only to the markdown viewer and file
editor. A terminal fills its pane's columns. Levers: (1) **narrow the pane**, the real fix — but
`resize-pane` is a **no-op on a lone pane**, so `new-split right` first to give it a neighbour;
(2) `app.globalFontMagnification` in `cmux.json` (default 100, range 50–200) — scales *all*
cmux-owned terminals and chrome, not one pane, and trades font size for columns by definition. Prefer
the split.

Authoritative keybind source: `cmux docs shortcuts` prints the URLs. Note `cmux shortcuts` (without
`docs`) returns a bare `OK`, not the list.

## Inspect / Debug

```bash
cmux tree --all                          # full topology
cmux workspace list
cmux list-panes  --workspace workspace:2
cmux list-panels --workspace workspace:2
cmux list-pane-surfaces --pane pane:3
cmux surface-health
cmux capabilities --json | jq .methods   # full socket method list
cmux events --no-heartbeat --limit 20    # NDJSON event stream
cmux rpc <method> '{"key":"val"}'        # raw v2 RPC
```

## Additional Resources

### Reference files (load on demand)

- **`references/cli-reference.md`** — every subcommand, flags, handle model, global flags, env vars.
- **`references/agents.md`** — launching agents in panes, `claude-teams`, `omc`/`omx`/`omo`, grids.
- **`references/browser.md`** — the full browser surface, waits, snapshots, profiles, cookies.
- **`references/custom-commands.md`** — `cmux.json` schema, action types, layout examples.

### Live discovery

The help output is authoritative when the CLI evolves:

```bash
cmux --help
cmux <command> --help
cmux docs api | browser | agents | settings | shortcuts | dock | sidebars
```
