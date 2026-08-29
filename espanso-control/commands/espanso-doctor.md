---
description: Preflight-check Espanso — PATH, version, daemon status, service registration, config path
argument-hint: "[--selftest] — no argument runs the real checks"
allowed-tools:
  - Bash
---

Run the bundled doctor script:

```
"${CLAUDE_PLUGIN_ROOT}/scripts/espanso-doctor.sh" $ARGUMENTS
```

With no `$ARGUMENTS` it checks, each degrading independently rather than aborting the rest:

- `espanso` on PATH
- installed version vs the latest stable release on GitHub (skipped gracefully if offline)
- whether the **daemon is actually running** — installed says nothing about whether expansion works
- whether it is registered as a system service (auto-start on login)
- macOS Accessibility permission — **reported as unverifiable**, not guessed; see the skill for why
- where its config actually lives (`espanso path`)

`--selftest` unit-tests the script's parsing functions against canned strings — no network, no
`espanso` binary required.

It only reports and advises. It never restarts the daemon, registers the service, or touches config —
if a check fails, tell the user what to run themselves.

Report the result compactly: pass/warn/fail per line, already formatted by the script. Don't
re-summarize it into prose — show its output.
