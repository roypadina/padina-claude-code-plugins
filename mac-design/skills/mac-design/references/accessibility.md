# Accessibility

VoiceOver, keyboard access, accessibility settings, custom controls and testing for a native Mac app. Explains the A11Y rules in [rules.md](rules.md).

**When to read this:** you build a custom control or a custom `NSView`, add motion, glass or color-coded state, or review an app for accessibility. Standard controls already do most of this; read only the section for what you add.

Contents: [VoiceOver basics](#voiceover-basics) · [Custom controls](#custom-controls) · [Announcements and rotors](#announcements-and-rotors) · [Keyboard access](#keyboard-access) · [Settings to honor](#settings-to-honor) · [Size and contrast](#size-text-and-contrast) · [Voice Control and Switch Control](#voice-control-and-switch-control) · [AppKit custom views](#appkit-custom-views) · [Testing](#testing) · [Nutrition Labels](#app-store-accessibility-nutrition-labels)

Code compiles with Swift 6 at macOS 14. Minimum macOS comes from the Apple docs JSON. Full HIG text: `hig.sh accessibility --mac`, `hig.sh voiceover --mac`.

## VoiceOver basics

Every custom element answers four questions: what it is (label), what it is set to (value), what people can do (traits and actions), what changed (feedback).

- **A11Y-1** Label every icon-only control. `Button("Share", systemImage:)` with `.labelStyle(.iconOnly)` keeps "Share" as the VoiceOver label. Put what it does and its shortcut in `.help`.
- **A11Y-2** Anything clickable is a `Button`. A view with `.onTapGesture` has no button trait, no focus and no Space or Return. If forced, add `.accessibilityAddTraits(.isButton)`, `.focusable`, and key handling (see [Keyboard access](#keyboard-access)).
- **A11Y-3** The label is the visible words, without the role: not "Save button". State goes in the value ("3 of 5"), never in a stale label. Add `.accessibilityHint` only when the result is not obvious (macOS 13+).
- **A11Y-4** A row reads as one element. Combine it, and expose row and hover-only actions as named actions.
- **A11Y-5** Hide decorative images. Mark section titles as headers. Give every window a unique title.

```swift
Button("Share", systemImage: "square.and.arrow.up") { share() }
    .labelStyle(.iconOnly)
    .help("Share this task (⇧⌘S)")

HStack { Text(task.title); Text(task.due) }
    .accessibilityElement(children: .combine)           // macOS 10.15
    .accessibilityAction(named: "Complete") { complete(task) }   // 13

Text("Today").font(.headline).accessibilityAddTraits(.isHeader)
Image(systemName: "sparkles").accessibilityHidden(true)
```

| API | Min macOS |
|---|---|
| `accessibilityLabel`, `accessibilityValue`, `accessibilityHint`, `accessibilityAction(named:)` | 13 |
| `accessibilityElement(children:)` | 10.15 |
| `accessibilityAddTraits`, `accessibilityHidden`, `accessibilitySortPriority`, `accessibilityInputLabels` | 11 |
| `accessibilityHeading`, `accessibilityRepresentation`, `accessibilityChildren`, `accessibilityRespondsToUserInteraction`, `AccessibilityFocusState` | 12 |
| `accessibilityRotor`, `accessibilityCustomContent` | 13 |
| `accessibilityDirectTouch` | 14 |
| `accessibilityActions(category:_:)` | 15 |

Use `accessibilitySortPriority` when reading order differs from visual order, rather than reordering views. A chart gets a one-line summary as its label ("Spending rose 12% in October"); interactive charts keep their interactions (`accessibilityChartDescriptor`, macOS 12).

## Custom controls

**A11Y-7** A custom control has an adjustable action or named actions. Drag-only, hover-only and gesture-only actions also exist as accessibility actions and as menu commands, so VoiceOver, Voice Control and Switch Control reach them (WWDC26-220). A two-axis control gets four actions: "Move Up", "Move Down", "Move Left", "Move Right", with a fixed step that stops at the edges.

```swift
struct VolumeDial: View {
    @Binding var level: Double                       // 0...1
    @State private var lastSpoken = Date.distantPast
    private var spoken: String { level.formatted(.percent.precision(.fractionLength(0))) }

    var body: some View {
        Circle().trim(from: 0, to: level)
            .stroke(.tint, lineWidth: 5)
            .frame(width: 28, height: 28)            // Mac default control size
            .gesture(DragGesture().onChanged { drag in
                level = min(1, max(0, level - drag.translation.height / 400))
                if Date.now.timeIntervalSince(lastSpoken) >= 0.3 {   // A11Y-6 throttle
                    lastSpoken = .now
                    AccessibilityNotification.Announcement(spoken).post()
                }
            })
            .accessibilityElement()
            .accessibilityLabel("Volume")
            .accessibilityValue(spoken)
            .accessibilityAdjustableAction { direction in
                switch direction {
                case .increment: level = min(1, level + 0.1)
                case .decrement: level = max(0, level - 0.1)
                @unknown default: break
                }
            }
            .accessibilityAction(named: "Mute") { level = 0 }
    }
}
```

When a standard control already models the behavior, borrow its accessibility tree instead: `.accessibilityRepresentation { Slider(value: $level, in: 0...1) { Text("Volume") } }` (macOS 12). `accessibilityDirectTouch` (14) helps fine-grained drags, but never as the only path.

## Announcements and rotors

- **A11Y-6** Announce changes that happen without a click (sync done, list emptied, error). Use `AccessibilityNotification.Announcement(_:).post()`; it lives in the `Accessibility` framework (14.0), so `import Accessibility`. Post only on a value change and at most every 0.3 s. Never announce every drag tick.
- Move VoiceOver focus after an insert or navigation with `@AccessibilityFocusState` and `.accessibilityFocused(_:equals:)` (macOS 12).
- Long content gets a rotor: `accessibilityRotor(_:entries:)` (SwiftUI, 13) or `NSAccessibilityCustomRotor` (AppKit, 10.13). Typical rotors: errors, unread items, headings.

```swift
@AccessibilityFocusState private var errorFocused: Bool
Text("Fix the name").accessibilityFocused($errorFocused)
Button("Check") { errorFocused = true }
```

## Keyboard access

- **A11Y-8** With Keyboard navigation on, Tab reaches every control in reading order, Space activates, Escape cancels, Return commits, and there is no focus trap. On macOS a click does not focus a button; Tab reaches it only when System Settings > Keyboard > Keyboard navigation is on. Test with it on.
- Custom controls join the Tab loop with `.focusable(_:interactions:)` (macOS 14) and handle keys with `.onKeyPress` (14). Test Space on custom `ButtonStyle` controls; an old forum report says it did not fire.
- Groups in split layouts use `.focusSection()` (13). Initial focus: `@FocusState` plus `.defaultFocus(_:_:priority:)` (13). Typing panels get initial focus; see `noInitialFocus()` in [swiftui-appkit.md](swiftui-appkit.md) for the windows that should not.
- **A11Y-9** Keep the focus ring. `.focusEffectDisabled()` (macOS 14) only with an equally visible custom ring (3:1 contrast against its surroundings).
- Escape: `.onExitCommand` (10.15). Return: `.keyboardShortcut(.defaultAction)`. Every toolbar or hover action also has a menu command (rule MNU-2).

```swift
Text(title).padding(6)
    .focusable(true, interactions: .activate)
    .onKeyPress(.space) { action(); return .handled }
    .onKeyPress(.return) { action(); return .handled }
    .onTapGesture(perform: action)
    .accessibilityAddTraits(.isButton)
```

## Settings to honor

Read the SwiftUI environment value in views. Read the `NSWorkspace` flag in AppKit drawing code and re-read it on `NSWorkspace.accessibilityDisplayOptionsDidChangeNotification` (post it through `NSWorkspace.shared.notificationCenter`).

| Setting (System Settings > Accessibility) | SwiftUI environment (min macOS) | AppKit (`NSWorkspace.shared`) | What to change |
|---|---|---|---|
| Display > Reduce Motion (Motion pane) | `accessibilityReduceMotion` (10.15) | `accessibilityDisplayShouldReduceMotion` (10.12) | **A11Y-10** Slides, zooms and parallax become fades. Springs tighter. No blur or depth transitions. Stop loops. Never make people wait for an animation |
| Display > Reduce Transparency | `accessibilityReduceTransparency` (10.15) | `accessibilityDisplayShouldReduceTransparency` (10.10) | **A11Y-11** Custom glass and materials get an opaque fallback with equal contrast |
| Display > Increase Contrast | `colorSchemeContrast == .increased` (10.15) | `accessibilityDisplayShouldIncreaseContrast` (10.10) | Use asset-catalog High Contrast variants; stronger borders |
| Display > Differentiate Without Color | `accessibilityDifferentiateWithoutColor` (10.15) | `accessibilityDisplayShouldDifferentiateWithoutColor` (10.10) | Add an icon or word to every color-coded state |
| Show Borders | `accessibilityShowBorders` (compiles from 11; honored on macOS 27) | none verified | **A11Y-12** Draw an outline on borderless custom controls. The docs rename `accessibilityShowButtonShapes` to this value |
| Display > Invert Colors (Smart) | `accessibilityInvertColors` (10.15) | `accessibilityDisplayShouldInvertColors` (10.12) | **A11Y-15** Photos and video opt out: `.accessibilityIgnoresInvertColors(true)` (11) |
| Display > Text size | none | none | See [Size, text and contrast](#size-text-and-contrast) |

```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion
@Environment(\.accessibilityReduceTransparency) private var reduceTransparency
@Environment(\.accessibilityDifferentiateWithoutColor) private var noColorOnly
@Environment(\.accessibilityShowBorders) private var showBorders

panel
    .background(reduceTransparency ? AnyShapeStyle(.background) : AnyShapeStyle(.regularMaterial))
    .transition(reduceMotion ? .opacity : .move(edge: .trailing))
    .overlay { if showBorders { RoundedRectangle(cornerRadius: 6).stroke(.secondary) } }
Image(systemName: noColorOnly ? "exclamationmark.circle.fill" : "circle.fill").foregroundStyle(.red)
```

Notes:

- System glass adapts by itself under Reduce Transparency and the Liquid Glass Clear and Tinted choice (macOS 26.1+). On 27 the slider runs from clear to fully tinted. Test text over glass at both ends, plus Increase Contrast, in light and dark. Field reports on 26 say early point releases left toolbars translucent under Reduce Transparency: test the current release.
- **A11Y-16** Detect assistive technology only for small tweaks, never to gate a feature: `accessibilityVoiceOverEnabled`, `accessibilitySwitchControlEnabled` (macOS 12), `NSWorkspace.isVoiceOverEnabled`, `isSwitchControlEnabled` (10.13).
- `dynamicTypeSize` (macOS 12) has no effect on macOS: Apple's docs say the value cannot be changed by users and does not affect text size. Never gate a layout on it.
- No timed auto-dismiss as the only way to act. No flashing content.

## Size, text and contrast

Numbers from the HIG Accessibility page:

| Item | Mac value |
|---|---|
| Control size | 28 x 28 pt default, 20 x 20 pt minimum |
| Padding | about 12 pt around bezeled controls, about 24 pt around bezel-less ones |
| Text | 13 pt default, never under 10 pt; thin weights need larger sizes |
| Contrast | 4.5:1 up to 17 pt; 3:1 at 18 pt, or bold |

- If default colors miss the minimum, a higher-contrast scheme must appear when Increase Contrast is on. Check light and dark. Prefer system semantic colors; they carry accessible variants.
- **A11Y-15** Truncated text shows its full value in `.help`.
- macOS has no Dynamic Type. People still need larger text (HIG: at least 200 percent): reading apps add View > Bigger, Smaller and Actual Size (Command-Plus, Command-Minus, Command-0) driven by one stored scale, with a lower bound of 0.8 and an upper bound of 2. The system Text size setting (macOS 14+) is followed only by some Apple apps.

## Voice Control and Switch Control

- **A11Y-13** Set `accessibilityInputLabels(_:)` (macOS 11) when the visible label is long or the control is an icon. The visible label stays a valid input. Test with "Show names" and "Show numbers".
- Switch Control and Voice Control cannot drag or hover: every such action also exists as an action, a menu command or a button (**A11Y-7**).
- Pointer size and cursor color are system settings. Do not make essential UI depend on a custom cursor or hover zone.

## AppKit custom views

**A11Y-14** A custom `NSView` exposes element, role, label, value and frame. A view that draws several parts exposes one `NSAccessibilityElement` per part, with the frame in screen coordinates. Post `NSAccessibility.post(element:notification:)` when the value changes.

```swift
final class Meter: NSView {
    var value = 0.5 { didSet { needsDisplay = true
        NSAccessibility.post(element: self, notification: .valueChanged) } }
    override var acceptsFirstResponder: Bool { true }
    override var focusRingMaskBounds: NSRect { bounds }
    override func drawFocusRingMask() { NSBezierPath(roundedRect: bounds, xRadius: 4, yRadius: 4).fill() }

    override func isAccessibilityElement() -> Bool { true }
    override func accessibilityRole() -> NSAccessibility.Role? { .levelIndicator }
    override func accessibilityLabel() -> String? { "Battery" }
    override func accessibilityValue() -> Any? { "\(Int(value * 100)) percent" }
    override func accessibilityPerformIncrement() -> Bool { value = min(1, value + 0.1); return true }
}

// Drawn parts: isAccessibilityElement() == false on the container, then
// accessibilityChildren() returns NSAccessibilityElement.element(withRole:frame:label:parent:)
// items; call setAccessibilityFrame(_:) with window.convertToScreen(convert(rect, to: nil)).
```

`NSAccessibilityElement` is macOS 10.10, `drawFocusRingMask()` and `focusRingMaskBounds` 10.7, `NSAccessibilityCustomAction` and `NSAccessibilityCustomRotor` 10.13. The docs JSON has no availability for `NSAccessibility.post`; it compiles at macOS 14. Hosted SwiftUI inside an `NSHostingView` keeps its own tree.

## Testing

Run these in order after each new window, sheet, popover or empty, error and offline state.

1. **Accessibility Inspector** (Xcode > Open Developer Tool). Pick the app as target. Use the inspection pointer on each custom control and check label, value, traits, actions and that the frame matches the drawn bounds. Run the Audit tab and fix missing descriptions, contrast, small hit areas and clipped text.
2. **VoiceOver pass.** Toggle with Command-F5; VO is Control-Option. Move with VO-Right and VO-Left, press with VO-Space, open the rotor with VO-U, list actions with VO-Command-Space. Check: elements read as label, role, value; groups read once; no "button button"; decorative images skipped; headings reachable; focus lands sensibly after a sheet closes or a delete; a change without a click is announced; every hover-only and drag-only action shows in the actions menu.
3. **Keyboard-only pass.** Turn on Keyboard navigation (System Settings > Keyboard), then Full Keyboard Access (Accessibility > Keyboard). Tab through the window: every control reachable, order matches reading order, focus ring always visible, Space activates custom controls, no trap in sheets, popovers and text views.
4. **Settings pass.** One at a time, in light and dark: Increase Contrast, Reduce Transparency, Reduce Motion, Differentiate Without Color, Invert Colors, Show Borders (27), Liquid Glass Clear and Tinted. Voice Control with "Show names". Switch Control on each window.
5. **Automated audit** (**A11Y-17**). `XCUIApplication.performAccessibilityAudit(for:_:)` is macOS 14.0+. Run it per main window state. Skip a known false positive in the handler, with one comment per skip. The audit does not catch wrong reading order, stale values or missing announcements, so passes 2 to 4 stay required.

```swift
final class A11yAuditTests: XCTestCase {
    @MainActor func testMainWindowAudit() throws {
        let app = XCUIApplication()
        app.launch()
        try app.performAccessibilityAudit { issue in
            issue.element?.identifier == "knownFalsePositive"   // return true to ignore; comment why
        }
    }
}
```

Set `accessibilityIdentifier` (macOS 11) on elements the tests must find; identifiers are not read aloud.

Code review greps (bounded):

```bash
rg -n -m 20 '\.onTapGesture' --glob '*.swift'                        # needs Button or button trait
rg -n -m 20 '\.dynamicTypeSize' --glob '*.swift'                     # dead code on macOS
rg -n -m 20 'focusEffectDisabled|focusable\(false\)' --glob '*.swift'  # needs a custom ring
rg -n -m 20 'onHover' --glob '*.swift'                               # needs an action or menu command
rg -n -m 20 'accessibilityVoiceOverEnabled|isVoiceOverEnabled' --glob '*.swift'  # never gate features
rg -l 'class \w+: NSView' --glob '*.swift' | head -20                # then check isAccessibilityElement
rg -n -m 5 'performAccessibilityAudit' --glob '*.swift'              # at least one
```

## App Store Accessibility Nutrition Labels

On Mac, eight labels apply: VoiceOver, Voice Control, Dark Interface, Differentiate Without Color Alone, Sufficient Contrast, Reduced Motion, Captions, Audio Descriptions. There is no Larger Text label on Mac. A label claims that people can finish all common tasks with that feature, not that some screens work (WWDC25-224). Evaluate each label on every supported device before declaring it. Labels show on macOS 26+; they are voluntary now and Apple has said they will become required.

## Sources

- HIG Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- HIG VoiceOver: https://developer.apple.com/design/human-interface-guidelines/voiceover
- `dynamicTypeSize` (no effect on macOS): https://developer.apple.com/documentation/swiftui/environmentvalues/dynamictypesize
- `accessibilityShowBorders`: https://developer.apple.com/documentation/swiftui/environmentvalues/accessibilityshowborders
- `performAccessibilityAudit(for:_:)`: https://developer.apple.com/documentation/xcuiautomation/xcuiapplication/performaccessibilityaudit(for:_:)
- `AccessibilityNotification`: https://developer.apple.com/documentation/accessibility/accessibilitynotification
- WWDC26-220 Refine accessibility for custom controls: https://developer.apple.com/videos/play/wwdc2026/220/
- WWDC26-102 (Show Borders honored on macOS 27): https://developer.apple.com/videos/play/wwdc2026/102/
- WWDC25-224 Evaluate your app for Accessibility Nutrition Labels: https://developer.apple.com/videos/play/wwdc2025/224
- Nutrition Labels overview (App Store Connect help): https://developer.apple.com/help/app-store-connect/manage-app-accessibility/overview-of-accessibility-nutrition-labels
- Custom `ButtonStyle` and keyboard focus (forum): https://developer.apple.com/forums/thread/683157
- Liquid Glass settings behavior (field notes): https://sixcolors.com/post/2025/11/soaping-up-liquid-glass-less-transparency-more-contrast/
- Mac text size per app: https://support.apple.com/guide/mac-help/mchld786f2cd/
- Parts adapted from BAMA by Dave Ebbelaar (MIT); see THIRD_PARTY_NOTICES.md.
