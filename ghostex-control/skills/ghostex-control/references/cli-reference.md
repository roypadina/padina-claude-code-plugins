# Ghostex CLI reference

Every command in `ghostex --help` of Ghostex 10.40.0, grouped, with a risk class. `gx` is the same
binary. `ghostex <command> --help` prints that command's usage and runs nothing (help gate in
`server/src/ghostex_cli/mod.rs`); the commands with their own help pages are listed at the end.

Risk: **R** read-only · **W** changes Ghostex state, not the window · **UI** acts on the visible app
(focus, open, switch) · **X** closes, deletes or kills · **N** network, account or install side
effects. Only **R** runs without a reason; **UI**, **X** and **N** need the user's request.

`<sel>` = selector: global ref (`S…:P…:G…`, preferred), session id, zmx name, agent session id,
`project:title`, title (exact, then case-insensitive substring) or a numeric alias from the last
printed `gx sessions` list.

## Sessions: list, find, lifecycle

| Command | Risk | Notes |
|---|---|---|
| `sessions \| s \| ls [--ungrouped\|-u] [--json [--full]] [--mobile-summary]` | R | `--json` → `{ok, sessions[]}`: `globalRef,title,status,projectId,projectName,projectPath,agentName,agentSessionId,zmxName`. The human list also rewrites the numeric alias cache |
| `state \| dump-state` | R | Sidebar state JSON: `projects`, `sessions`, `product` |
| `session-groups [--project-id id] [--json]` | R | `groups[] {groupId,projectId,title,sessionIds}` |
| `previous-sessions [--query t] [--limit n] [--cursor c] [--project-id id] [--json]` | R | Closed sessions, newest first |
| `create-session [title] [--input text] [--start] [--project-id id] [--group-id id] [--cwd path]` | W | Terminal session. `--input` runs once, after `.zshrc`, from the first precmd. `--start` makes the pty live. Result `{ok, session{projectId,sessionId,…}, provider}` |
| `terminal \| t [--cwd path] [--title t] [-- command...]` | W | Quick terminal record, **not started**; registers a project for an unknown `--cwd` |
| `create-agent <agentId> --project-id id [--group-id id] [--model m] [--effort e] [--first-input-draft t] [--run-on loc] [--defer-start] [--replace-empty-sessions] [--allow-hidden]` | W | Agent session with a per-session model/effort |
| `run-agent <agentId> [--allow-hidden]` | UI | Clicks a configured agent button |
| `rename-session <sessionId> <title> [--json]` | W | Sidebar title |
| `rename-command <sel> <title>` | W | The agent's own rename command; wakes a sleeping session to deliver it |
| `tag-session <id> <tag\|none>` | W | One tag per session |
| `session-note read\|save --session-id id [--project-id id] [--note t] [--json]` | R / W | Note on the agent conversation |
| `sleep <sel\|all> [--json]`, `wake <sel\|all> [--json]` | W | Never `all` |
| `sleep-session\|pin-session <id> [true\|false]`, `park-session <sel> [true\|false] --json` | W | Raw flags |
| `kill \| k <sel\|all> [--json]` | X | Ends the process and any unfinished agent turn. Never `all` |
| `close-session\|restart-session\|fork-session\|reload-session <id>` | X / W | Lifecycle by raw id |
| `restore-previous-session --project-id id --session-id id [--json]` | W | Brings a closed session back as a new one |
| `close-after-done <id>` | W | Toggle: close the pane when its command exits |
| `delayed-send <id> (--delay-ms n \| --when-agent-finishes \| --when-all-agents-finish) \| --cancel` | W | Arms an Enter trigger |
| `acknowledge-session-attention <sel>` | W | Marks the attention event seen |
| `export-transcript <sel> [--project-id id] [--json]` | R | Writes a Markdown file, prints its path |

## Session groups

| Command | Risk | Notes |
|---|---|---|
| `create-session-group --project-id id [--title t] [--json]` | W | Prints the group id |
| `rename-session-group --project-id id --group-id id --title t [--json]` | W | |
| `delete-session-group --project-id id --group-id id [--json]` | X | Closes every session in it |
| `move-session-to-group <sel> --group-id id [--json]`, `remove-session-from-group <sel> [--json]` | W | |
| `focus-group <groupId>` | UI | |

Group edits go through the running app (Ghostex 10.36+).

## Input and output

| Command | Risk | Notes |
|---|---|---|
| `send-text <sel> <text>` | W | Types, no Enter, never signed |
| `send-enter <sel>`, `send-key <sel> <key>` | W | Keys: `enter`, `ctrl-c`, `escape`, `tab`, arrows |
| `send-message \| message \| msg <sel> <text>` | W | Text + Enter. From an agent session it appends a sender block; an unmatched first argument is taken as an agent id |
| `read-text \| read-messages \| read-thread <sel> [--lines n] [--visible] [--json]` | R | Terminal text |
| `wait-for-text <sel> <regex> [--timeout-seconds n] [--interval-seconds n] [--lines n] [--json]` | R | Exit 1 on timeout or dead session |
| `run-in-terminal --project-id id [--session-id id\|--cwd path] [--paste] [--json] (--command t \| -- cmd...)` | W | Runs in the project's Commands panel terminal, not in a session; `--paste` types without Enter |

## Session chat (agent sessions)

| Command | Risk | Notes |
|---|---|---|
| `read-session-chat <sel> [--last n] [--all] [--grep t] [--role r] [--context n] [--since d] [--until d] [--format text\|json] [--history-mode turns\|detail] [--subagent s] [--wait-ms n --fingerprint f]` | R | Conversation, not screen. Does not wake a sleeping session |
| `read-session-chat-queue <sel> --json`, `read-session-chat-skills`, `read-session-chat-files`, `read-session-files-links`, `read-session-details <sel> [--refresh] --json` | R | |
| `send-session-chat-message <sel> <text>` | W | Signed from an agent session |
| `queue-session-chat-prompt <sel> <text>` and the `update-/remove-/reorder-/send-session-chat-queued-prompt` family | W | The prompt queue |
| `answer-session-chat-prompt <sel> --answer-json json` | W | Answers a pending question or approval: only when the user decided the answer |
| `interrupt-session-chat <sel>` | W | Agent-aware interrupt |
| `rewind-session-chat <sel> --message-id uuid --json` | X | Drops the conversation after that prompt |
| `select-session-chat-model <sel> [--model m --effort e] [--scope session\|default] [--mode m] [--fast-mode on\|off] [--permissions …] [--defer] --json` | W | `--scope default` changes the agent's default |
| `handoff-session-chat-draft <sel>`, `set-session-chat-draft …`, `send-session-chat-key …`, `switch-draft-agent …` | W | Composer draft |
| `search-agent-prompts [--query t] [--agents a,b] [--project p] [--limit n] --json`, `read-agent-prompt-text --key k --json` | R | Every prompt sent from this machine |
| `toggle-agent-prompt-favorite`, `resolve-agent-prompt-launch` | W / R | |
| `session-chat-rpc <method> --params-base64 b64` | W | Remote chat clients |

## Agents and coordinators (own help pages)

| Command | Risk | Notes |
|---|---|---|
| `agents whoami [--json]` | R | The calling session, from the environment |
| `agents types [--json]`, `agents list [--all] [--json]` | R | |
| `agents create <agentId> [--title t] [--project-id id] [--task t \| --body-file p] [--allow-hidden] [--standalone]` | W | Returns `globalRef` |
| `agents send <ref> <text> \| --body-file p [--interrupt \| --queue] [--request-id id]` | W | Signed; delivery states `delivered/accepted/pending/queued` |
| `agents close <ref>` | X | |
| `agents switch-account <ref> --account n\|email [--force] [--json]`, `agents reload <ref> [--json]` | X | `--force` and `reload` lose the current turn |
| `accounts [--all] [--refresh] [--json]` | R | Claude and Codex accounts, usage, resets |
| `coordinator create\|promote\|list\|status\|start-thread\|link\|unlink\|rename-self\|rename\|resolve\|reopen\|…` | W | See `ghostex coordinator --help` and the ghostex-orchestrator skill |

## Projects and workspaces

| Command | Risk | Notes |
|---|---|---|
| `switch-project (--project-id\|--path\|--name) v` | UI | |
| `add-project <path> [--name n] [--create-if-missing] [--workspace w]` | W | Net-new sidebar project |
| `remove-project (--project-id\|--path\|--name) v` | X | Deletes session records; close sessions first |
| `move-project`, `group-project`, `restore-recent-project` | W | |
| `workspace list \| create \| rename \| move-project \| delete` | R / W / X | |
| `clone-repository <url> <dest> [--workspace w] --json` | N | Clones and registers |
| `browse-directories`, `discover-source-control --json`, `lookup-repository … --json` | R | |
| `read-sidebar-project-collections --json`, `read-sidebar-spaces --json`, `read-custom-session-tags --json` | R | The `update-*` counterparts replace the whole state: avoid |

## Files, UI, notifications

| Command | Risk | Notes |
|---|---|---|
| `open \| o <path...>`, `ghostex <path>` | UI | Opens in Ghostex |
| `edit \| e [--wait] [--goto] <file...>` | UI | Embedded Code view; `--goto file:line` |
| `focus <sel> [--json]`, `focus --agent-session-id id --agent a --if-running`, `focus-session <id\|--index n>` | UI | |
| `attach \| a \| resume \| r [sel]` | UI | Attaches the current terminal to the session |
| `floating-editor \| fe -- <editor> [args]`, `floating-monaco-editor \| fme <file>`, `toggle-sidebar` | UI | |
| `notify --title t [--body b] [--session-id id]` | W | Bell row; defaults to the calling session |
| `show <file.html> [--title t] [--json] [--no-check]`, `visual check …` | W / R | Chat cards: the ghostex-visuals skill |
| `screenshot [out.png]`, `bundle [dir]` | R | Capture the Ghostex window |
| `logs [--file f] [--lines n] [--grep t] [--json]` | R | |

## Settings, extensions, server, setup

| Command | Risk | Notes |
|---|---|---|
| `guide [overview\|features\|settings\|hotkeys]` | R | The built-in manual |
| `settings list [--json] [--writable] [--tab id]`, `settings get <key> [--json]` | R | |
| `settings set\|reset <key> …`, `settings hotkeys set\|reset …` | W | Through the running app; only on request |
| `settings open [<key>]` | UI | |
| `extensions list\|catalog [--json]`, `extensions state <id> [--json]` | R | |
| `extensions install\|install-local\|uninstall <id>`, `extensions state <id> --set k=v` | N / W | |
| `server status [--json]`, `server version`, `ports [--json]`, `resources [--json]` | R | |
| `server start`, `server stop` | W | Control plane only |
| `server stop-all` | X | Kills every tracked session |
| `server endpoint` | R | Prints the auth token: never in a transcript |
| `agent-sync status\|plan [--json]` | R | `apply` rewrites agent folders |
| `agent-cli status`, `app-update status\|check`, `tailcat status`, `android-check` | R | Their install/enable verbs are **N** |
| `account-login`, `app-update install\|auto`, `agent-cli install\|update`, `tailcat enable\|disable` | N | |

## Automations, actions, board, issues, team

Help pages: `ghostex automations --help`, `ghostex quick-actions --help`. Read verbs
(`automation-state`, `issues status`, `board` reads, `team status`) are **R**; saving, running,
deleting, posting to Slack, creating tickets and `team deploy` are **W/N**. Route to the
ghostex-cli and ghostex-manage-beads skills.

## Commands with their own help page

`account-login accounts agent-cli agentbox agents app-update claude-cloud coordinator orchestrator
automations bd beads board browser browser-use computer-use spaceo cli editor-daemon extensions
feedback find f agents-orchestration generate-title guide manage-beads notify visual history h
move-codex-session paired-device-seen ports resources quick-actions previous-sessions
restore-previous-session saved-prompts session-chat-rpc server settings tailcat voice web`

For these, `--help` is handled by the command itself, not by the global gate. Pass a bare
`<command> --help`, never `--help` mixed into a real invocation.

## Global flags

`--port <n>`, `--timeout <ms>`, `--token-stdin` (temporary remote token from stdin). Never use
`--token <t>`: argv is visible to other processes.
