#!/usr/bin/env bash
#
# UserPromptSubmit hook. When the user's whole message is a session-close reply ("close",
# "1,3 then close", "ok, close it"), hand Claude the /finish-session instructions, so `close`
# still works after /compact dropped the command text. Any other prompt: prints nothing.
# Fails soft — any error prints nothing and exits 0, so it can never block a prompt.
#
p=$(jq -r '.prompt // empty' 2>/dev/null) || exit 0
shopt -s nocasematch
sep='[[:space:][:punct:]]'
word='(ok|okay|yes|please|then|and|done|go|all|none|[0-9]+)'
re="^${sep}*(${word}${sep}+)*close([[:space:]]+(it|this|session|pane|out))?${sep}*$"
[[ $p =~ $re ]] || exit 0

f="${CLAUDE_PLUGIN_ROOT:-}/commands/finish-session.md"
[ -r "$f" ] || exit 0
body=$(awk 'NR == 1 && /^---$/ { fm = 1; next } fm && /^---$/ { fm = 0; next } !fm' "$f")
body=${body//'${CLAUDE_PLUGIN_ROOT}'/$CLAUDE_PLUGIN_ROOT}
body=${body//'$ARGUMENTS'/(none — the user replied \`$p\`)}
jq -n --arg c "The user's message looks like a reply to close this session. Below is /finish-session; \
apply its step 5 Trigger rule to decide. If \`close\` plainly answers something else you just asked, ignore this.

$body" '{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $c}}' 2>/dev/null || exit 0
