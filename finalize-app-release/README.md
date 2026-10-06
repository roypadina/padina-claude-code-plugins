# finalize-app-release

One skill that runs the end-of-dev release checklist for my Mac apps (LanGuard, MaccyPlus, VaultBar,
Window Organizer, SmartHiddenBar, MeetAlert, Agents Monitor, agentctl, claude-jam — and the next one),
so nothing gets missed when a version ships.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install finalize-app-release@padina
```

## The problem

Shipping a small Mac app is twenty little steps across four repos: the version, the CHANGELOG, the
README, the wiki, Ko-fi links, the GitHub release and its zip, the Homebrew cask, the tap's README,
pushing it all, and upgrading the copy you actually run. Each one is easy. One of them is always
forgotten — and a tap push that silently failed still upgrades your own Mac, so you never notice.

## What you get

- **`/finalize-app-release [app] [recheck]`** — run it at the end of a session. Claude also offers it
  on its own when work on one of these apps wraps up ("release", "ship it", "push all", a version
  bump, a release build).
- **A state script** (`scripts/release-state.sh`) that checks the mechanical part in about ten
  seconds and prints `OK` / `GAP` / `WARN` lines: version source vs tag vs GitHub release vs cask, the
  release asset name and sha256 vs the cask, tap and wiki pushed **to the server** (not just a local
  ref), tap README row, CHANGELOG/appcast top entry, README install line, Ko-fi in the README,
  `FUNDING.yml`, wiki and app, stale mentions of the previous version, and the installed copy in
  `/Applications` (version, quarantine, running from where).
- **The checklist** Claude works through for the gaps: docs, Ko-fi and About window, release, tap,
  local install, memory note, cleanup, report.
- **"Already done" memory** — after a clean run the script stamps the state
  (`~/.local/state/finalize-app-release/`). Next time, if the repo, wiki and tap haven't changed, it
  says so and skips the review. `recheck` forces a full pass.
- **A first-publish guide** for a new public app: privacy triple check, community files, branch
  protection, icons, About window with Ko-fi, wiki, first cask.

Public steps (push, tag, release, tap) run only when you asked for a release in that session;
anything net-new (going public, a new cask) always asks first.

## Requirements

macOS, `git`, the GitHub CLI `gh` logged in as the repo owner, Homebrew, and the tap checked out at
`~/Code/Padina/homebrew-tap` (override with `TAP_WORK`). It is written for my own repos and accounts —
fork it and change `OWNER` in the script and the account details in `SKILL.md` to use it for yours.
