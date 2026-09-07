#!/usr/bin/env bash
#
# Wire the Joplin MCP server into the local Claude Code and Codex clients,
# and install the skill where Codex looks for it.
#
# Both clients get the same stdio bridge rather than the raw
# http://127.0.0.1:PORT/mcp?token=... URL. That is deliberate: the URL form
# would write the token into ~/.claude.json (mode 644 on a default install)
# and ~/.codex/config.toml, and would have to be rewritten every time the
# token is renewed. The bridge reads the token from Joplin's own profile at
# call time, so no client config ever contains the secret.
#
#   scripts/joplin-mcp-install.sh            install for every client found
#   scripts/joplin-mcp-install.sh --print    show what it would run, change nothing
#   scripts/joplin-mcp-install.sh --remove   undo: drop the servers and the skill link
#
# Claude Code profiles: by default every profile directory that exists among
# ~/.claude, ~/.claude-work2 and ~/.claude3 is configured, because MCP config
# is per-profile and a partial install makes the profiles diverge silently.
# Set JOPLIN_CLAUDE_PROFILES to override with a space-separated list.
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$HERE/.." && pwd)"
BRIDGE="$HERE/joplin-mcp-stdio.py"
SERVER_NAME="joplin"
CODEX_SKILL_DIR="$HOME/.codex/skills/joplin-control"
SKILL_SOURCE="$PLUGIN_ROOT/skills/joplin-control"

DRY_RUN=0
MODE=install

# "default" is a sentinel, not a path. The default profile must be addressed by
# NOT setting CLAUDE_CONFIG_DIR: with it unset the CLI reads ~/.claude.json,
# but setting it to ~/.claude redirects to ~/.claude/.claude.json — a different
# file that the default profile does not read, so the server would be written
# somewhere Claude Code never looks.
CLAUDE_PROFILES=${JOPLIN_CLAUDE_PROFILES:-"default $HOME/.claude-work2 $HOME/.claude3"}

# claude_for <profile> <args...> — run the claude CLI against one profile.
claude_for() {
    local profile="$1"; shift
    if [ "$profile" = default ]; then
        claude "$@"
    else
        CLAUDE_CONFIG_DIR="$profile" claude "$@"
    fi
}

# profile_exists <profile>
profile_exists() {
    [ "$1" = default ] || [ -d "$1" ]
}

# label_for <profile> — what to print
label_for() {
    if [ "$1" = default ]; then echo "default (~/.claude.json)"; else echo "$1"; fi
}

run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  would run: %s\n' "$*"
    else
        "$@"
    fi
}

install_claude() {
    command -v claude >/dev/null 2>&1 || { echo "claude CLI not on PATH — skipping Claude Code"; return; }
    local profile
    for profile in $CLAUDE_PROFILES; do
        profile_exists "$profile" || continue
        echo "Claude Code profile: $(label_for "$profile")"
        # Remove first so a re-run updates rather than erroring on a duplicate.
        if [ "$DRY_RUN" -eq 1 ]; then
            printf '  would run: [%s] claude mcp remove --scope user %s (ignoring failure)\n' "$profile" "$SERVER_NAME"
            printf '  would run: [%s] claude mcp add --scope user %s -- %s\n' "$profile" "$SERVER_NAME" "$BRIDGE"
        else
            claude_for "$profile" mcp remove --scope user "$SERVER_NAME" >/dev/null 2>&1 || true
            claude_for "$profile" mcp add --scope user "$SERVER_NAME" -- "$BRIDGE"
            # Adding is not proof of anything — confirm the profile can read it back.
            if claude_for "$profile" mcp get "$SERVER_NAME" >/dev/null 2>&1; then
                echo "  verified: this profile can see '$SERVER_NAME'"
            else
                echo "  WARNING: added, but '$SERVER_NAME' is not readable back from this profile"
            fi
        fi
    done
}

remove_claude() {
    command -v claude >/dev/null 2>&1 || return 0
    local profile
    for profile in $CLAUDE_PROFILES; do
        profile_exists "$profile" || continue
        echo "Claude Code profile: $(label_for "$profile")"
        if [ "$DRY_RUN" -eq 1 ]; then
            printf '  would run: [%s] claude mcp remove --scope user %s\n' "$profile" "$SERVER_NAME"
        else
            claude_for "$profile" mcp remove --scope user "$SERVER_NAME" >/dev/null 2>&1 ||
                echo "  (no '$SERVER_NAME' server to remove)"
        fi
    done
}

install_codex() {
    command -v codex >/dev/null 2>&1 || { echo "codex CLI not on PATH — skipping Codex"; return; }
    echo "Codex: $HOME/.codex/config.toml"
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  would run: codex mcp remove %s (ignoring failure)\n' "$SERVER_NAME"
        printf '  would run: codex mcp add %s -- %s\n' "$SERVER_NAME" "$BRIDGE"
    else
        codex mcp remove "$SERVER_NAME" >/dev/null 2>&1 || true
        codex mcp add "$SERVER_NAME" -- "$BRIDGE"
    fi

    # Codex reads skills from ~/.codex/skills/<name>/SKILL.md, the same format
    # Claude Code plugins use. Symlink rather than copy so there is one source
    # of truth and an update to the plugin is picked up with no re-install.
    echo "Codex skill: $CODEX_SKILL_DIR -> $SKILL_SOURCE"
    run mkdir -p "$HOME/.codex/skills"
    if [ -e "$CODEX_SKILL_DIR" ] && [ ! -L "$CODEX_SKILL_DIR" ]; then
        echo "  refusing to replace $CODEX_SKILL_DIR — it is a real directory, not a symlink. Move it aside first."
        return
    fi
    run ln -sfn "$SKILL_SOURCE" "$CODEX_SKILL_DIR"
}

remove_codex() {
    command -v codex >/dev/null 2>&1 || return 0
    echo "Codex: $HOME/.codex/config.toml"
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  would run: codex mcp remove %s\n' "$SERVER_NAME"
        printf '  would run: rm %s (only if it is a symlink)\n' "$CODEX_SKILL_DIR"
        return
    fi
    codex mcp remove "$SERVER_NAME" >/dev/null 2>&1 || echo "  (no '$SERVER_NAME' server to remove)"
    # Only ever unlink our own symlink; never recursively delete a real directory.
    if [ -L "$CODEX_SKILL_DIR" ]; then rm "$CODEX_SKILL_DIR"; echo "  removed skill symlink"; fi
}

preflight() {
    [ -x "$BRIDGE" ] || { echo "error: bridge not executable at $BRIDGE" >&2; exit 1; }
    [ -d "$SKILL_SOURCE" ] || { echo "error: skill source missing at $SKILL_SOURCE" >&2; exit 1; }
    "$BRIDGE" --selftest >/dev/null || { echo "error: bridge selftest failed — refusing to install" >&2; exit 1; }
}

while [ $# -gt 0 ]; do
    case "$1" in
        --print | --dry-run) DRY_RUN=1 ;;
        --remove) MODE=remove ;;
        --help | -h) sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown argument '$1' (try --help)" >&2; exit 2 ;;
    esac
    shift
done

if [ "$MODE" = remove ]; then
    echo "Removing the Joplin MCP wiring"; echo
    remove_claude
    echo
    remove_codex
else
    preflight
    echo "Installing the Joplin MCP bridge: $BRIDGE"; echo
    install_claude
    echo
    install_codex
    echo
    echo "Restart any running Claude Code or Codex session — MCP servers are"
    echo "connected at startup, so an open session will not see it until then."
    echo "Then verify with: $HERE/joplin-doctor.sh"
fi
