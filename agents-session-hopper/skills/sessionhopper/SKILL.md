---
name: sessionhopper
description: Steer AgentsSessionHopper, which runs this Claude Code session on one of the user's own Claude accounts (profiles) and continues the same conversation on another one near a usage limit. Use for "switch account", "move to <profile>", "which account am I on", "how much usage is left", "stay on this account", "hold this session", "stop auto switching", "resume supervised", and whenever a "[sessionhopper]" message arrives.
---

# AgentsSessionHopper: the account this session runs on

AgentsSessionHopper (CLI `sessionhopper`, plus a menu-bar app) starts the unmodified `claude` under one
**profile**: one Claude Code configuration folder per account. Near a plan limit it moves the
conversation to the next profile with room: it ends `claude` when a turn is over and runs
`claude --resume <same id>` under the other profile. The conversation, files and history stay the same;
only the account changes.

## Is this session supervised?

- `SESSIONHOPPER_SESSION_ID` is set: yes. `SESSIONHOPPER_PROFILE` is the current profile, and
  `SESSIONHOPPER_BIN` is the CLI. Run every command as `"${SESSIONHOPPER_BIN:-sessionhopper}" …`.
- Not set: this session cannot move. Tell the user how to supervise it: `/exit`, then
  `sessionhopper -c` in the same folder (or `sessionhopper --resume <id>`). Never restart it yourself.

## Commands

| The user asks | Run |
|---|---|
| "which account am I on", "how much is left" | `"${SESSIONHOPPER_BIN:-sessionhopper}" status` (usage is what Claude Code's status line last reported per profile) |
| "switch account", "move off this one" | `… switch` (moves when this turn ends: finish the step you are on, then end your turn) |
| "move to <profile>" | `… switch <profile>` |
| "move right now", even mid-work | `… switch --now` (restarts Claude Code at once; only on an explicit ask) |
| "stay on this account", "stop auto switching" | `… hold on` (`hold off` undoes it; `--all` for every session) |
| "show the switch log" | `… log -n 20` |
| "what can I resume here" | `… sessions` (`all`, `--all-dirs` for every folder) |
| "what are the thresholds" | `… config` (read only) |

## Rules

- **A move lands at the turn end.** Once a move is pending (a `[sessionhopper] This conversation moves
  to …` note says so), finish the current step, start no new subagents or background jobs, and end
  your turn. The session continues on the other account by itself.
- **Never change settings unasked**: thresholds, "move without asking", park, the continue prompt
  (`config …`) are the user's choice.
- **Paid usage:** `hold on` keeps the session on its account even past 100% of the plan, which can bill
  paid extra usage where the account allows it. Say so, and only do it when the user asks.
- **Logins are the user's**: `sessionhopper login <profile>` runs Claude Code's own `claude auth login`.
  Never read, copy or move login or credential files.

## When a `[sessionhopper]` continue message arrives

The conversation was moved to another account and Claude Code restarted in the middle of your work.
Do what the message says: re-read the end of the conversation to find where you stopped, redo the
interrupted step, restart the subagents and background jobs it lists, run `CronList` and re-create only
the scheduled tasks that are missing, then carry on. Reply with one status line. Do not ask whether to
continue; only the account changed.

## Policy (live values: `config`)

- **Suggest threshold** (default 85%): the user is asked to move; with "move without asking" on, the
  move happens at the next turn end.
- **Park threshold** (default 97%): with "move at once" on, the move happens immediately, even
  mid-turn. If no profile has room, the session **parks**: it ends and prints the command to resume it
  later, so it never runs into paid usage (unless held).
- Profiles are tried in their configured order; `sessionhopper -P <profile>` starts on one first.

## Resuming into supervision

`sessionhopper -c` (newest session in this folder) · `sessionhopper --resume <id or name>` · a bare
`sessionhopper --resume` shows a numbered picker.
