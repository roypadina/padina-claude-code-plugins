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
#   scripts/close-own-pane.sh      # must be the session's last command: success ends it
#
set -u
S="${CMUX_SURFACE_ID:-}"
[ -n "$S" ] || { echo "Not in cmux — close the window yourself."; exit 0; }
export CMUX_QUIET=1

# Prints "<workspace uuid> <surface count>" for the one workspace holding $S; nothing otherwise.
where() {
    cmux --id-format both tree --all --json 2>/dev/null | jq -r --arg s "$S" '
        [.windows[].workspaces[] | select([.panes[].surfaces[].id] | index($s))]
        | if length == 1 then "\(.[0].id) \([.[0].panes[].surfaces[]] | length)" else empty end' 2>/dev/null
}

read -r W N <<<"$(where)"
[ -n "${W:-}" ] || { echo "Could not find this pane in cmux — closed nothing."; exit 1; }

out=$(cmux close-surface --workspace "$W" --surface "$S" 2>&1) && { echo "$out"; exit 0; }
case "$out" in
    *"Cannot close the last surface"*) ;;
    *) echo "$out — closed nothing."; exit 1 ;;
esac

# cmux says this is the workspace's last surface. Close the workspace only if the tree agrees:
# same workspace, exactly one surface, and that surface is this one.
read -r W2 N2 <<<"$(where)"
if [ "$N" = 1 ] && [ "${W2:-}" = "$W" ] && [ "${N2:-}" = 1 ]; then
    exec cmux close-workspace --workspace "$W"
fi
echo "Workspace $W does not hold only this pane — closed nothing."
exit 1
