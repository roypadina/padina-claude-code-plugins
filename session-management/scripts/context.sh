#!/usr/bin/env bash
#
# /session-recap's context line: the current context size, and the base /compact verdict from it.
# Prefers the status line's own numbers (the same ctx % the user sees, saved by the status-line
# tap in the README); falls back to the transcript's last real main-thread turn, where the window
# is unknown — the same model can run with a 200k or a 1000k window, so it is never guessed.
#
#   scripts/context.sh   # "Context: 132k / 200k (66%) → soon" | "Context: 132k (window unknown) → no"
#                        # | "Context: unknown" — no transcript or no jq
#
dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
id="${CLAUDE_CODE_SESSION_ID:-}"
command -v jq >/dev/null && [ -n "$id" ] || { echo "Context: unknown"; exit 0; }

# verdict <ctx tokens> [pct]: by pct when known; whatever the window, 200k+ is at least "soon"
# and 400k+ is "now" (recall degrades long before a 1000k window fills).
verdict() {
    local v=no
    [ -n "${2:-}" ] && { [ "$2" -ge 75 ] && v=now || { [ "$2" -ge 50 ] && v=soon; }; }
    [ "$1" -ge 400000 ] && v=now
    [ "$1" -ge 200000 ] && [ "$v" = no ] && v=soon
    [ "$v" = soon ] && v="soon — at next break"
    echo "$v"
}

read -r pct win ctx < <(jq -r '.context_window | [(.used_percentage | floor), .context_window_size,
    (.current_usage | .input_tokens + .cache_read_input_tokens + .cache_creation_input_tokens)]
    | map(tostring) | join(" ")' "$dir/context-window/$id.json" 2>/dev/null)
if [ -n "${ctx:-}" ] && [ "$ctx" != null ] && [ "${pct:-null}" != null ]; then
    echo "Context: $((ctx / 1000))k / $((win / 1000))k ($pct%) → $(verdict "$ctx" "$pct")"
    exit 0
fi

f=$(ls "$dir"/projects/*/"$id".jsonl 2>/dev/null | head -1)
# Never grep "usage" and take the last line — it matches prose and returns 0.
ctx=$([ -n "$f" ] && grep '"type":"assistant"' "$f" | tail -n 50 | jq -s -r '[.[] | select(.isSidechain != true
    and .message.model != "<synthetic>" and .message.usage != null)] | last | .message.usage
    | .input_tokens + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0)' 2>/dev/null)
case "$ctx" in
    '' | null | *[!0-9]*) echo "Context: unknown" ;;
    *) echo "Context: $((ctx / 1000))k (window unknown) → $(verdict "$ctx")" ;;
esac
