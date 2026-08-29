# cmux CLI Reference

Snapshot of **cmux 0.64.22**, taken from `cmux --help` and `cmux <command> --help`. Those are the
authority — re-run them when something looks missing. Upstream contract:
<https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/cli-contract.md>

## Global Invocation

```
cmux <path>                                 # open a directory in cmux (launches the app if needed)
cmux [global-options] <command> [options]
```

### Global options (before the command)

| Flag | Purpose |
|---|---|
| `--socket <path>` | Override the Unix socket path |
| `--password <value>` | Explicit socket password (beats the env var and the saved one) |
| `--window <id\|ref\|index>` | Route through a specific window |

### Presentation options

| Flag | Purpose |
|---|---|
| `--json` | JSON output where supported |
| `--id-format <refs\|uuids\|both>` | Handle style in output (default `refs`) |

### Handle inputs

Any window/workspace/pane/surface/tab flag takes a UUID, a short ref (`window:1`, `workspace:2`,
`pane:3`, `surface:4`, `tab:5`), or a numeric index. `tab-action` and `rename-tab` also accept
`tab:<n>`.

### Environment

| Var | Effect |
|---|---|
| `CMUX_WORKSPACE_ID` | Default `--workspace` inside cmux terminals |
| `CMUX_SURFACE_ID` | Default `--surface` |
| `CMUX_TAB_ID` | Default `--tab` for the tab commands |
| `CMUX_SOCKET_PATH` / `CMUX_SOCKET` | Socket path |
| `CMUX_SOCKET_PASSWORD` | Socket password fallback |
| `CMUX_QUIET` | Silences the legacy-alias deprecation notices on stderr |

## Top-Level Commands

### Discovery / meta
| Command | Notes |
|---|---|
| `ping` | Socket connectivity check |
| `version` | Print version |
| `capabilities [--json]` | List every socket method |
| `identify [--json] [--no-caller]` | Returns `.caller` (this shell) **and** `.focused` (what the user is looking at) — often different |
| `tree [--all]` | Window/workspace/pane/surface tree |
| `top [--all] [--processes] [--sort cpu\|mem\|proc] [--flat] [--format tree\|tsv]` | Process / resource usage |
| `memory [--all] [--groups <n>]` | Memory grouped by process |
| `events [--after <seq>] [--cursor-file <path>] [--name <event>] [--category <category>] [--reconnect] [--limit <n>] [--no-ack] [--no-heartbeat]` | NDJSON event stream |
| `rpc <method> [json-params]` | Raw v2 RPC |
| `docs [settings\|shortcuts\|api\|browser\|agents\|dock\|sidebars]` | Docs URLs + raw GitHub resources |
| `welcome`, `help`, `feedback`, `feed tui\|clear`, `themes [list\|set\|clear]` | |
| `iroh-diag` | Peer-to-peer transport diagnostics |

### Auth
`auth <status|login|logout>`. Top-level `login` / `logout` are aliases.

### Windows
`list-windows`, `current-window`, `new-window`, `focus-window --window <id>`,
`close-window --window <id>`, `rename-window [--workspace …] <title>`,
`move-workspace-to-window --workspace <id> --window <id>`.

### Workspaces

**Canonical noun form** (legacy flat verbs still work, with a one-time stderr deprecation hint):

```
workspace list
workspace create [--name <title>] [--description <text>] [--cwd <path>] [--command <text>]
                 [--layout <json>] [--window …] [--focus <true|false>]
                 [--group <id|ref>] [--group-placement afterCurrent|top|end] [--group-reference <ws>]
workspace env [workspace] [--mask]        # the workspace's configured env vars
workspace close <workspace>
workspace rename <workspace> --title <new>
workspace select <workspace>
workspace status [set <lane|auto>]        # show or pin the workspace todo status
workspace reconnect [workspace]           # remote (SSH) workspaces
workspace disconnect [workspace]
workspace loading <on|off> [--id <name>]  # the sidebar loading spinner
workspace group <subcommand>              # see `cmux workspace-group --help`
```

Legacy aliases: `list-workspaces`, `new-workspace`, `close-workspace`, `rename-workspace`,
`select-workspace`. Also `reorder-workspace`, `reorder-workspaces`, `current-workspace`.

`workspace-action --action <name> [--title <text>] [--color <name|#hex>] [--description <text>]`
actions: `pin`, `unpin`, `rename`, `clear-name`, `set-description`, `clear-description`, `move-up`,
`move-down`, `move-top`, `close-others`, `close-above`, `close-below`, `mark-read`, `mark-unread`,
`set-color`, `clear-color`. Named colors: Red, Crimson, Orange, Amber, Olive, Green, Teal, Aqua,
Blue, Navy, Indigo, Purple, Magenta, Rose, Brown, Charcoal.

### Panes / surfaces
| Command | Notes |
|---|---|
| `list-panes [--workspace …]` | The split regions |
| `list-panels [--workspace …]` | **The surfaces.** There is no `list-surfaces` |
| `list-pane-surfaces [--pane …]` | Surfaces of one pane |
| `new-pane [--type terminal\|browser\|simulator] [--direction left\|right\|up\|down] [--url <url>] [--profile <name\|uuid>] [--focus …]` | |
| `new-split <left\|right\|up\|down> [--surface …] [--panel …] [--focus …]` | Splits ~50/50; no ratio flag |
| `new-surface [--type terminal\|browser\|simulator\|agent-session] [--placement workspace\|dock] [--pane …] [--url <url>] [--provider codex\|claude\|opencode] [--renderer react\|solid] [--working-directory <path>] [--focus …]` | `--placement dock` puts it in the right-sidebar Dock (terminal and browser only) |
| `focus-pane --pane <id>` | **There is no `focus-surface`** — focus the surface's pane |
| `focus-panel --panel <id>` | |
| `close-surface [--surface …]` | Its `OK <ref>` names the surface focused *after* the close |
| `move-surface --surface <id> [--pane …] [--before <id>] [--after <id>] [--index <n>]` | |
| `split-off --surface <id> <direction>` | |
| `reorder-surface --surface <id> (--index <n> \| --before <id> \| --after <id>)` | |
| `drag-surface-to-split --surface <id> <direction>` | |
| `move-tab-to-new-workspace [--tab …] [--title <text>]` | |
| `rename-tab [--tab …] <title>` | Alias for `tab-action rename` |
| `tab-action --action <name> [--tab …] [--title …] [--url …] [--focus …]` | |
| `surface resume <set\|show\|get\|clear>` | Relaunch metadata for restore |
| `refresh-surfaces`, `reload-config`, `surface-health`, `debug-terminals` | |
| `trigger-flash [--surface …]` | Visual attention flash |

`tab-action` actions: `rename`, `clear-name`, `close-left`, `close-right`, `close-others`,
`new-terminal-right`, `new-browser-right`, `move-to-new-workspace`, `reload`, `duplicate`, `pin`,
`unpin`, `mark-unread`, `toggle-full-width-tab`.

### Input / output
`send [--surface …] <text>` (no implicit Enter), `send-key [--surface …] <key>`,
`send-panel --panel <id> <text>`, `send-key-panel --panel <id> <key>`,
`read-screen [--surface …] [--scrollback] [--lines <n>]`, `capture-pane` (tmux alias),
`clear-history`.

### Notifications
`notify --title <text> [--subtitle <text>] [--body <text>] [--workspace …] [--surface …]`,
`list-notifications`, `dismiss-notification (--id <uuid> | --all-read)`,
`mark-notification-read (--id <uuid> | --workspace … | --all)`, `open-notification --id <uuid>`,
`jump-to-unread`, `clear-notifications`.

### Sidebar metadata (status / progress / log / todo)
| Command | Notes |
|---|---|
| `set-status <key> <value> [--icon <name>] [--color <#hex>] [--priority <n>]` | Pills in the sidebar tab row. **Use a unique key** — cmux's own Claude wrapper owns `claude_code` |
| `clear-status <key>` / `list-status` | |
| `set-progress <0.0-1.0> [--label <text>]` / `clear-progress` | Sidebar progress bar |
| `log <message> [--level <level>] [--source <name>]` / `clear-log` / `list-log [--limit <n>]` | |
| `todo <add\|list\|check\|uncheck\|start\|edit\|rm\|clear\|set\|open>` | Per-workspace checklist, capped at 50 items. **Belongs to the user** — see the guardrail in SKILL.md |
| `sidebar-state` | |
| `right-sidebar <toggle\|show\|hide\|focus\|set\|mode\|files\|find\|vault\|sessions\|feed\|dock>` | |
| `sidebar <validate\|reload\|select\|open> [name]` | Custom sidebars from `~/.config/cmux/sidebars` (beta) |

### Diff viewer
```
diff [patch-file|-] [--source unstaged|staged|branch|last-turn] [--unstaged|--staged|--branch|--last-turn]
     [--cwd|--repo <path>] [--base <ref>] [--session <id>] [--title <text>]
     [--layout split|unified] [--font-size <points>] [--focus <true|false>]
```
Renders a unified diff in a browser split. Reads piped stdin with no argument (`git diff | cmux diff`).
`--last-turn` diffs against the surface's last agent-turn baseline.

### Agent / hook integrations
| Command | Notes |
|---|---|
| `claude-teams [args…]` | Claude Code with cmux-managed teammates as splits |
| `codex-teams [args…]` | Codex with subagent panes |
| `omc` / `omx` / `omo` | Oh My Claude Code / Codex / OpenCode |
| `hooks setup\|uninstall [agent] [--agent <name>] [--yes]` | |
| `hooks <agent> install\|uninstall\|<event>` | |
| `hooks feed --source <agent> [--event <event>]` | Hook events → sidebar Feed |
| `agent-hibernation <on\|off>` | |

**Claude Code is not in the agent list** — "Claude Code hooks are injected automatically by the cmux
Claude wrapper". The agents `cmux hooks` manages are: `codex`, `grok`, `opencode`, `pi`, `omp`,
`campfire`, `amp`, `cursor`, `gemini`, `kiro`, `antigravity` (alias `agy`), `rovodev` (alias `rovo`),
`hermes-agent`, `copilot`, `codebuddy`, `factory`, `qoder`.

`claude-hook <event>` still exists as a compatibility entrypoint for Claude Code hook stdin events.

### Remote / cloud
| Command | Notes |
|---|---|
| `ssh <dest> [--transport ssh\|mosh] [--name …] [--command …] [--port <n>] [--identity <path>] [-A\|-a] [--ssh-option <opt>] [-- <remote-args>]` | SSH workspace |
| `mosh <dest> […]` | Same shape, mosh transport |
| `mosh-tmux <dest> [--session <name>] […]` / `ssh-tmux <dest> [--port <n>] [--identity <path>] [--new-window]` | Attach a remote tmux |
| `ssh-session-list` / `ssh-session-attach --session-id <id>` / `ssh-session-cleanup` | |
| `remote-daemon-status [--os darwin\|linux] [--arch arm64\|amd64]` | |
| `remotes <list\|add\|remove> [--route <host:port>] [--tag <tag>] [--json]` | alias `remote` |
| `vm <base\|new\|ls\|status\|snapshot\|fork\|restore\|rm\|exec\|shell\|ssh>` | alias `cloud` |
| `ai-accounts <list\|upload\|remove> [--team <id>] [--json]` | |

### Simulators / iOS
`simulator <subcommand> [--surface …]`, `ios <subcommand> [--surface …]`, plus
`new-pane --type simulator` / `new-surface --type simulator`.

### Restore
| Command | Notes |
|---|---|
| `restore-session` | Reopen the previous saved app session (File → Restore Previous Launch) |
| `restore <kind> <checkpoint-id>` / `restore --surface [id\|ref]` | Restore one checkpointed surface |
| `surface resume set\|show\|get\|clear` | Attach relaunch metadata so a restore knows what to run |

There is **no CLI command to reopen a single closed pane**. The GUI has it: History → Recently Closed
(Tab, Window, Workspace, and individual panels), File → Reopen Closed Browser Panel, and the Command
Palette entries "Restore Previous App Launch" / "Reopen Closed Browser Tab".

### Browser
See `browser.md`. Subcommand list from `cmux browser --help`:

```
disable | enable | status
open|open-split|new [url] [--profile <name|uuid>] [--focus <true|false>]
goto|navigate <url> [--snapshot-after]     back | forward | reload
url|get-url                                 focus-webview | is-webview-focused
snapshot [--interactive|-i] [--cursor] [--compact] [--max-depth <n>] [--selector <css>]
eval [--script <js> | <js>]
wait [--selector <css>] [--text <text>] [--url-contains <text>] [--load-state interactive|complete]
     [--function <js>] [--timeout-ms <ms>|--timeout <seconds>]
click|dblclick|hover|focus|check|uncheck|scroll-into-view [--selector <css>] [--snapshot-after]
type|fill [--selector <css>] [--text <text>]      press|key|keydown|keyup [--key <key>]
select [--selector <css>] [--value <value>]       scroll [--selector <css>] [--dx <n>] [--dy <n>]
screenshot [--out <path>]
get <url|title|text|html|value|attr|count|box|styles> [...]
is <visible|enabled|checked> [...]
find <role|text|label|placeholder|alt|title|testid|first|last|nth> [...]
frame <main|selector>     dialog <accept|dismiss> [text]
download [wait] [--path <path>] [--timeout-ms <ms>]
profiles <list|add|rename|clear|delete>   import [...]
cookies <get|set|clear>                   storage <local|session> <get|set|clear>
tab <new|list|switch|close|<index>>
console <list|clear>                      errors <list|clear>
highlight [--selector <css>]              state <save|load> <path>
addinitscript|addscript [--script <js>]   addstyle [--css <css>]
viewport <width> <height> | reset         geolocation|geo <lat> <lon>
offline <true|false>                      trace <start|stop> [path]
network <route|unroute|requests> ...      screencast <start|stop>
input <mouse|keyboard|touch> [args...]    identify [--surface ...]
```

### Settings / config
`settings [open [target] | path | docs | <target>]`,
`config <doctor|check|validate|path|paths|docs|documentation|reload>`, `shortcuts`,
`disable-browser` / `enable-browser` / `browser-status`, `reload-config`.

Note: `cmux shortcuts` returns a bare `OK`, not a list — use `cmux docs shortcuts` for the URLs.

### tmux compatibility
Lowest-priority surface; prefer the native commands. `capture-pane`, `resize-pane`, `pipe-pane`,
`wait-for`, `swap-pane`, `break-pane`, `join-pane`, `next-window`, `previous-window`, `last-window`,
`last-pane`, `find-window`, `clear-history`, `set-hook`, `set-buffer`, `paste-buffer`,
`list-buffers`, `respawn-pane`, `display-message`. `popup`, `bind-key`, `unbind-key`, `copy-mode`
resolve but are placeholders.

### Misc
`open <path-or-url>… [--workspace …] [--focus <true|false>]`, `markdown [open] <path>`,
`set-app-focus <active|inactive|clear>`, `simulate-app-active`,
`simulate-sidebar-drag --window <id> --from <ws> --to <ws>`.

## Socket API (raw v2)

`cmux rpc <method> [json-params]`, or write `{"id":"…","method":"…","params":{…}}\n` to the socket.

```bash
cmux capabilities --json | jq -r '.methods[]'
```

Method families: `system.*`, `app.*`, `auth.*`, `workspace.*`, `window.*`, `surface.*`, `pane.*`,
`notification.*`, `sidebar.*`, `browser.*`, `vm.*`, `ssh.*`.

## Event Stream

```bash
cmux events --no-heartbeat --limit 50
cmux events --reconnect --cursor-file /tmp/cmux.cursor --name surface.created
cmux events --category notifications
```

`--cursor-file` makes consumption resumable. Each line is
`{"seq":N,"name":"…","category":"…","data":{…}}`.
