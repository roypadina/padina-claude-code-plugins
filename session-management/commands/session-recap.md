---
description: Mid-session recap for coming back cold — the story so far (finished topics in one line each, the current one in detail), what is running, next steps, side findings and later-todos, and every question waiting on you with enough context to answer on the spot. Read-only.
argument-hint: "[optional focus]"
---

The user wants to re-orient mid-session: where are we, what is in flight and where, what is
blocking, what they owe, what comes next. Produce a short recap and stop. This is NOT a close-out —
nothing gets stopped, cleaned, pushed or posted here; that is `/finish-session`.

Focus from the user (narrows Story, Current and Next steps to that topic; the title, Needs you and Next always appear): $ARGUMENTS

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

Scan the conversation from the start (and the compact summary, if any). Assume the user has read
none of it. Collect three things.

**a. Topics.** Long sessions drift; split the session into topics.
- A topic = one goal with its own deliverable (a fix, a release, a feature, a research answer). A
  new topic starts when the user redirects or the deliverable changes. Steps toward the same
  deliverable are parts of a topic, not topics.
- Give each topic a status:
  - **finished** — delivered and verified, or explicitly closed by the user.
  - **current** — exactly one: the topic with work in motion now; if nothing is in motion, the most
    recent unfinished one.
  - **parked** — started, not finished, no longer being worked on.
- For the current topic, list its parts (≤6, merge small ones), each done / in progress / blocked /
  not started. Done parts stay listed: they show how far the topic is.
- For finished and parked topics keep only the outcome, plus the one fact the user would look for
  (PR number, version, where the result lives).

**b. Questions that never got an answer.** Check every assistant turn, and every report from a
subagent or other agent, for: a question, an offered choice, an approval request, a request for a
credential / file / manual test / privileged command, and any "I'll assume X unless you say
otherwise". For each, look for a later user message that answers it. No answer → it goes in Needs
you. No answer and work went on anyway → record what was assumed and what undoing it costs. Skip a
question that later events made irrelevant. Note when it was asked: a time if known, else a
landmark ("right after the release").

**c. Everything else.** Decisions; side findings (bugs, risks, gaps noticed along the way and not
acted on); promises and "later"s from either side; things explicitly dropped or deferred; questions
the user asked that were never answered; and everything launched: subagents, background shells,
Monitors, crons/loops/wakeups, Workflow runs, other panes/workspaces/sessions.

## 2. Check state

Only the checks that apply:
- **Task/todo list** — read it with the tool; `pending` / `in_progress` items.
- **Background subagents, background Bash, Workflow runs** — state from the harness: a completion
  notification arrived → finished; none yet → still running. Don't poll.
- **Live processes** — `bash "${CLAUDE_PLUGIN_ROOT}/scripts/session-procs.sh"`: every process this
  session started that still runs (pid, elapsed, command). Each belongs under Running now — fold it into
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
- **Disk** — `du -sh` of the session's work folder and anything big it downloaded or built, plus
  every entry in `~/.claude/session-management/big-files/$CLAUDE_CODE_SESSION_ID.md` (if it exists):
  one line with the total, plus each item ≥ 50 MB (`⚠` at ≥ 1 GB). Cleanup itself is `/finish-session`.
- **PRs** opened or updated here — `gh pr view <n> --json state,reviewDecision,mergeable,statusCheckRollup`
  with the right account; one line each.
- **Session metadata** — if `agentctl` is on PATH:
  `agentctl annotations --json | jq --arg id "$CLAUDE_CODE_SESSION_ID" '.[] | select(.sessionId==$id)'`;
  report only a reminder/due that has passed or a flag that no longer matches reality. It goes on the
  Also line.

## 3. Report

Written for someone who comes back after hours with no context. Order is fixed: past → present →
future → their move, so what needs them is the last thing on screen.

Format rules:
- Plain words, full short sentences. No internal ids, file dumps or evidence. Name things the way
  the user would ("the settings screen"), with the identifier after it only if they will need it.
- ≤5 lines per list (merge, or end with `+n more`). **Needs you is never truncated.**
- Marks: `✓` done · `▸` in progress · `?` blocked on the user · `✗` blocked on something else ·
  `○` not started · `‖` parked.
- Omit any section with nothing in it. Each item appears once.
- Known only from a compact summary → append `(from summary)`. Check skipped → `unverified`.

```
# Recap — <current topic, ≤8 words>
<duration if known> · <n> topics (<n> finished, 1 in progress[, <n> parked]) · <n> jobs running · <n> items need you

## Story so far
1. ✓ **<topic>** — <outcome in one line; PR / version / where the result is>
2. ‖ **<topic>** — parked: <what is left, one line>
3. ▸ **<topic>** — current, <n> of <m> parts done.

## Current — <topic>
Goal: <one sentence: what will exist when this is done>
- ✓ <part> (<proof: tests pass / PR #n state>)
- ▸ <part> — <what is happening now and who is doing it>
- ? <part> — stopped, needs answer <n>
- ○ <part>

## Running now (n)
1. <what, in plain words> — <how/where> — <state>
- Waiting outside: <what> ← <who/what>, since <when>

## Next steps
1. <next step of the current topic> (<what it waits for, if anything>)

## Side topics & later
- **Found:** <bug / risk / gap noticed along the way, not acted on> — <one line on why it matters>
- **Later:** <a "later" either side said> (<when it came up>)
- **Parked:** <topic or part started and left> — <what is left>
- **Not doing:** <explicitly dropped or deferred — things the user might assume are happening>

## Needs you (n)
**1. <Decide | Approve | Confirm | Provide | Test by hand | Run> — <subject>** (blocks <what>; asked <when>)
<1–2 sentences: what this is and why it came up, readable with no other context>
- **A** — <option + its consequence> *(recommended)*
- **B** — <option + its consequence>

Also: <git: repo/branch, unpushed commits, modified files> · <disk total; items ≥ 50 MB, `⚠` at ≥ 1 GB> · <passed reminder / stale flag>

**→ Next:** <one concrete action>
```

Section rules:
- **Title line** — always. The counts line only when the session has more than one topic or
  anything running or waiting.
- **Story so far** — only with 2+ topics. Session order, finished topics one line each; more than
  5 → merge the oldest into `Earlier: <n> small tasks, all done`. The current topic is last.
- **Current** — parts of the current topic. PR state goes on the part it belongs to
  (`PR #n open, checks green, no review yet`). One topic and ≤3 parts → drop the header and the
  Goal line, print the parts directly under the title.
- **Running now** — everything this session started that is not yet handled. How/where:
  `bg agent <name>` · `bg bash <desc>` · `Monitor <desc>` · `cron <id> every <n>` /
  `wakeup <time>` / `loop <interval>` · `workflow <name>` · `workspace:N "title"` /
  `pane surface:N` (+ `report → <file>` or `no report-back`) · `session <name>`.
  State: `running <elapsed>` · `finished — result not read yet` · `blocked: <why>` · `unknown`.
  Things blocked on someone other than the user go on `Waiting outside` lines.
- **Next steps** — ordered steps of the current topic only, each with what it waits on.
- **Side topics & later** — everything off the main line, one tag per line, most important first:
  `Found` = noticed while working, not acted on (bug, risk, untested path, unverified claim,
  missing prerequisite); `Later` = a deferred todo or "later" from either side, plus questions the
  user asked that never got an answer; `Parked` = a topic or part started and left; `Not doing` =
  explicitly dropped or out of scope. More than 5 → `+n more`, listed in full only when asked.
- **Needs you** — only what the user alone can do, most-blocking first. Rewrite each question so
  it stands alone; never "see above", never the bare original question. Give lettered options for
  a choice, mark one recommended, state what the item blocks. `Confirm` = a choice already made
  without an answer: say what was done, the alternative, and the cost of undoing it. `Test by
  hand` / `Run` / `Provide` = the exact steps or the exact thing needed, no options.
- **Also** — one line, facts that need no decision. Print only what is not clean: unpushed or
  uncommitted work, big files, a passed reminder, a flag that no longer matches. All clean → omit.
- **→ Next** — always the last line, one action. Needs you has items → the shortest reply that
  unblocks the most (`reply 1A 2A`). Otherwise what you will do on "go", or `nothing from you —
  <what is running> reports when done`.

Short session (one topic, nothing waiting): title, 1–3 lines of what was done and what is
happening now, `→ Next`.
