# Review mode: audit a Mac app

Audit an existing macOS app against [rules.md](rules.md) and return one ranked fix list. The review reads code and screenshots. It changes nothing until the user picks fixes.

## Inputs

- **Code:** the app's repository path. Read-only during the audit.
- **Screenshots:** images the user gives, or captures you make with the user's OK (step 3).
- **Running app:** never launch, click through or drive the user's app or desktop without an explicit OK for that run. Prefer Xcode previews, snapshot tests, or screenshots the user provides.
- **Scope:** the whole app by default. When the user names a surface ("the Settings window", "the status menu"), audit only that surface and the rules for it.

With code only, the screenshot rules stay unchecked. With screenshots only, the code rules stay unchecked. Say which in the output.

## Step 1: Detect stack, deployment target, archetype

Run from the repo root. Keep every command bounded.

```bash
# Deployment target (Xcode project, xcconfig, XcodeGen, SwiftPM)
rg -o --no-filename 'MACOSX_DEPLOYMENT_TARGET = [0-9.]+' -g '*.pbxproj' -g '*.xcconfig' . | sort -u | head -5
rg -n -m 3 'deploymentTarget|macOS:' -g 'project.yml' . | head -5
rg -n -m 3 'platforms:|\.macOS\(' -g 'Package.swift' . | head -5

# Stack: SwiftUI, AppKit or mixed (file counts)
rg -l 'import SwiftUI' -g '*.swift' . | wc -l
rg -l 'import AppKit|import Cocoa' -g '*.swift' . | wc -l

# Archetype signals
rg -l -m 1 'MenuBarExtra|NSStatusItem' -g '*.swift' . | head -3
rg -n -m 1 'LSUIElement' -g '*.plist' -g 'project.yml' -g '*.pbxproj' . | head -3
rg -l -m 1 'NavigationSplitView|NSSplitViewController' -g '*.swift' . | head -3
rg -l -m 1 'DocumentGroup|NSDocument\b' -g '*.swift' . | head -3
rg -l -m 1 'NSPanel|nonactivatingPanel|UtilityWindow' -g '*.swift' . | head -3
```

Several targets (app, tests, extensions): use the app target's value; if unclear, the lowest one that ships. None found: ask; if the user does not know, assume macOS 14 and say so.

Record three facts at the top of the report: archetype, deployment target, stack. The deployment target decides which version gates count (IMP-1): an API newer than the target with no `#available` is `P1`. A gate that can never fail (target already 26+) is dead code, not a finding.

Pick the archetype from the signals. A menu-bar-only app has `LSUIElement` and a status item. A sidebar app has `NavigationSplitView` or `NSSplitViewController`. A document app has `DocumentGroup` or `NSDocument`. A quick-capture or HUD app has a non-activating `NSPanel`. Mixed signals mean a hybrid: audit each part with its own areas.

## Step 2: Code smell sweep

Use one helper so every search stays bounded. Each hit is a lead, not a finding: open the file and confirm before you list it. Hits are capped per file and in total, so a full output may hide more.

```bash
S() { rg -n -m 6 -g '*.swift' -g '!**/*Tests*/**' -e "$1" . | head -n 20; }
```

Each line: pattern to pass to `S` (plus what to confirm by hand) → rule IDs. Pass every pattern in single quotes, so `"` and `$` stay literal: `S '\.alert\("(Error|Warning)"'`.

- `\.glassEffect\(` in a file with `ForEach` or `List` rows → GLS-1
- `\.glassEffect\(` with no `#available\(macOS 26` nearby, target < 26 → IMP-1, IMP-2
- `NSVisualEffectView` in sidebar, inspector, sheet or popover code → GLS-2
- `\.background\(.*(Material|Color)` on a sidebar or toolbar container → GLS-2
- `Color\.(white|black|gray)|Color\(red:|Color\(hex|#[0-9A-Fa-f]{6}` (a `Color(red:`/`NSColor(red:` inside an `NSColor(name:dynamicProvider:)` helper is CLR-2-compliant: check that it flips in dark) → CLR-1
- `\.foregroundColor\(\.gray\)|\.opacity\(0\.[1-6]\)` on text → CLR-1
- `preferredColorScheme` outside `#Preview` → CLR-6
- `Circle\(\)\.fill\(|\.foregroundStyle\(\.(red|green)\)` as status with no word or symbol → CLR-4
- `(\.font\(|Font)\.system\(size: *[0-9](\.[0-9]+)?\b` (sizes below 10, also `Font.system(size:)` constants) → TYP-1
- `\.(ultraLight|thin|light)\b` in a font weight → TYP-2
- `dynamicTypeSize` → TYP-3
- `\.tracking\(|\.kerning\(` on system text → TYP-4
- `height: *44\b|minHeight: *44\b` → NAT-4, LAY-1
- `\.frame\(width: *1[0-9], *height: *1[0-9]\)` on a button → LAY-2
- `RoundedRectangle\(cornerRadius:|\.cornerRadius\(` on a nested container → LAY-3
- `Image\("` in `.toolbar`, sidebar rows or menus → SYM-1
- `\.repeatForever|\.repeat\(\.continuous\)` on a symbol effect → SYM-6
- `standardWindowButton|NSWindow\.StyleMask\.borderless` on a main window → WIN-2
- `\.padding\(\.top, *[0-9]+\)` at a window root → WIN-3
- `level = \.floating|\.windowLevel\(\.floating\)` on a main window → WIN-15
- `ToolbarOverflowMenu|topBarLeading|topBarTrailing|topBarPinnedTrailing|\.bottomBar|navigationBarTitleDisplayMode` → TBR-6
- `gearshape` inside a `.toolbar` → TBR-9, SET-1
- `\.alert\("(Error|Warning)"` → MOD-8
- `Button\("(OK|Yes|No)"` on a choice → MOD-8
- `role: \.destructive` (check what the person chose) → MOD-9
- `runModal\(\)` → MOD-11
- `"[^"]*\.\.\."` in a menu or button title → MNU-7
- `CommandGroup\(replacing: *\.(pasteboard|undoRedo|textEditing)` → MNU-5
- `\.focusedValue\(` feeding `Commands` → MNU-9
- `keyboardShortcut` inside a `.contextMenu` block → MNU-12
- `keyboardShortcut\(\.(delete|return|upArrow|downArrow)` on a menu `Button` → KBD-6
- `addLocalMonitorForEvents` → KBD-6, IMP-10, MBX-14
- `addGlobalMonitorForEvents` used as a hotkey → KBD-8, FLW-6
- `RegisterEventHotKey|KeyboardShortcuts\.Name` (read the default modifiers) → KBD-7
- `kVK_` used to match shortcuts → KBD-4
- `activate\(ignoringOtherApps` → IMP-6
- `NSApp\.activate\(\)` inside `applicationDidFinishLaunching` → IMP-6
- `NSApp\.windows\.(first|\[0\])|NSApplication\.shared\.windows\.first` → IMP-4
- `window\.delegate *=` in a SwiftUI app → IMP-5
- `styleMask\.(insert|formUnion)\(.*nonactivatingPanel` → IMP-7
- `\.borderless` panel with no `canBecomeKey` override → IMP-7
- `NSHostingView\(rootView:` with no `sizingOptions` line → IMP-8
- `\.layoutManager\b` on an `NSTextView` → IMP-11
- `CGWindowListCreateImage|ImageRenderer\(` used for window captures → IMP-13
- `@State (private )?var \w+ = [A-Z]\w*\(\)` with init side effects → IMP-14
- `SettingsLink|openSettings|showSettingsWindow|showPreferencesWindow` in a menu-bar-only app → MBX-16
- `setActivationPolicy` (each `.regular` needs a matching `.accessory`) → MBX-15
- `terminationOnRemoval` → MBX-9
- `SMAppService` (needs `.status` read and `.requiresApproval`; no `register()` at launch) → MBX-17
- `Timer\.scheduledTimer` with no `tolerance` → MBX-19
- `requestAuthorization|AXIsProcessTrustedWithOptions|CGRequestScreenCaptureAccess` in launch code → FLW-5, FLW-19
- `x-apple\.systempreferences` with no fallback when `open` returns false → FLW-9
- `NSPasteboard\.general` read on a timer → FLW-12
- `tapCreate` with `\.defaultTap` → FLW-13
- `ProgressView\(\)` with no label and no error branch → FLW-16, FLW-17
- `"(Oops|Error|Are you sure|Please wait|Something went wrong|Click here)` → FLW-23, MOD-8
- `registerUndo` with no `setActionName` nearby → UND-2
- `dropDestination\(for:.*isTargeted|\.onDrop\(of:` on a 26+ target → DND-6
- `\.onTapGesture` on a control → A11Y-2
- `Button\("",` → A11Y-1 (fix: `.accessibilityHidden(true)` on invisible helper buttons)
- `focusEffectDisabled` → A11Y-9
- `accessibilityVoiceOverEnabled|isVoiceOverEnabled` gating a feature → A11Y-16
- `applicationIconImage *=` (assignments only) → ICN-8
- `NSCursor\.pointingHand|pointerStyle\(\.link\)` on buttons or rows → NAT-1
- `scrollIndicators\(\.hidden\)|hasVerticalScroller = false` → NAT-2
- `WKWebView` (then check NAT-8 by hand) → NAT-8

Absence checks (each prints at most 10 files):

```bash
# Animations with no Reduce Motion check (A11Y-10)
comm -23 <(rg -l 'withAnimation|\.transition\(' -g '*.swift' . | sort) <(rg -l 'accessibilityReduceMotion' -g '*.swift' . | sort) | head -10
# Custom translucency with no Reduce Transparency check (A11Y-11): opacity fills on Color, custom NSVisualEffectView, glassEffect. Comment lines skipped. System SwiftUI materials already go opaque under Reduce Transparency.
comm -23 <(rg -l '^[^/]*(Color[^/]*\.opacity\(|NSVisualEffectView|glassEffect)' -g '*.swift' . | sort) <(rg -l 'accessibilityReduceTransparency' -g '*.swift' . | sort) | head -10
# Custom NSViews with no accessibility (A11Y-14)
comm -23 <(rg -l 'class \w+: NSView\b' -g '*.swift' . | sort) <(rg -l 'isAccessibilityElement|accessibilityRole|NSAccessibilityElement' -g '*.swift' . | sort) | head -10
# Hover that shows or reveals controls (A11Y-7; a hover highlight alone is fine): onHover files with no named accessibility action
comm -23 <(rg -l '\.onHover' -g '*.swift' . | sort) <(rg -l 'accessibilityAction' -g '*.swift' . | sort) | head -10
# Status item files with no template image or symbol (MBX-4)
comm -23 <(rg -l 'NSStatusItem|MenuBarExtra' -g '*.swift' . | sort) <(rg -l 'isTemplate|systemSymbolName|systemImage:' -g '*.swift' . | sort) | head -10
# Icon-only buttons to triage by hand (A11Y-1)
rg -n -A2 'Button *\{' -g '*.swift' . | rg 'Image\(systemName' | head -10
rg -U -n 'label: *\{\s*Image\(systemName' -g '*.swift' . | head -10
```

Project checks:

```bash
rg -n -m 3 'UIDesignRequiresCompatibility' -g '*.plist' -g '*.pbxproj' -g '*.swift' . | head -5   # GLS-7
rg -n -m 5 'NS\w+UsageDescription' -g '*.plist' -g 'project.yml' . | head -10   # FLW-7: one per protected API used
find . -maxdepth 6 \( -name '*.icon' -o -name 'AppIcon.appiconset' \) -not -path '*/.build/*' | head -5   # ICN-1, ICN-5
rg -l 'performAccessibilityAudit' -g '*.swift' . | head -3   # A11Y-17 (empty = finding)
```

Commands parity (MNU-2, and MBX-22 for actions on floating windows): button titles that appear in no `Commands` file. For `LSUIElement` apps compare against the `MenuBarExtra` or status-menu file instead (second command). Each is a lead: the menu item may use another title or a `Toggle`, so confirm by hand.

```bash
comm -23 \
  <(rg -o --no-filename 'Button\("[^"]+"' -g '*.swift' . | sort -u) \
  <(rg -l 'CommandGroup|CommandMenu|: Commands' -g '*.swift' . | while IFS= read -r f; do rg -o --no-filename 'Button\("[^"]+"' "$f"; done | sort -u) \
  | head -40
```

```bash
# LSUIElement apps: same check against the status-menu files
comm -23 \
  <(rg -o --no-filename 'Button\("[^"]+"' -g '*.swift' . | sort -u) \
  <(rg -l 'MenuBarExtra|NSStatusItem|NSMenuItem' -g '*.swift' . | while IFS= read -r f; do rg -o --no-filename 'Button\("[^"]+"|NSMenuItem\(title: *"[^"]+"' "$f"; done | sed 's/NSMenuItem(title: *"/Button("/' | sort -u) \
  | head -40
```

## Step 3: Screenshot pass

Get the images in this order of preference:

1. Screenshots the user provides.
2. Xcode `#Preview`s for component states (they show no real window chrome, toolbar glass or menus, so they cannot judge WIN, TBR or GLS).
3. With the user's OK for this run: build, launch, and capture real windows. The terminal needs Screen Recording permission. A capture taken from the terminal shows the app inactive (gray traffic lights, dimmed custom chrome): use it for layout, type and color, not for key-window state.

```bash
# Window IDs of an app by name (no Accessibility permission needed)
swift -e 'import CoreGraphics; let l = CGWindowListCopyWindowInfo(.optionOnScreenOnly, kCGNullWindowID) as? [[String: Any]] ?? []; for w in l where (w[kCGWindowOwnerName as String] as? String) == "MyApp" { print(w[kCGWindowNumber as String] ?? "") }' | head -5
screencapture -x -o -l <window-id> /tmp/review-main-light.png
```

Offscreen renders are a valid no-GUI capture for single views: host the view in an `NSHostingView`, then `cacheDisplay(in:to:)` into an `NSBitmapImageRep`. Limits: no real chrome, glass, menu bar or menus; offscreen windows are never key, so accent fills render gray; Increase Contrast cannot be simulated (`colorSchemeContrast` is read-only, and a high-contrast `NSAppearance` changed nothing).

Never change system settings to capture. Use the appearance the user already has; for the other mode, Increase Contrast or Reduce Transparency, give the user the steps (System Settings > Appearance, System Settings > Accessibility > Display) and ask for screenshots. Key-window shots, menu bar menus, context menus and status menus come from the user (Shift-Command-4, then Space, then click, while the app is frontmost; Shift-Command-5 with a timer for open menus). Without them, list those rules as not checked.

Cover every surface in light and dark mode, as the key window:

- Each main window page, including empty, loading, error and no-results states.
- Each sheet, popover, panel, alert and inspector.
- The menu bar menus (App, File, Edit, View, Window) and one context menu.
- For menu-bar apps: the status icon (light and dark wallpaper, highlighted), its menu or panel, the welcome window.
- Every Settings tab.
- One inactive-window capture, to check that custom chrome dims (WIN-10).
- One capture each with Increase Contrast and with Reduce Transparency, on the busiest surface (CLR-5, A11Y-11).

An inactive capture (gray traffic lights) does not count as the key-window review; say so when it is all you have.

On each image check:

| Look for | Rules |
|---|---|
| Glass only on toolbar, sidebar, floating controls; content on plain or standard material; nothing under glass at rest | GLS-1, GLS-8 |
| Custom band or background behind toolbar or sidebar | GLS-2, GLS-9 |
| Hard-coded colors that break in dark mode; low-contrast secondary text | CLR-1, CLR-5, CLR-7 |
| Status shown by color only | CLR-4, MBX-5 |
| Body text 13 pt, nothing under 10 pt, no thin weights, no all-caps headers | TYP-1, TYP-2, TYP-7 |
| 44 pt controls, pill buttons, bottom tab bar, floating + button, large title | NAT-4, LAY-1 |
| Pinched or flared nested corners; content clipped in window corners | LAY-3, LAY-5 |
| Controls or key facts on the bottom edge | LAY-6 |
| Bitmap or mixed-weight icons; wrong symbol for a standard action | SYM-1, SYM-2, SYM-3 |
| Fake traffic lights; controls under the real ones | WIN-2, WIN-3 |
| Title is the app name or "Untitled"; subtitle on some pages only | WIN-4, WIN-5 |
| More than three toolbar groups; items over the wrong column; two sidebar toggles; tinted items | TBR-1, TBR-2, TBR-4, TBR-7 |
| Gear button in the toolbar; switches or checkboxes in the toolbar | TBR-9 |
| Sidebar hidden by default, deeper than two levels, action rows in it | SBR-1, SBR-2, SBR-5 |
| Two sheets or popovers at once; popover arrow off its source | MOD-2, MOD-12 |
| Alert titled "Error", buttons OK/Yes/No, red button on a chosen action, Cancel as default | MOD-8, MOD-9 |
| Settings: tabs as toolbar icons, title follows the tab, minimize and zoom dimmed, no Save button, no empty band | SET-2, SET-3, SET-4, SET-8 |
| Menu order, "…" vs "...", dimmed items kept, Window and Help present | MNU-1, MNU-7, MNU-8 |
| Context menu with shortcuts or dimmed inapplicable items | MNU-12 |
| Status icon: template, tints in dark and when highlighted, Settings and Quit last in its menu | MBX-4, MBX-11, MBX-12 |
| Blank pane where an empty, error or offline state belongs | FLW-14, FLW-17 |
| Spinner with "Loading…" and no count; error only in a toast | FLW-16, FLW-18 |
| Focus ring or selected text in a window that is not for typing | KBD-9 |
| Arrow-key and Tab focus ring visible on custom controls | A11Y-8, A11Y-9 |
| App icon on a gray plate, not a full squircle, or different elements per appearance | ICN-1, ICN-4, ICN-5 |

## Step 4: Walk the rules for the archetype

Read [rules.md](rules.md) and walk the areas below in order. For each rule decide: finding, verified OK, or not checkable with the inputs. Do not stop at the smell sweep: many rules (MNU-2, PRN-2, MOD-1, FLW-5) need reading the flow, not a pattern.

| Archetype | Areas, most important first |
|---|---|
| Sidebar window | STR, WIN, TBR, SBR, MNU, KBD, GLS, CLR, TYP, LAY, SYM, MOD, LST, FLW, UND, DND, SET, A11Y, ICN, IMP, NAT, PRN |
| Single-window or document | STR, WIN (tabs, restore), MNU (File), KBD, UND, DND, LST, GLS, CLR, TYP, LAY, SYM, MOD, FLW, SET, A11Y, ICN, IMP, NAT, PRN |
| Menu bar extra | MBX, SET, KBD (hotkey), FLW (permissions, onboarding), A11Y, CLR, TYP, SYM, MNU (status menu), IMP (activation, panels), ICN, NAT |
| Quick-capture panel | STR-5, IMP-7, KBD, NAT, MOD, UND, A11Y, GLS, CLR, TYP, PRN |
| Utility or HUD | MOD-13, WIN-10, WIN-15, KBD, A11Y, GLS, CLR, TYP, NAT, PRN |

Hybrids walk the union. Add ICN for every app that ships an icon.

When a rule needs Apple's current text, read the page: `"${CLAUDE_PLUGIN_ROOT}/skills/mac-design/scripts/hig.sh" <topic> --mac`. When a finding depends on an API's availability, check it in Apple's docs JSON before you report it (see SKILL.md, "Verify").

## Step 5: Rank

1. Merge duplicates: one item per root cause, listing every location.
2. Set the severity: start from the rule's default. Raise it when the problem sits on the main flow or blocks a task. Lower it on rare surfaces. Say why when you change it.
3. Order: all `P1`, then `P2`, then `P3`. Within one severity, cheapest fix first: a one-line API or string swap, then a local view change, then a structural change.
4. Every item names a concrete fix: the API, modifier, string or setting, not "improve" or "consider".

## Output format

Use exactly this layout. Locations are `path:line` (repo-relative) or `screenshot-name (region)`.

```markdown
## Mac design review: <App name>

Archetype: <archetype> · Deploys to: macOS <N> · Stack: <SwiftUI | AppKit | mixed> · Inputs: <code, N screenshots>

### Top 10
1. P1 · MBX-16 · Sources/Status/StatusController.swift:88 · `SettingsLink` inside `MenuBarExtra` often fails to open Settings in a menu-bar-only app · Open a `SettingsWindow` (`NSWindow` + `NSHostingController`) after `NSApp.setActivationPolicy(.regular)` and `NSApp.activate()` (14+); return to `.accessory` in `windowWillClose`.
2. P1 · A11Y-1 · Sources/UI/Toolbar.swift:31 · Icon-only "trash" button has no label · `Button("Delete", systemImage: "trash") { … }.labelStyle(.iconOnly)`.
3. …

### By area
#### GLS · Liquid Glass and materials
- P2 · GLS-2 · Sources/UI/Sidebar.swift:12 · `.background(.ultraThinMaterial)` behind the sidebar blocks the system glass · Delete the modifier.

#### MNU · Menu bar and commands
- P3 · MNU-7 · Sources/App/Commands.swift:40, :52 · "Export..." uses three periods · Write "Export…" (U+2026).

### Verified OK
GLS-1, CLR-6, TYP-1, WIN-2, MNU-1, KBD-2 · Not checked: screenshot rules (no captures), MBX-14 (needs a running app).

Apply fixes? I can apply all P1 items, a list of items by number, or one area.
```

Rules for the output:

- Items 11 and later go only under "By area", areas in rules.md order; within an area, severity first, then cheapest fix. Do not repeat the top 10 there.
- One line per item, in the order severity · rule ID · location · problem · fix.
- No praise and no summary paragraph. The verified line lists rule IDs only.
- Never edit code during the review. Apply fixes only after the user picks them, then rebuild and re-check the touched rules.
