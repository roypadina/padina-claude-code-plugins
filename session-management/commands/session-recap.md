---
description: Mid-session recap — done / now / next, then what is running and where, open items, gaps, what is waiting on whom, and what you must do. Read-only.
argument-hint: "[optional focus]"
---

The user wants to re-orient mid-session: where are we, what is in flight and where, what is
blocking, what they owe, what comes next. Produce a short recap and stop. This is NOT a close-out —
nothing gets stopped, cleaned, pushed or posted here; that is `/finish-session`.

Focus from the user (narrows the middle groups; the header always appears): $ARGUMENTS

## Rules

- **Read-only, zero side effects.** Gather and report. Do not stop, kill, delete, push, post,
  transition, launch, schedule, or message another agent or session (no `SendMessage` "status?"
  pings — they interrupt it). Checks only.
- **Verify, don't recall.** Real state via cheap commands and harness notifications. Anything known
  only from a compact summary → mark it `(from summary)`.
- **Bounded and cheap.** Only what THIS session started or touched; one command per check; never
  read other sessions' transcripts or screens, never audit their work. A check that would be slow →
  skip it and mark the line `unverified`.
- **Stop after the report.** End the turn — do not resume work in the same turn; the user may
  redirect.
- Housekeeping (temp files, memory, ticket transitions, closing panes) belongs to `/finish-session`
  — leave it out unless it blocks the goal.

## 1. Review

Scan the conversation from the start (and the compact summary, if any): the goal, requests,
decisions, what was built or changed, questions asked (answered or not), promises ("later", "after
this"), things explicitly dropped or deferred, and everything launched — subagents, background
shells, Monitors, crons/loops/wakeups, Workflow runs, other panes/workspaces/sessions.

## 2. Check state

Only the checks that apply:
- **Task/todo list** — read it with the tool; `pending` / `in_progress` items.
- **Background subagents, background Bash, Workflow runs** — state from the harness: a completion
  notification arrived → finished; none yet → still running. Don't poll.
- **Live processes** — `bash "${CLAUDE_PLUGIN_ROOT}/scripts/session-procs.sh"`: every process this
  session started that still runs (pid, elapsed, command). Each belongs under Running — fold it into
  the background job that started it, or list it on its own.
- **Monitors, CronCreate, ScheduleWakeup, `/loop`** — id, schedule, what it does, last/next fire
  (list tool if available, else from the conversation).
- **Other top-level agents this session launched** (new pane/workspace/session) — where it runs
  (`workspace:N "title"` / `pane surface:N` / session name) and how it reports back: a report file
  (e.g. `ls "${TMPDIR:-/tmp}/invoke-new-agent/"<ts>-<slug>.report.md` — exists → finished, read its
  first lines; absent → running), a `[report from …]` line already received, or no report-back →
  `check its pane`. `ListAgents` if this session talked to other sessions. Never read their screen
  or message them.
- **Git** — per repo touched: `git status -sb` (dirty files, ahead/behind).
- **PRs** opened or updated here — `gh pr view <n> --json state,reviewDecision,mergeable,statusCheckRollup`
  with the right account; one line each.
- **Session metadata** — if `agentctl` is on PATH:
  `agentctl annotations --json | jq --arg id "$CLAUDE_CODE_SESSION_ID" '.[] | select(.sessionId==$id)'`;
  report only a reminder/due that has passed or a flag that no longer matches reality.

## 3. Report — one screen

Numbered lines, ≤5 per group (merge, or end with `+n more`), no evidence dumps, no explanations,
omit empty groups. Each item appears in exactly one group:
- **Running** — started by this session, not yet handled: `<what> — <how/where> — <state>`.
  How/where: `bg agent <name>` · `bg bash <desc>` · `Monitor <desc>` · `cron <id> every <n>` /
  `wakeup <time>` / `loop <interval>` · `workflow <name>` · `workspace:N "title"` / `pane surface:N`
  (+ `report → <file>` or `no report-back`) · `session <name>`.
  State: `running` · `finished — result not handled` · `blocked: <why>` · `unknown`.
- **Open** — agreed or requested, not running, not done: todo items, unactioned requests, questions
  the user asked and never got answered, "later"s.
- **Missing** — needed for the goal but nobody has asked yet: untested path, unverified claim,
  missing prerequisite, step the plan skips.
- **Not planned** — explicitly descoped, deferred, rejected or out of scope — things the user might
  assume are happening.
- **Waiting on** — blocked on something external to both of you: `<what> ← <who/what>, since <when>`.
  Blocker is the user → it goes under **You** instead.
- **You** — only what the user alone can do, verb first: answer (quote the question), approve,
  provide, test manually, run (sudo).

```
Done: <1–3 lines>
Now: <one line — the step in progress, or "idle — waiting on you">
Then: <1–2 lines — what comes after>

Running (n):
1. <what> — <how/where> — <state>
Open (n):
1. ...
Missing:
1. ...
Not planned:
1. ...
Waiting on:
1. <what> ← <who/what>, since <when>
You:
1. <verb> ...

→ Next: <one concrete action to take right now — the user's first You item, or what you will do on "go">
```

Nothing running, open, missing or waiting: header + `→ Next` only.
