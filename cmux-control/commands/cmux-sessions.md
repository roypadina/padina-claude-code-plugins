---
description: List every Claude Code session running across cmux workspaces, with its resume command
argument-hint: "[check | restore --dry-run | restore] — no argument lists everything"
allowed-tools:
  - Bash
---

Inventory the Claude Code sessions running in cmux, using the bundled script:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cmux-sessions.py" $ARGUMENTS
```

With no `$ARGUMENTS`, run `list` — a markdown inventory of every pane: workspace ref and UUID, pane
ref and tty, whether a `claude` process is actually alive, cwd, which config profile it was launched
under, the session id, and a ready-to-paste resume command.

The other two subcommands:

- `check` — what did not come back after a cmux restart: `MISSING workspace` (saved but not live),
  `DEAD pane` (pane is live, no agent in it), plus warnings about session ids with no transcript on
  disk. Add `--session-file ~/Library/Application\ Support/cmux/session-com.cmuxterm.app-previous.json`
  to inspect the launch before this one — the current file is rewritten to match whatever actually
  came up, so a workspace that failed to restore may only exist in the previous one.
- `restore` — recreate the missing workspaces and send the resume command into panes that lost their
  agent. **Always run `restore --dry-run` first and show the user the commands before running it for
  real** — it creates workspaces and types into existing panes.

Report the result compactly: how many panes, how many are actually running, and anything `check`
flagged. Do not paste the whole inventory back unless the user asked for it — offer
`-o <file>` instead.
