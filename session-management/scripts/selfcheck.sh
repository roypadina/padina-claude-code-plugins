#!/usr/bin/env bash
#
# The one runnable check for close-own-pane.sh, against a fake `cmux` that serves a canned tree
# and logs every close call. No framework — run it and read the output.
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
        case "$FAKE_CLOSE" in
            ok) echo "OK surface:9 workspace:9" ;;
            last) echo "Error: invalid_state: Cannot close the last surface"; exit 1 ;;
            *) echo "Error: not_found: Surface not found"; exit 1 ;;
        esac ;;
    close-workspace*) echo "$*" >>"$FAKE_LOG"; echo "OK workspace:9" ;;
    *) exit 2 ;;
esac
EOF
chmod +x "$tmp/cmux"
export PATH="$tmp:$PATH" FAKE_TREE="$tmp/tree.json" FAKE_LOG="$tmp/log"

# tree <workspace>:<surface>,<surface> ... -> canned `tree --json`
tree() {
    local ws=() w
    for w in "$@"; do
        ws+=("$(jq -nc --arg w "${w%%:*}" --arg s "${w#*:}" \
            '{id:$w, panes:[{surfaces:[$s | split(",")[] | {id:.}]}]}')")
    done
    printf '%s\n' "${ws[@]}" | jq -sc '{windows:[{workspaces:.}]}' >"$FAKE_TREE"
}

fails=0
check() { # check <what> <close mode> <expected exit> <expected close calls, ";"-joined>
    : >"$FAKE_LOG"
    FAKE_CLOSE=$2 bash "$here/close-own-pane.sh" >/dev/null 2>&1
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
export CMUX_SURFACE_ID=me CMUX_WORKSPACE_ID=P
tree P:parent C:me
check "moved pane, alone in its workspace: closes its own workspace, never the stale one" last 0 \
    "close-surface --workspace C --surface me;close-workspace --workspace C"
check "cmux refuses with any other error: closes nothing more" notfound 1 \
    "close-surface --workspace C --surface me"
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

if [ "$fails" != 0 ]; then
    printf '\n%s check(s) failed\n' "$fails"
    exit 1
fi
printf '\nall checks passed\n'
