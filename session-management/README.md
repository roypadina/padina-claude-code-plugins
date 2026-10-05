# session-management

Three slash commands for the life of a Claude Code session: a mid-session recap, an end-of-session
close-out, and a final close.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install session-management@padina
```

## The problem

A long session starts things everywhere — background agents, other panes, PRs, tickets, temp
files, promises to reply to someone. Halfway through you lose track of what is still running and
what is waiting on you; at the end you close the window and something falls through the cracks.

## Commands

| Command | When | What it does |
|---|---|---|
| `/session-recap [focus]` | Mid-session | Done / now / next in a few lines, then open items and *how* each runs (background agent, other pane, workspace, session, cron), what's missing, not planned, waiting on, and what you need to do. Ends with a `/compact` verdict from the measured context size, plus a ready-to-paste `/compact` line when it's time. Read-only. |
| `/finish-session [notes]` | Before closing | Recap, then every open, un-done, un-cleaned or owed item with a proposed action. Acts only on the items you pick. |
| `/close-session [force \| -f]` | Last | Checks every `/finish-session` item is done or skipped, marks the session done in `agentctl`, closes the cmux pane. `force` skips the checks. |

## Requirements

None for the recap and close-out. Optional:

- [`jq`](https://jqlang.org) — `/session-recap` reads the current context size from the session
  transcript; without it the size is an estimate.
- [`agentctl`](https://github.com/roypadina/agentctl) — `/close-session` marks the session done.
- [cmux](https://cmux.com) — `/close-session` closes the pane. Outside cmux it tells you to close the
  window yourself. It closes only its own pane, found by `$CMUX_SURFACE_ID` (needs `jq`), and the
  workspace only when that pane is its single surface; when unsure it closes nothing.

Every command is read-only until you approve an action, and all the gates in your own `CLAUDE.md`
still apply.
