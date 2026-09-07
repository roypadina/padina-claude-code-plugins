#!/usr/bin/env bash
#
# Preflight for the Joplin integration: is the desktop app running, which
# port did the Web Clipper service actually land on, does the token work,
# is the MCP server answering, and which MCP tools are really enabled.
#
# Every check degrades independently — one missing piece never hides the
# rest. It only reports and advises: it never enables a setting, renews a
# token, edits a client config or touches a note.
#
#   scripts/joplin-doctor.sh              run the checks
#   scripts/joplin-doctor.sh --selftest   unit-test the parsers, offline
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=joplin-api.sh
source "$HERE/joplin-api.sh"

PASS="ok  "
WARN="warn"
FAIL="fail"

say() { printf '%-4s  %s\n' "$1" "$2"; }

# ---------------------------------------------------------------------------
# Pure parsers — --selftest exercises these with canned strings.
# ---------------------------------------------------------------------------

# parse_tools_list "<tools/list JSON>" -> newline-separated tool names, sorted
parse_tools_list() {
    printf '%s' "$1" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for t in sorted(d.get("result", {}).get("tools", []), key=lambda t: t.get("name", "")):
    print(t.get("name", ""))
' 2>/dev/null || true
}

# parse_jsonrpc_error "<JSON>" -> error message, or "" when the call succeeded
parse_jsonrpc_error() {
    printf '%s' "$1" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("unparseable response"); sys.exit(0)
e = d.get("error")
print(e.get("message", "unknown error") if e else "")
' 2>/dev/null || true
}

# classify_write_tools "<newline-separated tool names>" -> comma list of write-capable tools
classify_write_tools() {
    printf '%s\n' "$1" | grep -E '^(create_note|update_note|delete_note|manage_tags|create_notebook)$' | paste -sd, - || true
}

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

mcp_call() { # mcp_call <port> <token> <json-body>
    printf 'url = "http://127.0.0.1:%s/mcp?token=%s"\n' "$1" "$2" |
        curl -s -m "$CURL_TIMEOUT" \
            -H 'Content-Type: application/json' \
            -H 'Accept: application/json, text/event-stream' \
            -d "$3" --config - 2>/dev/null || true
}

run_checks() {
    local port="" token="" body rc=0

    # 1. desktop app running
    if pgrep -x Joplin >/dev/null 2>&1 || pgrep -f '/Applications/Joplin.app' >/dev/null 2>&1; then
        say "$PASS" "Joplin desktop is running"
    else
        say "$FAIL" "Joplin desktop is not running — the API and MCP server only exist while the app is open"
        rc=1
    fi

    # 2. clipper port
    if port="$(discover_port)"; then
        say "$PASS" "Web Clipper service answering on port $port"
    else
        say "$FAIL" "no Web Clipper service on ports $PORT_MIN-$PORT_MAX — enable it in Joplin: Settings > Web Clipper > Enable Web Clipper Service"
        echo
        echo "Nothing else can be checked without the service. Stopping here."
        return 1
    fi

    # 3. token present
    token="$(read_token 2>/dev/null || true)"
    if [ -n "$token" ] && [ "$(looks_like_token "$token")" = "yes" ]; then
        say "$PASS" "authorisation token found $(redact "$token")"
    elif [ -n "$token" ]; then
        say "$WARN" "token found but does not look like Joplin's 128-char hex token $(redact "$token")"
    else
        say "$FAIL" "no api.token in $DEFAULT_PROFILE_DIR/settings.json"
        rc=1
    fi

    # 4. token actually accepted by the Data API
    if [ -n "$token" ]; then
        if api GET /notes 'limit=1&fields=id' >/dev/null 2>&1; then
            say "$PASS" "Data API accepts the token"
        else
            say "$FAIL" "Data API rejected the token — renew it in Settings > Web Clipper, then re-run scripts/joplin-mcp-install.sh"
            rc=1
        fi
    fi

    # 5. MCP server
    if [ -n "$token" ]; then
        body="$(mcp_call "$port" "$token" '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"joplin-doctor","version":"1"}}}')"
        local err; err="$(parse_jsonrpc_error "$body")"
        if [ -z "$body" ]; then
            say "$FAIL" "MCP endpoint /mcp gave no response — tick Settings > AI > 'Enable MCP server'"
            rc=1
        elif [ -n "$err" ]; then
            say "$FAIL" "MCP initialize failed: $err"
            rc=1
        else
            say "$PASS" "MCP server responded to initialize"

            # 6. which tools are exposed
            local tools; tools="$(parse_tools_list "$(mcp_call "$port" "$token" '{"jsonrpc":"2.0","id":2,"method":"tools/list"}')")"
            if [ -z "$tools" ]; then
                say "$WARN" "MCP exposes no tools — enable them in Settings > Tools"
            else
                say "$PASS" "MCP tools enabled: $(printf '%s' "$tools" | paste -sd, -)"
                local writes; writes="$(classify_write_tools "$tools")"
                [ -n "$writes" ] && say "$WARN" "write-capable tools are on and Joplin does NOT prompt per action: $writes"
                if printf '%s\n' "$tools" | grep -qx delete_note; then
                    say "$WARN" "delete_note is on — an agent can trash notes without confirmation. Turn it off in Settings > Tools unless you want that."
                fi
            fi
        fi
    fi

    # 7. client wiring
    check_client_claude
    check_client_codex

    return $rc
}

check_client_claude() {
    if ! command -v claude >/dev/null 2>&1; then
        say "$WARN" "claude CLI not on PATH — skipping Claude Code check"
        return
    fi
    if claude mcp get joplin >/dev/null 2>&1; then
        say "$PASS" "Claude Code has an MCP server named 'joplin'"
    else
        say "$WARN" "Claude Code has no 'joplin' MCP server — run scripts/joplin-mcp-install.sh"
    fi
}

check_client_codex() {
    if ! command -v codex >/dev/null 2>&1; then
        say "$WARN" "codex CLI not on PATH — skipping Codex check"
        return
    fi
    if codex mcp get joplin >/dev/null 2>&1; then
        say "$PASS" "Codex has an MCP server named 'joplin'"
    else
        say "$WARN" "Codex has no 'joplin' MCP server — run scripts/joplin-mcp-install.sh"
    fi
    if [ -e "$HOME/.codex/skills/joplin-control" ]; then
        say "$PASS" "Codex skill installed at ~/.codex/skills/joplin-control"
    else
        say "$WARN" "Codex skill missing — run scripts/joplin-mcp-install.sh"
    fi
}

selftest() {
    local fails=0
    check() { if [ "$2" = "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1: got '$2' want '$3'"; fails=$((fails + 1)); fi; }
    echo "joplin-doctor.sh selftest"

    local list='{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"read_note"},{"name":"create_note"},{"name":"search_notes"}]}}'
    check "tools sorted"    "$(parse_tools_list "$list" | paste -sd, -)" "create_note,read_note,search_notes"
    check "tools empty"     "$(parse_tools_list '{"result":{"tools":[]}}')" ""
    check "tools garbage"   "$(parse_tools_list 'not json')" ""

    check "err none"        "$(parse_jsonrpc_error '{"jsonrpc":"2.0","id":1,"result":{}}')" ""
    check "err present"     "$(parse_jsonrpc_error '{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"Method not found"}}')" "Method not found"
    check "err garbage"     "$(parse_jsonrpc_error 'nope')" "unparseable response"

    check "writes found"    "$(classify_write_tools 'read_note
create_note
delete_note')" "create_note,delete_note"
    check "writes none"     "$(classify_write_tools 'read_note
list_tags')" ""

    echo
    if [ "$fails" -eq 0 ]; then echo "all passed"; else echo "$fails failed"; return 1; fi
}

case "${1:-}" in
    --selftest) selftest ;;
    "") echo "Joplin integration preflight"; echo; run_checks ;;
    *) echo "usage: joplin-doctor.sh [--selftest]" >&2; exit 2 ;;
esac
