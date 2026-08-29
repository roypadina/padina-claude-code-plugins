#!/usr/bin/env bash
#
# Preflight checks for Espanso: is it installed, is the daemon actually
# running, is it registered as a system service, where does its config
# live, and is it up to date against the latest GitHub release. Every check
# degrades independently — one missing piece never hides the rest.
#
# This script only reports and advises. It never restarts, installs,
# registers, or edits anything.
#
#   scripts/espanso-doctor.sh              run the checks
#   scripts/espanso-doctor.sh --selftest   unit-test the parsers, offline,
#                                          no espanso binary required
#
set -euo pipefail

GITHUB_LATEST_URL="https://api.github.com/repos/espanso/espanso/releases/latest"
CURL_TIMEOUT=5

# ---------------------------------------------------------------------------
# Pure functions — no I/O, each takes a string and returns a string. These
# are what --selftest exercises against canned input.
# ---------------------------------------------------------------------------

# parse_version_output "<raw `espanso --version` output>" -> "2.4.0" or ""
# Verified on 2.4.0: the command prints a bare "2.4.0", no "espanso" prefix.
parse_version_output() {
    printf '%s' "$1" | tr -d '[:space:]' | grep -Eo '^[0-9]+\.[0-9]+\.[0-9]+' || true
}

# parse_status_output "<raw `espanso status` output>" -> running|not-running|unknown
parse_status_output() {
    case "$1" in
        *"is not running"*) echo "not-running" ;;
        *"is running"*) echo "running" ;;
        *) echo "unknown" ;;
    esac
}

# parse_service_check_output "<raw `espanso service check` output>" -> registered|not-registered|unknown
parse_service_check_output() {
    case "$1" in
        *"registered as a service"*) echo "registered" ;;
        *"not registered"*) echo "not-registered" ;;
        *) echo "unknown" ;;
    esac
}

# parse_config_path "<raw `espanso path` output>" -> the Config: line's value, or ""
parse_config_path() {
    printf '%s\n' "$1" | grep -m1 '^Config:' | sed -E 's/^Config:[[:space:]]*//'
}

# extract_tag_name '<GitHub releases/latest JSON>' -> "v2.4.0" or ""
extract_tag_name() {
    printf '%s' "$1" | grep -o '"tag_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 \
        | sed -E 's/.*"([^"]+)"$/\1/'
}

# strip_v "v2.4.0" -> "2.4.0"
strip_v() {
    printf '%s' "$1" | sed -E 's/^[vV]//'
}

# version_compare "A" "B" -> gt|eq|lt  (3-part numeric versions, e.g. 2.4.0)
version_compare() {
    local a="$1" b="$2"
    if [ "$a" = "$b" ]; then
        echo "eq"
        return
    fi
    local IFS=.
    # shellcheck disable=SC2206 # intentional word-split into version parts
    local -a av=($a) bv=($b)
    local i ai bi
    for i in 0 1 2; do
        ai=${av[i]:-0}
        bi=${bv[i]:-0}
        if [ "$ai" -gt "$bi" ] 2>/dev/null; then
            echo "gt"
            return
        fi
        if [ "$ai" -lt "$bi" ] 2>/dev/null; then
            echo "lt"
            return
        fi
    done
    echo "eq"
}

# ---------------------------------------------------------------------------
# Self-test — canned strings only, no network, no espanso binary.
# ---------------------------------------------------------------------------

selftest() {
    local fails=0
    check() { # check <expected> <actual> <what>
        if [ "$1" = "$2" ]; then
            printf 'ok    %s\n' "$3"
        else
            printf 'FAIL  %s\n        expected [%s]\n        got      [%s]\n' "$3" "$1" "$2"
            fails=$((fails + 1))
        fi
    }

    check "2.4.0" "$(parse_version_output '2.4.0')" "bare version string"
    check "2.4.0" "$(parse_version_output '  2.4.0  ')" "version string with surrounding whitespace"
    check "" "$(parse_version_output 'espanso 2.4.0')" "unverified prefixed shape parses as unknown, not a guess"

    check "running" "$(parse_status_output 'espanso is running')" "daemon running"
    check "not-running" "$(parse_status_output 'espanso is not running')" "daemon not running"
    check "unknown" "$(parse_status_output 'something unexpected')" "unrecognized status text"

    check "registered" "$(parse_service_check_output 'registered as a service')" "service registered"
    check "not-registered" "$(parse_service_check_output 'not registered as a system service')" "service not registered"
    check "unknown" "$(parse_service_check_output 'garbage output')" "unrecognized service-check text"

    local path_output
    path_output=$'Config: /Users/example/Library/Application Support/espanso\nPackages: /Users/example/Library/Application Support/espanso/match/packages\nRuntime: /Users/example/Library/Caches/espanso'
    check "/Users/example/Library/Application Support/espanso" "$(parse_config_path "$path_output")" "config path extraction from multi-line output"

    check 'v2.4.0' "$(extract_tag_name '{"tag_name":"v2.4.0","prerelease":false,"draft":false}')" "tag_name extraction from release JSON"
    check '2.4.0' "$(strip_v 'v2.4.0')" "leading v stripped"
    check '2.4.0' "$(strip_v '2.4.0')" "no-op when there is no leading v"

    check "eq" "$(version_compare '2.4.0' '2.4.0')" "equal versions"
    check "gt" "$(version_compare '2.4.0' '2.3.9')" "newer minor beats higher patch on the older minor"
    check "lt" "$(version_compare '2.3.0' '2.4.0')" "older minor"
    check "gt" "$(version_compare '3.0.0' '2.9.9')" "newer major beats everything on the older major"

    if [ "$fails" -ne 0 ]; then
        printf '\n%s check(s) failed\n' "$fails" >&2
        exit 1
    fi
    printf '\nall checks passed\n'
}

if [ "${1:-}" = "--selftest" ]; then
    selftest
    exit 0
fi

# ---------------------------------------------------------------------------
# The report. Every check is independent — a failure in one does not skip
# the others (except the PATH check, which everything else depends on).
# ---------------------------------------------------------------------------

status_line() { # status_line <label> <ok|warn|fail|info> <detail>
    local icon
    case "$2" in
        ok) icon="[ok]  " ;;
        warn) icon="[warn]" ;;
        fail) icon="[FAIL]" ;;
        *) icon="[info]" ;;
    esac
    printf '%s %-28s %s\n' "$icon" "$1" "$3"
}

overall_fail=0

echo "espanso-doctor"
echo "=============="

# 1. On PATH?
if ! command -v espanso >/dev/null 2>&1; then
    status_line "espanso on PATH" fail "not found — install with: brew install --cask espanso"
    echo
    echo "Stopping here — nothing else can be checked without the binary."
    exit 1
fi
status_line "espanso on PATH" ok "$(command -v espanso)"

# 2. Installed version vs latest stable on GitHub.
raw_version=$(espanso --version 2>/dev/null || true)
installed=$(parse_version_output "$raw_version")
if [ -z "$installed" ]; then
    status_line "version" warn "could not parse 'espanso --version' output: $raw_version"
else
    latest_json=$(curl -fsS --max-time "$CURL_TIMEOUT" "$GITHUB_LATEST_URL" 2>/dev/null || true)
    if [ -z "$latest_json" ]; then
        status_line "version" info "installed $installed — latest stable unknown (offline, or GitHub unreachable)"
    else
        latest=$(strip_v "$(extract_tag_name "$latest_json")")
        if [ -z "$latest" ]; then
            status_line "version" info "installed $installed — could not parse GitHub's latest-release response"
        elif [ "$(version_compare "$installed" "$latest")" = "lt" ]; then
            status_line "version" warn "installed $installed — $latest is out: brew upgrade --cask espanso"
        else
            status_line "version" ok "installed $installed — up to date (latest stable: $latest)"
        fi
    fi
fi

# 3. Is the daemon actually running? Installed says nothing about this.
raw_status=$(espanso status 2>&1 || true)
case "$(parse_status_output "$raw_status")" in
    running) status_line "daemon" ok "running" ;;
    not-running)
        status_line "daemon" fail "not running — expansions will silently not fire"
        overall_fail=1
        ;;
    *) status_line "daemon" warn "could not tell: $raw_status" ;;
esac

# 4. Registered as a system service (auto-start on login)?
raw_check=$(espanso service check 2>&1 || true)
case "$(parse_service_check_output "$raw_check")" in
    registered) status_line "service registration" ok "registered (auto-starts on login)" ;;
    not-registered) status_line "service registration" warn "not registered — won't survive a reboot: espanso service register" ;;
    *) status_line "service registration" warn "could not tell: $raw_check" ;;
esac

# 5. macOS Accessibility permission.
# Verified empirically (2026-08-30, macOS): querying TCC.db for
# kTCCServiceAccessibility from an unprivileged shell returns zero rows
# unconditionally, whether or not Espanso is actually granted access. A
# script-based check here would always report "not granted" and would be
# actively misleading — so this is reported as unverifiable, not guessed.
if [[ "${OSTYPE:-}" == darwin* ]]; then
    status_line "Accessibility permission" info "cannot verify from a script — check System Settings > Privacy & Security > Accessibility > Espanso is ON"
fi

# 6. Where matches actually live.
raw_path=$(espanso path 2>&1 || true)
config_path=$(parse_config_path "$raw_path")
if [ -n "$config_path" ]; then
    status_line "config path" ok "$config_path"
else
    status_line "config path" warn "could not parse 'espanso path' output: $raw_path"
fi

echo
if [ "$overall_fail" -ne 0 ]; then
    echo "One or more checks failed. Nothing was changed — this tool only reports."
    exit 1
fi
echo "Nothing was changed — this tool only reports."
