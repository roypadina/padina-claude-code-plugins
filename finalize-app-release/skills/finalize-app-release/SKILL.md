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
  To reuse it, define a function: `ghp() { env -u GITHUB_TOKEN GH_TOKEN="$(command gh auth token -u roypadina)" command gh "$@"; }`.
  Never store it in a variable (`GH="env … $(…)"; $GH …`): zsh does not split the variable, so the
  "command not found" error prints the whole token into the transcript. Push over the SSH alias `github-padina` only — an HTTPS push can authenticate as a different account
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

3. **CHANGELOG.md** — required for every version built and every release, also patch and
   pre-releases: add `## [X.Y.Z] - YYYY-MM-DD` with `### Added / Changed / Fixed / Removed`
   (Keep a Changelog, as LanGuard). Keep the file's existing heading style if it has one. No file →
   create it once, seeded from past releases (`gh release list`, `gh release view <tag> --json body`),
   newest first, under `## [Unreleased]`. User-facing and public-clean: this text is published
   three times (repo, release notes, the site's "What's new"). Step 1 GAPs when the top entry is not
   the source version or the latest tag has no entry.
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
    CHANGELOG section (never empty notes; Step 1 GAPs on them). **First line of the notes: `SHA-256: <zip sha256>`** (`shasum -a 256 <zip>`; the
    site promises it; Step 1 flags a release without it). claude-jam: the tag tarball's hash.
    **Signing (apps, not CLIs):** the build must use the stable identity `KeyLayoutSwitcher Dev`
    (ad-hoc only in CI). Before tagging, unzip the built zip and check the app and every nested
    Mach-O: `codesign -dvv <path> 2>&1 | grep ^Authority=` shows `KeyLayoutSwitcher Dev`, and
    `codesign --verify --deep --strict <App>.app` passes. Reference: `Maccay/Scripts/build-release.sh`.
    Step 1 flags a latest release whose app is not signed with it.
11. Download the asset with a cache-busting query (`?x=$RANDOM`; a fresh asset can 404 for 1–2 min,
    retry) and check its sha256 equals the local zip.
    claude-jam is a formula: the release has no asset; hash the tag tarball
    `https://github.com/roypadina/claude-jam/archive/refs/tags/vX.Y.Z.tar.gz` instead.

### E. Tap — public repos

12. In `~/Code/Padina/homebrew-tap`: bump the cask `version` + `sha256` (formula: `url` + `sha256`).
    Keep `desc` current. New app → new cask from the template in the reference file. Add
    ``- `<token>` X.Y.Z`` under `### Changed` (new cask: `### Added`) in today's `## YYYY-MM-DD`
    section of the tap's `CHANGELOG.md` (create the section at the top, below `## [Unreleased]`).
13. Tap `README.md`: the app has a row in the Casks (or Formulae) table and its description names the
    current headline features.
14. `brew style ~/Code/Padina/homebrew-tap/Casks/<token>.rb` clean (the file path — `brew style roypadina/tap/<token>`
    lints brew's own clone under `/opt/homebrew/Library/Taps`, i.e. the old, unedited cask). Commit `<token> X.Y.Z`, then push by URL:
    `git push git@github-padina:roypadina/homebrew-tap.git HEAD:main`.
15. Verify on the server, not a local ref: re-run Step 1 (`tap working copy = server`), then
    `brew update` so brew's own clone (`brew --repository roypadina/homebrew-tap`) matches. A green
    `brew upgrade` proves nothing — brew reads its local clone, so a failed push still upgrades this Mac.

### E2. Marketing site + repo marketing — every release (pre-releases and BETA too)

Site repo `~/Code/Padina/roypadina-apps` (PRIVATE; `main` unprotected, push by SSH; the push deploys: CI
publishes `deploy`, NAS git-sync pulls it, the `verify` job polls `/version.txt`). Contract and page
how-to: its `README.md`, `docs/design.md`, `CLAUDE.md`. Skip when the app has no entry in
`data/apps.json` (match on `repo`); a new app → [references/new-public-app.md](references/new-public-app.md) § 7.

15a. **Facts.** Set `version` (tag without `v`), `released` (ISO date) and, if changed, `requirements`,
    `badge` (alpha/beta, drop it at stable), `installNpm`, `tagline`/`pitch`/`features`. Validate with
    `node build.mjs`. Never commit anything but the files this release needs.
    One-liner: `cd ~/Code/Padina/roypadina-apps && git pull --rebase -q && node -e 'const f="data/apps.json",d=require("./"+f),a=d.apps.find(a=>a.slug==process.argv[1]);a.version=process.argv[2];a.released=process.argv[3];require("fs").writeFileSync(f,JSON.stringify(d,null,2)+"\n")' <slug> X.Y.Z YYYY-MM-DD && node build.mjs`,
    then check `git diff --stat` shows only a few changed lines: it re-serialises the whole file and, if the
    formatting drifted, rewrites hundreds of lines. Then `git checkout -- data/apps.json` and edit just the
    `version`/`released` lines in place (sed on the line number).
15b. **Prose + screenshots.** The release changes user-facing features or the UI → update the page prose
    `src/pages/<slug>.mjs` and `static/screenshots/<slug>/` (WebP, offscreen renders, fake data, public-clean;
    list them in `apps.json`). Keep the page section order from `docs/design.md`.
15c. **Social preview.** Tagline, name or badge changed → `sh og/render.sh <slug>` in the site repo, copy
    `og/out/<slug>.png` to `docs/social-preview.png` in the app repo (commit via the app's own PR/push), and
    commit `og/out/<slug>.png` in the site repo. GitHub has no upload API: tell Roy the click path
    "repo → Settings → Social preview → Edit → Upload an image → `docs/social-preview.png`", then verify
    after his upload: `curl -sL "$(gh api graphql -f query='{repository(owner:"roypadina",name:"<Repo>"){openGraphImageUrl}}' -q .data.repository.openGraphImageUrl)" -o /tmp/og.png && cmp /tmp/og.png docs/social-preview.png`
    (`gh` as the personal account; a default avatar-style URL means no upload yet).
15d. `git add` the named files, commit `<slug> X.Y.Z`, `git push git@github-padina:roypadina/roypadina-apps.git main`,
    then wait for the `deploy` run (`gh run watch`) and check `curl -s https://apps.roypadina.synology.me/version.txt`
    equals the pushed sha. The page's **"What's new"** is built from the app repo's `CHANGELOG.md` at deploy
    time, so push the CHANGELOG entry (B3) before the site; a CHANGELOG fix after the deploy needs a redeploy
    (`gh workflow run deploy --repo roypadina/roypadina-apps`). Step 1 GAPs when the live page lacks the latest tag. Step 1 GAPs when the site lags the latest tag and WARNs when the app's GitHub
    homepage is not its site page or the README lacks the site link. Release notes keep the `SHA-256:` first line (D10).
    App pages live at `https://apps.roypadina.synology.me/apps/<slug>/` (not `/<slug>/`, which is a 404). The site
    clone may hold another session's uncommitted edit, so `git pull --rebase` refuses. Then `git fetch` and
    check `status -sb`: not behind means no pull is needed. Stage only `data/apps.json` and leave the other file.
    Several apps released together → edit all their lines in one commit, one deploy.

### F. Local install — part of the release, not optional

16. Put the released version on the user's Mac:
    - Default: `brew upgrade --cask roypadina/tap/<token>`, then
      `xattr -dr com.apple.quarantine "/Applications/<App>.app"` (self-signed with a stable identity; Gatekeeper may
      otherwise offer to move it to the Trash).
    - Exception: an app whose Accessibility grant belongs to a local signing identity and whose release is
      not signed with it is installed with its dev build script, never `brew upgrade` — the app's memory
      note says which. (SmartHiddenBar no longer: releases share the identity since 1.3.2.)
    - Quit the old copy by exact PID (`pgrep -x <Executable>` → `kill <pid>`, or
      `osascript -e 'quit app id "<bundle id>"'`). Relaunch from `/Applications` with the session
      environment stripped —
      `env $(env | grep -o '^CLAUDE[A-Z0-9_]*' | sort -u | sed 's/^/-u /') -u CLAUDECODE open "/Applications/<App>.app"` —
      only if the user's rules allow relaunching apps from a session; otherwise ask them to open it.
      Stripping only the 4 session vars still leaks ~12 `CLAUDE*` vars (incl. a messaging token) into
      the app; check `ps eww -o command= -p <pid> | tr ' ' '\n' | grep -c '^CLAUDE'` prints `0`.
    - Verify with Step 1: `installed … is X.Y.Z`, one PID running from `/Applications`, no quarantine.

### G. Wrap-up

17. Update the user's memory note for the app: current version, release date, new gotchas.
18. **Obsidian Mac inventory** (personal vault `~/Obsidian/Padina`, `mac-app-inventory` conventions): update
    `Setup/Mac/Apps/<Category>/<App>.md` (find it with `grep -rli <app> ~/Obsidian/Padina/Setup/Mac`) — version, "Last
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
window and Ko-fi, wiki, first cask and tap README row, marketing site + repo marketing (site entry and page, website badge, feature-request block, More Mac apps, social preview). Every step there is net-new: show the plan, get
an explicit OK.

## Per-app notes

Summary only — the app's `CLAUDE.md` and memory note win.

| App | Dir in `~/Code/Padina` | Quirks |
|---|---|---|
| LanGuard | `LanGuard-app` | Version in `Config/Shared.xcconfig`; xcodebuild Release + ditto zip; universal build needs `-destination 'generic/platform=macOS'`; wiki clone `LanGuard.wiki` next to the repo; helper script/plist changed → after `brew upgrade` the user relaunches it (Raycast) and clicks Settings › Protection › Update helper, then `launchctl print system/com.roypadina.languard-net` shows `runs = 1` staying at 1 |
| MaccyPlus | `Maccay` | Remote `padina`, never `origin`; version in the pbxproj; prepend an `appcast.xml` item (length = zip bytes, `sparkle:version` = build) after the release asset exists. `main` is protected, so it goes in its own PR `appcast: X.Y.Z`; `xmllint --noout appcast.xml` first; wiki clone is `maccyplus.wiki` (slug, not folder name); upstream-sync PRs merge with `--merge`, never `--squash`; build with `MACCYPLUS_SIGN_IDENTITY` set (see memory) |
| VaultBar | `VaultBar` | Push only `main`; privacy triple check before every public push; `RELEASE=1 Scripts/package_app.sh` |
| Window Organizer | `window-organizer` | Version is a literal in the `Scripts/package_app.sh` plist heredoc; asset `Window-Organizer.zip` |
| SmartHiddenBar | `SmartHiddenBar` | `RELEASE=1 ./build.sh`; since 1.3.2 releases share the dev identity, so local install = `brew upgrade` + quarantine clear (grant survives, verified 1.3.3) |
| MeetAlert | `MeetAlert` | Wiki is the nested clone `MeetAlert/wiki`; `build.sh` makes no zip — ditto it; bump `Info.plist` with `sed` on the two version lines, because `PlistBuddy` reformats the whole file |
| Agents Monitor | `AgentsMonitor` | Asset must be `AgentsMonitor.zip`; never commit work or topic strings; local install: after `brew upgrade`, extract the release zip to `/tmp`, clear quarantine there, `ditto` it over `/Applications` before launch (Gatekeeper trashes the brew copy) |
| agentctl | `agentctl` | CLI-only cask since 0.11.0 (`binary "agentctl/bin/agentctl"`, no app, no About window — Ko-fi lives in `--help`). `main` protected: bump `package.json` + lock + CHANGELOG in a PR, admin-merge; `sh scripts/build-release.sh` → `release/agentctl.zip` in a throwaway worktree at the merge sha; local install = `brew upgrade --cask agentctl` only (no xattr, no relaunch) |
| Obsidian Vault Git Watcher | `ObsidianVaultGitWatcher` | Plain `swiftc` via `build.sh` (no SwiftPM/Xcode), version in `Info.plist`; `./build.sh dist` → `dist/ObsidianVaultGitWatcher.zip`; `main` protected; never push local `backup/pre-public`; after `brew upgrade` reload the LaunchAgent (copy repo plist, `bootout` exact label, `bootstrap`) |
| claude-jam | `claude-jam` | Formula from the tag tarball; README and wiki quote the npm tarball version — bump them |

## Self-update

A run hit something this file did not predict — a failed command, a new per-app quirk, a step the user
had to ask for? Before reporting, patch this file (and the script, if a check was missing) in
`~/Code/Padina/padina-claude-code-plugins/finalize-app-release/`, bump `.claude-plugin/plugin.json`,
commit, push, then `claude-plugin-all marketplace update padina` and
`claude-plugin-all update finalize-app-release@padina`.
