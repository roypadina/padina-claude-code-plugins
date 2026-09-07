#!/usr/bin/env bash
#
# Thin curl wrapper over the Joplin Data API, plus the shared token/port
# discovery used by the other scripts in this plugin.
#
# The token is read from Joplin's own profile settings and passed to curl
# through a config file on stdin, so it never appears in argv, in `ps`, in
# a shell history file, or in this script's output.
#
#   joplin-api.sh GET  /notes 'limit=5&fields=id,title'
#   joplin-api.sh GET  /search 'query=recipe&fields=id,title'
#   joplin-api.sh POST /notes '' '{"title":"x","body":"y","parent_id":"..."}'
#   joplin-api.sh PUT  /notes/<id> '' '{"body":"new body"}'
#   joplin-api.sh --port          print the discovered port, nothing else
#   joplin-api.sh --check         exit 0 if the API answers and the token works
#   joplin-api.sh --selftest      offline unit tests, no Joplin required
#
# Env overrides: JOPLIN_PORT, JOPLIN_TOKEN, JOPLIN_PROFILE_DIR.
#
set -euo pipefail

DEFAULT_PROFILE_DIR="${JOPLIN_PROFILE_DIR:-$HOME/.config/joplin-desktop}"
# Joplin's clipper server takes the first free port in this range.
PORT_MIN=41184
PORT_MAX=41194
CURL_TIMEOUT=5

# ---------------------------------------------------------------------------
# Pure functions — string in, string out. --selftest exercises these.
# ---------------------------------------------------------------------------

# parse_ping_output "<raw GET /ping body>" -> joplin|other
parse_ping_output() {
    case "$1" in
        *JoplinClipperServer*) echo "joplin" ;;
        *) echo "other" ;;
    esac
}

# looks_like_token "<string>" -> yes|no
# Joplin issues a 128-char lowercase hex authorisation token.
looks_like_token() {
    # BSD grep caps a repetition bound at 255, so express the floor open-ended.
    if printf '%s' "$1" | grep -Eq '^[0-9a-f]{64,}$'; then echo "yes"; else echo "no"; fi
}

# redact "<string>" -> a safe-to-print fingerprint, never the secret itself
redact() {
    local s="$1"
    if [ -z "$s" ]; then echo "<empty>"; else echo "<${#s} chars, sha256:$(printf '%s' "$s" | shasum -a 256 | cut -c1-8)>"; fi
}

# build_url <port> <path> <query>  -> full URL, token NOT included
build_url() {
    local port="$1" path="$2" query="${3:-}"
    path="/${path#/}"
    if [ -n "$query" ]; then echo "http://127.0.0.1:${port}${path}?${query}"; else echo "http://127.0.0.1:${port}${path}"; fi
}

# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

# Read api.token out of Joplin's settings.json. Prints the token on stdout —
# only ever consumed into a variable, never echoed to a terminal or a log.
read_token() {
    if [ -n "${JOPLIN_TOKEN:-}" ]; then printf '%s' "$JOPLIN_TOKEN"; return 0; fi
    local f="$DEFAULT_PROFILE_DIR/settings.json"
    [ -f "$f" ] || return 1
    python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("api.token",""), end="")' "$f"
}

# Probe the port range for a live clipper server. Prints the port.
discover_port() {
    if [ -n "${JOPLIN_PORT:-}" ]; then echo "$JOPLIN_PORT"; return 0; fi
    local p body
    for ((p = PORT_MIN; p <= PORT_MAX; p++)); do
        body="$(curl -s -m 2 "http://127.0.0.1:$p/ping" 2>/dev/null || true)"
        if [ "$(parse_ping_output "$body")" = "joplin" ]; then echo "$p"; return 0; fi
    done
    return 1
}

# api <METHOD> <path> [query] [json-body]
# Token is fed to curl via --config on stdin so it stays out of argv.
api() {
    local method="$1" path="$2" query="${3:-}" body="${4:-}"
    local port token url
    port="$(discover_port)" || { echo "joplin-api: no Joplin clipper server on ports $PORT_MIN-$PORT_MAX" >&2; return 3; }
    token="$(read_token)" || { echo "joplin-api: could not read api.token from $DEFAULT_PROFILE_DIR/settings.json" >&2; return 4; }
    [ -n "$token" ] || { echo "joplin-api: api.token is empty — is the Web Clipper service enabled?" >&2; return 4; }

    if [ -n "$query" ]; then query="${query}&token=${token}"; else query="token=${token}"; fi
    url="$(build_url "$port" "$path" "$query")"

    local -a args=(--silent --show-error --max-time "$CURL_TIMEOUT" --request "$method")
    if [ -n "$body" ]; then
        args+=(--header 'Content-Type: application/json' --data-binary "$body")
    fi
    # --config - reads the URL from stdin; keeps the token out of the process table.
    printf 'url = "%s"\n' "$url" | curl "${args[@]}" --config -
}

selftest() {
    local fails=0
    check() { # check <label> <actual> <expected>
        if [ "$2" = "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1: got '$2' want '$3'"; fails=$((fails + 1)); fi
    }
    echo "joplin-api.sh selftest"
    check "ping joplin"       "$(parse_ping_output 'JoplinClipperServer')" "joplin"
    check "ping trailing ws"  "$(parse_ping_output 'JoplinClipperServer
')" "joplin"
    check "ping foreign"      "$(parse_ping_output 'nginx welcome')" "other"
    check "ping empty"        "$(parse_ping_output '')" "other"
    check "token 128 hex"     "$(looks_like_token "$(printf 'a%.0s' {1..128})")" "yes"
    check "token short"       "$(looks_like_token 'abc')" "no"
    check "token uppercase"   "$(looks_like_token 'ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789')" "no"
    check "token empty"       "$(looks_like_token '')" "no"
    check "redact empty"      "$(redact '')" "<empty>"
    check "url no query"      "$(build_url 41184 /notes '')" "http://127.0.0.1:41184/notes"
    check "url with query"    "$(build_url 41184 notes 'limit=5')" "http://127.0.0.1:41184/notes?limit=5"
    check "url path slash"    "$(build_url 41190 '/search' 'query=x')" "http://127.0.0.1:41190/search?query=x"
    # redact must never leak the secret itself
    local t="supersecrettoken"
    if printf '%s' "$(redact "$t")" | grep -q "$t"; then
        echo "  FAIL redact leaks the secret"; fails=$((fails + 1))
    else
        echo "  ok   redact hides the secret"
    fi
    echo
    if [ "$fails" -eq 0 ]; then echo "all passed"; else echo "$fails failed"; return 1; fi
}

main() {
    case "${1:---help}" in
        --selftest) selftest ;;
        --port) discover_port || { echo "no Joplin clipper server found" >&2; exit 3; } ;;
        --check)
            api GET /notes 'limit=1&fields=id' >/dev/null && echo "ok: Data API reachable and token accepted"
            ;;
        --help | -h)
            sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
            ;;
        GET | POST | PUT | DELETE)
            api "$@"
            ;;
        *)
            echo "joplin-api: unknown argument '$1' (try --help)" >&2
            exit 2
            ;;
    esac
}

# Only run main when executed, not when sourced for its functions.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then main "$@"; fi
