---
description: Close out this session — full recap, then everything still open, un-done, un-cleaned, or owed to someone, with proposed actions
argument-hint: "[optional focus or extra notes]"
---

The user is about to close this session. Before they do, review the ENTIRE session and produce a
close-out report: what was done, and everything left open, unanswered, un-done, un-cleaned, or
owed to someone. Nothing should fall through the cracks when this window closes.

Extra notes from the user: $ARGUMENTS

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
- **Files** — temp/scratch files, work-folder leftovers, generated artifacts, debug logs.
- **Memory / config** — any gotcha or durable fact learned that isn't saved yet; skills or commands
  that should be patched with a lesson learned here.
- **Session metadata** — if `agentctl` is on PATH: is the session named/labelled; should it be
  marked done or flagged?

## 3. Report — SHORT

The user will ask for detail if they want it.
- **Recap:** a few one-line bullets.
- **Open items:** one line each — `<what> → <proposed action>` (path/PR/ticket inline, no evidence
  dumps, no explanations). Only items that need action; skip anything clean.
- Merge similar items (e.g. "3 temp files in X → delete").
- No section headers for empty categories, no per-category walkthrough, no draft messages yet —
  just "notify <who> about <what>". Draft text only when the user picks that item.
- Whole report fits on one screen.

Format:

```
Done:
- ...
Open:
1. <item> → <action>
2. ...
Run which? (all / 1,3 / none)
```

If nothing is open: one line saying so + `Run /close-session to close it out.`

## 4. Act on the user's picks

Execute only the approved items, then one line per item: done / skipped / failed.
If every item is now done or skipped, end with: `Run /close-session to close it out.`
