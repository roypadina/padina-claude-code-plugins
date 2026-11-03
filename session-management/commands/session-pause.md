---
description: Before a reboot, shutdown or sleep — bring every background agent, shell, Monitor, cron, loop and Workflow this session started to a safe stop without losing work, record how to resume each, then say when it is safe. `/resume-all` picks it up after.
argument-hint: "[sleep | reboot] [now | <wait limit, e.g. 3m>]"
---

The user is about to reboot, shut down or sleep the computer. Everything this session has running
must reach a safe stopping point quickly — no lost work — with an exact record of how to resume it.
This is not a close-out (`/finish-session`) and not a re-plan: no new work, no cleanup, no commit or
push the plan did not already have.

Arguments: $ARGUMENTS
- `sleep` → the machine only sleeps: local processes freeze and continue on wake, so background
  Bash keeps running. Default (or `reboot` / `shutdown`) → stop everything.
- `now` → no grace wait: stop each item as soon as it is not inside a risky call. A time (`2m`,
  `10m`) → grace limit. Default: 5 minutes.

## Rules

- **Never cut a risky call.** A call that changes things outside the work tree finishes first,
  however long it takes: push, publish, release, deploy, migration, DB or API write, upload,
  send/post/comment/transition, package install, a script that does several writes. Safe to cut
  (they rerun): reads, searches, `sleep`/waits/polls, builds, tests, linters, downloads to a temp
  dir. Unsure → risky.
- **Stop only with `TaskStop`** (subagents, Workflow runs, background Bash, Monitors) — it keeps a
  subagent resumable. Never tell the user to press `x` in `/tasks`: that cancels a subagent for good.
- **Start nothing new** — no new steps, agents or schedules. A subagent that finishes while pausing:
  note its result, don't act on it. If this command arrived mid-task, finish only the current
  atomic action (the edit or command in progress) so files stay consistent, then stop.
- **Own work only.** Other sessions and panes run their own `/session-pause` — **You** item.
- Every rule in the user's CLAUDE.md and memory still applies.

## How background work takes a stop

Tested on Claude Code 2.1.317:
- **Unnamed background subagent** (spawned without `name`): a `SendMessage` reaches it after its
  current tool call — the send result says `next tool round`. It stops there and replies.
- **Named agent / teammate** (spawned with `name`; send result `queued … for its next turn`): a
  message — even a `shutdown_request` — waits until its whole run ends. It cannot be asked to stop
  mid-run: `TaskStop` it at a safe moment instead.
- After `TaskStop` an agent keeps its full history; a later `SendMessage` resumes it, also after
  `claude --resume`. Address it by agent **ID** — a name survives a restart only if it was used
  since the last compaction.
- `claude --resume` brings back the conversation, subagent transcripts and Workflow results
  (`resumeFromRunId`). It does not bring back background Bash, Monitors, crons (`CronCreate` jobs
  are session-only), `ScheduleWakeup` or `/loop` — those restart from the record.

## 1. Inventory

Scan the conversation from the start (and the compact summary, if any) for everything in flight:
subagents, background Bash, Monitors, crons, wakeups and `/loop`, Workflow runs, agents launched in
other panes/workspaces/sessions, the main-thread step. Then check, one command each:
- `bash "${CLAUDE_PLUGIN_ROOT}/scripts/agent-state.sh"` — each unfinished subagent of this session:
  `<id> <name> <state> <age> <call in flight>`. State `in-tool` = inside a call, `thinking` = between
  calls (safe to stop), `idle` = its turn ended. A run already stopped mid-call stays `in-tool` with
  a growing age.
- `bash "${CLAUDE_PLUGIN_ROOT}/scripts/session-procs.sh"` — processes this session still runs.
- `CronList` — crons.

Nothing running → one line: `Nothing running — safe to <reboot|sleep>.` plus the resume command
(step 5), and stop. No record file.

## 2. Stop — one turn, all items at once

- **Unnamed subagent, running** → `SendMessage` to its ID:
  ```
  PAUSE — the computer is about to reboot or sleep. Stop at the next safe point: finish the call
  you are in and any write, push or deploy you already started, then start nothing new. Leave files
  consistent; don't commit, push or clean up because of the pause. Reply with: PAUSED · done:
  <steps> · in progress: <step, how far> · next: <exact next step> · files touched: <paths> ·
  unfinished commands: <any command that stops with you>. You will be resumed with your history.
  ```
- **Named agent, running** → state `thinking`, or `in-tool` on a call safe to cut → `TaskStop` now.
  `in-tool` on a risky call → wait for that call (step 3), then `TaskStop`. Don't message it.
- **Idle named agent** → nothing to stop; record it.
- **Workflow run** → `TaskStop` (finished agent calls stay cached for `resumeFromRunId`). If the
  conversation shows it is in a push/publish/deploy phase, wait for that phase first.
- **Background Bash** (main thread) → risky, or ends within the grace → let it finish. Otherwise:
  reboot → `TaskStop`; `sleep` → leave it running.
- **Monitor** → `TaskStop`.
- **Cron** → `CronDelete`, so nothing fires before the reboot or on wake. **`/loop` /
  `ScheduleWakeup`** → `ScheduleWakeup` with `stop: true`.
- **Agents in other panes/sessions** this session launched → **You**: run `/session-pause` there.

Record every stopped item with what it needs to restart: agent ID, name, type, model; the exact
command and cwd; the Monitor command, description and timeout; the cron schedule, prompt and
recurring flag; the loop prompt and interval; the Workflow run id and script path.

## 3. Wait — bounded

Skip this step for `now`: go straight to the expiry check below.
- Start one timer: Bash `sleep <grace seconds>` with `run_in_background` (foreground sleep is
  blocked). For each risky call you wait on, also start a background poll that ends when the agent
  leaves that call:
  `until ! bash "${CLAUDE_PLUGIN_ROOT}/scripts/agent-state.sh" | grep -F "<id> " | grep -qF "<start of the call>"; do sleep 2; done`
- End the turn with one line: `Pausing — waiting on <n>: <names> (until <hh:mm>). Don't sleep yet.`
- Each notification → an unnamed agent's `PAUSED` reply marks it paused; a poll ending → `TaskStop`
  that agent right away. If it already started another risky call, wait for that one too.
- **Timer expires** with items still running → re-run `agent-state.sh`: `thinking`, or `in-tool` on
  a call safe to cut → `TaskStop`; a risky call → keep waiting for that call only, nothing else.

## 4. Verify

- `agent-state.sh` — every agent left is `idle`, or one you stopped.
- `session-procs.sh` — nothing of this session still runs, except background Bash left on purpose
  for `sleep`. A leftover child of a stopped job → `kill <pid>`, only PIDs that script listed.

## 5. Record, then report

Write the record to `~/.claude/session-pause/<session id>.md` (`$CLAUDE_CODE_SESSION_ID`; create the
dir; replace an older record for this session). Never write a secret: a command that holds a token
→ write `<secret>` and where it comes from. `<cwd>` = the folder the session started in — `claude
--resume` only finds it from there — not the shell's current dir:
`jq -r 'select(.cwd) | .cwd' "$(ls "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/projects/*/"$CLAUDE_CODE_SESSION_ID".jsonl | head -1)" | head -1`

```
# Paused session <session id>
Paused: <date time> · for: <reboot|sleep> · cwd: <dir>
Resume: cd <cwd> && claude --resume <session id>   then   /resume-all after pause
Main thread: last done <step> · next <step>

## Paused
- subagent <agent id> (<name or ->, <type>, <model>) — <PAUSED reply: in progress / next | stopped in <call>: check its effect> — resume: SendMessage to <agent id>
- bash `<command>` (cwd <dir>) — stopped — resume: rerun, run_in_background
- monitor "<description>" `<command>` timeout <ms> — stopped — resume: Monitor, same
- cron "<schedule>" <recurring|once> "<prompt>" — deleted — resume: CronCreate, same
- loop "<prompt>" every <interval> — stopped — resume: /loop, same
- workflow <run id> (<name>, script <path>) — stopped — resume: Workflow resumeFromRunId <run id>
## Idle agents — nothing stopped; resume only if they had work left: SendMessage to <agent id>
## Left running (sleep only)
## Finished while pausing — result not handled yet
## Needs you
```

Omit empty sections. Then the report, and end the turn — resume nothing until the user says so:

```
Safe to <reboot|sleep> now.                    ← or: Not safe yet — <what still runs, why>
Paused (n):
1. <what> — <how it stopped> — <state>
Left running (n): <item, …>
Finished while pausing (n): <item, …>
Needs you (n):
1. <verb first: run /session-pause in <pane/session>, …>
Resume: cd <cwd> && claude --resume <session id>  →  /resume-all after pause
Record: ~/.claude/session-pause/<session id>.md
```
