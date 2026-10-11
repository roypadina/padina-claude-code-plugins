# session-management

Three slash commands for the life of a Claude Code session: a mid-session recap, a resume check
after a disruption, and an end-of-session close-out that also closes the session when you say `close`.

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
| `/session-recap [focus]` | Mid-session | Done / now / next in a few lines, then open items and *how* each runs (background agent, other pane, workspace, session, cron), what's missing, not planned, waiting on, and what you need to do. Read-only. |
| `/resume-all [what happened]` | After the Mac slept, the network changed (Wi-Fi ⇄ LAN, VPN drop), or the account switched | Checks everything the session had running — background agents, shells, Monitors, crons, dev servers, port-forwards, auth, MCP — and restarts only what the disruption stopped, exactly as it was (same command, prompt, schedule). No plan changes; never repeats a push/post/deploy blind. Lists what needs you (reconnect `/mcp`, re-login), then continues the main task. |
| `/finish-session [cleanup] [close] [force] [notes]` | Before closing | Recap, then every open, un-done, un-cleaned or owed item with a proposed action. Acts only on the items you pick. Then reply `close`: it re-checks the items, asks only about the `!` ones the close would kill or orphan (things still running, unsaved lessons, unsent drafts), marks the session done in `agentctl` and closes the cmux pane. `cleanup` deletes this session's own leftovers (temp files, merged local branches it created — never `~/ClaudWork`, never what you'd need to resume) without asking; `close` closes right after, but only if nothing else is open. `force` closes with no report or checks. |

`close` works even after `/compact`: a `UserPromptSubmit` hook spots a reply that is only a close
(`close`, `close it`, `1,3 then close` — not `close the PR`) and hands Claude the close steps again.
For every other prompt it prints nothing (~7 ms). Both commands list the processes the session
started that are still running (`scripts/session-procs.sh`) — the close would kill them.

## Requirements

None for the recap and close-out. Optional:

- [`jq`](https://jqlang.org) — the pane close and the `close` hook need it.
- [`agentctl`](https://github.com/roypadina/agentctl) — the close marks the session done.
- [cmux](https://cmux.com) — the close closes the pane. Outside cmux it tells you to close the
  window yourself. It closes only its own pane: found by `$CMUX_SURFACE_ID` (needs `jq`) and
  confirmed by the pane's tty sitting on the session's own process chain, so an env var leaked
  from another pane can't aim it elsewhere. It closes the workspace only when that pane is its
  single surface; a pinned workspace is kept, with a fresh shell in place of the session. When
  unsure it closes nothing. Before closing it says what it will close
  (`scripts/close-own-pane.sh --dry-run`).
  `scripts/selfcheck.sh` (fake cmux) and `scripts/livecheck.sh` (real cmux, throwaway
  `zz-close-test-*` workspaces) prove it after any change.

Every command is read-only until you approve an action, and all the gates in your own `CLAUDE.md`
still apply.
