# mac-design

A Claude Code plugin that makes Claude design, build and review native macOS app interfaces —
SwiftUI and AppKit — so they look and behave like Apple built them. It covers macOS 14 through 27,
with a version gate on every API newer than your deployment target.

One skill, `mac-design`, with three modes:

| Mode | What Claude does |
|---|---|
| **Design** | Writes a short design plan before any view code: archetype, information architecture, entry points, command map, empty/error states, permissions plan, deployment floor, the one feeling. |
| **Build** | Loads the topic reference for the surface it is writing, follows the rules, gates new APIs, then checks the surface against the rule IDs. |
| **Review** | Audits an existing app's code and/or screenshots: detects the stack, deployment target and archetype, runs a bounded `rg` sweep for known smells, walks the rules, and returns one ranked fix list (P1 first, cheapest fix first). |

The skill triggers on Mac UI work ("review my macOS UI", "make it feel like a real Mac app", "fix the
menu bar app") and on `/mac-design`. It stays out of web, iOS-only, Windows and general graphic design.

## What it covers

- **Design language** — Liquid Glass and materials, semantic color, dark mode and contrast, macOS text
  styles, spacing and concentric shapes, SF Symbols.
- **Windows and chrome** — window scenes and sizing, toolbars per column, sidebars, split views,
  inspectors, search placement, sheets, alerts, popovers, panels.
- **Menus and keyboard** — menu bar order, `Commands` plumbing, context menus, the Dock menu,
  standard shortcuts, focus, global hotkeys.
- **Settings** — the Settings window: tabs, rows, controls, sizing.
- **Menu-bar apps** — menu vs panel, `MenuBarExtra` vs `NSStatusItem`, activation policy, opening
  Settings from an accessory app, launch at login, status icon states, macOS 26/27 menu bar changes.
- **UX flows** — onboarding, permissions/TCC with System Settings deep links, empty/loading/error
  states, progress, notifications, undo, drag and drop, writing.
- **Accessibility** — VoiceOver, keyboard access, Reduce Motion/Transparency, Increase Contrast,
  custom controls, how to test.
- **Icons** — Icon Composer `.icon` files (also for SwiftPM apps without an Xcode project),
  document icons, menu-bar template images, custom symbols.
- **SwiftUI vs AppKit** — version gates, small house helpers, AppKit interop, floating panels, window
  access, tables, text, previews and captures.
- **Native feel** — what best-in-class Mac apps do, and the web/Electron/iOS anti-patterns.

## Layout

```
skills/mac-design/
  SKILL.md                  modes, version policy, the rules that matter most, reference map
  references/rules.md       the master checklist: one testable line per rule, with an ID
                            (WIN-3), a default severity (P1–P3), a version gate and a source
  references/*.md           one topic file per area (loaded only when needed)
  references/review.md      the audit procedure and the ranked-fix output format
  scripts/hig.sh            prints Apple's current HIG page on a topic as plain text
```

Rules cite their sources (HIG, Apple docs, WWDC sessions, release notes). Claims about macOS 27
that come from beta-era reports are marked `(27, verify)`.

## Live sources

The rules go stale as Apple ships. The skill checks current facts instead of trusting memory:

- **API availability** — Context7 when available; otherwise Apple's documentation JSON, with a
  one-line `curl | jq` shell function in `SKILL.md` that prints a symbol's macOS availability and
  deprecation.
- **HIG text** — `scripts/hig.sh <topic> --mac` prints Apple's current Human Interface Guidelines
  page without the other platforms (`hig.sh --list` for topic names). Pages are cached for 7 days in
  `~/Library/Caches/mac-design/hig/` and never written into a repo.

**Requires** macOS with `curl`, `jq` (ships with macOS 15+), `python3` and `zsh` for the live
sources; `rg` (ripgrep) for the review sweep. The rules themselves need nothing.

## Safety

The skill asks before it launches or drives your app or desktop, prefers Xcode previews, snapshot
tests or screenshots you provide, and never changes system settings, privacy grants or login items.

## Credits

Built on [BAMA](https://github.com/daveebbelaar/bama) by Dave Ebbelaar — its `mac-design`, `ux-design`,
`design-system`, `layout-grid`, `app-icon` and related design skills were the starting point, extended
with new research and corrected where Apple's docs disagree. `scripts/hig.sh` is BAMA's, with a renamed
cache path. BAMA is MIT-licensed; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Install

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install mac-design@padina
```

Development: `claude --plugin-dir /path/to/mac-design`.
