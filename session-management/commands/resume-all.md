---
description: After a disruption (Mac slept, network changed, Wi-Fi/LAN flip, VPN drop, account switch, app restart) — check everything this session had running, resume only what the disruption stopped, exactly as it was. No plan changes.
argument-hint: "[what happened, e.g. \"mac slept\" / \"switched claude1 -> claude2\"]"
---

Something outside the session interrupted it: the Mac slept, the network changed (Wi-Fi ⇄ LAN,
new Wi-Fi, VPN dropped), the Claude account or profile switched, or an app restarted. Background
work may have died silently. Find what stopped and put it back exactly as it was — then carry on.

What happened (from the user; may be empty — then assume any of the above): $ARGUMENTS

## Rules

- **Restore, don't re-plan.** Same plan, same steps, same prompts, same arguments, same schedule.
  No new work, no improvements, no "while I'm here". A finished item stays finished. Something the
  user stopped or descoped on purpose stays stopped.
- **Check before you restart.** Never start a second copy of something still alive — duplicate
  agents, two dev servers on one port, a cron fired twice.
- **Never repeat an outward action blind.** Push, publish, deploy, post, send, comment, transition,
  pay — anything others see or that cannot be undone: first check whether it already landed (remote
  ref, PR, message, ticket state). Landed → mark done. Not landed → redo it only if the user had
  already approved it in this session; else ask. Unclear → ask.
- **Own work only.** Only what THIS session started. Other sessions and panes are not yours to
  restart — report them, don't touch them.
- Every rule in the user's CLAUDE.md and memory still applies (approval gates, accounts, etc.).

## 1. Inventory

Scan the conversation from the start (and the compact summary, if any) for everything in flight
when the disruption hit: the main-thread step in progress, subagents, background Bash, Monitors,
crons/loops/wakeups, Workflow runs, agents launched in other panes/workspaces/sessions, long-lived
processes (dev servers, watchers, port-forwards, tunnels, `ssh`, `tmux`), and anything mid-way
through a network call (push, upload, download, API sync).

## 2. Check each item

Only the checks that apply, one command each:
- **Live processes** — `bash "${CLAUDE_PLUGIN_ROOT}/scripts/session-procs.sh"` for what still runs.
  Gone, or alive but stuck (no new output since the disruption, socket dead) → stopped.
- **Background Bash / subagents / Workflow runs** — harness notifications: a completion that
  reports a network error, timeout, `ECONNRESET`, 401/403, auth or rate-limit failure, or
  "interrupted" counts as stopped by the disruption, not finished. Read the tail of its output.
- **Monitors, crons, wakeups, `/loop`** — list them with the tool (`CronList`, etc.); compare with
  what the conversation set up. Missing or failed → stopped.
- **Network-bound things** — dev servers, port-forwards, tunnels, VPN-only targets: probe once
  (`curl -sS -m 5`, `nc -z`, `lsof -i :<port>`). Network or VPN not back yet → that is a **You**
  item, don't loop on it.
- **Auth** — after an account switch or a long sleep, tokens may have changed or expired: one cheap
  check per tool used here (`gh auth status`, `aws sts get-caller-identity`, etc.). Wrong or expired
  account → **You** item (the user re-logs in), unless the fix is a documented non-interactive
  switch.
- **MCP servers** this session used — a failing call means it disconnected. You cannot reconnect
  it; **You** item: `/mcp` → reconnect.
- **Agents in other panes/workspaces** this session launched — report file or report-back channel
  (e.g. `${TMPDIR:-/tmp}/invoke-new-agent/<ts>-<slug>.report.md`). No progress and no report →
  **You** item: check that pane. Don't read its screen or message it.
- **Git** — repos touched: `git status -sb`; a push/pull/fetch that was mid-flight → compare with
  the remote (`git fetch` then `ahead/behind`).
- **Main thread** — the step in progress when the disruption hit: did its last command finish?
  Check its effect, not its output.

## 3. Resume

For each stopped item, restore it the way it ran before:
- Background Bash → rerun the same command, same `run_in_background`, same cwd/env. Skip the parts
  already done when the command is not idempotent.
- Subagent → continue it with `SendMessage` if it is still addressable; else relaunch with the same
  prompt, type and model, plus one line: "Resuming after an interruption — already done: <…>;
  continue from: <…>".
- Monitor / cron / wakeup / `/loop` → recreate with the same schedule and prompt.
- Workflow → resume from its run id (`resumeFromRunId`) so completed steps are cached.
- Dev server / port-forward / tunnel → restart with the same command once its port is free.
- Network-bound step that failed (push, upload, sync) → check it did not land, then retry once.

Fails again → stop retrying that item; report it with the error line.

## 4. Report, then continue

```
Disruption: <what happened, or "unknown">
OK (n): <item, item, …>                                  ← still running fine, one line
Resumed (n):
1. <what> — <how it was restarted> — <state now>
Done before the disruption (n): <item, …>                ← nothing to do
Needs you (n):
1. <verb first: reconnect /mcp <server>, log in to <tool> as <account>, check pane <…>, approve redo of <…>>
```

Omit empty groups. Nothing was affected → one line: `All <n> items running — nothing stopped.`

Then continue the main task from where it stopped, on the same plan — unless a **Needs you** item
blocks it; then stop and wait.
