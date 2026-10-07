# maccyplus-clipboard

Lets Claude Code hand you values through your [MaccyPlus](https://github.com/roypadina/maccyplus)
clipboard history instead of a bare `pbcopy`. Each value carries a **label** (the session that
produced it) and a **note** (what it is, where to run it).

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install maccyplus-clipboard@padina
```

## The problem

You run several Claude sessions at once, plus your own work. Each one prepares a SQL query or a
command and "copies it to your clipboard". By the time you get to it, you can't tell which value came
from which session. Worse, each `pbcopy` overwrites what you were copying.

## What it does

The skill teaches Claude the `MaccyPlus history` CLI (MaccyPlus 2.8.0+):

- **Leave a value**: added to the top of history without touching your live clipboard, labelled
  with the session name and a note like `DataGrip → prod (read-only)` or `run in pane: ~/repo`.
- **Read history**: list, filter by label, search, get full text.
- **Manage items**: pin and unpin, move to the top, copy to the live clipboard, edit the label or
  note, delete.

In MaccyPlus the label shows as a chip on the row and the note shows on hover and in the preview.
Type a session name in the popup search to see only its values.

| Feature | Mechanism | File |
|---|---|---|
| When and how to leave values, label/note conventions, full command reference | skill | `skills/maccyplus-clipboard/SKILL.md` |

No hooks, no agents, no MCP server.

## Requirements

- macOS with MaccyPlus **2.8.0+**, running: `brew install --cask roypadina/tap/maccyplus`
- Optional: [agentctl](https://github.com/roypadina/agentctl) for readable session-name labels;
  without it the label is `<folder>·<session id prefix>`.

## Privacy

The CLI can read your whole clipboard history, like any process running as you could already
(`pbpaste`, the app's database). Claude Code's Bash permission is the gate. The skill tells Claude
to read history only for the task at hand, never to store secrets, and never to change items it
did not add.

## More

- [Wiki page](https://github.com/roypadina/padina-claude-code-plugins/wiki/maccyplus-clipboard)
- MaccyPlus side: [Agent clipboard API](https://github.com/roypadina/maccyplus/wiki/Agent-clipboard-API)
