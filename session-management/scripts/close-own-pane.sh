#!/usr/bin/env bash
#
# Close the cmux pane this Claude session runs in. Close its workspace only when that pane is
# provably the workspace's single surface. When anything is uncertain, close nothing.
#
# Never trusts $CMUX_WORKSPACE_ID. It is fixed when the shell starts, so it goes stale when the
# pane is moved to another workspace, and cmux uses it as the default --workspace. A stale value
# once made `close-surface` fail with "Surface not found", and a `|| close-workspace
# "$CMUX_WORKSPACE_ID"` fallback then closed the *parent* session's workspace (2026-10-05).
# The surface UUID stays valid, so the real workspace is looked up by it.
#
# Doesn't trust $CMUX_SURFACE_ID alone either: cmux has no caller identity of its own, and an env
# var can leak into a process started from another pane (tmux server, copied env). The surface's
# tty must sit on this process's own ancestor chain — every ancestor, since claude may run under a
# pty wrapper such as ccpool whose tty differs from the pane's.
#
# A pinned workspace is kept: when this pane is its only one, a fresh shell tab opens there first.
#
# Exit 0 = closed (or not in cmux, or dry run). Exit 1 = closed nothing; the last line says why.
# Known gap: a surface dragged into the workspace in the ms between the re-check and
# close-workspace dies with it.
#
#   scripts/close-own-pane.sh             # must be the session's last command: success ends it
#   scripts/close-own-pane.sh --dry-run   # says what it would close, closes nothing
#
set -u
fail() {
    echo "$1 — closed nothing."
    echo "Don't close it by hand: a bare \`cmux close-surface\` closes the focused pane, not this one."
    exit 1
}
S="${CMUX_SURFACE_ID:-}"
[ -n "$S" ] || { echo "Not in cmux — close the window yourself."; exit 0; }
command -v cmux >/dev/null || fail "cmux CLI not found"
command -v jq >/dev/null || fail "jq not found"
export CMUX_QUIET=1

# For the one workspace holding $S, prints "<workspace uuid> <surface count> <pinned>
# <tty of $S> <pane uuid of $S> <surface ref> <workspace ref> <workspace title>"; else nothing.
where() {
    cmux --id-format both tree --all --json 2>/dev/null | jq -r --arg s "$S" '
        [.windows[].workspaces[] | select([.panes[].surfaces[].id] | index($s))]
        | if length == 1 then .[0] | (.panes[] | select([.surfaces[].id] | index($s))) as $p
            | ($p.surfaces[] | select(.id == $s)) as $me
            | "\(.id) \([.panes[].surfaces[]] | length) \(.pinned == true) \($me.tty // "none") \($p.id) \($me.ref) \(.ref) \(.title)"
          else empty end' 2>/dev/null
}

# The ttys of this process and every ancestor, space-separated ("??" = none).
my_ttys() {
    local p=$$ pp t out=" "
    while [ "${p:-0}" -gt 1 ]; do
        read -r pp t <<<"$(ps -o ppid=,tty= -p "$p" 2>/dev/null)"
        out="$out${t:-??} "
        p=$pp
    done
    echo "$out"
}

read -r W N PIN TTY P SREF WREF TITLE <<<"$(where)"
[ -n "${W:-}" ] || fail "Could not find this pane in cmux"
case "$(my_ttys)" in
    *" ${TTY#/dev/} "*) ;;
    *) fail "Pane $S (tty $TTY) is not this session's terminal" ;;
esac

if [ "${1:-}" = --dry-run ]; then
    if [ "$N" != 1 ]; then what="only its tab"
    elif [ "$PIN" = true ]; then what="its tab; pinned workspace kept with a fresh shell"
    else what="the whole workspace — this pane is its only one"; fi
    echo "Would close $SREF in $WREF \"$TITLE\": $what."
    exit 0
fi

out=$(cmux close-surface --workspace "$W" --surface "$S" 2>&1) && { echo "$out"; exit 0; }
case "$out" in
    *"Cannot close the last surface"*) ;;
    *) fail "$out" ;;
esac
if [ "$PIN" = true ]; then
    # Never unpin or close a pinned workspace: leave a fresh shell in it, then close our tab.
    cmux new-surface --workspace "$W" --pane "$P" >/dev/null 2>&1 ||
        fail "Workspace $W is pinned and a fresh shell could not be opened there"
    out=$(cmux close-surface --workspace "$W" --surface "$S" 2>&1) && { echo "$out"; exit 0; }
    fail "$out"
fi

# cmux says this is the workspace's last surface. Close the workspace only if the tree agrees:
# same workspace, exactly one surface, and that surface is this one.
read -r W2 N2 PIN2 _ <<<"$(where)"
[ "$N" = 1 ] && [ "${W2:-}" = "$W" ] && [ "${N2:-}" = 1 ] && [ "${PIN2:-}" = false ] ||
    fail "Workspace $W does not hold only this pane"
out=$(cmux close-workspace --workspace "$W" 2>&1) && { echo "$out"; exit 0; }
fail "$out"
