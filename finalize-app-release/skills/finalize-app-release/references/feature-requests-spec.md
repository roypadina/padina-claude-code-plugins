# Feature requests & contributions: one block for every app (2026-10-23)

Reusable copy for all roypadina/* apps. Apply verbatim; only the placeholders change.
Placeholders: `{AppName}` (display name, e.g. `Window Organizer`), `{repo}` (GitHub repo name, e.g. `window-organizer`; note `LanGuard`, `AgentsSessionHopper`, `Agentctl`, `claude-jam` casing as on GitHub).
Voice: warm, plain, confident. No guilt, no hype, no em dashes.

---

## 1. Mechanism (decided)

**One path for every repo: GitHub Issues, via the `feature_request.yml` issue form.** Code goes in as pull requests. Discussions are not part of the block.

Why Issues and not Discussions "Ideas" + upvotes:
- Discussions are on in only 4 of the 12 app repos (window-organizer, LanGuard, claude-jam, ObsidianVaultGitWatcher) and hold 0 threads. Issues exist everywhere, with templates already in place.
- One maintainer, one inbox. Two queues split attention and the "Ideas" one is the one that goes stale.
- An issue can carry labels (`enhancement`, `supporter`), is closed by `Closes #n` in the PR, shows up in cross-repo searches, and has a stable deep link the About window and `--help` can open directly (`issues/new?template=feature_request.yml`). Discussions do none of that cleanly.
- Upvotes only mean something with hundreds of users. At 0-24 stars a 👍 on an issue does the same job.

Why "supporters first" and how it stays honest (Ko-fi rules):
- Ko-fi's terms separate **Donations** (gifts) from **Commissions, Shop and Memberships** (sold Creator Content). A tip buys nothing, so priority must be a courtesy, never a product: no price, no "tip to unlock", no delivery promise, no timeline, and a request without a tip is never turned away on that ground. Do not set this up as a Ko-fi Commission (that is a sale with delivery obligations).
- Mechanism: the issue form has an optional, public "Ko-fi supporter?" field for the Ko-fi display name. Roy checks it against the Ko-fi dashboard, adds the `supporter` label, and reads supporter requests before the rest. That is the whole promise.
- Wording used on every surface: *"It's a thank-you, not a purchase: no promise on what ships or when."*
- Escape hatch for people who tipped anonymously or do not want their name on a public issue: leave the request in the Ko-fi tip message; Roy files the issue.

Code contributions: PRs welcome, small and focused, issue first for anything bigger, link to CONTRIBUTING.md. "Best effort, evenings" stated once per surface (STRATEGY.md risk 7).

---

## 2. Repo settings per repo (checklist)

1. **Replace** `.github/ISSUE_TEMPLATE/feature_request.yml` with section 3d (whole file).
2. **Create label `supporter`** (one per repo; personal gh account):
   ```bash
   env -u GITHUB_TOKEN GH_TOKEN="$(gh auth token -u roypadina)" gh label create supporter -R roypadina/{repo} -c F16061 -d "Requested by a Ko-fi supporter: front of the queue"
   ```
   Keep the existing `enhancement` label as the feature-request label (it exists in every repo, the forms already apply it, old issues carry it). No new `feature request` label: it would duplicate `enhancement` and need creating in 12 repos.
3. **Discussions:** not required by the block. Leave them on where they are on. Gap found: `config.yml` in LanGuard, SmartHiddenBar, VaultBar, MeetAlert, AgentsSessionHopper, agentctl points "Question / discussion" at `/discussions` while Discussions are OFF there (dead link). Cheapest fix, no file change: `env -u GITHUB_TOKEN GH_TOKEN="$(gh auth token -u roypadina)" gh repo edit roypadina/{repo} --enable-discussions`. (NtfyBar and AgentsMonitor `config.yml` have no Discussions link; leave them.) Roy's call per repo.
4. **Roy's queue** (bookmark, cross-repo): `https://github.com/issues?q=is%3Aopen+is%3Aissue+user%3Aroypadina+label%3Aenhancement+label%3Asupporter`
5. Optional, Ko-fi page About text (Roy, 1 min): add *"Tipped? Your feature requests go to the front of my queue: add your Ko-fi name to the GitHub issue."*

Implementers touch only: `README.md`, `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/feature_request.yml`, the About view Swift file (menu-bar apps), `--help` text (CLI apps), the wiki clone (`Feature-requests-and-contributing.md` + `_Sidebar.md`, optional `Home.md` line).

---

## 3. Copy per surface

### 3a. README section

Place **right above `## More Mac apps by Roy`** (which sits above `## Support`). Heading level matches the README (`##`).

```markdown
## Feature requests and contributions

Have an idea for {AppName}? [Request a feature](https://github.com/roypadina/{repo}/issues/new?template=feature_request.yml) and say what you're trying to do; that matters more than the exact feature. Found a bug? [Report it](https://github.com/roypadina/{repo}/issues/new?template=bug_report.yml).

Code is welcome too: small, focused pull requests, and an issue first for anything bigger. See [CONTRIBUTING.md](CONTRIBUTING.md).

Tipped on [Ko-fi](https://ko-fi.com/roypadina)? Add your Ko-fi name to the request and it goes to the front of my queue. It's a thank-you, not a purchase: no promise on what ships or when.
```

If the README already has a `## Contributing` section (agentctl does), keep it and put this block directly after it; drop the second paragraph's first sentence to avoid saying "PRs welcome" twice.

### 3b. Wiki

**Page file:** `Feature-requests-and-contributing.md` (page title "Feature requests and contributing").

```markdown
# Feature requests and contributing

{AppName} is built by one person, in the evenings, and shaped by what people ask for. Here is how to ask, and how to help.

## Request a feature

1. Search the [open requests](https://github.com/roypadina/{repo}/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement) first. If your idea is there, add a 👍 and a comment with your use case.
2. Otherwise [open a feature request](https://github.com/roypadina/{repo}/issues/new?template=feature_request.yml). Say what you're trying to do and where {AppName} gets in the way; that matters more than the exact feature.
3. Bugs go through the [bug report](https://github.com/roypadina/{repo}/issues/new?template=bug_report.yml) instead.

## Ko-fi supporters go first

If you've tipped on [Ko-fi](https://ko-fi.com/roypadina), add your Ko-fi name in the "Ko-fi supporter?" field. I check it, add the `supporter` label, and read those requests before the rest. It's a thank-you, not a purchase: no promise on what ships or when, and a request without a tip is just as welcome. Tipped anonymously, or rather not say in public? Leave the request in your Ko-fi message instead and I'll file the issue.

## Contribute code

Pull requests are welcome.

- Keep them small and focused: one change per PR, the smallest diff that solves it.
- Open an issue first for anything bigger than a fix, so we agree on the shape before you spend an evening on it.
- Setup, layout, tests and the PR flow are in [CONTRIBUTING.md](https://github.com/roypadina/{repo}/blob/main/CONTRIBUTING.md).

## What to expect

I read every issue and PR, usually within a few days. Replies and releases are best effort, evenings and weekends. Open requests stay open; closed ones get a reason.
```

**Sidebar:** one line, last entry of the page list (before the first `---`), in the sidebar's existing list style:

```markdown
- [Feature requests and contributing](Feature-requests-and-contributing)
```
(LanGuard sidebar style: `[Feature requests and contributing](Feature-requests-and-contributing)` on its own line. claude-jam style: `- [[Feature requests and contributing|Feature-requests-and-contributing]]`.)

**Home.md** (optional, only if Home has a "Pages" list): add as the last list item
`- **[Feature requests and contributing](Feature-requests-and-contributing)**: how to ask, supporters first, PR rules.`

### 3c. In-app About window (menu-bar apps)

Layout stays as in the Ko-fi standard (icon, name, version, Made by, bio, Ko-fi prominent + GitHub, "Report an issue"). Insert the new block **after the "Report an issue" link and before the caption lines** (`© Roy Padina · MIT`; in AgentsSessionHopper before the disclaimer caption; where third-party credits exist, before those). Ko-fi stays the only `.borderedProminent` `.large` button; the two new buttons are `.bordered` at the default control size, so they read as secondary. See `about-mock.html` / `about-mock.png`.

Copy (2 lines + 2 buttons):

- Line 1 (headline): **Have an idea, or want to help build it?**
- Line 2 (callout, secondary): Feature requests and pull requests are welcome. Ko-fi supporters go to the front of the queue.
- Button 1: **Request a feature** → `https://github.com/roypadina/{repo}/issues/new?template=feature_request.yml`
- Button 2: **Contribute** → `https://github.com/roypadina/{repo}/blob/main/CONTRIBUTING.md`

SwiftUI (drop in; matches the existing `AboutView` style):

```swift
Divider()

VStack(spacing: 8) {
    Text("Have an idea, or want to help build it?").font(.headline)
    Text("Feature requests and pull requests are welcome. Ko-fi supporters go to the front of the queue.")
        .font(.callout)
        .foregroundStyle(.secondary)
        .multilineTextAlignment(.center)
        .fixedSize(horizontal: false, vertical: true)

    HStack {
        Link(destination: URL(string: "https://github.com/roypadina/{repo}/issues/new?template=feature_request.yml")!) {
            Text("Request a feature").frame(minWidth: 120)
        }
        .buttonStyle(.bordered)

        Link(destination: URL(string: "https://github.com/roypadina/{repo}/blob/main/CONTRIBUTING.md")!) {
            Text("Contribute").frame(minWidth: 90)
        }
        .buttonStyle(.bordered)
    }
}
```

Verify the standard way: render the view standalone (main.swift + `screencapture -l`), no clicking. Window width stays 380 (400 in AgentsSessionHopper); nothing else in the view changes.

### 3d. Issue form: `.github/ISSUE_TEMPLATE/feature_request.yml` (whole file)

```yaml
name: Feature request
description: Suggest an idea for {AppName}
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: What are you trying to do?
      description: The situation where {AppName} gets in the way or falls short. This matters more than the exact feature.
    validations:
      required: true
  - type: textarea
    id: proposal
    attributes:
      label: What would you like {AppName} to do?
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Workarounds or alternatives you've tried
  - type: input
    id: kofi
    attributes:
      label: Ko-fi supporter? (optional)
      description: Your Ko-fi name, if you've tipped. Supporter requests go to the front of the queue. It's a thank-you, not a purchase, so no promise on what ships or when. This field is public; skip it if you'd rather not say.
      placeholder: Ko-fi name
  - type: checkboxes
    id: pr
    attributes:
      label: Would you build it?
      options:
        - label: I'd be up for sending a pull request for this.
```

`labels` keeps `enhancement` (exists everywhere). `supporter` is added by Roy by hand after checking Ko-fi, never by the form.

### 3e. CONTRIBUTING.md section

Replace the existing `## Reporting bugs / requesting features` section (claude-jam: `## Reporting bugs and security issues`, keep its security bullet) with:

```markdown
## Feature requests and bugs

- **Feature requests:** [open one](https://github.com/roypadina/{repo}/issues/new?template=feature_request.yml) and say what you're trying to do; that matters more than the exact feature. Search the [open requests](https://github.com/roypadina/{repo}/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement) first and 👍 an existing one if it's there.
- **Bugs:** use the [bug report](https://github.com/roypadina/{repo}/issues/new?template=bug_report.yml).
- **Ko-fi supporters:** add your Ko-fi name to the request and it goes to the front of my queue. It's a thank-you, not a purchase: no promise on what ships or when.
- **Bigger changes:** open an issue before the PR so we agree on the shape first. Small, focused PRs can come straight in.
- Replies are best effort, evenings and weekends. I read everything.
```

Keep any repo-specific bug line that exists today (agentctl: "include your macOS + Node versions and how you launched it") as the second half of the **Bugs** bullet.

---

## 4. Variants

### ALPHA: claude-jam ("help finish it")

- **README:** keep the existing `## Help build it` section and heading (it already does the job). Append two list items and one paragraph; do not add the 3a block separately.
  ```markdown
  5. Missing something? [Request a feature](https://github.com/roypadina/claude-jam/issues/new?template=feature_request.yml), or better, help finish it: most alpha gaps are in the [roadmap](docs/ROADMAP.md) and open for a PR.
  6. Tipped on [Ko-fi](https://ko-fi.com/roypadina)? Add your Ko-fi name to the request and it goes to the front of my queue. It's a thank-you, not a purchase: no promise on what ships or when.
  ```
- **Wiki page:** section 3b with the intro replaced by:
  `claude-jam is alpha and built by one person, in the evenings. The fastest way to get a feature is to help finish it: most gaps are in the [roadmap](https://github.com/roypadina/claude-jam/blob/main/docs/ROADMAP.md) and open for a PR. Here is how to ask, and how to help.`
  Sidebar: `- [[Feature requests and contributing|Feature-requests-and-contributing]]` after the Windows WSL2 Host entry.
- **CONTRIBUTING.md:** 3e, inserted above `## Reporting bugs and security issues`; delete that section's "Bugs:" bullet (now covered) and keep its "Security problems" bullet under a `## Security issues` heading.
- **Issue form:** 3d as is (`labels: ["enhancement"]`; the repo's `alpha` label is not auto-applied).
- **No About window.** `--help` (launcher script `claude-jam`, the `usage` function, after the `Support on Ko-fi` echo):
  ```
  Feature requests: https://github.com/roypadina/claude-jam/issues/new?template=feature_request.yml
  Help finish it:   https://github.com/roypadina/claude-jam/blob/main/CONTRIBUTING.md
  Supporters' requests go to the front of the queue. A thank-you, not a purchase.
  ```

### BETA: AgentsSessionHopper

- **README:** 3a with one extra sentence at the end of the first paragraph: `AgentsSessionHopper is in beta, so a bug report counts as much as a feature request.`
- **About window:** 3c block placed after "Report an issue" and before `HopperInfo.disclaimer`. Width stays 400.
- **Wiki, CONTRIBUTING, issue form:** standard (3b, 3e, 3d).

### CLI apps: agentctl, claude-jam (no About window)

- README (3a / ALPHA variant), wiki (3b), CONTRIBUTING (3e), issue form (3d) as above.
- `--help` footer. agentctl (`src/cli/index.ts`, the top-level help text, after `Support Agentctl: https://ko-fi.com/roypadina`):
  ```
  Feature requests: https://github.com/roypadina/Agentctl/issues/new?template=feature_request.yml
  Contribute:       https://github.com/roypadina/Agentctl/blob/main/CONTRIBUTING.md
  Supporters' requests go to the front of the queue. A thank-you, not a purchase.
  ```
  claude-jam: see ALPHA above.

### Standard (everything else)

LanGuard, MaccyPlus, Agents Monitor, MeetAlert, SmartHiddenBar, Window Organizer, VaultBar, ObsidianVaultGitWatcher, NtfyBar: 3a-3e as written. MaccyPlus About: same block, same position; credit lines to Maccy stay below it.

---

## 5. Do-not list (all surfaces)

- Never "tip to unlock", never a price, never a timeline, never "guaranteed", never feature gating.
- Never link Discussions from the block.
- Never make the Ko-fi field required or private-by-default (GitHub issue forms are public; say so).
- Never put the Ko-fi ask above the request path in the About window; Ko-fi keeps the prominent button, the new buttons stay bordered.
