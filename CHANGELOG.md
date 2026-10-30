# Changelog

Changes to the `padina` Claude Code plugin marketplace, newest first. The marketplace has no
releases; sections are dated and name the plugin version each change shipped in (every plugin's
version is in its `.claude-plugin/plugin.json`). Format follows
[Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

## 2026-10-30

### Added
- smart-compact 0.1.0: new plugin. `/smart-compact` reads the session without asking anything and copies
  a tuned `/compact` instruction to the clipboard, plus a handoff file (goal, decisions with reasons,
  do-not-redo, next step); free-text dials (`long haul`, `minimize`, a mode name) set depth and size.
  Hooks: PreCompact refreshes the handoff and backs up the whole session (transcript gzip-copied,
  subagents and tool results hardlinked; newest per session, 5 GB cap); SessionStart re-injects the
  handoff capped at 9,000 chars, most important sections first, with the notes' real age; Stop nudges
  once at 50/70/85 % fill. `search` gives the model bounded hits over the full session instead of
  guessing. Shares its state dir with a same-script copy in another marketplace; each hook event runs once.

### Changed
- finalize-app-release 0.5.2: Step 1 note — the state script skips worktrees outside ~/Code/Padina, run it on the shared clone; PullPing row in the per-app table.
- finalize-app-release 0.5.1: rule for parallel sessions releasing the same app — fetch tags, take the next free version above the latest tag, coordinate tap/site bumps.
- mac-design 0.1.3: two window gotchas in `swiftui-appkit.md` — a reused window (`isReleasedWhenClosed = false`) keeps SwiftUI timers running after close (drop it on `willClose`), and windows report `isVisible == false` while the app is hidden.
- mac-design 0.1.2: MBX-12 — a menu-bar panel's action menu is a More menu (`ellipsis.circle`) matching the right-click menu; a gear only for a button that opens Settings directly.

## 2026-10-29

### Added
- ghostex-control 0.1.0: new plugin. A skill to drive the Ghostex agent workspace through its `ghostex`
  / `gx` CLI: find your own session, start terminal and agent sessions (`create-session --input …
  --start`, no `.zshrc` race), type into, read, wait on and close them, with hard safety rules, the
  CLI's traps (`terminal` is not started, `send-message` signs and falls back to an agent id,
  substring titles and shared numeric aliases), a full command reference with risk classes, and
  routing to the skills Ghostex bundles in the app.
- session-management 0.4.0: the `/finish-session` close also closes a Ghostex session (`ghostex kill`),
  confirmed by its `zmx run` process on the session's own process chain; selfcheck covers it.

### Changed
- finalize-app-release 0.5.0: plugin updates get the same pass as app releases. The state script has a
  marketplace mode (a repo with `.claude-plugin/marketplace.json`): per plugin it GAPs on changes after the
  last version bump, a missing CHANGELOG line, README row or section, wiki page, Home row or sidebar link,
  and an older installed copy in any Claude config dir (`FAR_CLAUDE_DIRS`); it checks the wiki push and
  prints the site card. The skill has a Plugin marketplace checklist: bump, CHANGELOG, READMEs, wiki, site
  card, push + CI, install on every profile, inventory.
- mac-design 0.1.1: ships the Review-mode feedback (Settings window snippet, rules MBX-22 and SYM-8, 243
  rules) to installs made before it landed under 0.1.0.
- heeng-keyboard-translator 0.1.1: ships the 2026-08-30 skill wording fix, which landed after the 0.1.0
  bump, to existing installs.
- cmux-control 0.2.5: check that the shell is inside cmux, not Ghostex, before pane work.
- finalize-app-release 0.4.7: the plugin marketplace repo is no longer just `SKIP`ped — the skill lists
  its docs to keep in step after a plugin change (CHANGELOG, root and plugin README, wiki page + Home +
  sidebar, site card).
- ghostex-control 0.1.3: keyboard-shortcut questions are answered from the live hotkey list
  (`ghostex settings hotkeys list [word]`, `--terminal` for terminal-focused keys) and
  `ghostex guide hotkeys`, in one call, instead of searching the bundled `ghostex-help` skill.
- ghostex-control 0.1.2: pitfall — Session Chat's `$` skill picker lists only skill folders, never
  Claude Code plugin skills or commands; type the full `/<plugin>:<name>` or use the terminal view.
- ghostex-control 0.1.1: live runs settled three open points — `create-session --start` leaves focus
  on the caller, its result carries `session.globalRef`, and a `claude` child reaches its parent over
  Claude Code's `ListAgents` / `SendMessage`. New trap: a Claude Code child keeps only the visible
  screen and `wait-for-text` never matched its banner, so wait for a line of your own prompt.

## 2026-10-28

### Added
- mac-design 0.1.0: new plugin. A skill to design, build and review native macOS app UI/UX (SwiftUI +
  AppKit, macOS 14–27): 243 rules with IDs, severities, version gates and sources; topic references
  (Liquid Glass, windows and toolbars, menus and keyboard, Settings, menu-bar apps, permission flows,
  accessibility, icons, SwiftUI/AppKit patterns, native feel); an audit mode with a ranked fix list;
  `hig.sh` for Apple's current HIG text. Built on BAMA's design skills (MIT).

### Changed
- finalize-app-release 0.4.3: gh via a `ghp` function (a zsh variable leaks the token in its error), site page URL `/apps/<slug>/`,
  site clone with another session's edit (fetch, no pull), MaccyPlus appcast in its own PR, MeetAlert plist bump with sed.

## 2026-10-27

### Added
- obsidian-vault-manager 0.1.0: new plugin. Vault Structure note with a writers registry and a last-review
  marker, regenerable index, safe restructuring, reference updates after moves; git and non-git vaults.

### Changed
- finalize-app-release 0.4.2: the Mac inventory note path follows the vault restructure (`MAC/` is now
  `Setup/Mac/`).

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
- agentctl-sessions 0.2.1: the session picker is the agentctl TUI only.
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
- espanso-control 0.1.0 and recipe-research 0.1.0 plugins.

### Changed
- cmux-control: the SessionStart tab/workspace naming hook is gone (breaking).

### Fixed
- Docs claims that did not match the code, across all five plugins.

## 2026-08-29

### Added
- cmux-control: wires Claude Code into cmux.
- agentctl-sessions: session names, labels, notes, flags, reminders, due dates; hide and delete.
- heeng-keyboard-translator 0.1.0; READMEs for the marketplace and its plugins.
