#!/usr/bin/env bash
#
# Lists the processes this Claude session started that are still running: everything under its
# Bash tool shells (foreground and run_in_background), minus this check itself. MCP servers and
# claude's own helpers are not listed. These die (or are orphaned) when the pane closes.
# shortcut: a process started with `&`/nohup whose shell already exited is re-parented to launchd
# and can't be traced back; those still come from the conversation.
#
#   scripts/session-procs.sh    # "<pid> <elapsed> <command>" per process; nothing = none
#
c=${CLAUDE_PID:-}
[ -n "$c" ] || { echo "CLAUDE_PID not set — unknown"; exit 0; }
ps -A -o pid=,ppid=,etime=,command= | awk -v c="$c" -v me=$$ '
    function walk(p, up,   k, n, i, s) {
        s = cmd[p]
        if (match(s, /eval '\''[^'\'']*'\''/)) s = substr(s, RSTART + 6, RLENGTH - 7)
        if (s != up) printf "%s %s %s\n", p, et[p], substr(s, 1, 120)  # a shell and its one command: once
        n = split(kids[p], k, " ")
        for (i = 1; i <= n; i++) walk(k[i], s)
    }
    { pid = $1; pp[pid] = $2; et[pid] = $3; kids[$2] = kids[$2] " " pid
      sub(/^ *[0-9]+ +[0-9]+ +[^ ]+ +/, ""); cmd[pid] = $0 }
    END {
        for (p = me; p > 1; p = pp[p]) mine[p] = 1
        n = split(kids[c], top, " ")
        for (i = 1; i <= n; i++)
            if (cmd[top[i]] ~ /shell-snapshots\/snapshot-/ && !mine[top[i]]) walk(top[i], "")
    }'
