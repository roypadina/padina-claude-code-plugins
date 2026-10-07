---
name: finalize-app-release
description: End-of-dev release checklist for the user's personal Mac apps (roypadina/* repos under ~/Code/Padina shipped through the roypadina/homebrew-tap Homebrew tap — LanGuard, MaccyPlus, VaultBar, Window Organizer, SmartHiddenBar, MeetAlert, Agents Monitor, agentctl, claude-jam — or a new app headed there). Checks and fixes version bump, CHANGELOG, README, wiki, Ko-fi (README, FUNDING.yml, wiki, in-app About), GitHub release + asset, tap cask + tap README, server-side push verification and the local install. Use when one of these apps gets a version bump, release build, tag or GitHub release, goes public, or when the user says "release", "full release", "ship it", "push all", "finalize", "wrap up", "update readme/wiki/tap", or a session that changed one of these apps is ending; also /finalize-app-release. Offer it unprompted at the end of dev work on these apps. Skips the review when its state script reports the app already finalized and unchanged, unless the user asks to recheck.
---

# Finalize app release

One pass at the end of dev work on a personal Mac app, so no release step is missed. A bundled script
checks the mechanical state in about 10 s; you fix its GAPs and review what a script cannot judge
(does the README and wiki describe what the app does now?).

## When to run

**Personal apps only.** The repo must sit under `~/Code/Padina`, push to a `roypadina/*` GitHub repo,
and be in the tap or be a Mac app project headed there. Step 1 checks this and prints `SKIP …` for
anything else (work repos, the tap itself, wikis, private scripts, local-only projects) — then say one
line ("<repo>: not a personal app, skipped") and stop.

- **Unprompted:** dev work on one of these apps is wrapping up — the user says release / ship / push
  all / finalize / we're done, a version was bumped or a release built, or the session is ending
  (including `/finish-session`) after changes to an app repo. Run Step 1; if it shows gaps, offer the
  fix list in one line.
- **Manual:** `/finalize-app-release [app dir or name] [recheck]`. No argument → the app repo(s) this
  session changed.
- **Skip the review** when (a) you already finalized this app in this session and nothing changed
  since, or (b) Step 1 prints `STAMP MATCH`. Then say one line — "<App> vX.Y.Z already finalized on
  <date>, nothing changed since" — and stop. `recheck`, "check again" or "force" overrides both.

## Rules

- **Release gate.** Repo push, tag, GitHub release, wiki push and tap push are public. Do them when the
  user asked to release, ship or push in this session ("full release", "commit push release",
  "push all + tap"). Otherwise list them as pending and ask once. Net-new things — first public push,
  new repo, new cask, history rewrite, visibility change — always need an explicit OK.
- **The app's own notes win.** Read the repo's `CLAUDE.md` and the user's memory note for the app
  before acting; per-app quirks live there. The table at the end is a summary, not the source.
- **Personal account only.** `gh` as `env -u GITHUB_TOKEN GH_TOKEN="$(command gh auth token -u roypadina)" command gh …`.
  Push over the SSH alias `github-padina` only — an HTTPS push can authenticate as a different account
  and fail with 403. Never the GitHub MCP tools for these repos (authenticated as another account).
- **Commits.** `git status -sb` right before every commit, stage named files only (never `git add -A`).
  Repo-local `user.email` must be `4943097+roypadina@users.noreply.github.com` (GitHub email privacy
  rejects the other address).
- **Public = clean.** No employer or client names, internal hostnames, emails, tokens, notification
  topics or home paths in code, docs, screenshots or history.
- **Processes.** Quit or kill only by exact PID. Never a name pattern.

## Step 1 — state

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/finalize-app-release/scripts/release-state.sh" <repo-dir>
```

Read every `GAP` and `WARN`; `INFO` is context. The script only reads (plus `git fetch --tags`). It
finds the version source, tag, latest GitHub release and its assets, the cask or formula in
`~/Code/Padina/homebrew-tap`, tap README row, tap and wiki push state against the server,
CHANGELOG/appcast top entry, README install line, Ko-fi everywhere, stale mentions of the previous
version, and the installed copy in `/Applications`.

## Step 2 — version

- `WARN … commit(s) on HEAD since vX` with user-visible changes → a release is due. Patch for fixes,
  minor for features, minor for a breaking change before 1.0, major after. Docs- or CI-only changes →
  no release, but README and wiki still get updated.
- Bump the version at the source the script names, plus every copy: `appcast.xml`, `package-lock.json`,
  the bug-report template placeholder, docs that quote it.

## Step 3 — checklist

Top to bottom. Skip what Step 1 already shows as OK.

### A. Code

1. Build and tests green with the repo's own commands. Protected `main` → branch, PR, wait for CI,
   `gh pr merge --squash --admin`.
2. Commit and push to the `roypadina/*` remote (MaccyPlus: remote `padina`; `origin` is upstream
   Maccy — never push there).

### B. Docs — every app

3. **CHANGELOG.md** — add `## [X.Y.Z] - YYYY-MM-DD` with `### Added / Changed / Fixed / Removed`
   (Keep a Changelog, as LanGuard). Keep the file's existing heading style if it has one. No file →
   create it once, seeded from past releases (`gh release list`, `gh release view <tag> --json body`),
   newest first, under `## [Unreleased]`.
4. **README** — matches the new behaviour: features, settings, shortcuts, permissions, limitations,
   install, uninstall. Screenshots retaken if the UI changed (privacy-check the image). Install line
   `brew install --cask roypadina/tap/<token>`. No stale version strings (Step 1 lists mentions of the
   previous version; "since X.Y.Z" history notes are fine).
5. **Wiki** — update every page that touches the change. A new page goes into `_Sidebar.md` too (the
   custom sidebar replaces GitHub's page list). The clone sits next to the repo as `<Repo>.wiki`,
   branch `master` (MeetAlert: nested `MeetAlert/wiki`). Commit, then push by URL:
   `git push git@github-padina:roypadina/<Repo>.wiki.git HEAD:master`. Wiki not initialised → ask the
   user to click "Create the first page" in the web UI once (there is no API), then clone and push.
   Live but no local clone → clone it next to the repo.
6. **Other docs** that describe changed behaviour: `docs/*.md`, `MANUAL.md`, the repo `CLAUDE.md`,
   `.claude/skills/<app>/SKILL.md`. Where cheap, run what the docs claim (`--help`, CLI examples).

### C. Ko-fi — public repos

7. README: shields badge in the header row —
   `[![Ko-fi](https://img.shields.io/badge/Ko--fi-support-F16061?logo=ko-fi&logoColor=white)](https://ko-fi.com/roypadina)` —
   and a `## Support` section with
   `[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/roypadina)`.
   `.github/FUNDING.yml`: `ko_fi: roypadina`. Wiki: Ko-fi line in `_Footer.md`, button at the bottom of
   `_Sidebar.md`, support paragraph on `Home.md`.
8. In-app: existing apps already have the About window and menu items — verify only (Step 1). New app →
   build them per [references/new-public-app.md](references/new-public-app.md) § 4.
   Ko-fi only: never Buy Me a Coffee or GitHub Sponsors (neither pays out to Israel).

### D. Release — gated

9. Build the release zip with the repo's script (`RELEASE=1 Scripts/package_app.sh`,
   `RELEASE=1 ./build.sh`, `gui/build-release.sh`, or xcodebuild Release +
   `ditto -c -k --keepParent <App>.app <App>.zip`). The asset name must equal the cask `url` filename
   (`Window-Organizer.zip`; `AgentsMonitor.zip`, not `AgentsMonitor.app.zip`).
10. Tag `vX.Y.Z` on the pushed commit and push the tag. Then
    `gh release create vX.Y.Z <zip> --repo roypadina/<Repo> --target main --title vX.Y.Z --notes "…"`.
    `--target` takes `main` or a full sha, never a short one. Notes in house style: short and
    user-facing — one line for a small release, bullets with bold lead-ins for a bigger one; reuse the
    CHANGELOG section.
11. Download the asset with a cache-busting query (`?x=$RANDOM`; a fresh asset can 404 for 1–2 min,
    retry) and check its sha256 equals the local zip.
    claude-jam is a formula: the release has no asset; hash the tag tarball
    `https://github.com/roypadina/claude-jam/archive/refs/tags/vX.Y.Z.tar.gz` instead.

### E. Tap — public repos

12. In `~/Code/Padina/homebrew-tap`: bump the cask `version` + `sha256` (formula: `url` + `sha256`).
    Keep `desc` current. New app → new cask from the template in the reference file.
13. Tap `README.md`: the app has a row in the Casks (or Formulae) table and its description names the
    current headline features.
14. `brew style roypadina/tap/<token>` clean. Commit `<token> X.Y.Z`, then push by URL:
    `git push git@github-padina:roypadina/homebrew-tap.git HEAD:main`.
15. Verify on the server, not a local ref: re-run Step 1 (`tap working copy = server`), then
    `brew update` so brew's own clone (`brew --repository roypadina/homebrew-tap`) matches. A green
    `brew upgrade` proves nothing — brew reads its local clone, so a failed push still upgrades this Mac.

### F. Local install — part of the release, not optional

16. Put the released version on the user's Mac:
    - Default: `brew upgrade --cask roypadina/tap/<token>`, then
      `xattr -dr com.apple.quarantine "/Applications/<App>.app"` (ad-hoc signed; Gatekeeper may
      otherwise offer to move it to the Trash).
    - Exception: an app whose Accessibility grant belongs to a local signing identity (SmartHiddenBar)
      is installed with its dev build script, never `brew upgrade` — the app's memory note says which.
    - Quit the old copy by exact PID (`pgrep -x <Executable>` → `kill <pid>`, or
      `osascript -e 'quit app id "<bundle id>"'`). Relaunch from `/Applications` with the session
      environment stripped —
      `env -u CLAUDECODE -u CLAUDE_CODE_CHILD_SESSION -u CLAUDE_CODE_SESSION_ID -u CLAUDE_PID open "/Applications/<App>.app"` —
      only if the user's rules allow relaunching apps from a session; otherwise ask them to open it.
    - Verify with Step 1: `installed … is X.Y.Z`, one PID running from `/Applications`, no quarantine.

### G. Wrap-up

17. Update the user's memory note for the app: current version, release date, new gotchas.
18. **Obsidian Mac inventory** (personal vault `~/Obsidian/Padina`, `mac-app-inventory` conventions): update
    `MAC/Apps/<Category>/<App>.md` (find it with `grep -rli <app> ~/Obsidian/Padina/MAC`) — version, "Last
    updated", `updated:` frontmatter, a dated Changelog line, and any system pieces the release installs
    (helpers, LaunchDaemons, sudoers, scripts). No note → create one per the inventory README. Then show
    `git status --short` in the vault (it may hold edits from other devices) and offer commit + push; never
    touch `.git`, `.stignore*`, `.stfolder`, `.obsidian/`.
19. List the temp files you created (build dirs, zips in `/tmp` or `dist/`, worktrees) and ask before
    deleting them.
20. Re-run Step 1. Every GAP fixed, or accepted by the user → stamp it:
    `release-state.sh <repo-dir> --stamp`. The next run then prints `STAMP MATCH` until the repo, the
    wiki or the tap changes.
21. Report as a table, one row per item: ✅ done · ⏭ skipped (why) · ❗ needs the user. Include the
    release URL and the repo, wiki and tap commits.

## New public app

Repo going public or first cask → [references/new-public-app.md](references/new-public-app.md): privacy
triple check, history squash, community files, CI and branch protection, repo metadata, icons, About
window and Ko-fi, wiki, first cask and tap README row. Every step there is net-new: show the plan, get
an explicit OK.

## Per-app notes

Summary only — the app's `CLAUDE.md` and memory note win.

| App | Dir in `~/Code/Padina` | Quirks |
|---|---|---|
| LanGuard | `LanGuard-app` | Version in `Config/Shared.xcconfig`; xcodebuild Release + ditto zip; wiki live but not cloned locally yet |
| MaccyPlus | `Maccay` | Remote `padina`, never `origin`; version in the pbxproj; prepend an `appcast.xml` item (length = zip bytes, `sparkle:version` = build) after the release asset exists; wiki clone is `maccyplus.wiki` (slug, not folder name) |
| VaultBar | `VaultBar` | Push only `main`; privacy triple check before every public push; `RELEASE=1 Scripts/package_app.sh` |
| Window Organizer | `window-organizer` | Version is a literal in the `Scripts/package_app.sh` plist heredoc; asset `Window-Organizer.zip` |
| SmartHiddenBar | `SmartHiddenBar` | `RELEASE=1 ./build.sh`; local install is the dev-signed `./build.sh`, never `brew upgrade` |
| MeetAlert | `MeetAlert` | Wiki is the nested clone `MeetAlert/wiki`; `build.sh` makes no zip — ditto it |
| Agents Monitor | `AgentsMonitor` | Asset must be `AgentsMonitor.zip`; never commit work or topic strings |
| agentctl | `agentctl` | `main` protected: bump `package.json` + lock + CHANGELOG in a PR, admin-merge; build the zip in a throwaway worktree at the merge sha |
| claude-jam | `claude-jam` | Formula from the tag tarball; README and wiki quote the npm tarball version — bump them |

## Self-update

A run hit something this file did not predict — a failed command, a new per-app quirk, a step the user
had to ask for? Before reporting, patch this file (and the script, if a check was missing) in
`~/Code/Padina/padina-claude-code-plugins/finalize-app-release/`, bump `.claude-plugin/plugin.json`,
commit, push, then `claude-plugin-all marketplace update padina` and
`claude-plugin-all update finalize-app-release@padina`.
