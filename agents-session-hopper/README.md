# agents-session-hopper

A skill that teaches Claude to steer [AgentsSessionHopper](https://github.com/roypadina/AgentsSessionHopper),
the Mac app and CLI that keeps your own Claude accounts side by side and continues the same Claude Code
conversation on another account near a usage limit.

With it, Claude knows:

- whether the session is supervised and on which profile it runs;
- how to switch, hold, show usage and the switch log (`sessionhopper status | switch | hold | log`);
- to end its turn when a move is pending, so the move lands cleanly;
- what to do when a moved session resumes with a `[sessionhopper]` message: redo the interrupted step,
  restart what was running, and carry on;
- never to change settings or enable paid usage unasked.

## Install

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install agents-session-hopper@padina
```

Install it in **every** profile (each Claude account folder has its own plugins). AgentsSessionHopper's
setup does this for you, or run per profile:

```bash
CLAUDE_CONFIG_DIR=~/.claude-work claude plugin marketplace add roypadina/padina-claude-code-plugins
CLAUDE_CONFIG_DIR=~/.claude-work claude plugin install agents-session-hopper@padina
```

**Requires** AgentsSessionHopper 0.1.8+ (`brew install --cask roypadina/tap/agents-session-hopper`).
Not affiliated with Anthropic.
