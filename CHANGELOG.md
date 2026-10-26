# Changelog

Changes to the `padina` Claude Code plugin marketplace, newest first. The marketplace has no
releases; sections are dated and name the plugin version each change shipped in (every plugin's
version is in its `.claude-plugin/plugin.json`). Format follows
[Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

## 2026-10-26

### Added
- session-management 0.3.3: a `Stop` hook and the `/finish-session` close call `~/.claude/bin/claudwork touch`
  when that script exists, so a per-session work folder keeps its last-update / status stamp.

## 2026-10-25

### Changed
- cmux-control 0.2.4, session-management 0.3.2: wording no longer names the retired ccpool; cmux-control notes
  that a restored pane replays the wrapper it was first opened with.

### Added
- agents-session-hopper 0.1.0: a skill that teaches Claude to steer AgentsSessionHopper (account,
  usage, switch, hold, picking work back up after a move).

### Changed
- finalize-app-release 0.4.1: the state script reads a Swift `static let version` as the
  source version (AgentsSessionHopper).
- finalize-app-release 0.4.0: every version and release needs a CHANGELOG entry, non-empty release
  notes and the site's "What's new"; the state script GAPs when the CHANGELOG lacks the latest tag,
  the release notes are empty, the tap CHANGELOG lacks the cask version or the live site page does
  not show the latest tag.
- finalize-app-release 0.3.0: releases must be signed with the stable `KeyLayoutSwitcher Dev`
  identity; the state script checks the latest release asset.
- finalize-app-release 0.2.1: strip every `CLAUDE*` variable when relaunching an app; MaccyPlus
  sync and signing quirks.
- finalize-app-release 0.2.0: marketing site and repo marketing steps for releases and new apps; the
  state script warns when the GitHub homepage or README does not link the site page.

### Added
- This CHANGELOG.

## 2026-10-24

### Changed
- finalize-app-release 0.1.12: LanGuard row (wiki clone, universal build, Update helper step).
- finalize-app-release 0.1.11: the state script sees pre-releases and backticked SHA-256 lines.
- finalize-app-release 0.1.10: the `apps.json` one-liner can reformat the whole file; check the diff.

## 2026-10-23

### Changed
- finalize-app-release 0.1.9: release notes carry a SHA-256 first line; the state script checks it.
- finalize-app-release 0.1.8: update the marketing site's `apps.json` on release; GAP when the site
  lags the latest tag.
- agentctl is CLI-only (0.11.0): menu-bar mentions dropped; finalize-app-release checks binary-only
  casks.
- README: plugin table, Ko-fi, website badge, social preview; manifest-validation CI and CODEOWNERS.

## 2026-10-22

### Fixed
- cmux-control 0.2.3: pin and pane-size caveat, safety rules, cross-references.

## 2026-10-20

### Changed
- finalize-app-release 0.1.6: warn when the running app predates the installed binary.

## 2026-10-19

### Changed
- finalize-app-release 0.1.5: detect `build.sh` + `Info.plist` apps, fresh-repo publish recipe,
  ObsidianVaultGitWatcher row.

## 2026-10-15

### Changed
- finalize-app-release 0.1.4: `brew style` the working-copy cask file; AgentsMonitor local-install
  quirk.

## 2026-10-13

### Changed
- cmux-control: note that a post-panic restore leaves Claude panes as bare shells.

## 2026-10-11

### Changed
- session-management 0.3.1: `/session-recap` drops the `/compact` verdict step.
- session-management 0.3.0: `/resume-all` restores work stopped by sleep, a network change or an
  account switch.

## 2026-10-10

### Changed
- session-management 0.2.2: `/finish-session` cleanup and close arguments.
- session-management 0.2.0: `/close-session` merged into `/finish-session`; reliable pane close.

### Fixed
- session-management 0.2.1: the close hook finds itself and accepts trailing filler.

## 2026-10-07

### Added
- maccyplus-clipboard 0.1.0: leave labelled values in the MaccyPlus clipboard history.

### Changed
- finalize-app-release 0.1.3: ignore appcast-only commits after the tag; MaccyPlus wiki clone name.
- finalize-app-release 0.1.2: update the Obsidian Mac inventory note on release.

## 2026-10-06

### Added
- finalize-app-release: end-of-dev release checklist for the Mac apps, with a state script; also run
  from `/finish-session`, personal apps only.

## 2026-10-05

### Changed
- session-management: `/session-recap` reads the real context percentage from a status-line tap.

### Fixed
- session-management: close only this session's own cmux pane, never by `$CMUX_WORKSPACE_ID`.

## 2026-10-04

### Added
- session-management: session recap, close-out and final close commands.

## 2026-10-03

### Changed
- cmux-control 0.2.1: document `identify` returning `caller=null` after a pane moves workspaces.

## 2026-09-28

### Changed
- cmux-control: send / send-key pitfalls.

## 2026-09-26

### Removed
- joplin-control plugin.

## 2026-09-07

### Added
- joplin-control: local Joplin notes for Claude Code and Codex.

## 2026-08-30

### Added
- espanso-control and recipe-research plugins.

### Changed
- cmux-control: the SessionStart tab/workspace naming hook is gone (breaking).

### Fixed
- Docs claims that did not match the code, across all five plugins.

## 2026-08-29

### Added
- cmux-control: wires Claude Code into cmux.
- agentctl-sessions: session names, labels, notes, flags, reminders, due dates; hide and delete.
- heeng-keyboard-translator; READMEs for the marketplace and its plugins.
