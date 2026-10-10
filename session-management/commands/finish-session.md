---
description: Close out this session — full recap, everything still open, un-done, un-cleaned, or owed to someone, with proposed actions; then "close" marks it done and closes this cmux pane
argument-hint: "[close | force | optional focus or extra notes]"
---

The user is about to close this session. Before they do, review the ENTIRE session and produce a
close-out report: what was done, and everything left open, unanswered, un-done, un-cleaned, or
owed to someone. Nothing should fall through the cracks when this window closes. When the user
then says `close`, close the session (step 5).

Arguments: $ARGUMENTS
- First word `force` or `-f` → skip steps 1–4 and 5.1: no report, no checks, no questions. Run
  step 5.2 with the reply `Force-closed. Closing <what the dry run said>.`
- First word `close` (rest = notes) → steps 1–3, then step 5 in the same turn, as if the user had
  replied `close` to the report.
- Anything else → extra notes / focus for the report.

## Rules

- **Read-only until the user approves.** Gather and report first. Do NOT close, merge, delete, push,
  transition, post, email, or remove anything on your own — propose it, then do only what the user picks.
- All normal gates still apply — every rule in the user's CLAUDE.md and memory, plus: remove a
  worktree only by the exact path this session created; use the right account for each repo and
  service; tracker writes need confirmation; messages (chat, email, comments) go out as the user,
  only after they approve the text; confirm any notification target before publishing to it.
- Verify, don't recall. Check real state with commands (git, gh, the issue tracker, files) — don't
  list a PR as open or a branch as unmerged from memory.
- Scope = things THIS session touched or created. Don't audit the whole machine or other sessions'
  work (an unknown worktree/branch is someone else's live workspace — leave it).

## 1. Review the session

Go through the whole conversation from the start (and the compact summary, if there was one):
requests, decisions, tool calls, files created/edited, commands run, background agents/tasks,
monitors/crons/loops, the todo/task list, questions asked and whether they were answered.

## 2. Check real state

Only what applies to this session:
- **Todo/task list** — anything not `completed`.
- **Git** — for every repo touched: `git status -sb`, unpushed commits, stashes, branches created,
  worktrees created (`git worktree list`, but only report ones this session made).
- **PRs** — `gh pr list --author @me` / `gh pr view` for PRs opened or updated here: state, checks,
  review status, mergeable? Use the right gh account for the repo.
- **Issue tracker** (Jira, GitHub Issues, Linear…) — tickets touched: current status vs. what the
  work actually did (needs transition, comment, PR link, due date?).
- **Running things** — background shells, agents, Monitors, CronCreate/loops/ScheduleWakeup,
  port-forwards, preview/QA environments, local servers started this session. Should any be stopped?
  `bash "${CLAUDE_PLUGIN_ROOT}/scripts/session-procs.sh"` lists every process this session started
  that still runs — each is a `!` item.
- **Files** — temp/scratch files, work-folder leftovers, generated artifacts, debug logs.
- **Memory / config** — any gotcha or durable fact learned that isn't saved yet; skills or commands
  that should be patched with a lesson learned here.
- **Session metadata** — if `agentctl` is on PATH: is the session named/labelled; should it be
  marked done or flagged?

- **App release** — if the `finalize-app-release` skill is installed: for every repo this session
  changed, run its state script (Step 1 of that skill). It prints `SKIP` for repos it doesn't cover —
  drop those silently. For the rest, `STAMP MATCH` or no GAP → nothing to report; otherwise one open
  item `<app>: <n> release gaps → /finalize-app-release <dir>`.

## 3. Report — SHORT

The user will ask for detail if they want it.
- **Recap:** a few one-line bullets.
- **Open items:** one line each — `<what> → <proposed action>` (path/PR/ticket inline, no evidence
  dumps, no explanations). Only items that need action; skip anything clean.
- Merge similar items (e.g. "3 temp files in X → delete").
- Prefix `!` to an item the close would kill or orphan: something started here that is still
  running (background shell or agent, port-forward, local server, Monitor, cron, loop), a lesson
  not yet saved to memory or a skill, an unsent draft, uncommitted changes in a worktree this
  session created. Unpushed commits and edits in a shared clone stay on disk — no `!`.
- No section headers for empty categories, no per-category walkthrough, no draft messages yet —
  just "notify <who> about <what>". Draft text only when the user picks that item.
- Whole report fits on one screen.

Format:

```
Done:
- ...
Open:
1. <item> → <action>
2. ! <item> → <action>
Run which? (all / 1,3 / none) — or "close" to close the session
```

If nothing is open: one line saying so + `Say "close" to close the session.`

## 4. Act on the user's picks

Execute only the approved items, then one line per item: done / skipped / failed.
End with: `Say "close" to close the session.` A reply like `1,3 then close` runs those items, then
step 5.

## 5. Close — when the user says `close`

**Trigger.** The user's reply, ignoring `ok`/`yes`/`please`/`then`/`and` and punctuation, is
`close` with at most `it`/`this`/`session`/`pane`/`out` after it, optionally after picks
(`1,3 then close`, `all, close` → run those items, then close). `close the PR` / `close RD-123`
is an ordinary request, not this. It counts only while your latest message is this close-out
report or the result of acting on its picks; otherwise ask one line — `Close this session
(re-check, agentctl done, close pane)? yes/no` — and close only on yes. If the report survives
only in a compact summary, or new work happened since it, re-run steps 2–3 first; never close
from a summary.

1. **Check what's left.** Re-check every item from the latest "Open:" list with a real check (git,
   gh, the issue tracker, files, processes) — done or not. Items the user didn't pick count as
   skipped: they saw the list and chose to close. Ask only when a `!` item is still open:
   `Closing kills/orphans: <a>; <b>. Close anyway? yes/no` — on no, stop. Otherwise ask nothing.
2. `bash "${CLAUDE_PLUGIN_ROOT}/scripts/close-own-pane.sh" --dry-run` — says what the close
   would close (`Would close surface:N in workspace:M "<title>": …`). If it says
   `closed nothing`, run only `agentctl done` (if on PATH), relay its first line, and stop.
   Otherwise reply one line — `Closed: <n> done, <m> skipped. Closing <what the dry run said>.` —
   then in ONE Bash call, the last tool call of the session, from this main session (never a
   subagent):
   `command -v agentctl >/dev/null && agentctl done; bash "${CLAUDE_PLUGIN_ROOT}/scripts/close-own-pane.sh"`
   On success the session ends. The script closes only this session's own pane — found by
   `$CMUX_SURFACE_ID`, confirmed by its tty — and the workspace only when this pane is provably
   its single surface; a pinned workspace is kept with a fresh shell. Outside cmux it prints
   `Not in cmux — close the window yourself.`
3. If the session is still alive after that, the script printed `… — closed nothing.`: relay that
   line verbatim and stop. Never close anything yourself — no `cmux close-surface` /
   `close-workspace` / unpin by hand (a bare `close-surface` closes the pane the user is looking
   at), and never use `$CMUX_WORKSPACE_ID` (it goes stale when a pane is moved; a fallback on it
   once closed the parent session's workspace).
