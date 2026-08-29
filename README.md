# Claude Code plugins

Plugins for [Claude Code](https://claude.com/claude-code), by Roy Padina.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
```

## Plugins

### [`agentctl-sessions`](agentctl-sessions)

Gives a Claude session a memory of itself: a real name, labels, notes, flags, a done state,
reminders and due dates — all shown in [`agentctl`](https://github.com/roypadina/agentctl)'s session
picker so you can find any past session again.

```
/plugin install agentctl-sessions@padina
```

Claude does most of it without being asked — names the session once the task is clear, labels it
with the issue key from your branch — and handles plain requests like "mark this done", "remind me
in 2h", or "what do I need to get back to?".

Requires the `agentctl` CLI (`brew install --cask roypadina/tap/agentctl`), **0.5.0 or newer** for
labels and due dates. The plugin offers to install it if it is missing.

## License

MIT © Roy Padina
