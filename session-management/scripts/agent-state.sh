#!/usr/bin/env bash
#
# Lists this session's subagents and what each is doing right now, read from their transcripts
# (<config dir>/projects/*/<session id>/subagents/agent-<id>.jsonl + .meta.json):
#
#   <agent id> <name or -> <state> <age>s <tool: what it runs>
#
# state  in-tool   a tool call has no result yet — stopping now cuts that call
#        thinking  between tool calls — safe to stop
#        idle      its turn ended (a named agent waiting for a message)
#        finished  done (unnamed agents only; named ones stay idle)
# age  = seconds since its last transcript entry.
# shortcut: a run stopped mid-tool (TaskStop, crash) keeps showing in-tool with a growing age; the
# conversation says which ones were stopped.
#
#   scripts/agent-state.sh          # every agent not finished
#   scripts/agent-state.sh --all    # finished ones too
#
sid=${CLAUDE_CODE_SESSION_ID:-}
[ -n "$sid" ] || { echo "CLAUDE_CODE_SESSION_ID not set — unknown"; exit 0; }
command -v jq >/dev/null || { echo "jq not found — unknown"; exit 0; }
now=$(date +%s)
for f in "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/projects/*/"$sid"/subagents/agent-*.jsonl; do
    [ -f "$f" ] || continue
    m=${f%.jsonl}.meta.json
    fin=$(jq -r '.finished // false' "$m" 2>/dev/null || echo false)
    [ "$fin" = true ] && [ "${1:-}" != --all ] && continue
    id=$(basename "$f" .jsonl)
    jq -rs --arg id "${id#agent-}" --arg name "$(jq -r '.name // "-"' "$m" 2>/dev/null || echo -)" \
        --arg fin "$fin" --argjson now "$now" '
        def ts: (.timestamp // "") | sub("\\.[0-9]+Z$"; "Z") | (try fromdateiso8601 catch null);
        [ .[] | select(.type == "assistant" or .type == "user") ] as $e
        | [ $e[] | .message.content | arrays | .[] | select(.type == "tool_result") | .tool_use_id ] as $done
        | ([ $e[] | select(.type == "assistant") | .message.content | arrays | .[]
             | select(.type == "tool_use") ] | last) as $t
        | ($e | last) as $l
        | ([ $e[] | ts | numbers ] | last) as $at
        | (if $fin == "true" then "finished"
           elif $t != null and ($done | index($t.id)) == null then "in-tool"
           elif $l.type == "assistant" and ([ $l.message.content | arrays | .[] | select(.type == "text") ] | length) > 0
             then "idle"
           else "thinking" end) as $s
        | [ $id, $name, $s, "\(if $at then $now - $at else "?" end)s",
            (if $s == "in-tool" then "\($t.name): " + ($t.input | (.command // .description // .file_path
               // .url // .prompt // "") | tostring | gsub("\\s+"; " ") | .[0:100]) else "" end) ]
        | join(" ")' "$f"
done
