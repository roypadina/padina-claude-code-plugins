# espanso-control

Teaches Claude Code the [Espanso](https://espanso.org) CLI — config paths, match YAML patterns,
package management — and adds `/espanso-doctor`, a preflight that checks the daemon, service
registration and config path before anyone trusts an expansion to fire.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install espanso-control@padina
```

## The problem

Espanso is a cross-platform text expander configured entirely through YAML files, driven by a CLI
whose subcommands have shifted across 2.x releases. A binary being installed and on PATH says
nothing about whether the daemon is actually running, registered to survive a reboot, or has the
macOS Accessibility permission it silently requires — expansions just don't fire, with no error
anywhere.

## Features

| Feature | Mechanism | File |
|---|---|---|
| The whole Espanso CLI, for Claude | skill | `skills/espanso-control/SKILL.md` |
| Match/config YAML patterns (variables, dates, shell) | skill reference | `skills/espanso-control/references/yaml-patterns.md` |
| `/espanso-doctor` — PATH, version, daemon, service, config path | slash command | `commands/espanso-doctor.md` → `scripts/espanso-doctor.sh` |

### `/espanso-doctor`

Six checks, each degrading independently rather than one bad check hiding the rest:

- `espanso` on PATH
- installed version vs. the latest stable release on GitHub (skips gracefully if offline)
- **daemon actually running** — the installed-binary equivalent of a token being present but never
  verified
- registered as a system service (auto-start on login)
- macOS Accessibility permission
- config path (`espanso path`)

It **only reports and advises** — it never restarts the daemon, registers the service, or edits
anything.

`scripts/espanso-doctor.sh --selftest` unit-tests the script's parsing functions against canned
strings offline, no network or `espanso` binary required.

### An honest limitation, not a guess

Espanso requires macOS Accessibility permission and fails **completely silently** without it — no
error, no crash, expansions just never fire. There is no reliable way to check that grant from a
script: querying `TCC.db` for `kTCCServiceAccessibility` from an unprivileged shell returns zero rows
whether or not the permission is actually granted, so a script that tried to report "granted" would
be wrong exactly when it mattered. `/espanso-doctor` reports this permission as **unverifiable** and
tells you where to check by hand (System Settings > Privacy & Security > Accessibility) rather than
claiming it's fine.

## Prerequisites

- **macOS**, [Espanso](https://espanso.org) installed (`brew install --cask espanso`), and its
  Accessibility permission granted — see above, nothing in this plugin can grant or verify that for
  you.
- Everything else is standard `bash`/`curl`, already on the system.

## Layout

```
.claude-plugin/plugin.json
commands/espanso-doctor.md              the /espanso-doctor slash command
scripts/espanso-doctor.sh               PATH · version · daemon · service · Accessibility · config path
skills/espanso-control/SKILL.md         the Espanso CLI, for Claude
skills/espanso-control/references/      yaml-patterns.md — match/config YAML syntax
```

## Checking it works

```bash
scripts/espanso-doctor.sh --selftest
```

Runs the parsing functions against canned strings — version output, daemon status text, service
registration text, config-path output, GitHub release JSON — no network or `espanso` binary touched.

## License

MIT © Roy Padina
