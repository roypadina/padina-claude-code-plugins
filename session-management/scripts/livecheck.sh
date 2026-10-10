#!/usr/bin/env bash
#
# Live end-to-end check for close-own-pane.sh against the real cmux. Creates throwaway
# "zz-close-test-*" workspaces (never focused), runs the script inside their panes the way
# Claude's Bash tool does (a child with no controlling tty, under the pane's shell), and checks
# what survived. Touches only workspaces it creates, by UUID; closes its leftovers at exit.
# Takes ~1 min. Run it from inside cmux after any change to close-own-pane.sh:
#
#   scripts/livecheck.sh
#
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
[ -n "${CMUX_SURFACE_ID:-}" ] || { echo "run this inside cmux"; exit 2; }
export CMUX_QUIET=1
tmp=$(mktemp -d)
touch "$tmp/made"
cleanup() {
    local w
    for w in $(cat "$tmp/made"); do
        cmux workspace-action --workspace "$w" --action unpin >/dev/null 2>&1
        cmux close-workspace --workspace "$w" >/dev/null 2>&1
    done
    rm -rf "$tmp"
}
trap cleanup EXIT

# Runs the script with no controlling tty (like Claude's Bash tool): run.sh <out> [--dry-run] [VAR=x...]
cat >"$tmp/run.sh" <<EOF
out=\$1; shift
a=; [ "\${1:-}" = --dry-run ] && { a=--dry-run; shift; }
env "\$@" python3 -c 'import os,sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' \\
    bash "$here/close-own-pane.sh" \$a >"\$out.tmp" 2>&1
mv "\$out.tmp" "\$out"
EOF

tree() { cmux --id-format both tree --all --json; }
ws_of() { tree | jq -r --arg s "$1" '.windows[].workspaces[] | select([.panes[].surfaces[].id] | index($s)) | .id'; }
has_ws() { tree | jq -e --arg w "$1" '[.windows[].workspaces[] | select(.id == $w)] | length == 1' >/dev/null; }
has_s() { [ -n "$(ws_of "$1")" ]; }
surfaces() { tree | jq -r --arg w "$1" '.windows[].workspaces[] | select(.id == $w) | .panes[].surfaces[].id'; }
pane_of() { tree | jq -r --arg s "$1" '.windows[].workspaces[].panes[] | select([.surfaces[].id] | index($s)) | .id'; }

# need <id...>: abort on an empty id. cmux treats an empty --surface/--workspace as the caller's or
# focused one — the operator's own pane — so a lost test id must never reach a cmux command.
need() {
    local v
    for v in "$@"; do
        case "$v" in '' | null | "$CMUX_SURFACE_ID") echo "lost a test pane — abort"; exit 2 ;; esac
    done
}

# mkws <name> -> "<workspace uuid> <surface uuid>"
mkws() {
    local ref w
    ref=$(cmux new-workspace --name "zz-close-test-$1" --cwd "$tmp" --focus false | awk '{print $2}')
    w=$(tree | jq -r --arg r "$ref" '.windows[].workspaces[] | select(.ref == $r) | .id')
    echo "$w" >>"$tmp/made"  # a file: mkws runs in a subshell
    echo "$w $(surfaces "$w" | head -1)"
}
# newest <workspace> <command...> -> uuid of the surface the command added to the workspace
newest() {
    local w=$1 before
    shift
    need "$w"
    before=$(surfaces "$w")
    "$@" >/dev/null
    surfaces "$w" | grep -vxF "$before"
}
# ready <surface>: start its shell and wait until it runs commands.
ready() {
    local w i
    w=$(ws_of "$1")
    need "$1" "$w"
    cmux send-key --workspace "$w" --surface "$1" backspace >/dev/null
    for i in $(seq 40); do
        cmux send --workspace "$w" --surface "$1" "touch $tmp/ready-$1\n" >/dev/null
        sleep 0.5
        [ -e "$tmp/ready-$1" ] && return 0
    done
    echo "pane $1 never got a shell"; exit 2
}
# run_in <surface> [VAR=value...]: run the script inside that pane, wait for its output.
run_in() {
    local s=$1 w i
    shift
    w=$(ws_of "$s")
    need "$s" "$w"
    ready "$s"
    rm -f "$tmp/out-$s"
    cmux send --workspace "$w" --surface "$s" "bash $tmp/run.sh $tmp/out-$s $*\n" >/dev/null
    for i in $(seq 40); do [ -e "$tmp/out-$s" ] && break; sleep 0.25; done
    sleep 1
    out=$(cat "$tmp/out-$s" 2>/dev/null || echo "<no output>")
}

fails=0
expect() { # expect <what> <condition...>
    local what=$1
    shift
    if "$@"; then printf 'ok    %s\n' "$what"; else
        printf 'FAIL  %s\n        script said: %s\n' "$what" "$out"; fails=$((fails + 1))
    fi
}
nope() { ! "$@"; }
said() { case "$out" in *"$1"*) return 0 ;; esac; return 1; }

echo "1. pane alone in its workspace"
read -r A a <<<"$(mkws alone)"
need "$A" "$a"
run_in "$a" --dry-run
expect "dry run closes nothing" has_ws "$A"
expect "dry run says it would close the workspace" said "the whole workspace"
run_in "$a"
expect "its workspace is closed" nope has_ws "$A"

echo "2. pane split next to another pane"
read -r B b1 <<<"$(mkws split)"
need "$B" "$b1"
b2=$(newest "$B" cmux new-split right --workspace "$B" --surface "$b1" --focus false)
need "$b2"
run_in "$b2"
expect "its own pane is closed" nope has_s "$b2"
expect "the other pane is untouched" has_s "$b1"

echo "3. pane is one of two tabs"
read -r C c1 <<<"$(mkws tabs)"
need "$C" "$c1"
pc=$(pane_of "$c1")
need "$pc"
c2=$(newest "$C" cmux new-surface --workspace "$C" --pane "$pc" --focus false)
need "$c2"
run_in "$c2"
expect "its own tab is closed" nope has_s "$c2"
expect "the other tab is untouched" has_s "$c1"

echo "4. pane moved to a new workspace (stale \$CMUX_WORKSPACE_ID — the 2026-10-05 incident)"
read -r D d1 <<<"$(mkws moved-from)"
need "$D" "$d1"
d2=$(newest "$D" cmux new-split right --workspace "$D" --surface "$d1" --focus false)
need "$d2"
ready "$d2"
cmux move-tab-to-new-workspace --workspace "$D" --surface "$d2" --focus false >/dev/null
E=$(ws_of "$d2")
need "$E"
echo "$E" >>"$tmp/made"
run_in "$d2"
expect "the pane left its first workspace" test "$E" != "$D"
expect "its new workspace is closed" nope has_ws "$E"
expect "the workspace its env still names is untouched" has_s "$d1"

echo "5. \$CMUX_SURFACE_ID leaked from another pane"
read -r F f <<<"$(mkws leak-runner)"
need "$F" "$f"
read -r G g <<<"$(mkws leak-victim)"
need "$G" "$g"
ready "$g"
run_in "$f" CMUX_SURFACE_ID="$g" CMUX_WORKSPACE_ID="$G"
expect "the other pane is untouched" has_s "$g"
expect "the runner's own pane is untouched" has_s "$f"
expect "says it closed nothing" said "closed nothing"

echo "6. pinned workspace, pane alone"
read -r H h <<<"$(mkws pinned-alone)"
need "$H" "$h"
cmux workspace-action --workspace "$H" --action pin >/dev/null
run_in "$h"
expect "its own tab is closed" nope has_s "$h"
expect "the pinned workspace stays, with a fresh shell" test -n "$(surfaces "$H")"

echo "7. pinned workspace, pane split next to another"
read -r I i1 <<<"$(mkws pinned-split)"
need "$I" "$i1"
i2=$(newest "$I" cmux new-split right --workspace "$I" --surface "$i1" --focus false)
need "$i2"
cmux workspace-action --workspace "$I" --action pin >/dev/null
run_in "$i2"
expect "its own pane is closed" nope has_s "$i2"
expect "the other pane is untouched" has_s "$i1"

if command -v tmux >/dev/null; then
    echo "8. run inside tmux started from a pane (env inherited, chain never reaches the pane)"
    read -r J j <<<"$(mkws tmux)"
    need "$J" "$j"
    ready "$j"
    cmux send --workspace "$J" --surface "$j" \
        "tmux -L zz-close-test new-session -d 'bash $tmp/run.sh $tmp/out-tmux'\n" >/dev/null
    for i in $(seq 40); do [ -e "$tmp/out-tmux" ] && break; sleep 0.25; done
    sleep 1
    out=$(cat "$tmp/out-tmux" 2>/dev/null || echo "<no output>")
    tmux -L zz-close-test kill-server 2>/dev/null
    expect "the pane that started tmux is untouched" has_s "$j"
    expect "says it closed nothing" said "closed nothing"
fi

if [ "$fails" != 0 ]; then
    printf '\n%s check(s) failed\n' "$fails"
    exit 1
fi
printf '\nall live checks passed\n'
