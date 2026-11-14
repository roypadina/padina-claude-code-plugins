---
name: finalize-app-release
description: End-of-dev release checklist for the user's personal Mac apps (roypadina/* repos under ~/Code/Padina shipped through the roypadina/homebrew-tap Homebrew tap — LanGuard, MaccyPlus, VaultBar, Window Organizer, SmartHiddenBar, MeetAlert, Agents Monitor, agentctl, claude-jam — or a new app headed there). Checks and fixes version bump, CHANGELOG, README, wiki, demo GIF + site video, Ko-fi (README, FUNDING.yml, wiki, in-app About), GitHub release + asset, tap cask + tap README, server-side push verification and the local install. Use when one of these apps gets a version bump, release build, tag or GitHub release, goes public, or when the user says "release", "full release", "ship it", "push all", "finalize", "wrap up", "update readme/wiki/tap", or a session that changed one of these apps is ending; also /finalize-app-release. Also covers the plugin marketplace repo padina-claude-code-plugins: after a plugin change it keeps the plugin version, CHANGELOG, READMEs, wiki, site card and the installed copies on every Claude profile in step — use it when a plugin there was changed, bumped or added. Offer it unprompted at the end of dev work on these apps or plugins. Skips the review when its state script reports the app already finalized and unchanged, unless the user asks to recheck.
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

**Plugin marketplace** — a repo with `.claude-plugin/marketplace.json` (`padina-claude-code-plugins`):
Step 1 runs the plugin checks instead of the app checks. Work through § Plugin marketplace instead of
Steps 2–3.

- **Unprompted:** dev work on one of these apps is wrapping up — the user says release / ship / push
  all / finalize / we're done, a version was bumped or a release built, or the session is ending
  (including `/finish-session`) after changes to an app repo or a plugin in the marketplace repo. Run Step 1; if it shows gaps, offer the
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
- **Parallel sessions release too.** Another Claude session may be releasing the same app (e.g. a
  "push all + finalize all" batch). Before the version bump and again before tagging: `git fetch --tags`,
  `git ls-remote --tags origin`, and take the next free version above the latest tag (a release that sorts
  below an existing tag is wrong); `git rebase origin/main`. Message the other `padina-*` sessions
  (ListAgents) about the version you take, and agree who bumps the tap and site, so the cask and
  `apps.json` move forward in order (fetch right before each push).
- **Another session's uncommitted edit in the same file** (tap `CHANGELOG.md`, site `data/apps.json`): stage
  only yours. Build the index copy from HEAD (`git show HEAD:<f> > /tmp/x`, apply your edit there), then
  `git update-index --cacheinfo 100644,$(git hash-object -w /tmp/x),<f>`; make the same edit in the working
  file so their hunk stays unstaged. Check `git diff --cached <f>` shows only your lines before committing.

## Step 1 — state

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/finalize-app-release/scripts/release-state.sh" <repo-dir>
```

Read every `GAP` and `WARN`; `INFO` is context. The script only reads (plus `git fetch --tags` and dark-mode previews in `$TMPDIR/release-state-dark`). It
finds the version source, tag, latest GitHub release and its assets, the cask or formula in
`~/Code/Padina/homebrew-tap`, tap README row, tap and wiki push state against the server,
CHANGELOG/appcast top entry, README install line, screenshots with transparent pixels, the demo GIF
(sources, UI drift since its last render, site video, orphan media), Ko-fi everywhere,
stale mentions of the previous version, the support popup (B4b), and the installed copy in `/Applications`.

The script SKIPs any path outside `~/Code/Padina`, including a feature worktree in a ClaudWork folder.
Run it on the shared clone: before the merge for the docs checks, after the merge for the release.

## Step 2 — version

- `WARN … commit(s) on HEAD since vX` with user-visible changes → a release is due. Patch for fixes,
  minor for features, minor for a breaking change before 1.0, major after. Docs- or CI-only changes →
  no release, but README and wiki still get updated.
- Bump the version at the source the script names, plus every copy: `appcast.xml`, `package-lock.json`,
  the bug-report template placeholder, docs that quote it.
- Bump the build number too (CFBundleVersion / `BUILD_NUMBER` / `CURRENT_PROJECT_VERSION` — wherever the repo
  keeps it): Sparkle compares `sparkle:version` (the build), never the version string. Same build as the
  previous release = no update offered (ASH 1.8.1–1.11.0 all shipped build 10). Step 1 GAPs on it.

## Step 3 — checklist

Top to bottom. Skip what Step 1 already shows as OK.

### A. Code

1. Build and tests green with the repo's own commands. Protected `main` → commit on a branch now; push
   it, open the PR, wait for CI and `gh pr merge --squash --admin` only after the review gate (§ C2).
   Right after `gh pr create`, `gh pr checks --watch` prints "no checks reported" and exits non-zero:
   poll `gh pr checks` until a check exists, then watch. A helper script run in the background must not
   be edited while that run is open (bash reads the file as it goes) — run a copy.
   CI may run an older Swift than the Mac: mirror `.github/workflows/*` locally. An app that defines its
   own `State` (or another SwiftUI name) must qualify `@SwiftUI.State` (OVGW 0.5.0 failed CI on this).
2. Commit now; push to the `roypadina/*` remote (MaccyPlus: remote `padina`; `origin` is upstream
   Maccy — never push there) only after the review gate (§ C2).

### B. Docs — every app

3. **CHANGELOG.md** — required for every version built and every release, also patch and
   pre-releases: add `## [X.Y.Z] - YYYY-MM-DD` with `### Added / Changed / Fixed / Removed`
   (Keep a Changelog, as LanGuard). Keep the file's existing heading style if it has one. No file →
   create it once, seeded from past releases (`gh release list`, `gh release view <tag> --json body`),
   newest first, under `## [Unreleased]`. User-facing and public-clean: this text is published
   three times (repo, release notes, the site's "What's new"). Step 1 GAPs when the top entry is not
   the source version or the latest tag has no entry.
4. **README** — matches the new behaviour: features, settings, shortcuts, permissions, limitations,
   install, uninstall. Screenshots retaken if the UI changed (privacy-check the image); they must be opaque,
   because transparent ones lose their text in GitHub dark mode — on a Step 1 WARN, view the dark preview it
   prints and flatten or re-render the image (optionally a `<picture>` with a `-dark` variant). Install line
   `brew install --cask roypadina/tap/<token>`. No stale version strings (Step 1 lists mentions of the
   previous version; "since X.Y.Z" history notes are fine).
4a. **Demo** — the looping GIF in the README (hero under the badges) and the MP4 on the site page, kept
   true at all times; how to build and ship one is in [references/demo.md](references/demo.md), Step 1
   WARNs on each case below.
   - **New app, no demo** → build one (storyboard, render, README hero, site video).
   - **A release changes UI the demo shows** → re-render with `docs/demo/render.sh`, then refresh the README
     GIF and the site MP4 + poster together from that one render.
   - **A feature is removed or renamed, or a demo is replaced** → delete the old gif/mp4/webp and every
     reference to it (repo, wiki, site `static/screenshots/<slug>/`, `apps.json`, page): no orphans left.
   - A real recording without `docs/demo/` (LanGuard) is re-recorded by hand under the same names.
4b. **Support popup** — the in-app Ko-fi tip popup, rolling out to every app one by one (MeetAlert first:
   `Sources/MeetAlert/SupportPrompt.swift`, a "receipt" of what the app did for the user). Step 1 prints it as
   `INFO support popup <file>`, found by a source file named `SupportPrompt*`, so every app keeps that name.
   On every version, spawn ONE reviewer with `model: "opus"` whose only goal is more tips without annoying
   users. Give it the popup source (text, look, motion, trigger and ask rules), this version's CHANGELOG
   section and what the app does for its users. It replies `NO CHANGE`, or a short list of proposed
   changes, each with why it should bring in more tips.
   - `NO CHANGE` → continue the release; nothing else to do.
   - Proposed changes → **always ask the user first.** Show each change and its reason, wait for an explicit
     OK per change, apply only what they approve. Never change the popup on your own, not even a word.
   - The popup is not a "what's new" panel: no feature lists in it.
   - Rollout (2026-11-14): shipped in MeetAlert 1.10.0, NtfyBar 1.7.0, Window Organizer 0.5.0, LanGuard 1.4.0,
     OVGW 0.5.0, VaultBar 0.5.0, SmartHiddenBar 1.7.0, MaccyPlus 2.11.0, Agents Monitor 1.10.0,
     AgentsSessionHopper 1.11.0. PullPing pending; CLIs (agentctl, claude-jam) skipped.
   - Hold every app to these principles:
     - only measured stats; title literally true ("since <date>" when counting starts at the update); zero rows hidden; `.formatted()`
     - never after a stressful moment; skip while the app's own events still arrive; skip while the mic is in use (fade an open card when a call starts)
     - only when settled: no sleep during the wait, no very recent input, not mid-typing, no menu open (CGWindowList popUpMenu level), no mouse button held
     - unanswered 5 min or 2 min without input = snooze; app UI, update window, sleep or lock = snooze
   - Approved changes: run the app's popup tests. A preview needs the user (MeetAlert: `MEETALERT_TEST=1`
     + ⌥-click "Show support prompt now") unless the app renders it offscreen in a screenshot test.
5. **Wiki** — update every page that touches the change. A new page goes into `_Sidebar.md` too (the
   custom sidebar replaces GitHub's page list). The clone sits next to the repo as `<Repo>.wiki`,
   branch `master` (MeetAlert: nested `MeetAlert/wiki`). Commit now; after § C2 push by URL:
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

### C2. Review gate — before anything public

Everything this pass changes is done and committed locally, nothing pushed: also prepare the site edits
(E2 15a–15c: `apps.json`, page prose, screenshots, demo MP4/poster) in the site clone first, push them
after `APPROVE`. Skip only when the pass changed nothing (Step 1 clean, no new commits).

8a. Spawn ONE reviewer subagent with `model: "fable"` (the user approved fable for this step on
    2026-10-30; one app at a time, never a fan-out). Give it the whole diff of this pass: code since the
    last tag (`git diff v<last>..HEAD`), CHANGELOG, the release-notes text, README, the wiki clone's diff,
    new or changed screenshots and demo media, and the site files (`apps.json`, page,
    `static/screenshots/<slug>/`). It checks:
    - **Correctness**: README, wiki, CHANGELOG, notes, demo captions and the support popup text (B4b) match
      the code (features, settings, shortcuts, versions).
    - **Look**: views each new image on white and on `#0d1117` (Step 1's dark previews), site images also on
      `#1c2243`, and the demo's first, mid-crossfade, last and poster frames.
    - **Security and privacy**: public-clean (no tokens, emails, hostnames, home paths, employer names or
      notification topics in files, media or the new commits).
    - **Links and paths**: every image and link target exists; no orphan files (Step 1).
    - **Version consistency**: source, CHANGELOG, notes, `apps.json` (tag and cask come later; G20's Step 1
      re-run checks them).

    It replies `APPROVE` or a numbered list `file:line — problem — fix`. Fix, then send the same reviewer
    back to re-check. Only `APPROVE` unlocks the first public push (A2, the wiki B5, D, E, E2). Tell it:
    wrap long commands as `perl -e 'alarm shift; exec @ARGV' 600 <cmd>`, view one contact sheet per image
    (its backgrounds side by side, `ffmpeg … hstack`) and one for the demo frames, downscaled to ≤ 1600 px,
    and give the verdict as its final reply.

### D. Release — gated

9. Build the release zip with the repo's script (`RELEASE=1 Scripts/package_app.sh`,
   `RELEASE=1 ./build.sh`, `gui/build-release.sh`, or xcodebuild Release +
   `ditto -c -k --keepParent <App>.app <App>.zip`). The asset name must equal the cask `url` filename
   (`Window-Organizer.zip`; `AgentsMonitor.zip`, not `AgentsMonitor.app.zip`).
10. Tag `vX.Y.Z` on the pushed commit and push the tag. Then
    `gh release create vX.Y.Z <zip> --repo roypadina/<Repo> --verify-tag --title vX.Y.Z --notes-file notes.md`
    (tag pushed first; never type a short or invented `--target` sha). Build and check the file first:
    `{ echo "SHA-256: $SHA"; echo; awk -v v="## [X.Y.Z]" 'index($0,v)==1{f=1;next} /^## \[/{f=0} f' CHANGELOG.md; } > notes.md`
    (three releases on 2026-11-14 shipped an empty body from a sed one-liner and needed `gh release edit`). Notes in house style: short and
    user-facing — one line for a small release, bullets with bold lead-ins for a bigger one; reuse the
    CHANGELOG section (never empty notes; Step 1 GAPs on them). **First line of the notes: `SHA-256: <zip sha256>`** (`shasum -a 256 <zip>`; the
    site promises it; Step 1 flags a release without it). claude-jam: the tag tarball's hash.
    **Signing (apps, not CLIs):** the build must use the stable identity `KeyLayoutSwitcher Dev`
    (ad-hoc only in CI). Before tagging, unzip the built zip and check the app and every nested
    Mach-O: `codesign -dvv <path> 2>&1 | grep ^Authority=` shows `KeyLayoutSwitcher Dev`, and
    `codesign --verify --deep --strict <App>.app` passes. Reference: `Maccay/Scripts/build-release.sh`.
    Step 1 flags a latest release whose app is not signed with it.
    **Sparkle apps** (in-app updates; § Sparkle updates): upload the feed with the zip —
    Agents Monitor `gh release create … build/AgentsMonitor.zip build/appcast.xml`; MaccyPlus signs
    its `appcast.xml` item instead (per-app notes). Step 1 GAPs on a missing asset or signature.
11. Download the asset with a cache-busting query (`?x=$RANDOM`; a fresh asset can 404 for 1–2 min,
    retry) and check its sha256 equals the local zip.
    claude-jam is a formula: the release has no asset; hash the tag tarball
    `https://github.com/roypadina/claude-jam/archive/refs/tags/vX.Y.Z.tar.gz` instead.

### E. Tap — public repos

12. In `~/Code/Padina/homebrew-tap`: `git fetch` first. Other sessions push the tap by URL, so the
    `origin/main` ref goes stale and `status -sb` can show "ahead 1" for a commit that is already on the
    server. Then bump the cask `version` + `sha256` (formula: `url` + `sha256`).
    Keep `desc` current. Sparkle apps carry `auto_updates true` (so `brew upgrade` skips a copy Sparkle
    already updated). New app → new cask from the template in the reference file. Add
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
    The push by URL leaves `origin/main` stale, so `status -sb` then shows "ahead 1" for a commit already on the
    server: `git fetch` before judging it (or compare with `git ls-remote`).
    Several apps released together → edit all their lines in one commit, one deploy.
    A clone `ahead 1` that `ls-remote` shows is NOT on the server is another session's unpushed release commit
    (e.g. `agentctl 0.14.0`): never push it with yours. Prepare your edit, `git fetch` again right before the push
    (it usually lands within minutes); still unpushed → commit yours in a worktree at `origin/main` and push that.

### F. Local install — part of the release, not optional

16. Put the released version on the user's Mac. Pick the path by what is installed now.

    **A. In-app update** — the app has an update flow (Sparkle) and the installed copy already has it
    (`/Applications/<App>.app/Contents/Frameworks/Sparkle.framework` exists). No `brew upgrade`, no zip copy:
    the app updates itself, which also tests the release's feed on a real install.
    - Check the live feed serves the release first:
      `curl -sL "<SUFeedURL>?x=$RANDOM" | grep -o '<sparkle:shortVersionString>[^<]*'` shows X.Y.Z.
    - Tell the user the one step: **<App> menu → Check for Updates… → Install Update**. Sparkle downloads,
      installs and relaunches the app itself. A check the user starts always shows the update window, even
      with silent updates on.
    - Offer to run it for them. It works without touching the UI, but it quits and relaunches their app, so
      ask each time: the user's rules forbid relaunching a menu-bar app from a session without an explicit
      OK, and never an always-on app (meeting alarm, auto-lock, ntfy client) while they are away. With the OK:
      1. `defaults delete <bundle id> SULastCheckTime`, so the next launch checks at once.
      2. Quit: `osascript -e 'quit app id "<bundle id>"'` (exact-PID `kill` if it hangs).
      3. Relaunch env-stripped (command under "Both paths") and check the env count is `0`.
      4. Wait for Sparkle to stage the update (a background until-loop, not sleeps):
         `~/Library/Caches/<bundle id>/org.sparkle-project.Sparkle/Installation/*/*/<App>.app` with
         `CFBundleShortVersionString` X.Y.Z (a sandboxed app: under
         `~/Library/Containers/<bundle id>/Data/Library/Caches/`). This needs silent updates
         (`defaults read <bundle id> SUAutomaticallyUpdate` = 1, set on Roy's Mac per § Sparkle updates).
         Without them the update window opens instead: ask the user to click Install Update.
      5. Quit again: Sparkle installs on quit. Wait until `/Applications/<App>.app` reports X.Y.Z.
      6. Relaunch env-stripped. Check the env count is `0` and `vmmap <pid> | grep -c Sparkle.framework` > 0.
    - brew keeps recording the old version for these casks. That is expected (`brew upgrade` skips
      `auto_updates true` casks without `--greedy`); don't "fix" it.
    - A LaunchAgent app (KeepAlive; verified Obsidian Vault Git Watcher 0.4.0 → 0.5.0, 2026-11-14): replace
      the osascript quit (KeepAlive relaunches it at once) with `launchctl bootout gui/$(id -u)/<label>`, and
      the env-stripped relaunch with `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/<label>.plist`
      (launchd gives it a clean env). Order: bootstrap → Sparkle stages → bootout (installs on quit) → bootstrap.
    - An app lacking `SUAutomaticallyUpdate` gets it set per § Sparkle updates before the update. Sandboxed
      apps (MaccyPlus, Agents Monitor) staged fine under `~/Library/Containers/<id>/Data/Library/Caches`.
      Verified on 7 apps in one batch (Window Organizer, LanGuard, NtfyBar, SmartHiddenBar, MaccyPlus,
      Agents Monitor, OVGW).
    - Verified on MeetAlert 1.9.2 → 1.9.3 (2026-11-13): staged within seconds of launch, installed on quit.

    **B. brew** — no Sparkle, a CLI cask or formula, or the app's first Sparkle release (the installed copy
    has no Sparkle yet, so it cannot update itself):
    - Default: `brew upgrade --cask roypadina/tap/<token>` (a Sparkle cask with `auto_updates true` needs
      `--greedy`, else brew skips it and keeps recording the old version), then
      `xattr -dr com.apple.quarantine "/Applications/<App>.app"` (self-signed with a stable identity; Gatekeeper may
      otherwise offer to move it to the Trash).
    - Exception: an app whose Accessibility grant belongs to a local signing identity and whose release is
      not signed with it is installed with its dev build script, never `brew upgrade` — the app's memory
      note says which. (SmartHiddenBar no longer: releases share the identity since 1.3.2.)

    **Both paths:**
    - Quit the old copy by exact PID (`pgrep -x <Executable>` → `kill <pid>`, or
      — `pgrep -x` matches the 15-character process name, so a longer executable (`ObsidianVaultGitWatcher`)
      needs `pgrep -f "/Applications/<App>.app/Contents/MacOS/"` —
      `osascript -e 'quit app id "<bundle id>"'`). Relaunch from `/Applications` with the session
      environment stripped —
      `env $(env | grep -oE '^(CLAUDE|SESSIONHOPPER|AGENTCTL|CODEX)[A-Z0-9_]*' | sort -u | sed 's/^/-u /') -u CLAUDECODE open "/Applications/<App>.app"` —
      only if the user's rules allow relaunching apps from a session; otherwise ask them to open it.
      Stripping only the 4 session vars still leaks ~12 `CLAUDE*` vars (incl. a messaging token) into
      the app, and a `CLAUDE*`-only filter still leaks `SESSIONHOPPER_SESSION_ID` (an app that starts
      agents then hands them this session's identity); check
      `ps eww -o command= -p <pid> | tr ' ' '\n' | grep -cE '^(CLAUDE|SESSIONHOPPER|AGENTCTL|CODEX)'` prints `0`.
      The same applies to every dev-build launch during the session, not only the final install.
    - The release build in the repo (`dist/<App>.app`, `build/…`) is registered with LaunchServices too, and on
      macOS 27 a menu-bar app then runs without a visible status item. After packaging, unregister and delete it:
      `/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -u <repo>/dist/<App>.app && rm -rf <repo>/dist/<App>.app`;
      `lsregister -dump | grep "^path:.*<App>.app"` must list only `/Applications`. Then relaunch.
    - App run by a LaunchAgent with KeepAlive (Obsidian Vault Git Watcher, VaultBar), brew path: brew swaps the bundle under
      the running agent, launchd relaunches it while still quarantined → SIGKILL "Launch Constraint Violation"
      (crash report). Clear the quarantine, then `launchctl kickstart -k gui/$(id -u)/<label>` — not `open`
      (a second, non-agent copy). If quitting it changes the user's state (VaultBar locks open vaults), leave
      the upgrade + restart to the user.
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
    release URL, the repo, wiki and tap commits and the review verdict.

## Plugin marketplace

`padina-claude-code-plugins` is public and ships by `git push`: no tag, no GitHub release, no tap. Step 1
prints one line per plugin. Fix every GAP, then review what a script cannot judge: does each README and
wiki page describe what the plugin does now?

1. **Version.** Bump the changed plugin's `.claude-plugin/plugin.json`: patch for a fix or wording, minor
   for a feature (minor for a breaking change before 1.0). The plugin cache is stored per version
   (`plugins/cache/<marketplace>/<plugin>/<version>`), so an unbumped change does not reach existing
   installs. Step 1 GAPs on commits that changed the plugin after its last bump (its `README.md`
   excepted). `marketplace.json` entries carry no version.
2. **CHANGELOG.md** (repo root): today's `## YYYY-MM-DD` section below `## [Unreleased]`, under
   `### Added` / `### Changed` / `### Fixed`, newest first, one line per version:
   `- <plugin> X.Y.Z: <what changed, user-facing>`. Step 1 GAPs when the line for the current version is
   missing.
3. **Plugin `README.md`**: features table, requirements and layout match the change.
4. **Root `README.md`**: the At a glance row, the ``### [`<plugin>`](<plugin>)`` section and, for a new
   plugin, the intro sentence and the Repository layout line. **`.claude-plugin/marketplace.json`**: a new
   plugin gets an entry (`name`, `source`, `description`, `category`, `keywords`); keep the description
   current.
5. **Wiki** (`padina-claude-code-plugins.wiki` next to the repo, branch `master`): the plugin's page
   `<plugin>.md` (same shape as the others: the problem, Setup, What you get, feature sections,
   Uninstalling), its `Home.md` table row (and the intro sentence for a new plugin), its `_Sidebar.md`
   link. Commit, then push by URL:
   `git push git@github-padina:roypadina/padina-claude-code-plugins.wiki.git HEAD:master`.
6. **Site card**: `roypadina-apps/data/apps.json`, slug `padina-claude-code-plugins` (Step 1 prints its
   text). The home page card shows `tagline` and the install line; `pitch` names the plugins (rendered
   only on a page, and this entry has `hasPage: false`, so keep it right for when it gets one). A new
   plugin or a changed headline feature → edit those lines in place, `node build.mjs`, commit, push and
   check the deploy as in 15d. No version, no page, no "What's new".
7. **Push.** `git status -sb`, stage named files, commit `<plugin> X.Y.Z: <summary>`,
   `git push origin main`. `main` is protected, and the owner's direct push bypasses it (the "Bypassed rule
   violations" notice is expected). Then check CI:
   `gh run list --repo roypadina/padina-claude-code-plugins -L 1` must end `success` (Validate manifests).
8. **Install on every profile.** `claude-plugin-all marketplace update padina`, then
   `claude-plugin-all plugin update <plugin>@padina` (a new plugin: `plugin install`), then
   `claude-plugin-drift`. Tell the user to run `/reload-plugins`. Step 1 GAPs while any Claude config dir
   (`FAR_CLAUDE_DIRS`) has an older version installed. Both are zsh functions, not on `PATH`: from a Bash
   tool call run `zsh -ic 'claude-plugin-all …'`. Their output ends in inventory-drift noise, so confirm
   with `jq -r '.plugins["<plugin>@padina"][].version' ~/.claude*/plugins/installed_plugins.json`.
9. **Wrap-up.** The `claude-setup-inventory` skill (offer it, then `sync` + `refresh` and a changelog line
   on each changed plugin's note); the user's memory note for the plugin when it pins a version. Then
   Step 3 G20–21: re-run Step 1, stamp, and report as a table.

## New public app

Repo going public or first cask → [references/new-public-app.md](references/new-public-app.md): privacy
triple check, history squash, community files, CI and branch protection, repo metadata, icons, About
window and Ko-fi, wiki, first cask and tap README row, marketing site + repo marketing (site entry and page, website badge, feature-request block, More Mac apps, social preview). Every step there is net-new: show the plan, get
an explicit OK.

## Per-app notes

Summary only — the app's `CLAUDE.md` and memory note win.

| App | Dir in `~/Code/Padina` | Quirks |
|---|---|---|
| LanGuard | `LanGuard-app` | Version in `Config/Shared.xcconfig`; xcodebuild Release + ditto zip; universal build needs `-destination 'generic/platform=macOS'`; wiki clone `LanGuard.wiki` next to the repo; helper script/plist changed → after the update (§ F) the user relaunches it (Raycast) and clicks Settings › Protection › Update helper, then `launchctl print system/com.roypadina.languard-net` shows `runs = 1` staying at 1 |
| MaccyPlus | `Maccay` | Remote `padina`, never `origin`; version in the pbxproj; prepend an `appcast.xml` item (length = zip bytes, `sparkle:version` = build) after the release asset exists; since 2.10.2 (`SUPublicEDKey`) the `<enclosure>` must carry `sparkle:edSignature` + `length` exactly as `build-release.sh` prints them (`appcast enclosure:` line) — an unsigned item is refused by every keyed copy. `main` is protected, so it goes in its own PR `appcast: X.Y.Z`; `xmllint --noout appcast.xml` first; wiki clone is `maccyplus.wiki` (slug, not folder name); upstream-sync PRs merge with `--merge`, never `--squash`; build with `MACCYPLUS_SIGN_IDENTITY` set (see memory) |
| VaultBar | `VaultBar` | Push only `main`; privacy triple check before every public push; `RELEASE=1 Scripts/package_app.sh` |
| Window Organizer | `window-organizer` | Version is a literal in the `Scripts/package_app.sh` plist heredoc; asset `Window-Organizer.zip` |
| SmartHiddenBar | `SmartHiddenBar` | `RELEASE=1 ./build.sh` (Sparkle since 1.6.0: also writes `build/appcast.xml` from the CHANGELOG section — heading first, upload both assets; local install = in-app update, § F path A); since 1.3.2 releases share the dev identity, so the brew path (§ F B) is `brew upgrade` + quarantine clear (grant survives, verified 1.3.3) |
| MeetAlert | `MeetAlert` | Wiki is the nested clone `MeetAlert/wiki`; `build.sh` makes no zip — ditto it; bump `Info.plist` with `sed` on the two version lines, because `PlistBuddy` reformats the whole file |
| Agents Monitor | `AgentsMonitor` | Asset must be `AgentsMonitor.zip`; Sparkle since 1.9.0: `Scripts/build-release.sh` also writes `build/appcast.xml` (feed = `releases/latest/download/appcast.xml`, notes = the CHANGELOG section, so the `## [X.Y.Z]` heading must exist before the build) — upload it with the zip; never commit work or topic strings; local install = in-app update (§ F A); on the brew path, after `brew upgrade` extract the release zip to `/tmp`, clear quarantine there, `ditto` it over `/Applications` before launch (Gatekeeper trashes the brew copy) |
| agentctl | `agentctl` | CLI-only cask since 0.11.0 (`binary "agentctl/bin/agentctl"`, no app, no About window — Ko-fi lives in `--help`). `main` protected: bump `package.json` + lock + CHANGELOG in a PR, admin-merge; `npm ci` then `sh scripts/build-release.sh` → `release/agentctl.zip` in a throwaway worktree at the merge sha (the script's `npm run build` needs devDeps); CI's `Test (ubuntu, best-effort)` leg flakes, macOS `Test & build` is the gate; local install = `brew upgrade --cask agentctl` only (no xattr, no relaunch) |
| Obsidian Vault Git Watcher | `ObsidianVaultGitWatcher` | Plain `swiftc` via `build.sh` (no SwiftPM/Xcode), version in `Info.plist`; `./build.sh dist` → `dist/ObsidianVaultGitWatcher.zip`; `main` protected; never push local `backup/pre-public`; after `brew upgrade` reload the LaunchAgent (copy repo plist, `bootout` exact label, `bootstrap`) |
| PullPing | `PullPing` | Version in `Info.plist` (`CFBundleShortVersionString` + `CFBundleVersion`) + bug_report.yml placeholder; `main` protected → PR, admin-merge; `RELEASE=1 Scripts/package_app.sh` → `dist/PullPing.zip`; README screenshots `RENDER_SCREENSHOTS=$PWD/docs/screenshots swift test --filter ScreenshotRenderTests` (fake data); site WebP = `cwebp -q 85` (main-window `-resize 1600 0`, others native); menu-bar app, Sparkle since 0.6.0: local install = in-app update (§ F A); cask has `binary … target: "pullping"` (the app executable is the `pullping` CLI); a feature branch whose history holds private names (old test fixtures) is squashed to one local commit before the first push |
| claude-jam | `claude-jam` | Formula from the tag tarball; README and wiki quote the npm tarball version — bump them |

## Sparkle updates

In-app update check + prompt (Sparkle 2) — template: Agents Monitor commit "Add Sparkle in-app updates".
- **One EdDSA key for every app**: login Keychain item "Private key for signing Sparkle updates"
  (made by `generate_keys`). Public key `qq4oZAVmJanKJ1bTAzGSO94WWX6cx+/5kCjBZxJXEm0=` → `SUPublicEDKey`.
  Each Sparkle tool (`generate_appcast`, `sign_update`) asks for Keychain access once: Roy types the
  login password + **Always Allow**; a background build blocks until he does. Tools come with the
  package: `build/SourcePackages/artifacts/sparkle/Sparkle/bin/` (no install).
- **Add to an app**: Sparkle SPM package; `SUFeedURL` = `https://github.com/roypadina/<Repo>/releases/latest/download/appcast.xml`
  (no commit per release), `SUPublicEDKey`, `SUEnableAutomaticChecks` true; one `SPUStandardUpdaterController`
  started at launch + a "Check for Updates…" button; build script re-signs Sparkle inside-out
  (XPCs, `Updater.app`, `Autoupdate`, framework) and runs `generate_appcast --embed-release-notes`;
  entitlement `com.apple.security.cs.disable-library-validation` (self-signed + hardened runtime has no
  Team ID, so library validation refuses Sparkle.framework); cask `auto_updates true`.
- **Build-script musts** (review of Agents Monitor 1.9.0): `rm -f build/appcast.xml` before
  `generate_appcast` (it merges into a leftover file — a stale signed item shipped otherwise); run it only
  when `generate_keys -p` equals the app's `SUPublicEDKey` (another key = a feed every copy refuses);
  `CODE_SIGN_INJECT_BASE_ENTITLEMENTS = NO` in Release (Xcode injects `get-task-allow` outside archives,
  which with hardened runtime lets any user process attach and read memory).
- **Menu-bar (LSUIElement) apps**: a scheduled update alert opens behind other windows with no Dock icon.
  Give the controller a `SPUStandardUserDriverDelegate` (`supportsGentleScheduledUpdateReminders` true;
  `standardUserDriverWillHandleShowingUpdate` → `.regular` + `NSApp.activate()`;
  `standardUserDriverWillFinishUpdateSession` → back to `.accessory` when no other window is open).
- **Never drop `SUPublicEDKey` or change the signing identity** once shipped — Sparkle refuses key
  removal, and a keyless old copy (MaccyPlus ≤ 2.10.1) only accepts an update whose code signature matches.
- **rpath**: the binary needs `@executable_path/../Frameworks` — Xcode projects scaffolded without
  frameworks lack it (`LD_RUNPATH_SEARCH_PATHS = $(inherited) @executable_path/../Frameworks` in the
  xcconfig); SwiftPM-built apps copy `Sparkle.framework` into `Contents/Frameworks` and add the rpath
  themselves. Missing → dyld aborts at launch (`Library not loaded: @rpath/Sparkle.framework…`), which for
  a menu-bar app only looks like "no icon". Check `otool -l <binary> | grep -A2 LC_RPATH`, and launch the
  signed release build from `/Applications` (Roy opens it) before tagging: `vmmap <pid> | grep Sparkle`.
- **SwiftPM apps** (template: PullPing 0.6.0): `.package(url: "https://github.com/sparkle-project/Sparkle",
  from: "2.10.0")` placed *after* `products:` (manifest argument order), product on the app target only,
  `linkerSettings: [.unsafeFlags(["-Xlinker", "-rpath", "-Xlinker", "@executable_path/../Frameworks"])]`;
  the packager dittos `$(swift build … --show-bin-path)/Sparkle.framework` into `Contents/Frameworks`;
  tools live in `.build/artifacts/sparkle/Sparkle/bin`. A cask `binary` symlink to the app executable
  (CLI) keeps working: dyld resolves `@executable_path` through the symlink.
- **Never `codesign --deep --identifier <app id>`** once Sparkle is embedded: it stamps the app's identifier
  on Sparkle's helpers. Sign inside-out (`find … -depth` over frameworks/xpc/app/Autoupdate with
  `--preserve-metadata=identifier,entitlements,flags`), then the app with `--identifier`, then
  `codesign --verify --deep --strict`.
- **Apps that promised "no network"** (NtfyBar, Window Organizer, MeetAlert) ship **without**
  `SUEnableAutomaticChecks`: Sparkle asks on the second launch and contacts nothing before a yes. Rewrite
  every "no network / no update checks" claim (README, wiki Home/FAQ/Permissions, site page + apps.json).
  Other apps ship it `true`.
- **Updater start** in `applicationDidFinishLaunching`, gated on the app's test env var and
  `Bundle.main.bundleIdentifier != nil` (a bare `swift run` would show Sparkle's "Unable to Check" alert).
  An updater created inside a view (`@State`, MaccyPlus upstream) only runs while that view lives — keep
  one app-lifetime instance.
- **Swift 6 targets**: the presenter class needs `@unchecked Sendable` (no stored state) or `nonisolated`
  plus `MainActor.assumeIsolated` in the delegate methods.
- **Roy's own Mac updates silently**: `defaults write <bundle id> SUEnableAutomaticChecks -bool YES` and
  `SUAutomaticallyUpdate -bool YES` per Sparkle app (a sandboxed app's container gets it through cfprefsd).
- **Live install test**: installing a release build in `/Applications` quits Roy's running copy — never for
  his always-on apps (meeting alarm, auto-lock, ntfy client) while he is away; build and review, install
  when he is back. Every release after an app's first Sparkle one reaches the installed copy through
  Sparkle: § F path A. The first Sparkle release cannot (the installed copy has no Sparkle) → § F path B.

## Self-update

A run hit something this file did not predict — a failed command, a new per-app quirk, a step the user
had to ask for? Before reporting, patch this file (and the script, if a check was missing) in
`~/Code/Padina/padina-claude-code-plugins/finalize-app-release/`, bump `.claude-plugin/plugin.json`,
commit, push, then `claude-plugin-all marketplace update padina` and
`claude-plugin-all update finalize-app-release@padina`.
