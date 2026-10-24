# New public app — first publish

Everything here is net-new and public. Show the plan, then get an explicit OK for each irreversible
step: making the repo public, a force-push, a history squash, the first cask.

The most complete existing repos to copy from: `~/Code/Padina/window-organizer` and
`~/Code/Padina/VaultBar` (SwiftPM), `~/Code/Padina/LanGuard-app` (Xcode project).

## 1. Privacy triple check

Before the first public push, and before every push of a repo that was private until now.

1. **Denylist grep** over the tree, the full history, the wiki and the release zip: employer and client
   names, internal hostnames, work and personal emails, phone numbers, `/Users/<name>` paths,
   notification topics, tokens and keys.
   `git grep -inE '<pattern>'`, `git log -p --all | grep -inE '<pattern>'`,
   `strings <App>.app/Contents/MacOS/<App> | grep -iE '/Users/|<pattern>'`.
2. **gitleaks:** `gitleaks git --log-opts=--all` and `gitleaks dir .` (`brew install gitleaks`).
3. **Independent reviewer:** a subagent re-checks the tree, the wiki and the images with no context
   from you.

Also:

- Screenshots show no personal or work text (menu bar, account names, calendar titles, file names).
  PNG files can embed the monitor's ICC profile with its name: keep only the IHDR/IDAT/IEND chunks.
- Release builds strip paths: `strip -S -x` and `-file-prefix-map`, so no home path ships in the binary.
- A leak in history → squash to one initial commit and keep a local `backup/*` branch that is never
  pushed. Don't force-push the squash into the existing repo: once public, its Activity page lists
  the force-push with the old sha, and GitHub keeps unreferenced commits reachable by sha. Instead
  rename the old repo to `<Repo>-private-archive` (stays private, nothing deleted; needs an
  explicit OK), create a fresh public repo under the old name and push the squashed `main`. The
  fresh repo's wiki needs "Create the first page" again; push the prepared pages on top of it with
  `git fetch <wiki url> master && git reset --soft FETCH_HEAD`, then commit (no force-push).

## 2. Repo

- `git config user.email 4943097+roypadina@users.noreply.github.com` (repo-local, before the first commit).
- Files:
  - `LICENSE` — MIT © Roy Padina.
  - `README.md` — centered header (icon, name, tagline), badge row (macOS, Swift, CI, License,
    Ko-fi; Homebrew, Release, PRs, Stars where they fit), screenshot in `docs/screenshots/`. Sections:
    Features, Install (Homebrew + build from source), Usage, Permissions, Limitations, Privacy,
    Uninstall, Support, License.
  - `CHANGELOG.md` (Keep a Changelog), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
  - `.github/FUNDING.yml` (`ko_fi: roypadina`), `.github/CODEOWNERS` (`* @roypadina`),
    `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/{bug_report,feature_request,config}.yml`,
    `.github/workflows/ci.yml` (job "Build and test").
- Create the repo public under `roypadina`, remote `git@github-padina:roypadina/<Repo>.git`, push `main`.
- Metadata: description, homepage = `https://apps.roypadina.synology.me/apps/<slug>/` (the site page, not the wiki; set it after § 8 deploys), topics (`macos`, `menu-bar`, `swift`, …).
- Branch protection on `main`: the CI job as required check, code-owner review, admins can bypass
  (`enforce_admins` off — the sole owner cannot approve their own PR).

## 3. Icons

App icon and a menu-bar template icon in the house style (squircle, gradient). SVG sources in
`Assets/icons`, rendered by `Scripts/make_icons.sh` (rsvg-convert + iconutil) — copy from
window-organizer. Menu-bar icon: template `menubar.png` + `@2x`.

## 4. About window and Ko-fi in the app

Reference window: `~/Code/Padina/Maccay/Maccy/About.swift`. Reference menu and Settings wiring:
window-organizer `Sources/WindowOrganizerApp/WindowOrganizerApp.swift` and `SettingsView.swift`.

- A custom, fit-to-content SwiftUI window — never the standard About panel (its credits box clips).
  `NSWindow(contentViewController: NSHostingController(rootView: AboutView()))`, style
  `[.titled, .closable]`, `isReleasedWhenClosed = false`, `center()`, activate, `makeKeyAndOrderFront`.
- `AboutView`: `VStack(spacing: 12)`, `.padding(24)`, `.frame(width: 380)`, in this order:
  1. App icon, 96×96.
  2. Name in `.title.bold()`; "Version X.Y.Z (build)" from `Bundle.main.infoDictionary`, `.callout`, secondary.
  3. "Made by Roy Padina" in `.headline`, then the bio (below), centered,
     `.fixedSize(horizontal: false, vertical: true)`.
  4. Buttons: `Link("Support on Ko-fi ☕")` → `https://ko-fi.com/roypadina` (`.borderedProminent`,
     `.large`), `Link("GitHub")` → the repo (`.bordered`).
  5. `Link("Report an issue")` → `<repo>/issues`, `.callout`.
  6. `Divider()`, then third-party credits small (`.caption`, secondary) at the bottom.
- Bio — approved wording, do not change it without asking:
  "I'm a software engineer from Israel who builds small, focused Mac tools to fix the little
  annoyances in my own day — then shares them free and open source. If this app saves you time, a
  coffee on Ko-fi keeps the next one coming. ☕"
- Menu: "About <App>" and "Support on Ko-fi ☕" above Quit.
- Settings: a compact About row with "About <App>…" and "Support on Ko-fi ☕".
- CLI-only tool: put "Made by Roy Padina", the bio and the Ko-fi URL in `--help` (as claude-jam does).
- CI runs an older Swift than the local toolchain: push early and read the first CI run (a local
  `typealias State` compiled on 6.4 but shadowed SwiftUI's `@State` on 6.3).
- Verify by rendering the view standalone — a tiny `main.swift` that shows the window, then
  `screencapture -l <window id>` — and check nothing clips. Do not click around the user's live Mac.

## 5. Wiki

- The user creates the first page in the web UI (no API can). Then clone
  `git@github-padina:roypadina/<Repo>.wiki.git` to `~/Code/Padina/<Repo>.wiki` and set the
  repo-local noreply email.
- Pages: Home (what it is, install, a Ko-fi paragraph), Installation, Usage, Permissions,
  Troubleshooting, FAQ, Building-from-source.
- `_Sidebar.md`: every page, a Releases link, then `---` and the Ko-fi button at the bottom.
- `_Footer.md`:
  `[<App>](https://github.com/roypadina/<Repo>) · MIT © Roy Padina · [Support on Ko-fi ☕](https://ko-fi.com/roypadina)`
- Privacy-check the wiki like the code.

## 6. First release and cask

- Release per SKILL.md § D.
- Build/release script signs with the stable identity from day one: use `KeyLayoutSwitcher Dev` when
  `security find-identity -v -p codesigning | grep -q "KeyLayoutSwitcher Dev"`, env override
  `<APP>_SIGN_IDENTITY`; ad-hoc (`-`) fallback only when the identity is missing (CI, contributors), and
  print it. Sign nested Mach-Os inner-first, then the app. Reference: `~/Code/Padina/Maccay/Scripts/build-release.sh`.
- `~/Code/Padina/homebrew-tap/Casks/<token>.rb`:

  ```ruby
  cask "<token>" do
    version "X.Y.Z"
    sha256 "<sha256 of the release zip>"

    url "https://github.com/roypadina/<Repo>/releases/download/v#{version}/<Asset>.zip"
    name "<App>"
    desc "<one line, no trailing period>"
    homepage "https://github.com/roypadina/<Repo>"

    depends_on macos: :sonoma

    app "<App>.app"

    zap trash: "~/Library/Preferences/<bundle id>.plist"

    caveats <<~EOS
      <App> is self-signed with a stable identity (not notarized), so on first launch macOS may block it.
      Right-click <App> in /Applications and choose Open, or run once:
        xattr -dr com.apple.quarantine "/Applications/<App>.app"
    EOS
  end
  ```

  Add
  `binary "#{appdir}/<App>.app/Contents/MacOS/<cli>", target: "<cli>"` only if the app ships a CLI.
  Never `uninstall quit:` or `launchctl:` for an app that runs a login item — they kill the running
  copy on every upgrade; put login jobs under `zap` only.
- `brew style roypadina/tap/<token>` and `brew audit --cask --new roypadina/tap/<token>` clean.
- Tap `README.md`: a row in the Casks table, alphabetical —
  `| **<token>** | <one line> [Repo](https://github.com/roypadina/<Repo>) |`.
- Push the tap by URL, verify on the server, install locally (SKILL.md § E–F).

## 7. Marketing site + repo marketing

Site repo `~/Code/Padina/roypadina-apps` (private; `README.md` = apps.json contract, `docs/design.md` =
page how-to, `CLAUDE.md`). Copy blocks from [feature-requests-spec.md](feature-requests-spec.md). Public-clean
rules apply to every image and file.

1. **Site entry + page.** New object in `data/apps.json` (keys in README order; `badge` alpha/beta if not
   stable; `hasPage: true`), `src/pages/<slug>.mjs` copied from a sibling per `docs/design.md`, icon
   (256 px WebP in `static/icons/`) and screenshots (`static/screenshots/<slug>/`, WebP, offscreen renders,
   fake data, nothing personal). Add the app's 16x16 glyph in `src/glyphs.mjs` if the build asks.
   `node build.mjs`, review light + dark, desktop + 390 px (recipe in the site `CLAUDE.md`). Never hard-code
   an app count anywhere (site, READMEs, wiki, tap, plugin docs): count nothing, or derive it.
2. **Deploy = push to `main`** (unprotected): CI builds and publishes `deploy`, NAS git-sync pulls it
   within ~1 min, `verify` polls `/version.txt` = the pushed sha. Check the page is live:
   `curl -sI https://apps.roypadina.synology.me/apps/<slug>/ | head -1`. Never touch the NAS stack.
3. **Repo homepage** = `https://apps.roypadina.synology.me/apps/<slug>/`:
   `gh repo edit roypadina/<Repo> --homepage …` (personal account).
4. **README:** a "website" badge in the header row
   (`[![Website](https://img.shields.io/badge/website-apps.roypadina.synology.me-2F62E6)](https://apps.roypadina.synology.me/apps/<slug>/)`),
   then, **above `## Support`**: the "Feature requests and contributions" block (spec § 3a; ALPHA/BETA/CLI
   variants in § 4) and `## More Mac apps by Roy` with 3-4 sibling apps (each linking its site page;
   pick the closest in purpose). Keep the order: Feature requests, More Mac apps, Support.
5. **Siblings:** add the new app to the "More Mac apps" list of the sibling READMEs where it is relevant
   (their repos; a protected `main` → PR). Update the tap README row.
6. **Wiki:** footer and sidebar link to the site page; add `Feature-requests-and-contributing.md` (spec § 3b)
   and its sidebar line. `CONTRIBUTING.md` section from spec § 3e.
7. **Issue form + label:** `.github/ISSUE_TEMPLATE/feature_request.yml` from spec § 3d, then
   `gh label create supporter -R roypadina/<Repo> -c F16061 -d "Requested by a Ko-fi supporter: front of the queue"`.
8. **About window / `--help`:** the "Have an idea, or want to help build it?" block + two bordered buttons
   (spec § 3c) in the About view, after "Report an issue"; CLI tools get the `--help` footer (spec § 4).
9. **Stage tags:** an alpha/beta app shows an ALPHA/BETA tag on its icon everywhere (site card and page via
   `badge`, README header, social preview, wiki, tap `desc`).
10. **Social preview:** `sh og/render.sh <slug>` in the site repo, commit `docs/social-preview.png` in the app
    repo and `og/out/<slug>.png` in the site repo; Roy uploads it by hand (SKILL.md § E2 15c has the click path
    and the `cmp` check).

## 8. Optional — ask first

Awesome-list submissions from the `roypadina` account: `jaywcjlove/awesome-mac`,
`serhii-londar/open-source-mac-os-apps`, `jaywcjlove/awesome-swift-macos-apps`. Skip
`iCHAIT/awesome-macOS` — it mass-closes new-app PRs.
