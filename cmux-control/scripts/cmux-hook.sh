#!/usr/bin/env bash
#
# cmux-control — one entrypoint for all three Claude Code hooks.
#
#   cmux-hook.sh session-start    rename the cmux tab + workspace to "repo · branch"
#   cmux-hook.sh stop             notify the sidebar that the turn finished
#   cmux-hook.sh subagent-stop    notify the sidebar that a subagent finished
#
# Reads the hook JSON payload on stdin. Silent and harmless outside cmux, and
# always exits 0 — it must never block or prolong a session.
#
# Set CMUX_CONTROL_QUIET=1 to keep the tab naming but suppress the notifications.

set -u

# ---------------------------------------------------------------- helpers ---

# One line, whitespace collapsed, ellipsised. jq slices by codepoint, so this
# never cuts a multi-byte character in half.
JQ_CLEAN='def clean: (. // "") | gsub("\\s+"; " ") | sub("^ +"; "") | sub(" +$"; "");'

payload=""
jqr() { # jqr <filter> -> value, or "" if jq is missing / the field is absent
  command -v jq >/dev/null 2>&1 || return 0
  printf '%s' "$payload" | jq -r "$JQ_CLEAN $1" 2>/dev/null || true
}

summary() { # the assistant's closing message, trimmed to a notification-sized line
  jqr '(.last_assistant_message | clean) | if length > 180 then .[0:179] + "…" else . end'
}

# "repo · branch" for a directory: the repo the work belongs to, and the branch
# it is on. Falls back to the directory name outside git.
#
# Uses --git-common-dir rather than --show-toplevel so a linked worktree still
# reports the MAIN repository's name (a worktree directory is usually named
# after the branch, which would make the label say the branch twice).
workspace_label() {
    local dir=${1:-} common repo branch
    [ -n "$dir" ] && [ -d "$dir" ] || dir=$PWD

    common=$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
    # --path-format needs git 2.31; fall back to the worktree root on anything older.
    [ -n "$common" ] || common=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null || true)
    if [ -z "$common" ]; then
        basename "$dir"
        return 0
    fi

    common=${common%/}
    if [ "$(basename "$common")" = ".git" ]; then
        repo=$(basename "$(dirname "$common")")
    else
        repo=$(basename "${common%.git}")   # bare repo: /srv/thing.git -> thing
    fi

    branch=$(git -C "$dir" symbolic-ref --quiet --short HEAD 2>/dev/null || true)
    if [ -z "$branch" ]; then               # detached HEAD, rebase, bisect
        branch=$(git -C "$dir" rev-parse --short HEAD 2>/dev/null || true)
        if [ -n "$branch" ]; then
            branch="@$branch"
        fi
    fi

    if [ -n "$branch" ]; then
        printf '%s \302\267 %s' "$repo" "$branch"
    else
        printf '%s' "$repo"                 # repo with no commits yet
    fi
}

notify() { # notify <title> <subtitle> <body>
    [ -z "${CMUX_CONTROL_QUIET:-}" ] || return 0
    local args=(--workspace "$CMUX_WORKSPACE_ID" --title "$1")
    [ -n "${2:-}" ] && args+=(--subtitle "$2")
    [ -n "${3:-}" ] && args+=(--body "$3")
    cmux notify "${args[@]}" >/dev/null 2>&1 || true
}

# ------------------------------------------------------------------ main ---

main() {
    payload=$(cat 2>/dev/null || true)

    # Guards. No cmux CLI, or not running inside a cmux terminal, means there is
    # nothing to talk to — leave without a sound.
    command -v cmux >/dev/null 2>&1 || exit 0
    [ -n "${CMUX_WORKSPACE_ID:-}" ] || exit 0
    export CMUX_QUIET=1     # mute cmux's own legacy-alias deprecation notices

    case "${1:-}" in
    session-start)
        local dir label args
        dir=$(jqr '.cwd // ""')
        label=$(workspace_label "$dir")
        [ -n "$label" ] || exit 0

        # The horizontal tab.
        args=(--workspace "$CMUX_WORKSPACE_ID")
        [ -n "${CMUX_TAB_ID:-}" ] && args+=(--tab "$CMUX_TAB_ID")
        cmux rename-tab "${args[@]}" -- "$label" >/dev/null 2>&1 || true

        # The sidebar entry.
        cmux workspace-action --workspace "$CMUX_WORKSPACE_ID" \
            --action rename --title "$label" >/dev/null 2>&1 || true

        # Claude Code's own session title. Whether cmux mirrors it anywhere is
        # unverified; it costs nothing and names the session in Claude's picker.
        if command -v jq >/dev/null 2>&1; then
            printf '%s' "$label" | jq -Rs \
                '{hookSpecificOutput: {hookEventName: "SessionStart", sessionTitle: .}}' \
                2>/dev/null || true
        fi
        ;;

    stop)
        # stop_hook_active means Claude is already running because of a previous
        # Stop hook. Firing again would notify on every continuation.
        [ "$(jqr '.stop_hook_active // false')" = "true" ] && exit 0

        local subtitle bg
        subtitle=$(workspace_label "$(jqr '.cwd // ""')")
        bg=$(jqr '(.background_tasks // []) | length')
        case "${bg:-0}" in
            ''|0) ;;
            1) subtitle="$subtitle · 1 background task" ;;
            *) subtitle="$subtitle · $bg background tasks" ;;
        esac
        notify "Claude finished" "$subtitle" "$(summary)"
        ;;

    subagent-stop)
        local kind title
        kind=$(jqr '(.agent_type | clean)')
        [ -n "$kind" ] && title="Subagent finished · $kind" || title="Subagent finished"
        notify "$title" "$(workspace_label "$(jqr '.cwd // ""')")" "$(summary)"
        ;;
    esac

    exit 0
}

# Sourced by scripts/selfcheck.sh to test workspace_label without running a hook.
[ "${CMUX_HOOK_LIB:-}" = "1" ] || main "$@"
