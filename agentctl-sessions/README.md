# agentctl-sessions

Gives a Claude Code session a memory of itself — a real name, labels, notes, flags, a done state,
reminders and due dates — so you can find it again among the hundreds you have.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install agentctl-sessions@padina
```

**Requires** the [`agentctl`](https://github.com/roypadina/agentctl) CLI, **0.5.0 or newer** for
labels and due dates:

```
brew install --cask roypadina/tap/agentctl
```

The plugin checks for it and offers to install it rather than failing quietly.

## The problem

Claude Code names a session after your first prompt — `Run the shell command 'sleep 20' in the
back…` — and records nothing else. A month in you have hundreds of them and no way to find the one
where you fixed that billing bug.

## What Claude does on its own

- **Names the session** once your first task is clear — a short name describing the work. Once,
  quietly, without asking.
- **Labels it with the ticket.** If your branch is `feature/RD-12345-fix-thing`, the session gets
  labelled `RD-12345`. Every session on that ticket is then one search away.
- **Leaves a note before a long pause**, so a resumed session tells you where you left off.

It will *not* mark a session done, set reminders or due dates, hide a session, or delete one on its
own — those are your judgement calls, and it never deletes anything you did not ask it to.

### Hiding and deleting

Both are listing preferences kept by `agentctl`. **Neither touches the Claude Code transcript** or
removes anything from `~/.claude` — a hidden or deleted session still resumes normally if you
address it by id.

- **Hidden** — out of the default list, still under `agentctl ls --hidden` (`v` cycles views in the
  TUI, and the GUI has a view menu). For sessions you want out of the way.
- **Deleted** — out of every list except `agentctl ls --deleted`. `agentctl delete --undo` restores
  it.

## What you can just ask for

> "name this session billing spike" · "mark this done" · "remind me in 2 hours" · "this is due
> Friday" · "tag this with RD-123" · "flag this to come back to" · "what do I need to get back to?"

Or use the slash commands directly:

| Command | Does |
|---|---|
| `/agentctl-name [name]` | Name it (no name → Claude suggests one) |
| `/agentctl-note [text]` | Attach a note (no text → Claude summarises where things stand) |
| `/agentctl-label <label>` | Ticket, repo, topic. No argument → reads the issue key from your branch |
| `/agentctl-flag <flag>` | `todo`, `later`, `blocked`… (`-flag` removes) |
| `/agentctl-remind <when>` | `2h`, `30m`, `tomorrow 9am`, `17:00`, ISO |
| `/agentctl-due <when>` | When the work is actually due |
| `/agentctl-done` | Finished (`--undo` reopens) |
| `/agentctl-hide` | Out of the default list, still under `--hidden` |
| `/agentctl-delete` | Out of every list — recoverable, transcript untouched |

## The hook

One `SessionStart` hook, running `agentctl hook session-start`. On a **named** session it hands
Claude the name, labels, note and due state, so a resumed session knows what it is and what is
overdue. On an **unnamed** one it asks Claude to name it once your first task is clear, and points
out any issue key it found in your branch. It also mentions reminders that came due elsewhere.

It runs once per session start and prints a handful of lines. If `agentctl` is not installed the
hook is skipped entirely — no error, no noise.

## Where the data lives

`~/.config/agentctl/annotations/<session-id>.json` — one small file per session, written atomically,
deliberately **outside `~/.claude`** so nothing here can corrupt a transcript.

Renaming goes through `agentctl` rather than the transcript on purpose: Claude Code re-flushes its
own cached title after almost every turn, so a rename written into the JSONL by an outside tool is
silently reverted on a live session.

## Layout

```
.claude-plugin/plugin.json
commands/agentctl-*.md            seven slash commands
hooks/hooks.json                  the SessionStart hook
skills/agentctl-sessions/SKILL.md the full toolset, for Claude
```

## License

MIT © Roy Padina
