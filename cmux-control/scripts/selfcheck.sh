#!/usr/bin/env bash
#
# The one runnable check for the two pieces of real logic in this plugin:
# the "repo · branch" derivation, and cmux-sessions.py's profile handling.
# No framework — run it and read the output.
#
#   scripts/selfcheck.sh
#
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)

# shellcheck source=cmux-hook.sh
CMUX_HOOK_LIB=1 . "$here/cmux-hook.sh"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
git_() { git -c user.email=selfcheck@example.com -c user.name=selfcheck -c commit.gpgsign=false "$@"; }

fails=0
check() { # check <expected> <actual> <what>
    if [ "$1" = "$2" ]; then
        printf 'ok    %s\n' "$3"
    else
        printf 'FAIL  %s\n        expected [%s]\n        got      [%s]\n' "$3" "$1" "$2"
        fails=$((fails + 1))
    fi
}

mkdir -p "$tmp/plain dir"
check "plain dir" "$(workspace_label "$tmp/plain dir")" "a non-git directory falls back to its basename"

git_ init -q -b main "$tmp/myrepo"
git_ -C "$tmp/myrepo" commit -q --allow-empty -m init
check "myrepo · main" "$(workspace_label "$tmp/myrepo")" "repo + branch"

git_ -C "$tmp/myrepo" checkout -q -b feature/RD-12851
check "myrepo · feature/RD-12851" "$(workspace_label "$tmp/myrepo")" "a branch name with a slash survives whole"

mkdir -p "$tmp/myrepo/src/deep"
check "myrepo · feature/RD-12851" "$(workspace_label "$tmp/myrepo/src/deep")" "a subdirectory still reports the repo"

sha=$(git_ -C "$tmp/myrepo" rev-parse --short HEAD)
git_ -C "$tmp/myrepo" checkout -q --detach HEAD
check "myrepo · @$sha" "$(workspace_label "$tmp/myrepo")" "detached HEAD shows the sha"
git_ -C "$tmp/myrepo" checkout -q feature/RD-12851

git_ -C "$tmp/myrepo" worktree add -q -b wt/topic "$tmp/wt-checkout" >/dev/null 2>&1
check "myrepo · wt/topic" "$(workspace_label "$tmp/wt-checkout")" "a worktree keeps the MAIN repo name"

git_ init -q -b main --bare "$tmp/bare.git"
check "bare · main" "$(workspace_label "$tmp/bare.git")" "a bare repo drops the .git suffix"

python3 "$here/cmux-sessions.py" --self-check || fails=$((fails + 1))

if [ "$fails" -ne 0 ]; then
    printf '\n%s check(s) failed\n' "$fails" >&2
    exit 1
fi
printf '\nall checks passed\n'
