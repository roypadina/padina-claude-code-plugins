---
description: Preflight the Joplin integration — app running, clipper port, token, Data API, MCP server, enabled tools, client wiring
argument-hint: "[--selftest] — no argument runs the real checks"
allowed-tools:
  - Bash
---

Run the bundled doctor script:

```
"${CLAUDE_PLUGIN_ROOT}/scripts/joplin-doctor.sh" $ARGUMENTS
```

With no `$ARGUMENTS` it checks, each degrading independently rather than aborting the rest:

- Joplin desktop actually running — both interfaces die with the app
- which port the Web Clipper service really landed on (Joplin walks 41184 → 41194)
- an `api.token` exists, reported as a length + hash fingerprint, **never** the token itself
- the Data API accepts that token
- the MCP server answers `initialize`
- which MCP tools are genuinely enabled, via `tools/list` — the applied state, not the docs
- whether Claude Code and Codex each have the `joplin` server, and whether the Codex skill is linked

It warns separately when write-capable tools are on (Joplin does not confirm agent writes) and when
`delete_note` is on.

`--selftest` unit-tests the script's parsers against canned JSON — no Joplin, no network.

It only reports and advises. It never enables a setting, renews a token, edits a client config or
touches a note — if a check fails, tell the user what to click themselves.

Report the result compactly: show the script's output as-is rather than re-summarizing it into
prose. If a line fails, quote the matching section of
`${CLAUDE_PLUGIN_ROOT}/skills/joplin-control/references/troubleshooting.md`.
