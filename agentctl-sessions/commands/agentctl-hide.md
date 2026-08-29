---
description: Keep this session out of the default agentctl list (still visible under hidden)
argument-hint: "[--undo to unhide]"
allowed-tools:
  - Bash
---

Keep the session you are running in out of the default list: `agentctl hide $ARGUMENTS`.

It stays available under `agentctl ls --hidden`, and `v` cycles to it in the TUI. `agentctl hide
--undo` puts it back.

This is a listing preference only — the Claude Code transcript is untouched, nothing leaves
`~/.claude`, and the session still resumes normally if addressed by id. Say so when you confirm.

Report the result in one line.
