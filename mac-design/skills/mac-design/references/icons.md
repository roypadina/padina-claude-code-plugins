# Icons: app, Dock, document, menu-bar and custom symbols

How to make and ship the icons of a Mac app. This file explains the ICN rules in [rules.md](rules.md) and the drawing side of MBX-4 and MBX-5. The rule text for status items stays in [menu-bar-apps.md](menu-bar-apps.md). Toolbar and menu symbols (SYM) are in [design-language.md](design-language.md).

**When to read this:** you make or review an app icon, a Dock tile, a document icon, a status-item image or a custom symbol.

Contents: App icon rules · Icon Composer and the `.icon` file · Workflow · Review renders · Back-deployment · Dock tile · Document icons · Menu-bar images · Custom symbols · Review checklist · Sources.

Tags: `(macOS 26)` = starts there. `(27, verify)` = beta-era claim: check on a shipping macOS 27 and Icon Composer 27. Tools were run on Xcode 27.0.0.

## App icon rules

**ICN-1** The app icon is an Icon Composer `.icon` file (macOS 26). Supply square, unmasked, full-bleed layers on a 1024 x 1024 px canvas. The system adds the rounded mask, highlights, shadow and the Dark, Clear and Tinted looks. Never ship pre-masked layers: they give jagged edges and wrong highlights. Do not draw the rounded square. Use Apple's icon template (Apple Design Resources) for the grid. Do not hand-make 16 to 512 px PNGs for a `.icon` app: the system scales it. Color spaces: sRGB, Gray Gamma 2.2, Display P3.

**ICN-2** One simple idea, few shapes, a plain or gradient background.

- Do: filled, overlapping shapes; depth from layers and opacity; the same core design on every platform.
- Do not: bake in a shadow, gloss, bevel, blur or glow. The system draws shadow and specular highlights.
- Do not: put text (not accessible, not localizable, too small) in the icon. A first-letter mnemonic is the only exception.
- Do not: use photos, app screenshots, copies of UI controls or replicas of Apple hardware.
- Do not: use an SF Symbol or a lookalike. The SF Symbols license forbids it.

**ICN-3** Use at most four groups. Keep edges crisp: no feathering or soft foreground shapes. Avoid thin lines and sharp corners: they vanish at small sizes. The glyph must read at 16 and 32 px. Glass effects react to shape count, size and overlap, so fewer, simpler shapes look better.

**ICN-4** Default, Dark, Clear and Tinted looks keep the same elements and vary only color.

- Dark: the light palette, more subdued. Color backgrounds give the best contrast. Avoid very bright images.
- Clear and Tinted: more muted still. Check legibility in each.
- Mono (clear and tinted): use one grayscale annotation and the full tonal range.
- Do not swap elements per appearance. Use `fill-specializations` and `image-name-specializations` only to fix contrast.

**ICN-5** Ship no flat-only icon. On macOS 26 a flat or non-conforming icon sits on a gray plate and looks smaller than its neighbors. A bigger flat image does not help. Adopt `.icon`. Never keep a second app-icon set with the same name next to it.

## Icon Composer and the `.icon` file

Icon Composer ships with Xcode (Xcode > Open Developer Tool > Icon Composer). A `.icon` is a folder with `icon.json` and an `Assets/` folder of layers. The format is resolution independent.

- Layers: SVG first. Use PNG for mesh gradients and raster art. Import layers opaque and set transparency in Icon Composer. Outline SVG text. PDF layers do not render. Name layers back to front (`1-back.svg`, `2-front.svg`).
- Groups: each group is a depth layer. Top of the list is the front. A group is Individual (effects per layer) or Combined (one object). Group-level controls: Specular, Blur, Refraction, Translucency, Shadow.
- Per-layer glass off: Effects toggle in the inspector. An opaque, full-bleed background layer is fine.
- Background: one brand color with `automatic-gradient` looks right almost always.
- Preview: Mono > Options sets Light/Dark, tinted on or off and tint color. Use a custom background image to judge Clear.
- Platforms: "vary for platform or appearance" keeps one setting per variant. Color varies by appearance, composition varies by platform.

**ICN-6** On macOS 27 the same `.icon` renders with a new look. Rules:

- Refraction only shows on macOS 27. Earlier releases show Specular but no refraction. Never rely on refraction for legibility.
- Icon Composer 27 adds refraction height and strength, an inverse refraction option, chromatic or neutral shadows, ring shadows and sharper specular (27, verify).
- An existing 26 `.icon` opened in Icon Composer 27 renders the new look with no rebuild. It has a back-deployment preview for the macOS 26 look (27, verify).
- When you support macOS 26, render both design generations (see Review renders).

A minimal `icon.json` that compiles with `actool` (tested):

```json
{
  "fill": { "automatic-gradient": "srgb:0.20000,0.42000,0.96000,1.00000" },
  "fill-specializations": [
    { "value": { "automatic-gradient": "srgb:0.20000,0.42000,0.96000,1.00000" } },
    { "appearance": "dark", "value": { "automatic-gradient": "srgb:0.10000,0.20000,0.50000,1.00000" } }
  ],
  "groups": [{
    "layers": [
      { "glass": true, "image-name": "front.svg", "name": "front" },
      { "glass": true, "image-name": "back.svg", "name": "back", "opacity": 0.6 }
    ],
    "shadow": { "kind": "neutral", "opacity": 0.5 },
    "translucency": { "enabled": true, "value": 0.5 }
  }],
  "supported-platforms": { "squares": ["macOS"] }
}
```

Hand-writing the JSON works; opening the file in Icon Composer and dragging layers in works too. Every `image-name` must exist in `Assets/`.

## Workflow

1. **Concept.** One object that says what the app does. Pick a background hue. Plan two or three flat layers: a front shape and a softer back shape.
2. **Layers.** SVG on a 1024 x 1024 canvas, white or one tint, opaque, no blur or shadow, text outlined. Do not export the mask.
3. **`.icon`.** Write or edit it (above). Add the Dark variant, then check Mono.
4. **Compile.** No Xcode project needed (works for SwiftPM apps):

   ```bash
   xcrun actool Icon/AppIcon.icon --compile out --platform macosx \
     --minimum-deployment-target 14.0 --app-icon AppIcon \
     --output-partial-info-plist out/partial.plist --output-format human-readable-text
   ```

   Output: `out/Assets.car` (the layered icon), `out/AppIcon.icns` (fallback for older macOS and Finder paths) and `out/partial.plist` with `CFBundleIconFile` and `CFBundleIconName`, both `AppIcon`. `actool` writes the `.icns` for any deployment target.
5. **Bundle by hand (SwiftPM app).** Copy `Assets.car` and `AppIcon.icns` into `MyApp.app/Contents/Resources/`. Add both plist keys to `Info.plist`. Sign the bundle after the files are in place.
6. **Xcode project instead.** Drag `AppIcon.icon` into the project and tick the target. In target General > App Icons, the name equals the filename without `.icon`. Delete any old `AppIcon.appiconset`: adding a `.icon` replaces the asset-catalog entry, and two sets with one name clash. The build setting is `ASSETCATALOG_COMPILER_APPICON_NAME`. Check the built app: `Contents/Resources` has `Assets.car` and `AppIcon.icns`, and `Info.plist` has `CFBundleIconName`.
7. **Review** every look (next section). Change one thing per round: glyph size, opacity, background. Compare with Apple apps near it in the Dock.
8. **Stale icon in the Dock.** `touch` the app and relaunch. `killall Dock` is a last resort and affects the user's session: ask first.

Debug and Release icons: set the Primary App Icon Set Name per build configuration and untick "Include all app icon assets".

## Review renders

`ictool` is Icon Composer's command-line tool. `xcrun ictool` may resolve to a different binary: use the path inside Icon Composer. Flags below come from its usage text (`ictool --help`).

```bash
ICT="$(xcode-select -p)/../Applications/Icon Composer.app/Contents/Executables/ictool"
for gen in 26 27; do
  "$ICT" Icon/AppIcon.icon --export-image --output-file "default-$gen.png" --platform macOS \
    --rendition Default --width 256 --height 256 --scale 1 --design-generation "$gen"
done
"$ICT" Icon/AppIcon.icon --export-image --output-file tinted.png --platform macOS \
  --rendition TintedDark --width 256 --height 256 --scale 1 --tint-color 0.25 --tint-strength 0.75
```

- Renditions accepted by Icon Composer 27: `Default`, `Dark`, `ClearLight`, `ClearDark`, `TintedLight`, `TintedDark`. Usage text shows only `Default` and `TintedDark`; the other four ran with exit code 0, a bad name exits 255.
- Render each at 256, 32 and 16 px. The glyph must read at 16.
- `--design-generation` takes 26 or 27. Render both when you support macOS 26.
- `ictool` can exit 0 on some errors: check that the PNG exists and open it.
- A pixel check is not enough. Look at the Dock, Cmd-Tab and Finder at small sizes. Ask the user before you drive their desktop.

## Back-deployment

**ICN-7** For a deployment target below 26, bundle both `Assets.car` and `AppIcon.icns`, and set `CFBundleIconName` and `CFBundleIconFile` (both `AppIcon`). Xcode builds a similar-looking icon for older releases from the `.icon`. If older releases must show your exact old artwork, keep a legacy asset-catalog icon for them instead. A legacy macOS asset catalog needs an image for each size.

A fallback `.icns` made from one PNG with `iconutil` works, but it is a legacy icon: on macOS 26 it gets the gray plate (ICN-5). Use it only as a last resort.

## Dock tile

**ICN-8** `NSApp.applicationIconImage` shows a flat image: no glass, no appearances. Use it, or `NSApp.dockTile` with a content view, only for temporary state (a badge, a progress ring). Never use it to dodge the shape rule or to ship the main icon. Set it to `nil` to restore the bundle icon. `dockTile.badgeLabel` is for the unread count (FLW-21).

For a user-chosen icon style, ship pre-rendered variants made with `ictool`, load them by name at runtime, and keep the `.icon` as the default so the system looks stay intact. A flat picture needs the transparent margin the Dock expects: compare it with a system icon.

```swift
@MainActor
func showBackup(progress: Bool, unread: Int, temporaryIcon: NSImage?) {
    NSApp.dockTile.badgeLabel = unread > 0 ? String(unread) : nil
    NSApp.applicationIconImage = progress ? temporaryIcon : nil   // nil restores the bundle icon
}
```

## Document icons

**ICN-9** Give each document type an icon, or let the system compose one (your app icon plus the extension). macOS builds the folded-corner icon from a background fill, an optional center image and optional text.

- Background fill: five sizes, 512 (1x) and 1024 (2x), 256/512, 128/256, 32/64, 16/32.
- Center image: half the canvas size, same five sizes. Keep the art inside about 80% of it.
- Keep nothing important in the top-right corner (the fold).
- Cut detail at small sizes: fewer lines at 32 px, none at 16 px @1x.
- Text defaults to the file extension, capitalized and auto-scaled. Give a short term when the extension is unfamiliar.

## Menu-bar images

Rules live in [menu-bar-apps.md](menu-bar-apps.md) (MBX-4, MBX-5). Drawing details:

**MBX-4** The status item image is a symbol or a template image: black and clear only, with alpha for opacity. The system tints it for light and dark, the selected state and the wallpaper. Never ship a full-color idle icon.

- The menu bar is 24 pt high in the HIG, but `NSStatusBar.thickness` still reports 22 (confirmed on macOS 27). Never hard-code either. Let the button size the image.
- Prefer `NSImage(systemSymbolName:accessibilityDescription:)` (macOS 11). SF Symbols are template images by default. Set weight and scale with `NSImage.SymbolConfiguration` (macOS 11).
- Custom glyphs: vector PDF or SVG in the asset catalog with Render As set to Template Image. Use a PNG @1x and @2x only if you must. Keep about 18 pt tall (36 px @2x) with transparent padding for optical centering: this is a community convention, not an Apple number.
- Code-drawn glyph: set `isTemplate = true`. A `Template` name suffix is a long-standing AppKit convention that Apple's pages do not document: set the flag explicitly.
- The menu bar is transparent on macOS 26 and 27, and Reduce Transparency makes it opaque. Check the image on light and dark wallpapers, in both modes, and when selected.

**MBX-5** Show states with the same glyph in a different variant: outline for idle, fill for on, a slash for paused or unavailable, a badge variant for attention. Never color alone. Set `appearsDisabled` for a paused item. Animate only during real activity (pulse, rotate), and honor Reduce Motion.

```swift
@MainActor
final class StatusIcon {
    enum State { case idle, active, paused, alert }
    let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

    init() {
        item.autosaveName = "main-status-item"   // stable: macOS remembers position and visibility
        apply(.idle)
    }

    func apply(_ state: State) {
        let (symbol, label): (String, String) = switch state {
        case .idle: ("bell", "Idle")
        case .active: ("bell.fill", "Active")
        case .paused: ("bell.slash", "Paused")
        case .alert: ("bell.badge", "Needs attention")
        }
        guard let button = item.button else { return }
        let base = NSImage(systemSymbolName: symbol, accessibilityDescription: label)
        button.image = base?.withSymbolConfiguration(.init(scale: .medium))
        button.appearsDisabled = state == .paused
        button.toolTip = "Reminders: \(label)"            // MBX-6: name and state
        button.setAccessibilityLabel("Reminders, \(label)")
    }
}
```

A custom template glyph drawn in code (black and clear only):

```swift
@MainActor
func makeTemplateGlyph() -> NSImage {
    let image = NSImage(size: NSSize(width: 18, height: 18), flipped: false) { rect in
        NSColor.black.setFill()
        NSBezierPath(roundedRect: rect.insetBy(dx: 3, dy: 3), xRadius: 3, yRadius: 3).fill()
        return true
    }
    image.isTemplate = true
    image.accessibilityDescription = "Reminders"
    return image
}
```

With SwiftUI's `MenuBarExtra` (macOS 13), pass a symbol name, or a custom label: `MenuBarExtra { … } label: { Image(nsImage: makeTemplateGlyph()) }`. `MenuBarExtra("Title", systemImage: on ? "bell.fill" : "bell.slash") { … }` switches variants by state. SwiftUI animation inside the label does not work reliably (MBX-20).

Image rules that also apply: a custom icon needs an accessibility description for VoiceOver (MBX-6); a menu, not a popover, opens on click unless the content needs a panel (MBX-1); never rely on the icon being visible: macOS can hide it for lack of space, and users can turn it off (MBX-8, MBX-10).

## Custom symbols

- Toolbar and sidebar icons: SF Symbols first. A custom symbol only when no symbol fits. One weight and one optical size across the set; match adjacent text weight.
- Do not supply selected and unselected images for toolbars or tab bars: the system draws selection, and a selected toolbar icon takes the accent color.
- Make a custom symbol from a template: in the SF Symbols app, export a similar symbol, edit it in a vector tool, then annotate layers (color or primary, secondary, tertiary) so monochrome, hierarchical, palette and multicolor all work. Start from the Regular weight; Ultralight and Black interpolate.
- Draw whole shapes, no cutouts. For Draw animations give each path at least two guide points, and draw arrowheads as separate paths.
- Use negative side margins for badges. Test every animation preset.
- Gradient rendering and Draw On/Off need SF Symbols 7 (macOS 26). Symbols added in 2026 need macOS 27: gate them (SYM-5).
- Custom interface icons are vectors (PDF or SVG) with an accessibility description. Flip those that suggest reading direction for right-to-left. Localize those that hold characters.
- Apple-product symbols (marked with an info badge in the SF Symbols app) cannot be customized or used in an icon or logo.

## Review checklist

- [ ] `.icon` folder name equals the App Icon setting; `CFBundleIconName` set; `Assets.car` and `AppIcon.icns` in `Contents/Resources` (ICN-1, ICN-7).
- [ ] No second app-icon set with the same name (ICN-5).
- [ ] 1024 x 1024 canvas; square, unmasked SVG or PNG layers; text outlined (ICN-1).
- [ ] At most four groups; every `image-name` exists in `Assets/` (ICN-3).
- [ ] No baked shadow, specular, blur, glow or bevel; no text, screenshot, photo, hardware or SF Symbol (ICN-2).
- [ ] Contact sheet: Default, Dark, Clear, Tinted, and 256/32/16 px, all readable (ICN-3, ICN-4).
- [ ] Rendered with `--design-generation 26` and `27` if the app supports macOS 26; no reliance on refraction (ICN-6).
- [ ] No gray plate in Finder or the Dock on macOS 26 (visual check; ask the user first) (ICN-5).
- [ ] Dock tile code touches only temporary state (ICN-8).
- [ ] Document icons: five background sizes, nothing in the top-right fold, 16 px simplified (ICN-9).
- [ ] Status item: template or SF Symbol, black and clear only, accessibility description, stable `autosaveName`, states by variant, checked on light and dark wallpaper (MBX-4, MBX-5).
- [ ] Custom symbols: annotated layers, tested in each rendering mode and animation preset.
- [ ] Changelog and release notes mention an icon change.

## Sources

- HIG App icons: https://developer.apple.com/design/human-interface-guidelines/app-icons
- HIG Icons (document and interface icons): https://developer.apple.com/design/human-interface-guidelines/icons
- HIG SF Symbols: https://developer.apple.com/design/human-interface-guidelines/sf-symbols
- HIG The menu bar: https://developer.apple.com/design/human-interface-guidelines/the-menu-bar
- Creating your app icon using Icon Composer: https://developer.apple.com/documentation/xcode/creating-your-app-icon-using-icon-composer
- Configuring your app icon: https://developer.apple.com/documentation/xcode/configuring-your-app-icon
- `NSImage.isTemplate`: https://developer.apple.com/documentation/appkit/nsimage/istemplate
- `NSStatusItem.isVisible`: https://developer.apple.com/documentation/appkit/nsstatusitem/isvisible
- `NSApplication.applicationIconImage`: https://developer.apple.com/documentation/appkit/nsapplication/applicationiconimage
- `MenuBarExtra`: https://developer.apple.com/documentation/swiftui/menubarextra
- WWDC26-8012 Icon Composer group lab (summary only): https://developer.apple.com/videos/play/wwdc2026/8012/
- Gray plate on macOS 26: https://9to5mac.com/2025/08/08/macos-tahoe-fix-gray-box-icons/
- Status item icon size convention (community, 2013): https://alastairs-place.net/blog/2013/07/23/nsstatusitem-what-size-should-your-icon-be/
- Local tool runs (Xcode 27.0.0): `xcrun actool` compile of a `.icon`; `ictool --help`, renditions and `--design-generation 26|27` renders.

Parts adapted from BAMA by Dave Ebbelaar (MIT); see THIRD_PARTY_NOTICES.md.
