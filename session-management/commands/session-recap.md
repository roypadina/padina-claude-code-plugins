---
description: Mid-session recap — done / now / next, then what is running and where, open items, gaps, what is waiting on whom, what you must do, and a /compact verdict. Read-only.
argument-hint: "[optional focus]"
---

The user wants to re-orient mid-session: where are we, what is in flight and where, what is
blocking, what they owe, what comes next. Produce a short recap and stop. This is NOT a close-out —
nothing gets stopped, cleaned, pushed or posted here; that is `/finish-session`.

Focus from the user (narrows the middle groups; the header and the Context verdict always appear): $ARGUMENTS

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

## 3. Measure context

Preferred — the status line's own numbers (the same `ctx` % the user sees), when the status line
writes them (setup in the plugin README):

```bash
jq -c '{pct: .context_window.used_percentage, window: .context_window.context_window_size, ctx: (.context_window.current_usage | .input_tokens + .cache_read_input_tokens + .cache_creation_input_tokens), ts}' "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/context-window/$CLAUDE_CODE_SESSION_ID.json"
```

Use `pct` and `window` exactly as given; never recompute or second-guess the window.

Fallback (file missing) — size from the transcript:

```bash
f=$(ls "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/projects/*/"$CLAUDE_CODE_SESSION_ID".jsonl | head -1)
grep '"type":"assistant"' "$f" | tail -n 50 | jq -s -c '[.[] | select(.isSidechain != true and .message.model != "<synthetic>" and .message.usage != null)] | last | {model:.message.model, ctx:(.message.usage|.input_tokens+(.cache_read_input_tokens//0)+(.cache_creation_input_tokens//0))}'
```

`ctx` = current context size in tokens. Do not grep `"usage"` and take the last line — it matches
prose and returns 0.

In the fallback the window is unknown: neither the transcript nor the `model` setting reveals it
(the same model can run with a 200k or a 1000k window). Never guess it. Report `ctx <n>k (window
unknown)` and judge only by the absolute caps below.
No transcript or no `jq` → estimate from conversation length and label the line `(estimate)`.

Verdict from `pct` (only when known):
- < 50% → `no`
- 50–75% → `soon — at next break` (next finished sub-task; the line below is ready to paste)
- ≥ 75% → `now`
- Whatever the window: ctx ≥ 200k → at least `soon`; ≥ 400k → `now` (recall degrades long before a
  1000k window fills).
- Bump one level up when the context is mostly stale bulk (file dumps, logs, finished sub-tasks).
- Never advise compacting mid-step: if something in flight still needs details that only exist in
  context, `now` becomes `now — right after <step>`.

You cannot run `/compact`; only the user can type it. For `soon`/`now` hand over ONE paste-ready
line, no newlines, filled from this recap — everything in Running/Open/Waiting/You must survive:
`/compact Keep: goal <…>; current step <…>; decisions <…>; in flight <what — how/where — state, …>; open <…>; waiting on <…>; user owes <…>; key paths/ids/PRs <…>. Drop: finished sub-tasks, file contents, logs, tool output.`

## 4. Report — one screen

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
  provide, test manually, run (sudo), type /compact.

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

Context: <ctx>k / <window>k (<pct>%)  — or <ctx>k (window unknown) in the fallback → <no | soon — at next break | now | now — right after <step>>
/compact <paste-ready line>                      ← only for soon / now

→ Next: <one concrete action to take right now — the user's first You item, or what you will do on "go">
```

Nothing running, open, missing or waiting: header + `Context` line + `→ Next` only.
