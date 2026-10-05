---
description: Final close — verify every /finish-session open item is done or skipped, mark the session done in agentctl, close this cmux pane
argument-hint: "[force | -f] [optional notes]"
---

The user wants to close this session for good. Extra notes: $ARGUMENTS

**Force mode:** if the arguments contain `force` or `-f`, skip steps 1 and 2 entirely — no
/finish-session check, no item checks, no questions. Go straight to step 3, and in step 3.2 reply
`Force-closed. Closing pane.`

## 1. Was /finish-session run?

Look back through this conversation (and the compact summary, if any) for a `/finish-session`
report. If none exists, stop and reply with one line:
`/finish-session hasn't run in this session — run it first, then /close-session.`
Do nothing else.

## 2. Validate its open items

For every item in the latest `/finish-session` "Open:" list, classify it:
- **done** — verify with a real check (git, gh, the issue tracker, file exists / removed, process
  gone), not memory.
- **skipped** — the user explicitly said skip / none / ignore for it.
- **still open** — anything else.

If any item is still open: list them one line each (`<n>. <item> → <action>`) and ask
`Do now / skip all / pick (e.g. 1,3)?`. Act only on what the user picks, then re-check. Do not
close until every item is done or skipped.

## 3. Close

Only when nothing is still open:
1. `agentctl done` — skip if `agentctl` is not on PATH.
2. Reply one line: `Closed: <n> done, <m> skipped. Closing pane.`
3. `bash "${CLAUDE_PLUGIN_ROOT}/scripts/close-own-pane.sh"` — must be the last tool call (it ends
   this session). It finds this pane by `$CMUX_SURFACE_ID`, closes only that pane, and closes the
   workspace only when this pane is provably its single surface. Outside cmux it prints
   `Not in cmux — close the window yourself.`
   If it prints `closed nothing`, relay that line and stop. Never close anything yourself: no
   `cmux close-surface` / `close-workspace` by hand, and never use `$CMUX_WORKSPACE_ID` — it goes
   stale when the pane is moved, and a fallback on it once closed the parent session's workspace.
