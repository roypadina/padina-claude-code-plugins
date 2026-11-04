# finalize-app-release

One skill that runs the end-of-dev release checklist for my Mac apps (LanGuard, MaccyPlus, VaultBar,
Window Organizer, SmartHiddenBar, MeetAlert, Agents Monitor, agentctl, claude-jam — and the next one),
so nothing gets missed when a version ships — and the same pass for a plugin change in this
marketplace.

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
  ref), tap README row and tap CHANGELOG line, CHANGELOG/appcast top entry and an entry for the
  latest tag, non-empty release notes with the SHA-256 line, README install line, README, wiki and site
  screenshots that are transparent (their text vanishes in GitHub dark mode; `WARN` with a dark preview
  image to look at; needs `ffmpeg` + `dwebp`), the demo (README GIF + `docs/demo/render.sh`, UI commits since its
  last render, the site's `demo` field, video and poster, orphan gif/mp4/webp/png in the repo and on the site), Ko-fi in the README,
  `FUNDING.yml`, wiki and app, stale mentions of the previous version, and the installed copy in
  `/Applications` (version, quarantine, running from where), and that the app's entry on my
  marketing site (`roypadina-apps/data/apps.json`, override `SITE_WORK`) is not behind the latest tag
  (skipped for apps not on the site or when the site repo is absent), and that the live app page's
  "What's new" (built from `CHANGELOG.md`) shows the latest tag.
- **Sparkle in-app updates** — the recipe for adding Sparkle to an app (one shared EdDSA key, feed = the latest
  release's `appcast.xml`, cask `auto_updates true`); the state script flags a missing feed asset or an unsigned item.
- **Demo lifecycle** — every public app gets a looping "how it works" GIF (README) and MP4 (site), rendered
  offscreen from the app's real views with a bundled kit (`references/demo.md`, `references/demo-kit/`). A new app gets
  one, a UI change re-renders it for README and site together, a removed feature or replaced clip leaves no orphan files.
- **Review gate** — before anything public, one `fable` reviewer checks the whole diff (code, CHANGELOG, notes, README,
  wiki, images and demo, site files) for correctness, look, privacy, links and version consistency; only `APPROVE` unlocks the push.
- **The checklist** Claude works through for the gaps: docs, Ko-fi and About window, release, tap,
  marketing-site data, local install, memory note, cleanup, report.
- **"Already done" memory** — after a clean run the script stamps the state
  (`~/.local/state/finalize-app-release/`). Next time, if the repo, wiki and tap haven't changed, it
  says so and skips the review. `recheck` forces a full pass.
- **Plugin marketplace mode** — run on this marketplace repo, the script checks each plugin instead:
  commits after its last version bump, its CHANGELOG line, README row and section, wiki page, Home row
  and sidebar link, the wiki push, and an older installed copy in any Claude config dir
  (`FAR_CLAUDE_DIRS`, default `~/.claude ~/.claude-work2 ~/.claude3`). It prints the site card's text
  for review. The skill's checklist adds the push, CI and the install on every profile.
- **A first-publish guide** for a new public app: privacy triple check, community files, branch
  protection, icons, About window with Ko-fi, wiki, first cask.

Public steps (push, tag, release, tap) run only when you asked for a release in that session;
anything net-new (going public, a new cask) always asks first.

## Requirements

macOS, `git`, the GitHub CLI `gh` logged in as the repo owner, Homebrew, and the tap checked out at
`~/Code/Padina/homebrew-tap` (override with `TAP_WORK`). Optional: `ffmpeg` and `webp` (`dwebp`) for the
screenshot check and demo renders (`brew install ffmpeg webp`); without them that check is skipped. It is written for my own repos and accounts —
fork it and change `OWNER` in the script and the account details in `SKILL.md` to use it for yours.
