---
name: mac-design
description: This skill should be used when designing, building or reviewing the UI/UX of a native macOS app in SwiftUI or AppKit — windows, toolbars, menus, Settings, menu-bar (status item, MenuBarExtra) apps, panels, permission flows, accessibility, Liquid Glass, app icons — or auditing a Mac app's code or screenshots ("make it feel native", "review my macOS UI", "fix the menu bar app"). macOS 14–27 with version gates. Not for web, iOS/iPadOS-only, Windows or general graphic design.
---

# Mac design

Make a Mac app look and behave like Apple built it. Use the system parts first, arrange them well, and add custom design only where the system has nothing. Every rule lives in [references/rules.md](references/rules.md) with an ID (`WIN-3`), a default severity and the topic file that explains it.

## Pick the mode

| The user wants | Mode |
|---|---|
| A new app, a new screen or feature, "how should this work" | **Design**, then Build |
| Code for a surface (window, toolbar, menu, Settings, status item, panel, flow) | **Build** |
| A critique, an audit, "what's wrong", "make it more native" on existing code or screenshots | **Review** |

When unsure, ask one question. A request to change existing UI is Build, preceded by a short Review of that surface.

## First step in every mode: the deployment target

Find the oldest macOS the app supports before you suggest any API.

```bash
rg -o --no-filename 'MACOSX_DEPLOYMENT_TARGET = [0-9.]+' -g '*.pbxproj' -g '*.xcconfig' . | sort -u | head -5
rg -n -m 3 'platforms:|\.macOS\(' -g 'Package.swift' . | head -5
rg -n -m 3 'deploymentTarget|macOS:' -g 'project.yml' . | head -5
```

Version policy:

- Most apps deploy back to macOS 14 or 15. Liquid Glass APIs are macOS 26+. Gate each one with `if #available(macOS 26, *)` and give a material fallback (`.regularMaterial`), through one helper, not scattered checks (IMP-1, IMP-2).
- macOS 15 window APIs (`windowLevel`, `WindowDragGesture`, window behavior modifiers) need a gate on a 14 target. `@SceneBuilder` has no `else`, so wrap a 15-only scene modifier in a plain function returning `some Scene` with one `return` per `#available` branch ([swiftui-appkit.md](references/swiftui-appkit.md), IMP-3).
- An app built with Xcode 27 always gets the new design. There is no Liquid Glass opt-out to plan for (GLS-7).
- No target found: ask. If the user does not know, assume macOS 14 and say so.

## Design mode

Before any view code, write a short design plan. If the app repo already has a design doc (look for `docs/DESIGN.md`, a design section in `docs/BRIEF.md` or the README), add the plan there. Otherwise show it in chat and get a yes before coding.

The plan, one or two lines each:

1. **Archetype**: pick from the quick pick below.
2. **Information architecture**: sidebar areas (two levels at most) or the single content view.
3. **Entry points**: main window, menu bar, status item, global hotkey, quick panel, drop on the Dock icon, Share, Services, Shortcuts.
4. **Command map**: every action, its menu, its shortcut, and where else it appears (toolbar, context menu).
5. **States**: empty, loading, error, offline and partial for each view; the first action in each empty state.
6. **Permissions plan**: each permission, the feature that triggers it, the narrowest API, and the Settings row.
7. **Deployment floor**: the target from the first step and the 26+/27+ features that need a fallback.
8. **The one feeling**: calm, quick or confident. Words, motion and color all serve it.

Then check the plan against PRN, STR and MOD-1 in rules.md.

## Build mode

1. Load the topic file for the surface you are about to write (reference map below). Read its rules before you write the view.
2. Use the standard structure (STR-2) and change only what the plan needs.
3. Gate every API newer than the deployment target (IMP-1). Check the exact availability when unsure ("Verify" below).
4. After each surface, run the matching rule IDs as a checklist against the code. Fix what fails before moving on.
5. Name the house helpers you use (`glassSurface(in:)`, `WindowAccessor`, `noInitialFocus()`); [swiftui-appkit.md](references/swiftui-appkit.md) defines them. They are not SDK APIs.

## Review mode

Follow [references/review.md](references/review.md): detect stack, target and archetype; run the bounded code sweep; review screenshots in light and dark; walk the rules for the archetype; output one ranked fix list (P1 first, cheapest fix first) and offer to apply fixes. Do not edit code during the review.

## Verify APIs and HIG text

- **Context7 first** when its query tools are available (`resolve-library-id`, then `query-docs` with the full question and the version).
- **Apple docs JSON** otherwise. This prints a symbol's macOS availability (jq ships with macOS 15+). The path is the lowercase docs path after `/documentation/`:

  ```bash
  avail() { curl -fsS "https://developer.apple.com/tutorials/data/documentation/$1.json" | jq -r '.metadata.title + ": " + ([.metadata.platforms[]? | select(.name=="macOS") | "macOS \(.introducedAt)" + (if .deprecatedAt then ", deprecated \(.deprecatedAt)" else "" end)] | join("; "))' | head -3; }
  avail 'swiftui/view/glasseffect(_:in:)'                    # glassEffect(_:in:): macOS 26.0
  avail 'appkit/nsapplication/activate(ignoringotherapps:)'  # activate(ignoringOtherApps:): macOS 10.0, deprecated 27.0
  ```

  An empty result after the colon means the symbol has no macOS availability: do not use it in a Mac target.
- **HIG text**: `"${CLAUDE_PLUGIN_ROOT}/skills/mac-design/scripts/hig.sh" <topic> --mac` prints Apple's current page without other platforms (outside a plugin install: `scripts/hig.sh` next to this file; `hig.sh --list` for topic names, for example `toolbars`, `the-menu-bar`, `sheets`, `privacy`). Use it when a rule is not enough or seems out of date.
- Claims marked `(27, verify)` in the topic files are beta-era. Check them on a shipping macOS 27 build before you rely on them.

## The rules that matter most

The full list is in [rules.md](references/rules.md). These catch most real problems:

**Structure**
- PRN-1: write the design plan first.
- STR-2: standard structures (`NavigationSplitView`, `.toolbar`, `.inspector`, `Settings`, `MenuBarExtra`).
- MNU-2: every command, from any toolbar, context menu or hover, is also in the menu bar.

**Look**
- GLS-1, GLS-2: glass only on the control layer; delete custom backgrounds behind toolbars, sidebars and sheets.
- CLR-1, CLR-5: semantic colors only; text contrast 4.5:1 (3:1 at 18 pt or bold) in light and dark.
- TYP-1: macOS text styles, body 13 pt, nothing under 10 pt, no iOS sizes.
- NAT-4: no iOS idioms (44 pt targets, bottom tab bars, floating + buttons, large titles).

**Windows and chrome**
- WIN-2: never fake the title bar or traffic lights.
- WIN-7, WIN-8: tested minimum size; frames and selection restored on relaunch.
- TBR-2, TBR-6: toolbar items over the column they act on; no iOS-only toolbar APIs.
- MOD-7, MOD-8: alerts only for critical, actionable problems, with verb buttons and a real title.

**Menus and keys**
- MNU-1, MNU-5: standard menu order; never break the Edit menu.
- KBD-2, KBD-6: never repurpose standard shortcuts; text fields get editing keys first.
- SET-1: Settings from the App menu with Command-Comma, never a toolbar gear.

**Menu-bar apps**
- MBX-1: a click opens a menu unless content truly needs a panel.
- MBX-8, MBX-12: another way in besides the icon; Settings and Quit always reachable.
- MBX-16: open Settings through your own window in a menu-bar-only app.

**Flows and access**
- FLW-5, FLW-9: ask for permissions at first use; Settings-only grants get a reason, a state and one deep link.
- FLW-14: every view has empty, loading, error and offline states.
- UND-1: Undo instead of confirmation for common actions.
- A11Y-1, A11Y-8: every icon-only control labeled; every control reachable by keyboard.
- IMP-1: nothing newer than the deployment target without `#available`.

## Reference map

| File | Load when |
|---|---|
| [rules.md](references/rules.md) | Always for Review; for Build, the areas of the surface you write |
| [native-feel.md](references/native-feel.md) | Choosing the archetype and entry points; the design plan; checking for web, Electron or iOS feel; deciding whether custom chrome is justified |
| [design-language.md](references/design-language.md) | Liquid Glass, materials, color, dark mode, contrast, typography, spacing, corner shapes, SF Symbols |
| [windows-and-chrome.md](references/windows-and-chrome.md) | Window scenes and sizing, toolbars, sidebars, split views, inspectors, search placement, sheets, alerts, popovers, panels |
| [menus-and-commands.md](references/menus-and-commands.md) | Menu bar, `Commands`, context menus, Dock menu, shortcuts, focus, global hotkeys |
| [settings.md](references/settings.md) | The Settings window: tabs, rows, controls, sizing |
| [menu-bar-apps.md](references/menu-bar-apps.md) | Status items, `MenuBarExtra`, popovers and panels from the menu bar, activation policy, launch at login |
| [ux-flows.md](references/ux-flows.md) | Onboarding, permissions and privacy, empty/loading/error states, progress, notifications, undo, drag and drop, writing |
| [accessibility.md](references/accessibility.md) | VoiceOver, keyboard access, Reduce Motion and Transparency, contrast settings, custom controls, testing |
| [icons.md](references/icons.md) | App icon with Icon Composer, document icons, menu-bar images, custom symbols |
| [swiftui-appkit.md](references/swiftui-appkit.md) | Version gates, house helpers, AppKit interop, panels, window access, tables, text, previews and captures |
| [review.md](references/review.md) | Review mode |

## Archetype quick pick

| Archetype | Use when | Key reference |
|---|---|---|
| Sidebar window | People browse collections and edit items (mail, notes, library) | windows-and-chrome.md |
| Single-window or document app | One canvas or one document per window (editor, viewer, utility) | windows-and-chrome.md, menus-and-commands.md |
| Menu bar extra, menu style | A few toggles, a status readout and some actions (a VPN toggle) | menu-bar-apps.md |
| Menu bar extra, panel style | The content needs a list, search, a field or a chart (a clipboard manager) | menu-bar-apps.md, swiftui-appkit.md |
| Quick-capture panel | One frequent input from anywhere via a global hotkey | native-feel.md, swiftui-appkit.md |
| Utility or HUD panel | Floating controls for the active window or media | windows-and-chrome.md |

Most apps are one main archetype plus one small entry point (a sidebar window plus a quick-capture panel). A menu-bar-only app is "status item + panel or menu + Settings window": the toolbar and sidebar rules then apply only to its Settings window.

## Safety

- Ask before you launch, click through or drive the user's app or desktop. Prefer Xcode previews, snapshot tests, or screenshots the user provides.
- Capturing windows (`screencapture`) needs the user's OK for that run and Screen Recording permission for the terminal.
- Never change system settings, privacy grants or login items on the user's Mac. Show the steps instead.
- Keep shell output bounded (`head`, `rg -m`).
