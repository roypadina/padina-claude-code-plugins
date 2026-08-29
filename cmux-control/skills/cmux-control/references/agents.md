# Running Agents Inside cmux

Three ways to put a coding agent in a cmux pane, from lowest to highest level.

## Level 1 — Raw: split + send

Full control, works for any CLI tool.

```bash
# Identify the caller. `.caller` is this shell; `.focused` is whatever the user is
# looking at, and the two are frequently different — you want `.caller`.
WS=$(cmux identify --json | jq -r .caller.workspace_ref)

NEW=$(cmux --json new-split right --workspace "$WS" | jq -r '.surface_ref // .surface')

# Or a new tab in the current pane:
# NEW=$(cmux --json new-surface --type terminal | jq -r '.surface_ref // .surface')

cmux send     --workspace "$WS" --surface "$NEW" "claude"
cmux send-key --workspace "$WS" --surface "$NEW" enter
```

**Always pass `--workspace` when the surface lives outside the caller's workspace** — otherwise the
ref is resolved in the caller's workspace and you get `invalid_params: Surface is not a terminal`.

Swap the binary for another agent: `claude`, `codex`, `opencode`, `gemini`, `aider`, `grok` — or any
shell command.

### Read agent output

```bash
cmux read-screen --workspace "$WS" --surface "$NEW" --lines 200
cmux read-screen --workspace "$WS" --surface "$NEW" --scrollback --lines 2000
```

### Send a follow-up prompt mid-session

```bash
cmux send --workspace "$WS" --surface "$NEW" "now add tests for foo\n"
```

`\n` (or `\r`) inside the string is Enter and `\t` is Tab, so one `send` is usually enough — no
separate `send-key` needed.

### Wait for the agent to idle

Poll `read-screen`, or stream events:

```bash
cmux events --no-heartbeat --category notifications --reconnect | while read -r line; do
    case "$line" in
        *agent.idle*) echo "agent ready"; break ;;
    esac
done
```

## Level 2 — Single-shot: a workspace with the command baked in

```bash
cmux workspace create \
    --name "claude: ticket-1234" \
    --cwd ~/Code/foo \
    --command "claude" \
    --description "investigating the null pointer in checkout" \
    --focus true
```

`--layout <json>` takes the same shape as the `workspace.layout` key in `cmux.json`, for multi-pane
templates. See `custom-commands.md`.

## Level 3 — Native multi-agent: teammate launchers

cmux ships launchers that intercept tmux calls and turn agent teammates into cmux splits with
sidebar metadata and notifications.

| Launcher | Purpose |
|---|---|
| `cmux claude-teams [claude-args…]` | Claude Code with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; workers appear as cmux splits |
| `cmux codex-teams [args…]` | Codex with subagent panes |
| `cmux omc [args…]` | Oh My Claude Code |
| `cmux omx [args…]` | Oh My Codex |
| `cmux omo [args…]` | Oh My OpenCode |

```bash
cmux claude-teams --continue --model sonnet
cmux omc team 3:claude "implement feature"
cmux omc --watch
```

Mechanism: a fake tmux shim at `~/.cmuxterm/<launcher>-bin/tmux` redirects tmux commands to the cmux
socket API. PATH is prepended with the shim dir, and `TMUX` / `TMUX_PANE` are set so the agent
believes it is inside tmux.

## Agent-session surfaces

cmux 0.64 can host an agent as a **native surface** rather than a terminal:

```bash
cmux new-surface --type agent-session --provider claude --renderer solid --focus true
```

`--provider codex|claude|opencode`, `--renderer react|solid`.

## Hooks — agent → sidebar feed

```bash
cmux hooks setup                        # install for every supported agent on PATH
cmux hooks setup --agent codex
cmux hooks opencode install --project   # project-local opencode plugin
cmux hooks feed --source codex          # convert hook events into Feed entries
cmux hooks uninstall
```

**Claude Code is not one of the agents `cmux hooks` manages** — from `cmux hooks --help`, "Claude
Code hooks are injected automatically by the cmux Claude wrapper". The managed agents are `codex`,
`grok`, `opencode`, `pi`, `omp`, `campfire`, `amp`, `cursor`, `gemini`, `kiro`, `antigravity`
(alias `agy`), `rovodev` (alias `rovo`), `hermes-agent`, `copilot`, `codebuddy`, `factory`, `qoder`.

## Grid of agents

Four agents side by side, for comparing answers.

```bash
WS=$(cmux workspace create --name "agent-bake-off" --cwd "$(pwd)" | awk '/^OK /{print $2}')

S1=$(cmux --json list-pane-surfaces --workspace "$WS" | jq -r '.surfaces[0].ref')
S2=$(cmux --json new-split right --workspace "$WS" --surface "$S1" | jq -r .surface_ref)
S3=$(cmux --json new-split down  --workspace "$WS" --surface "$S1" | jq -r .surface_ref)
S4=$(cmux --json new-split down  --workspace "$WS" --surface "$S2" | jq -r .surface_ref)

for pair in "$S1:claude" "$S2:codex" "$S3:opencode" "$S4:gemini"; do
    surf="${pair%:*}"; agent="${pair#*:}"
    cmux send --workspace "$WS" --surface "$surf" "$agent\n"
done
```

Note there is **no `focus-surface`**: give `new-split` the source surface with `--surface` instead of
trying to focus one first. (`cmux focus-surface` → `Error: Unknown command 'focus-surface'.`)

## Tips

- Pass `--focus false` / `--no-focus` for background workers so the user's pane keeps focus.
- `cmux set-status <your-key> running --icon hammer --color "#3b82f6"` surfaces live state; clear it
  when done. **Never use the key `claude_code`** — cmux's own wrapper owns it.
- `cmux trigger-flash --surface "$NEW"` flashes a pane when long work finishes, even without a notify.
- `cmux events --category notifications` lets you wait on agent notifications instead of polling.
- `cmux diff --last-turn` shows what an agent changed since its last turn baseline.
- Before using `--dangerously-skip-permissions` (or `--permission-mode bypassPermissions`) for a
  repo, confirm the user is happy with that mode. Do not add it on your own initiative.
