---
description: Keep this session out of every agentctl list (recoverable; the transcript is untouched)
argument-hint: "[--undo to restore]"
allowed-tools:
  - Bash
---

Keep the session you are running in out of every list: `agentctl delete $ARGUMENTS`.

**Only ever run this when the user explicitly asks for it.** Never as a tidy-up of your own.

It is recoverable — `agentctl delete --undo` restores it, and `agentctl ls --deleted` shows what is
in there. Nothing is destroyed: the Claude Code transcript is untouched and nothing is removed from
`~/.claude`. Say both of those things when you confirm, so "delete" is not mistaken for data loss.

Report the result in one line.
