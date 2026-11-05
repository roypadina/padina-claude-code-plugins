---
description: Close out this session — full recap, everything still open, un-done, un-cleaned, or owed to someone, with proposed actions; then "close" marks it done and closes this cmux pane or Ghostex session
argument-hint: "[cleanup] [close] [force] [optional focus or extra notes]"
---

The user is about to close this session. Before they do, review the ENTIRE session and produce a
close-out report: what was done, and everything left open, unanswered, un-done, un-cleaned, or
owed to someone. Nothing should fall through the cracks when this window closes. When the user
then says `close`, close the session (step 5).

Arguments: $ARGUMENTS
- First word `force` or `-f` → skip steps 1–4 and 5.1: no report, no checks, no questions. Run
  step 5.2 with the reply `Force-closed. Closing <what the dry run said>.`
- Contains the word `cleanup` → accepted for old habits; local cleanup now always runs in step 2b.
- Contains the word `close` → after steps 1–3, close in the same turn (step 5) **only if nothing
  is left open**. Anything still open → show the report and wait; the user decides.
- Anything else → extra notes / focus for the report.

**Local cleanup** = only things this session created that nothing needs any more: scratch / temp
files and dirs (`/tmp`, `$TMPDIR`, throwaway research downloads and test fixtures), leftover test
resources it made, local branches it created that are already merged (`git branch -d`, never `-D`,
never a remote branch). Never delete: anything under `~/ClaudWork/` (deliverables and artifacts
stay), anything needed to resume this session later (notes, handoff files, reports, configs it
wrote), worktrees, other sessions' files, anything outside this machine. Unsure → it is not
cleanup; list it as an open item.

**Ignore list** = `~/.claude/session-management/finish-ignore.md`, one line per thing the user
said never to raise again (`- <what> (<yyyy-mm-dd>)`), shared by every Claude config dir on this
machine. Rules in the user's CLAUDE.md or memory that say to never raise something count the same.

## Rules

- **Act alone when sure, ask only when not.** Step 2b does the sure, local, this-session things
  without asking. Everything else is read-only until the user picks it: do NOT merge, push,
  transition, post, email, or delete beyond local cleanup on your own. Ask only about what you are
  not highly confident about — one line each, never "should I…?" for things already decided.
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

## 2b. Do what you're sure of — no question

- **Drop ignored items.** Read the ignore list; anything it (or a never-raise rule in the user's
  CLAUDE.md / memory) covers is dropped silently. So is anything the user already skipped or
  declined earlier in this session.
- **Local cleanup** — delete every item that fits the definition above with high confidence.
- **Memory** — save each lesson, gotcha or durable fact learned here that isn't saved yet, the
  way the user's CLAUDE.md says (its memory procedure, skill and location; update an existing
  entry before adding one). Patch a skill or command this session found wrong, when the fix is
  clear. Not sure it's worth keeping, or where it goes → open item.
- Each one is a line under `Done:` in the report (`deleted 3 temp files in /tmp/x`, `saved
  memory: <title>`). Never do anything outward-facing, destructive beyond local cleanup, or
  outside this session's own work here.

## 3. Report — SHORT

The user will ask for detail if they want it.
- **Recap:** a few one-line bullets.
- **Open items:** one line each — `<what> → <proposed action>` (path/PR/ticket inline, no evidence
  dumps, no explanations). Only items that need action; skip anything clean.
- Merge similar items (e.g. "3 temp files in X → delete").
- Prefix `!` to an item the close would kill or orphan: something started here that is still
  running (background shell or agent, port-forward, local server, Monitor, cron, loop), a lesson
  step 2b could not save, an unsent draft, uncommitted changes in a worktree this
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
Run which? (all / 1,3 / none / ignore 2) — or "close" to close the session
```

If nothing is open: one line saying so + `Say "close" to close the session.`

## 4. Act on the user's picks

Execute only the approved items, then one line per item: done / skipped / failed.
`ignore <n>` (or "never ask about X again") → append the item to the ignore list (create the file
if missing): this one thing (`release gaps in agentctl`), or the whole kind only when the user
said so (`release gaps, any repo`). Then one line `ignored: <what>`.
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
   `command -v agentctl >/dev/null && agentctl done; test -x "$HOME/.claude/bin/claudwork" && "$HOME/.claude/bin/claudwork" touch; bash "${CLAUDE_PLUGIN_ROOT}/scripts/close-own-pane.sh"`
   On success the session ends. The script closes only this session's own pane — found by
   `$CMUX_SURFACE_ID`, confirmed by its tty — and the workspace only when this pane is provably
   its single surface; a pinned workspace is kept with a fresh shell. In Ghostex it closes this
   session (`ghostex kill`), found by `$GHOSTEX_SESSION_ID` and confirmed by its `zmx run` process
   on the session's own process chain, unpinning it first (a closed pinned session stays in the
   sidebar as a dead row). Elsewhere it prints
   `Not in cmux or Ghostex — close the window yourself.`
3. If the session is still alive after that, the script printed `… — closed nothing.`: relay that
   line verbatim and stop. Never close anything yourself — no `ghostex kill`, no `cmux close-surface` /
   `close-workspace` / unpin by hand (a bare `close-surface` closes the pane the user is looking
   at), and never use `$CMUX_WORKSPACE_ID` (it goes stale when a pane is moved; a fallback on it
   once closed the parent session's workspace).
