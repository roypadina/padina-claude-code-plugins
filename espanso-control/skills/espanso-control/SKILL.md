---
name: espanso-control
description: Use when managing Espanso text expansion on macOS, including installing Espanso, editing match/config YAML, adding/removing/updating snippets, listing or installing Espanso Hub packages, troubleshooting daemon status, or running the /espanso-doctor preflight.
---

# Espanso Control

## Overview

Espanso is a text expander configured by YAML files under its config directory. Prefer the `espanso`
CLI for paths, package management, and status checks. Everything below is verified against
**Espanso 2.4.0** (current latest stable as of 2026-08-30) — if you're on a different version, re-check
with `espanso <subcommand> --help` before trusting a command that isn't in the Quick Commands table.

Run `/espanso-doctor` first when something seems off, or before telling the user an expansion
"should" work — it checks PATH, version, daemon status, service registration, and config path in one
shot. See [Preflight](#preflight-espanso-doctor) below for what it can and can't verify.

## Quick Commands

| Goal | Command |
|---|---|
| Locate config | `espanso path` |
| Open config in editor | `espanso edit` (defaults to `match/base.yml`) |
| Is the daemon running? | `espanso status` or `espanso service status` |
| Is it registered as a system service? | `espanso service check` |
| Start app on macOS | `open -a Espanso` |
| Restart service | `espanso service restart` |
| Open search bar | `espanso cmd search` |
| List matches (verifies config parses) | `espanso match list` |
| List installed packages | `espanso package list` |
| Install Hub package | `espanso package install <name>` |
| Update one package | `espanso package update <name>` |
| Update all packages | `espanso package update all` |
| Remove package | `espanso package uninstall <name>` |

`espanso match list` prints the user's actual trigger/replace pairs to stdout — treat that output as
sensitive, the same way you would a config file. Don't quote it back or persist it anywhere unless
the user is deliberately reviewing their own snippets.

## Workflow

1. Run `espanso path` first unless the user gave an explicit config path.
2. Inspect existing files before editing, usually `match/base.yml` and `config/default.yml`.
3. Preserve YAML indentation and existing comments unless the user asks for cleanup.
4. Make the smallest matching edit.
5. Verify with `espanso match list`, `espanso status`, and/or `espanso service restart`.
6. If Espanso is not running, tell the user and use `open -a Espanso` only when they asked to start it.

## Config Paths

Typical macOS layout (confirmed via `espanso path` on 2.4.0):

```text
~/Library/Application Support/espanso          <- Config
~/Library/Application Support/espanso/match    <- match/*.yml files
~/Library/Application Support/espanso/match/packages
~/Library/Application Support/espanso/config   <- config/*.yml files
~/Library/Caches/espanso                       <- Runtime
```

Don't hard-code these without checking `espanso path` — they can differ by platform or install
method (Linux commonly uses `~/.config/espanso`).

## Editing Matches

Read [references/yaml-patterns.md](references/yaml-patterns.md) before adding anything more complex
than a simple trigger/replace pair.

Default file for global snippets:

```text
~/Library/Application Support/espanso/match/base.yml
```

Simple pattern:

```yaml
matches:
  - trigger: ":email"
    replace: "someone@example.com"
```

Multi-line pattern:

```yaml
matches:
  - trigger: ":sig"
    replace: |
      Best regards,
      Your Name
```

When adding snippets, avoid duplicate triggers. Search existing match files first:

```bash
rg -n 'trigger:\s*":email"' "$(espanso path | awk -F': ' '/^Config:/ {print $2}')/match"
```

## Packages

Use the CLI for package operations (verified subcommands on 2.4.0 — `install`, `list`, `uninstall`,
`update`):

```bash
espanso package install <package-name>
espanso package update all
espanso package uninstall <package-name>
```

Espanso 2.4.0's `package` subcommand has **no CLI search** — `espanso package --help` lists only
`install` / `list` / `uninstall` / `update`. For lookup/discovery, search the Espanso Hub site:

```text
https://hub.espanso.org/<package-name>
https://hub.espanso.org/
```

When installing a package from Hub, prefer a normal verified install. Use `--external`, `--git`, or
`--force` only when the user explicitly requests it or the package source requires it.

## App Configuration

Global options live in `config/default.yml`. Common edits:

```yaml
toggle_key: ALT
search_shortcut: ALT+SPACE
backend: Clipboard
auto_restart: true
clipboard_threshold: 100
```

On macOS, `ALT` means Option. The default search shortcut is commonly `Option+Space`; if unavailable
or conflicting, set `search_shortcut` explicitly.

**Unverified in this pass** — these keys are documented behavior from the original skill; they were
not re-tested against 2.4.0 (would require restarting the daemon, which this plugin never does
unprompted). Treat them as likely-correct, not confirmed.

## macOS Notes

- **Accessibility permission is required and Espanso fails silently without it** — no error, no
  crash, expansions just never fire. Grant it at System Settings > Privacy & Security > Accessibility
  > Espanso.
- **There is no reliable script-based way to check whether that permission is granted.** Verified
  empirically (2026-08-30): reading `~/Library/Application Support/com.apple.TCC/TCC.db` for
  `kTCCServiceAccessibility` from an unprivileged shell returns **zero rows unconditionally** —
  whether or not Espanso actually has the grant — so a script that tried to report "granted" from
  that query would be wrong every time it mattered. `/espanso-doctor` reports this permission as
  **unverifiable** rather than guessing. Don't tell a user "Accessibility looks fine" based on any
  automated check — only a human looking at System Settings can confirm it.
- If expansions do not fire after valid config edits, check `espanso status` first, then restart the
  service/app.
- Homebrew install command: `brew install --cask espanso`.
- App path after Homebrew cask install: `/Applications/Espanso.app` (confirmed via `brew info --cask
  espanso`).

## Preflight: `/espanso-doctor`

Run `/espanso-doctor` before diagnosing "my snippet didn't expand" from scratch — it's the espanso
equivalent of "the API key is present but nobody checked whether it's actually valid." A binary being
installed says nothing about whether the daemon is running, registered, or has permission to inject
text.

It checks, each degrading independently rather than the whole thing failing on one bad check:

- `espanso` on PATH
- installed version vs. the latest stable GitHub release (skips gracefully if offline)
- daemon actually running (`espanso status`)
- registered as a system service (`espanso service check`)
- Accessibility permission — reported as unverifiable, see above
- config path (`espanso path`)

It only reports and advises — never restarts the daemon, never registers the service, never installs
anything. If it flags a problem, tell the user the command to run themselves.

`scripts/espanso-doctor.sh --selftest` unit-tests its parsing functions against canned strings, no
network or `espanso` binary involved — run it after touching the script.

## Verification

After edits:

```bash
espanso status
espanso match list
espanso service restart
```

If `espanso service restart` fails because the service is not registered, report that and use
`open -a Espanso` for app launch when appropriate.

## Keeping this skill current

This is a living document, verified against Espanso 2.4.0 on 2026-08-30. Espanso's CLI has changed
across 2.x releases before (the `package search` subcommand existed in some builds and was removed;
subcommand names have shifted). If a command in the Quick Commands table fails on a newer Espanso:

1. Re-check with `espanso <subcommand> --help` before assuming the skill is wrong.
2. Patch this file with the correction.
3. **Quote the verbatim error string** in a short note near the corrected command — future agents
   grep for the exact text when the same failure recurs.
