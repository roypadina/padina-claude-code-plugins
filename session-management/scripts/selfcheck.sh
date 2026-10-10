#!/usr/bin/env bash
#
# The one runnable check for close-own-pane.sh, against a fake `cmux` that serves a canned tree
# and logs every close call, and a fake `ps` that puts $FAKE_TTY on the caller's ancestor chain.
# No framework — run it and read the output.
#
#   scripts/selfcheck.sh
#
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

cat >"$tmp/cmux" <<'EOF'
#!/usr/bin/env bash
case "$*" in
    *"tree --all --json"*) cat "$FAKE_TREE" ;;
    close-surface*) echo "$*" >>"$FAKE_LOG"
        [ -e "$FAKE_LOG.new" ] && { echo "OK surface:9 workspace:9"; exit 0; }
        case "$FAKE_CLOSE" in
            ok) echo "OK surface:9 workspace:9" ;;
            last) echo "Error: invalid_state: Cannot close the last surface"; exit 1 ;;
            *) echo "Error: not_found: Surface not found"; exit 1 ;;
        esac ;;
    close-workspace*) echo "$*" >>"$FAKE_LOG"
        grep -q '"pinned":true' "$FAKE_TREE" &&
            { echo "Error: protected: Pinned workspaces can't be closed while pinned."; exit 1; }
        [ -z "${FAKE_WS_FAIL:-}" ] || { echo "Error: $FAKE_WS_FAIL"; exit 1; }
        echo "OK workspace:9" ;;
    new-surface*) echo "$*" >>"$FAKE_LOG"; touch "$FAKE_LOG.new"; echo "OK surface:10" ;;
    *) exit 2 ;;
esac
EOF
printf '#!/usr/bin/env bash\necho "1 $FAKE_TTY"\n' >"$tmp/ps"
chmod +x "$tmp/cmux" "$tmp/ps"
export PATH="$tmp:$PATH" FAKE_TREE="$tmp/tree.json" FAKE_LOG="$tmp/log"

# tree [!]<workspace>:<surface>,<surface> ... -> canned `tree --json`. "!" pins the workspace.
# Surface X has tty "tty-X"; a surface named "notty" has none.
tree() {
    local ws=() w
    for w in "$@"; do
        ws+=("$(jq -nc --arg w "${w%%:*}" --arg s "${w#*:}" \
            '{id:($w | ltrimstr("!")), pinned:($w | startswith("!")),
              panes:[{id:("p-" + ($w | ltrimstr("!"))), surfaces:[$s | split(",")[] |
                  {id:., tty:(if . == "notty" then null else "tty-\(.)" end)}]}]}')")
    done
    printf '%s\n' "${ws[@]}" | jq -sc '{windows:[{workspaces:.}]}' >"$FAKE_TREE"
}

fails=0
check() { # check <what> <close mode> <expected exit> <expected close calls, ";"-joined>
    : >"$FAKE_LOG"
    rm -f "$FAKE_LOG.new"
    FAKE_CLOSE=$2 bash "$here/close-own-pane.sh" ${ARGS:-} >/dev/null 2>&1
    local rc=$? calls
    calls=$(paste -sd ';' "$FAKE_LOG")
    if [ "$rc" = "$3" ] && [ "$calls" = "$4" ]; then
        printf 'ok    %s\n' "$1"
    else
        printf 'FAIL  %s\n        expected rc=%s [%s]\n        got      rc=%s [%s]\n' "$1" "$3" "$4" "$rc" "$calls"
        fails=$((fails + 1))
    fi
}

# The 2026-10-05 incident: the pane was moved out of the parent's workspace P into its own
# workspace C, but its env still says P.
export CMUX_SURFACE_ID=me CMUX_WORKSPACE_ID=P FAKE_TTY=tty-me
tree P:parent C:me
check "moved pane, alone in its workspace: closes its own workspace, never the stale one" last 0 \
    "close-surface --workspace C --surface me;close-workspace --workspace C"
check "cmux refuses with any other error: closes nothing more" notfound 1 \
    "close-surface --workspace C --surface me"
FAKE_WS_FAIL=boom check "close-workspace fails: reports it, exit 1" last 1 \
    "close-surface --workspace C --surface me;close-workspace --workspace C"
tree P:parent C:me,other
check "pane shares its workspace: closes only its own surface" ok 0 \
    "close-surface --workspace C --surface me"
check "cmux says last surface but the tree shows two: closes no workspace" last 1 \
    "close-surface --workspace C --surface me"
tree P:parent C:other
check "pane not found in the tree: closes nothing" ok 1 ""
tree P:me C:me
check "pane found in two workspaces: closes nothing" ok 1 ""
tree P:parent C:me
CMUX_SURFACE_ID='' check "not inside cmux: closes nothing" ok 0 ""

# $CMUX_SURFACE_ID leaked from another pane: its tty is not on this process's ancestor chain.
FAKE_TTY=tty-parent check "env names a pane whose tty isn't ours: closes nothing" last 1 ""
tree P:parent C:notty
CMUX_SURFACE_ID=notty FAKE_TTY=?? check "pane has no tty: closes nothing" last 1 ""

# Pinned workspaces can't be closed; never unpin one. Keep it with a fresh shell instead.
tree P:parent '!C:me'
check "pinned workspace, pane alone: opens a fresh shell there, closes only its own tab" last 0 \
    "close-surface --workspace C --surface me;new-surface --workspace C --pane p-C;close-surface --workspace C --surface me"
tree P:parent '!C:me,other'
check "pinned workspace, pane shares it: closes only its own surface" ok 0 \
    "close-surface --workspace C --surface me"

tree P:parent C:me
ARGS=--dry-run check "dry run: closes nothing, exit 0" last 0 ""
ARGS=--dry-run FAKE_TTY=tty-parent check "dry run, not our pane: exit 1" last 1 ""

# close-trigger.sh (UserPromptSubmit hook): fires only on a whole-message session-close reply.
fires() { jq -nc --arg p "$1" '{prompt: $p}' | CLAUDE_PLUGIN_ROOT="$here/.." bash "$here/close-trigger.sh" |
    jq -e '.hookSpecificOutput.additionalContext | test("close-own-pane.sh\" --dry-run")' >/dev/null 2>&1; }
for m in close 'Close.' 'close it' '1,3 then close' 'ok, close it' 'all, close'; do
    if fires "$m"; then printf 'ok    trigger fires on "%s"\n' "$m"; else
        printf 'FAIL  trigger should fire on "%s"\n' "$m"; fails=$((fails + 1)); fi
done
for m in 'close the PR' 'close RD-123' '/finish-session close' 'please close the file' 'closed'; do
    if fires "$m"; then printf 'FAIL  trigger should not fire on "%s"\n' "$m"; fails=$((fails + 1))
    else printf 'ok    trigger ignores "%s"\n' "$m"; fi
done

if [ "$fails" != 0 ]; then
    printf '\n%s check(s) failed\n' "$fails"
    exit 1
fi
printf '\nall checks passed\n'
