# Design language: glass, color, type, layout, symbols

How a Mac app should look in 2026 (macOS 26 Tahoe, macOS 27). This file explains the rules GLS, CLR, TYP, LAY and SYM in [rules.md](rules.md).

**When to read this:** before you style a view, pick a color or font, add a symbol, or touch a corner radius. Skip it for behavior questions (windows, menus, flows).

Contents: Liquid Glass · Materials · Scroll edge effects · Color · Dark mode and contrast · Typography · Layout · Shape · SF Symbols · Sources.

`(macOS 26)` = API starts there. `(27, verify)` = beta-era claim: test on a shipping macOS 27. Check APIs with the docs-JSON one-liner in [SKILL.md](../SKILL.md).

## Liquid Glass

**GLS-1** Glass lives on the navigation and control layer: toolbars, sidebars, floating controls, sheets, popovers. Rows, cards and document content use a plain surface or a material. Exception: transient glass on a slider or toggle while active.

Standard components get glass from the new SDK with no code. Do not rebuild them.

**GLS-2** Delete custom backgrounds, scrims, borders and `NSVisualEffectView` behind toolbars, split-view sidebars, inspectors, sheets and popovers. The system draws them; a custom one blocks the glass and the scroll edge effect. Draw no toolbar background or divider of your own (27, verify: toolbars get more uniform).

**GLS-7** Plan no opt-out. Xcode 27 builds always get the new design. Apps built with Xcode 26 get the macOS 27 refinements without a rebuild, so a custom sidebar or fixed-radius window chrome will look wrong on 27.

### Custom glass APIs

All macOS 26: `glassEffect(_:in:)`; `Glass` (`.regular`, `.clear`, `.identity`, `.tint(_:)`, `.interactive(_:)`); `GlassEffectContainer(spacing:)`; `glassEffectID(_:in:)` and `glassEffectUnion(id:namespace:)` for morphing; `.buttonStyle(.glass)` and `.glassProminent`. AppKit: `NSGlassEffectView` (`contentView`, `cornerRadius`, `tintColor`), `NSGlassEffectContainerView`, `NSButton.BezelStyle.glass`.

Route custom glass through one helper with a material fallback below 26: see `glassSurface(in:)` in [swiftui-appkit.md](swiftui-appkit.md) (IMP-2). The gate itself is `if #available(macOS 26, *)` with `.background(.regularMaterial, in: .capsule)` as the fallback.

**GLS-3** Never put glass on glass. Apply `glassEffect` to the control, never to views inside it. Put neighbors in one `GlassEffectContainer`, so they sample the same background and morph together.

```swift
@available(macOS 26, *)
struct FloatingBar: View {
    var body: some View {
        GlassEffectContainer(spacing: 12) {
            HStack(spacing: 12) {
                Button("Filter", systemImage: "line.3.horizontal.decrease") {}
                    .buttonStyle(.glass)
                Button("Send") {}
                    .buttonStyle(.glassProminent)
                    .tint(.blue)
            }
        }
    }
}
```

**GLS-4** Use regular glass. Use clear glass only over rich media (photo, video, map), with a dark dim of about 35% when the media is bright. Never mix the two in one group. Text-heavy surfaces are always regular.

**GLS-5** Tint glass only on the one primary action, and only to carry meaning. A default button (Return) gets primary prominence on its own. Tint the glass, not the glyph.

**GLS-6** Interactive glass (`.interactive()`, `NSGlassEffectView.effectIsInteractive`) is for a few custom controls only. Standard controls already have it; on macOS 27 its bounce is tuned for the mouse.

**GLS-8** At rest (first launch, top of a scroll view) keep text and controls out from under glass. Extend rich art under a floating sidebar or inspector with `backgroundExtensionEffect()` or `NSBackgroundExtensionView` (both macOS 26); keep text and controls above it. On macOS 27 the system sidebar reaches the window edge (27, verify). Never add margins or backgrounds to imitate either look.

### The transparency setting

**GLS-11** Do not assume what glass looks like. macOS 26.1 added a Clear/Tinted choice. macOS 27 replaces it with a slider from clear to fully tinted. Standard components follow it. Custom glass must stay legible at both ends. Also test Reduce Transparency and Increase Contrast, alone and together. Do not rely on the toggles to fix your own contrast: the default must read well.

Give custom surfaces an opaque fallback (A11Y-11): read `@Environment(\.accessibilityReduceTransparency)` and `\.colorSchemeContrast`. When one is on, fill with `Color(nsColor: .windowBackgroundColor)` instead of `.regularMaterial`.

Misuse symptoms: text illegible under scrolling content, a selected row that overpowers the traffic lights, a strip of window background beside a custom sidebar.

## Materials

**GLS-10** Below glass, and for content-layer backgrounds, use materials by purpose, not by apparent color.

- SwiftUI (macOS 12): `.ultraThinMaterial` through `.ultraThickMaterial`, `.bar`. Default to `.regularMaterial`.
- AppKit semantic `NSVisualEffectView.Material` (macOS 10.14+): `titlebar`, `menu`, `popover`, `sidebar`, `headerView`, `sheet`, `windowBackground`, `hudWindow`, `fullScreenUI`, `toolTip`, `contentBackground`, `underWindowBackground`, `underPageBackground`.
- Never use the deprecated `.light`, `.dark`, `.mediumLight`, `.ultraDark`, `.appearanceBased`.
- Blending: `.behindWindow` blends with the desktop, `.withinWindow` with window content. State: `.followsWindowActiveState`, so the material dims when the window is inactive.
- Put vibrant system colors (labels, fills, separators) on materials. A fixed gray fails contrast. Avoid the quaternary label color on thin materials.
- Do not use `NSVisualEffectView` for a split-view sidebar or inspector on macOS 26+. `NSSplitViewController` makes the glass.

With `NSGlassEffectView`, set `contentView`; never add the content as a sibling.

## Scroll edge effects

**GLS-9** Floating bars need separation from content. Use the scroll edge effect, never a solid band.

- Standard toolbars get it automatically.
- One effect per pane. Panes side by side get effects of the same height.
- Keep `.automatic`. It resolves to hard where needed on macOS, for example with many toolbar controls, pinned table headers, or free-floating title text (27, verify).
- Set a style only for a custom floating bar, after a legibility test: `scrollEdgeEffectStyle(_:for:)` (macOS 26), `scrollEdgeEffectHidden(_:for:)` (macOS 26), `safeAreaBar(edge:alignment:spacing:content:)` (macOS 26).
- It is not decoration: add it only where floating UI overlaps scrolling content.

## Color

**CLR-1** Use semantic colors. Never hard-code white, black, gray or hex in chrome or text, and never copy a system color's value: it changes per release. Never repurpose one (no `separator` as text, no label color as a fill).

| Need | SwiftUI | AppKit |
|---|---|---|
| Text levels | `.primary`, `.secondary`, `.tertiary`, `.quaternary` | `labelColor`, `secondaryLabelColor`, `tertiaryLabelColor`, `quaternaryLabelColor` |
| Dividers | `.separator` (macOS 10.15) | `separatorColor` |
| Selection | `.selection` (macOS 12) | `selectedContentBackgroundColor`; non-key window: `unemphasizedSelectedContentBackgroundColor` |
| Accent | `.tint` (macOS 12), `Color.accentColor` | `controlAccentColor` |
| Surfaces | `.background`, `.fill` styles | `windowBackgroundColor`, `controlBackgroundColor`, `textBackgroundColor`, `alternatingContentBackgroundColors` |

**CLR-2** Define each custom color as an asset-catalog Color Set with Any, Dark and High Contrast appearances, so Increase Contrast works. Define light and dark even for an app with one look, so glass adapts. In code, use `NSColor(name:dynamicProvider:)` (macOS 10.15) and match the high-contrast appearance names (macOS 10.14). `Color(light:dark:…)` is not an Apple API; if you write one, wrap these.

```swift
extension NSColor {
    static let mutedAccent = NSColor(name: nil) { appearance in
        switch appearance.bestMatch(from: [.aqua, .darkAqua, .accessibilityHighContrastAqua,
                                           .accessibilityHighContrastDarkAqua]) {
        case .darkAqua: NSColor(srgbRed: 0.55, green: 0.70, blue: 1.00, alpha: 1)
        case .accessibilityHighContrastDarkAqua: NSColor(srgbRed: 0.70, green: 0.82, blue: 1.00, alpha: 1)
        case .accessibilityHighContrastAqua: NSColor(srgbRed: 0.00, green: 0.25, blue: 0.70, alpha: 1)
        default: NSColor(srgbRed: 0.05, green: 0.30, blue: 0.80, alpha: 1)
        }
    }
}
```

**CLR-3** Set one accent in the asset catalog (`AccentColor`). The system applies it only when the user's accent is Multicolor; any other accent replaces yours, including sidebar icons. Use a fixed icon color only with meaning (a yellow VIP star).

**CLR-4** Never show state by color alone. Add a shape or a word (a checkmark, "Offline"). Honor `accessibilityDifferentiateWithoutColor` (macOS 10.15) in custom views.

**CLR-8** (house convention) Accent-colored text uses a deep shade in light mode and a light shade in dark mode, from one named color. Text and symbols on an accent fill use an on-accent color, not fixed white: white fails on light accents and on Tinted glass. Check 4.5:1 in both modes.

**CLR-9** (house convention) Never lower contrast on hover or press. Text over user content (photos, video, screenshots) sits on a dark scrim or capsule.

Use `ColorPicker` (macOS 11) when people pick colors, and Display P3 for wide-gamut assets.

## Dark mode and contrast

**CLR-6** Follow the system appearance. No Light/Dark picker by default, and no `.preferredColorScheme` outside previews. Auto mode can change while the app runs.

**CLR-7** Dark mode is its own palette (dimmer backgrounds, brighter foregrounds), not an inversion: use Color Sets. Dark-only is fine for immersive media apps.

**CLR-5** Contrast floor, in light, dark and Increase Contrast:

- Text up to 17 pt, all weights: 4.5:1.
- Text at 18 pt, all weights: 3:1. Bold text at any size: 3:1.
- Small custom text: aim for 7:1 (a target, not the floor).

If default colors miss the floor, show a higher-contrast scheme under Increase Contrast. System colors already do.

Test matrix, per surface: Light, Dark, each with Increase Contrast, Reduce Transparency, the glass slider at both ends (27), an inactive window.

Dim custom chrome in inactive windows with `@Environment(\.appearsActive)` (macOS 10.15), never on HUDs or non-activating panels (WIN-10).

Custom controls draw a border when `accessibilityShowBorders` is on (compiles from macOS 11; honored on macOS 27). See [accessibility.md](accessibility.md).

## Typography

The system font is SF Pro; code uses SF Mono. macOS has no Dynamic Type.

**TYP-1** Use macOS text styles. Body is 13 pt, nothing goes below 10 pt, and iOS sizes (17 pt body) are wrong. Sizes confirmed with `NSFont.preferredFont(forTextStyle:)` on macOS 27.

| Style | SwiftUI | Size / leading | Weight | Emphasized |
|---|---|---|---|---|
| Large Title | `.largeTitle` | 26 / 32 | Regular | Bold |
| Title 1 | `.title` | 22 / 26 | Regular | Bold |
| Title 2 | `.title2` | 17 / 22 | Regular | Bold |
| Title 3 | `.title3` | 15 / 20 | Regular | Semibold |
| Headline | `.headline` | 13 / 16 | Bold | Heavy |
| Body | `.body` | 13 / 16 | Regular | Semibold |
| Callout | `.callout` | 12 / 15 | Regular | Semibold |
| Subheadline | `.subheadline` | 11 / 14 | Regular | Semibold |
| Footnote | `.footnote` | 10 / 13 | Regular | Semibold |
| Caption 1 | `.caption` | 10 / 13 | Regular | Medium |
| Caption 2 | `.caption2` | 10 / 13 | Medium | Semibold |

Match standard control text in AppKit with `NSFont.preferredFont(forTextStyle:)`, `controlContentFont(ofSize:)`, `menuFont(ofSize:)`, `menuBarFont(ofSize:)`, `messageFont(ofSize:)`, `titleBarFont(ofSize:)`, `toolTipsFont(ofSize:)`, `userFixedPitchFont(ofSize:)`. Custom fonts: headings and brand only, and they must honor Bold Text (`legibilityWeight`).

**TYP-2** Use Regular, Medium, Semibold or Bold. No Ultralight, Thin or Light in interface text. A `.fontWeight(.light)` at 11 pt is illegible.

**TYP-3** Never use `dynamicTypeSize` on macOS: users cannot change it and it does not affect text size. Offer text size only in reading apps, as View > Bigger, Smaller and Actual Size.

**TYP-4** Never hand-set `tracking` or `kerning` on system text. SF is a variable font; the system tunes spacing per size.

**TYP-5** Changing numbers use `.monospacedDigit()` (macOS 12) so they do not jitter. Code uses `.monospaced()` (macOS 13) or `NSFont.monospacedSystemFont(ofSize:weight:)` (macOS 10.15).

Build hierarchy from `.secondary` and `.tertiary`, not `.opacity(0.6)`.

**TYP-6** (macOS 26) Left-align alert and onboarding body text.

**TYP-7** (macOS 26) Write section headers in title case ("Recent Files"), never typed in all caps. Lists, tables and forms no longer force capitals.

## Layout and spacing

**LAY-1** Size controls with `.controlSize(_:)` (macOS 10.15), never fixed heights. Sizes: mini, small, regular (HIG: medium), large, extra large (`.extraLarge`: case since 14, renders from 26). Standard controls are about 22 to 28 pt tall. For dense inspectors and popovers, `NSView.prefersCompactControlSizeMetrics = true` (macOS 26) restores the pre-Tahoe metrics.

```swift
@MainActor @available(macOS 26, *)
func compact(_ v: NSView) { v.prefersCompactControlSizeMetrics = true }
```

**LAY-2** Click targets are at least 20 x 20 pt, and 28 x 28 pt by default. Leave about 12 pt around bezeled controls and about 24 pt around borderless ones. 44 pt targets are an iOS idiom (NAT-4).

**LAY-6** Put key content top-leading. Put no controls or critical info on a window's or sidebar's bottom edge. A bottom status bar may show small facts (a count, free space). The rule targets bottom toolbars and status bars, not the button row of a dialog, alert or panel.

**LAY-7** (house convention) Take spacing from system containers: `Form`, `LabeledContent`, `Grid`, default stack spacing, `.scenePadding()`. Apple publishes no margin numbers for macOS beyond control and hit-target sizes. A project grid is a convention, for example 20 pt window margins, 8 pt between related controls, 20 pt between groups. Never lint system metrics against it: system type sizes are not on a 4 pt grid.

**LAY-8** (house convention) Line up trailing values (`.monospacedDigit()`). Use one date format per view. Show each status once per row: a dot and the word "Failed" say it twice.

## Shape

Apple's model has three shapes: fixed, capsule and concentric. It publishes no radius scale. A token set such as 6/8/10/12/18/26 is a house choice: fine for small standalone chips, wrong for shapes inside a window, sheet or glass container.

**LAY-3** Nested corners are concentric: inner radius = outer radius minus the padding between them. Use `ConcentricRectangle` (macOS 26) and `containerShape(_:)` (macOS 26). Give a part that appears both nested and alone a minimum radius so it never goes square. In AppKit, override `NSView.cornerConfiguration` (macOS 27) and return `.corners(radius: .containerConcentric(8))`; the argument is the minimum radius. Fixed radii only on small standalone parts.

```swift
@available(macOS 26, *)
struct Tile: View {
    var body: some View {
        Text("Tile")
            .padding(10)
            .background(.quaternary, in: .rect(corners: .concentric(minimum: 8), isUniform: true))
            .padding(8)
            .containerShape(.rect(cornerRadius: 22))
    }
}
```

**LAY-4** (macOS 26) Mini, small and regular controls are rounded rectangles. Large and extra large controls are capsules. In dense layouts keep capsules for the one standout action. `buttonBorderShape(_:)` (macOS 12) sets the shape.

**LAY-5** Never mask window corners or hard-code a window radius. The radius changed on macOS 26 (windows with a toolbar are rounder than title-bar-only windows) and again on macOS 27 (all windows share one tighter radius). Keep content out of corners with the safe area; in AppKit use `NSView.LayoutRegion.safeArea(cornerAdaptation:)` (macOS 26). Do not run square content (images, video) into a window corner. Add no clipping to sheets or popovers.

## SF Symbols

**SYM-1** Use SF Symbols or custom symbols for toolbar, sidebar and menu icons, never bitmaps (no weight match, no tint). Give every icon-only control an accessibility label (A11Y-1).

**SYM-2** Use the standard symbol for each standard action. All names below exist on macOS 27 (checked with `NSImage(systemSymbolName:)`).

Copy `document.on.document`, Paste `document.on.clipboard`, Cut `scissors`, Duplicate `plus.square.on.square`, Rename `pencil`, Move `folder`, Delete `trash`, Share `square.and.arrow.up`, Undo `arrow.uturn.backward`, Redo `arrow.uturn.forward`, Filter `line.3.horizontal.decrease`, More `ellipsis`, Compose `square.and.pencil`, Archive `archivebox`.

`trash` means delete and nothing else. Where no symbol is unambiguous, use a text label. In menus on macOS 27, use standard selectors (`copy:`, `paste:`): the system picks their icon.

**SYM-3** Match symbol weight to the adjacent text (nine weights map to the font weights). Change emphasis with `imageScale(_:)` (macOS 11: small, medium, large), not by changing weight.

**SYM-4** Variants: outline in toolbars, lists and menus; fill for selection or emphasis; slash for unavailable; enclosed for small-size legibility. Let the container choose (`symbolVariant(_:)`, macOS 12). Never ship your own selected image: the system handles it.

**SYM-5** A symbol newer than your deployment target is missing at runtime. Check each symbol's release in the SF Symbols app, gate it with `#available`, and fall back to an older symbol. Symbols added in 2026 need macOS 27.

**SYM-6** (macOS 14+) Animate a symbol only to say something: an action happened (bounce), work is ongoing (pulse, breathe, rotate), a state changed (replace). One animated symbol per region. No loops in lists. None under Reduce Motion.

| Effect | Min macOS |
|---|---|
| appear, disappear, bounce, pulse, scale, variableColor, replace (Magic Replace between related symbols) | 14 |
| wiggle, breathe, rotate | 15 |
| drawOn, drawOff | 26 |

**SYM-7** Rendering modes: monochrome, hierarchical (depth: one color at several opacities), palette (two or more colors), multicolor. `automatic` is a start: check each symbol in context (`symbolRenderingMode(_:)`, macOS 12).

- Variable color shows a level (volume, signal), not depth: `Image(systemName:variableValue:)` (macOS 13). Variable draw shows progress: `symbolVariableValueMode(_:)` (macOS 26). One symbol uses color or draw, not both.
- Gradient rendering, `symbolColorRenderingMode(.gradient)` (macOS 26), suits large symbols; at 11 to 13 pt use flat.
- Custom symbols start from a template exported in the SF Symbols app. Annotate layers so all modes work, draw whole shapes (no cutouts), keep Regular as the master weight, and test every animation preset. Apple-product symbols cannot be customized or used in an icon or logo.
- **SYM-8** Symbols that depict Apple products (`iphone`, `macbook`, `applewatch`…) refer to that product only. Never use them as a generic "phone" or "computer" icon: pick `phone`, `desktopcomputer` or `laptopcomputer`. The HIG calls them copyrighted and not customizable; the SF Symbols app shows each one's usage restrictions in its inspector. Source: https://developer.apple.com/design/human-interface-guidelines/sf-symbols

```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion
// ...
Image(systemName: "checkmark.circle")
    .symbolEffect(.bounce, options: .nonRepeating, value: reduceMotion ? 0 : saves)
```

Menu-item icons: all items in a group get one, or none do. On macOS 27 menu images are hidden by default; see MNU-10 in [menus-and-commands.md](menus-and-commands.md). Menu-bar and app icons: [icons.md](icons.md).

## Sources

- HIG Materials, Color, Dark Mode, Typography, SF Symbols, Icons, Layout, Scroll views, Sidebars, Menus, Accessibility: `https://developer.apple.com/design/human-interface-guidelines/<page>` (print with `hig.sh <topic> --mac`)
- Adopting Liquid Glass: https://developer.apple.com/documentation/TechnologyOverviews/adopting-liquid-glass
- Availability: Apple docs JSON, `https://developer.apple.com/tutorials/data/documentation/<path>.json`
- WWDC25-356 Get to know the new design system: https://developer.apple.com/videos/play/wwdc2025/356/
- WWDC25-310 Build an AppKit app with the new design: https://developer.apple.com/videos/play/wwdc2025/310/
- WWDC25-337 What's new in SF Symbols 7: https://developer.apple.com/videos/play/wwdc2025/337/
- WWDC26-102 Platforms State of the Union: https://developer.apple.com/videos/play/wwdc2026/102/
- WWDC26-269 What's new in SwiftUI: https://developer.apple.com/videos/play/wwdc2026/269/
- WWDC26-289 Modernize your AppKit app: https://developer.apple.com/videos/play/wwdc2026/289/
- Field reports (secondary): https://mjtsai.com/blog/2025/12/29/liquid-glass-disbelief

Parts adapted from BAMA by Dave Ebbelaar (MIT); see THIRD_PARTY_NOTICES.md.
