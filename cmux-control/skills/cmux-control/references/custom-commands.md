# cmux.json — Custom Commands and Workspace Layouts

`cmux.json` defines reusable actions, commands and workspace layouts. They show up in the Command
Palette, the surface tab bar, and the keyboard-shortcut system.

## File Locations (priority order)

1. `./.cmux/cmux.json` — project-local (highest)
2. `./cmux.json` — project-local fallback
3. `~/.config/cmux/cmux.json` — global

Local actions/commands with a matching `id` or `name` override the global ones.

```bash
cmux config path         # every location cmux reads, including the legacy ones
cmux config check
cmux config validate
cmux reload-config       # reloads cmux.json AND ~/.config/ghostty/config, live
```

**Back up before editing** — cmux's own help says so, and it is the difference between a typo and a
lost config:

```bash
cp ~/.config/cmux/cmux.json ~/.config/cmux/cmux.json.$(date +%Y%m%d-%H%M%S).bak
```

## Two registries

### 1. `actions` — one command, bound to a palette entry and optionally a key

```jsonc
{
  "actions": {
    "agent-here": {
      "type": "command",
      "title": "Agent in a new tab",
      "command": "claude",
      "target": "newTabInCurrentPane",
      "keywords": ["agent", "claude"],
      "icon": { "type": "emoji", "value": "🤖" }
    }
  }
}
```

`target` accepts **`currentTerminal` or `newTabInCurrentPane` only.** Anything else
(`newWorkspace`, `newSplitRight`, `newSplitDown`, `currentSurface`) is silently invalid: the action
simply never appears in the Command Palette, and `config validate` will not catch it — the actions
schema is `additionalProperties: true`, so field typos pass validation.

Action `type` values:

| type | Meaning |
|---|---|
| `builtin` | A built-in cmux action |
| `command` | A shell command in a terminal |
| `agent` | A CLI agent in a new terminal tab |
| `workspaceCommand` | Runs a named `commands` entry, via `"commandName": "<name>"` |
| `workspace` | An inline workspace definition — the way to make an action open a **new** workspace |

```jsonc
"agent-workspace": {
  "type": "workspace",
  "title": "New workspace: agent",
  "icon": { "type": "emoji", "value": "🤖" },
  "workspace": {
    "name": "Agent",
    "layout": { "pane": { "surfaces": [
      { "type": "terminal", "command": "claude", "focus": true }
    ] } }
  }
}
```

- The root of `layout` may be a bare `pane` leaf for a single-pane workspace.
- `workspace` actions appear in the plus-button right-click menu; `"newWorkspaceMenu": false` hides one.
- `ui.newWorkspace.action: "<action-id>"` makes plain New Workspace (⌘N, plus button) run that action.
- `restart`: `new` (default) | `ignore` | `recreate` | `confirm` — what happens when a workspace of
  the same name already exists.
- Other fields: `subtitle`/`description`, `keywords`, `palette` (default true; false hides it from
  the Command Palette), `confirm`.

### 2. `commands` — multi-pane workspace recipes

```json
{
  "commands": [
    {
      "name": "Web Dev",
      "keywords": ["web", "dev"],
      "workspace": {
        "name": "Web Dev",
        "cwd": "~/code/web",
        "layout": {
          "direction": "horizontal",
          "split": 0.5,
          "children": [
            { "pane": { "surfaces": [
              { "type": "terminal", "name": "Next.js", "command": "npm run dev", "focus": true }
            ] } },
            { "pane": { "surfaces": [
              { "type": "browser", "name": "Preview", "url": "http://localhost:3000" }
            ] } }
          ]
        }
      }
    }
  ]
}
```

`layout` is recursive: every node is either a `pane` leaf or a `direction` + `children` split.

Pane surface fields: `type` (`terminal` | `browser`), `name` (tab title), `command` (terminal only),
`url` (browser only), `focus` (bool, the initially focused surface), `cwd` (per-surface override).

### The same shape, programmatically

```bash
cmux workspace create --name "Web Dev" --cwd ~/code/web --layout '{
  "direction":"horizontal","split":0.5,
  "children":[
    {"pane":{"surfaces":[{"type":"terminal","command":"npm run dev","focus":true}]}},
    {"pane":{"surfaces":[{"type":"browser","url":"http://localhost:3000"}]}}
  ]
}'
```

## Keyboard shortcuts for a custom layout

**An inline `"shortcut"` on a custom `actions` entry does not fire after `reload-config`.**
`config validate` accepts it and the action loads into the palette, but the key is dead. It may only
register on a full app restart (⌘Q and relaunch) — `reload-config` refreshes the palette but appears
not to rebuild the live keymap. Try a restart before concluding it is unsupported.

The top-level `shortcuts.bindings` map is **not** an escape hatch: its schema is
`"propertyNames": { "enum": [ …~50 built-in ids… ] }`, so only built-in action ids
(`openSettings`, `commandPalette`, …) are valid keys — a custom action id is rejected. Neither
`cmux shortcuts` nor `cmux settings shortcuts` lists custom bindings (the latter just prints
`OK target=keyboardShortcuts` and opens the UI), so the CLI cannot confirm one either way.

**What reliably works — two layers:**

1. **Command Palette, no key.** An `actions` entry of `type: "command"` whose `command` runs a
   **script on PATH**. A script rather than a shell function, so non-interactive callers can reach it
   too. It shows under ⌘⇧P.
   ```jsonc
   "project-session": {
     "type": "command",
     "title": "Project session",
     "command": "project-session && exit",
     "target": "newTabInCurrentPane",
     "keywords": ["project"],
     "icon": { "type": "emoji", "value": "🖥️" }
   }
   ```
   The `&& exit` closes the launcher tab once the script has done its work.

2. **A global hotkey**, via an external hotkey daemon bound to the same script. It fires even when
   cmux is not focused, and its event tap intercepts before cmux, so there is no double-trigger.
   The script must resolve the cmux CLI itself — it is not on PATH for a launchd-spawned process:
   ```bash
   CMUX="$(command -v cmux || true)"
   [ -z "$CMUX" ] && CMUX=/Applications/cmux.app/Contents/Resources/bin/cmux
   ```

   **macOS Secure Keyboard Entry silently kills event-tap hotkey daemons.** If a global hotkey does
   nothing, check the daemon's error log for a line like
   `secure keyboard entry is enabled by (NNN) 'AppName'! abort..` — password managers and Terminal's
   own "Secure Keyboard Entry" menu item enable system-wide secure input, which blocks the event tap
   from seeing **any** key and disables every binding at once. Fix: quit the offending app, or use a
   driver-level remapper (Karabiner-Elements), which is immune. A focused app still receives its own
   keys, so an in-app cmux keybind would be unaffected — but see the limitation above.

## Building a layout in place, without a new workspace

`--layout` always creates a new workspace. To rearrange the caller's own pane, build it imperatively
from `$CMUX_SURFACE_ID`:

```bash
S2=$(cmux --json new-split right --surface "$CMUX_SURFACE_ID" | grep -oE 'surface:[0-9]+')
S3=$(cmux --json new-split down  --surface "$S2"              | grep -oE 'surface:[0-9]+')
cmux send --surface "$S2" "npm run dev\n"          # \n is Enter, \t is Tab
cmux resize-pane --pane "$CMUX_PANE" -R --amount 10   # new-split has no ratio flag; it is ~50/50
exec htop                                          # the caller's own pane becomes the first pane
```

An action with `target: "currentTerminal"` runs such a script in the focused pane;
`newTabInCurrentPane` adds a tab instead. When `$CMUX_SURFACE_ID` is unset, fall back to
`workspace create --layout`.

## Pitfalls

- **`list-panes` / `list-pane-surfaces` prefix the focused row with a literal `* `**
  (`* pane:24 …`). A naive `awk '{print $1}'` grabs the `*` and you get
  `Error: Invalid surface handle: *`. Parse with `grep -oE 'pane:[0-9]+'` / `grep -oE 'surface:[0-9]+'`.
- **Trailing commas are invalid JSON.** `cmux config validate` catches those (but not field typos).
- **Shortcut conflicts.** `cmd+shift+c` and friends may already be bound; see `cmux docs shortcuts`.
- **`cwd` is resolved at workspace creation**, from the cmux app's cwd — not your shell's. Use
  absolute paths or `~/`.
- **Confirm an arrangement without side effects**: spawn a throwaway workspace with the same split
  shape but `echo` commands, check `cmux list-panes --workspace <ws>` (3 panes ⇒ correct), then close
  it. `cmux tree --all --json` shows refs and names but **no geometry** — use it to confirm wiring,
  and a screenshot for pixel sizes.
