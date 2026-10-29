# SwiftUI and AppKit: gates, helpers, interop

Read this when you write code for a window, panel, table or text view, or when an API is newer than the deployment target. It explains IMP-1 to IMP-14 and LST-1 to LST-6 and defines the house helpers other files use. Snippets type-check at a macOS 14 target (Swift 6, Xcode 27 SDK).

Contents: Capability table · Version gates · House helpers · Delegate forwarding · Hidden title bar · QuickPanel · Hosting view sizing · NSViewRepresentable · Tables · Text · Keys · AppKit menus · Activation · macOS 27 deltas · Previews · Gotchas · Sources.

`glassSurface`, `glassButtonStyle`, `WindowAccessor`, `withWindow`, `noInitialFocus()` and `QuickPanel` are house helpers, not SDK APIs. Copy them in once.

## Capability table

Min macOS from the Apple docs JSON, 2026-10-28. "AppKit on 14": the SwiftUI API starts at 15.

| Need | SwiftUI (min macOS) | AppKit route | Verdict |
|---|---|---|---|
| Hide title text, keep traffic lights | `.windowStyle(.hiddenTitleBar)` (11) | `titlebarAppearsTransparent` | SwiftUI |
| Window material, clear toolbar | `.containerBackground(_:for: .window)`, `.toolbarBackgroundVisibility(_:for:)` (15) | `NSVisualEffectView`, `titlebarSeparatorStyle` | AppKit on 14 |
| Drag by background, level, behaviors | `.windowBackgroundDragBehavior`, `.windowLevel`, `.windowMinimizeBehavior` and siblings (15) | `isMovableByWindowBackground`, `level`, `styleMask` | AppKit on 14 |
| Glass surface, buttons | `.glassEffect(_:in:)`, `.buttonStyle(.glass)` (26) | `NSGlassEffectView`, `BezelStyle.glass` (26) | helpers below |
| Table, outline | `Table` (12), `TableColumnCustomization` (14), `List(_:children:)` (12) | `NSTableView`, `NSOutlineView` | low thousands of rows |
| Rich text, find | `TextEditor(text:selection:)`, `.findNavigator` (26) | `NSTextView`, `usesFindBar` | 26+ only |

## Version gates

**IMP-1**. Find the deployment target first (SKILL.md). Every newer API sits behind `if #available` with a working fallback. A bare `.glassEffect` on a macOS 14 target is a compile error, not a runtime fallback.

- Put a gate in a `@ViewBuilder` helper; it cannot sit mid-chain.
- A stored property of a newer type (`@State var s = AttributedTextSelection()`) fails too: use an `@available(macOS 26, *)` view and gate the use.
- Delete a gate once the deployment target reaches the API.

### Scene gates (IMP-3)

**IMP-3**. These need a gate on a 14 target: `.windowLevel`, `.windowBackgroundDragBehavior`, `.restorationBehavior`, `.defaultLaunchBehavior`, `.windowIdealSize`, `.defaultWindowPlacement`, `.windowStyle(.plain)`, `WindowDragGesture`, and the View modifiers `.windowMinimizeBehavior`, `.windowResizeBehavior`, `.windowFullScreenBehavior`, `.windowDismissBehavior` (all macOS 15).

`SceneBuilder` has `buildLimitedAvailability` and `buildOptional`, no `buildEither`. Tested in a scratch package (Xcode 27, Swift 6.4, target macOS 14):

- `if #available(macOS 15, *) { A.windowLevel(.floating) }` plus `if #unavailable(macOS 15) { A }` fails: "generic parameter 'S' could not be inferred".
- `if #available { … } else { … }` in a `@SceneBuilder` fails: "closure containing control flow statement cannot be used with result builder 'SceneBuilder'".
- A plain function returning `some Scene`, one `return` per `#available` branch, compiles.

Use the plain function. It keeps one scene and applies the modifier only where it exists. It works for `#available` only. A lone `if #available(macOS 15, *) { Scene }` also compiles; the scene is then absent below 15.

```swift
import SwiftUI

extension Scene {
    /// House helper, not SDK. `windowLevel` is macOS 15+; below, the scene is unchanged.
    func floatingLevel() -> some Scene {
        if #available(macOS 15, *) {
            return windowLevel(.floating)
        } else {
            return self
        }
    }
}

// Use: WindowGroup("Tools", id: "tools") { RootView() }.floatingLevel()
```

For the four View modifiers, use a `@ViewBuilder` helper (as `clearWindowChrome` below) and give the `else` branch an AppKit fallback inside `withWindow`: `standardWindowButton(.miniaturizeButton)?.isEnabled = false`, `styleMask.remove(.resizable)`, `collectionBehavior.insert(.fullScreenNone)`.

For drag by background on 14, set `isMovableByWindowBackground = true` inside `withWindow`. `.containerBackground(_:for: .window)` is 15: the modifier is 14, the `.window` placement is 15.

## House helpers

All compile at a macOS 14 target. Put them in one file.

### `glassSurface` and `glassButtonStyle` (IMP-2)

**IMP-2**. Route glass through one helper. Glass is for floating controls, never rows or window backgrounds (GLS rules, [design-language.md](design-language.md)). The shape must be `InsettableShape`: the fallback calls `strokeBorder`, and a plain `Shape` does not compile.

```swift
// house helper: glassSurface, glassButtonStyle
import SwiftUI

extension View {
    /// Glass on macOS 26+, regular material below. Floating controls only.
    @ViewBuilder
    func glassSurface<S: InsettableShape>(in shape: S, interactive: Bool = false) -> some View {
        if #available(macOS 26, *) {
            let glass: Glass = interactive ? .regular.interactive() : .regular
            glassEffect(glass, in: shape)
        } else {
            background(.regularMaterial, in: shape)
                .overlay(shape.strokeBorder(.separator, lineWidth: 0.5))
        }
    }

    /// Glass button style on 26+, bordered below.
    @ViewBuilder
    func glassButtonStyle(prominent: Bool = false) -> some View {
        if #available(macOS 26, *) {
            if prominent { buttonStyle(.glassProminent) } else { buttonStyle(.glass) }
        } else {
            if prominent { buttonStyle(.borderedProminent) } else { buttonStyle(.bordered) }
        }
    }
}
```

Use: `Button("Play", systemImage: "play.fill") {}.buttonStyle(.plain).glassSurface(in: .capsule, interactive: true)`, with neighbours inside `GlassEffectContainer(spacing: 12) { … }` (26, gated). Never nest glass in glass. Standard toolbars, sidebars and sheets get glass on 26 with no code. Morphing needs `.glassEffectID(_:in:)` (26) behind its own gate. AppKit (26): wrap a view in `NSGlassEffectView` (`contentView`, `cornerRadius`); group neighbours in `NSGlassEffectContainerView` (`spacing`).

### `WindowAccessor` and `withWindow` (IMP-4)

**IMP-4**. SwiftUI has no public API for the `NSWindow`. A zero-size probe gets it from `viewDidMoveToWindow`. Never use `NSApp.windows.first`, `keyWindow` guesses or `DispatchQueue.main.async` after `onAppear` (nil at launch, wrong window with two open). Configure idempotently: the callback runs again if the view changes window.

```swift
// house helper: WindowAccessor, withWindow
import SwiftUI
import AppKit

struct WindowAccessor: NSViewRepresentable {
    let configure: (NSWindow) -> Void

    func makeNSView(context: Context) -> Probe { Probe(configure) }
    func updateNSView(_ view: Probe, context: Context) { view.configure = configure }

    final class Probe: NSView {
        var configure: (NSWindow) -> Void
        init(_ configure: @escaping (NSWindow) -> Void) {
            self.configure = configure
            super.init(frame: .zero)
        }
        required init?(coder: NSCoder) { nil }
        override func viewDidMoveToWindow() {
            if let window { configure(window) }
        }
    }
}

extension View {
    func withWindow(_ configure: @escaping (NSWindow) -> Void) -> some View {
        background(WindowAccessor(configure: configure))
    }
}
```

Set only what SwiftUI has no modifier for: `isMovableByWindowBackground` on 14, `tabbingMode`, `setFrameAutosaveName(_:)`. Never replace `window.delegate` (next section).

### `noInitialFocus()` (KBD-9)

A window or sheet opens with nothing focused: no ring, no caret, no selected text. `noInitialFocus()` clears the first responder once, after the window first becomes key. Put it on the root view of a window, sheet or Settings tab; never on a typing panel; not with `.defaultFocus` on the same window. Check that Tab and shortcuts still work afterwards.

```swift
// house helper: noInitialFocus (needs withWindow above)
import SwiftUI
import AppKit

private struct NoInitialFocus: ViewModifier {
    final class Once { var done = false; var token: NSObjectProtocol? }
    @State private var once = Once()

    func body(content: Content) -> some View {
        content.withWindow { window in
            guard !once.done else { return }
            if window.isKeyWindow { return clear(window) }
            once.token = NotificationCenter.default.addObserver(
                forName: NSWindow.didBecomeKeyNotification, object: window, queue: .main
            ) { note in
                MainActor.assumeIsolated { (note.object as? NSWindow).map(clear) }
            }
        }
    }

    private func clear(_ window: NSWindow) {
        once.done = true
        if let token = once.token { NotificationCenter.default.removeObserver(token) }
        once.token = nil
        window.makeFirstResponder(nil)
    }
}

extension View {
    func noInitialFocus() -> some View { modifier(NoInitialFocus()) }
}
```

Limit: type-checked only, not run. Focus behavior needs a launched app and nothing was launched. Test on a real window on each supported macOS.

## Window delegate forwarding

**IMP-5**. SwiftUI owns `window.delegate`; replacing it breaks restoration and close handling. To intercept one call (confirm unsaved work, hide instead of close), put a proxy in front and forward the rest.

```swift
import SwiftUI
import AppKit

/// Intercepts `windowShouldClose`; forwards the rest to SwiftUI's delegate.
final class CloseProxy: NSObject, NSWindowDelegate {
    private weak var original: NSWindowDelegate?
    private let allowClose: (NSWindow) -> Bool

    init(original: NSWindowDelegate?, allowClose: @escaping (NSWindow) -> Bool) {
        self.original = original
        self.allowClose = allowClose
    }
    func windowShouldClose(_ sender: NSWindow) -> Bool {
        allowClose(sender) && (original?.windowShouldClose?(sender) ?? true)
    }
    override func responds(to selector: Selector!) -> Bool {
        super.responds(to: selector) || (original?.responds(to: selector) ?? false)
    }
    override func forwardingTarget(for selector: Selector!) -> Any? {
        original?.responds(to: selector) == true ? original : super.forwardingTarget(for: selector)
    }
}
```

Install it once from `withWindow` (`guard !(window.delegate is CloseProxy)`), keep it alive (`NSWindow.delegate` is weak: `objc_setAssociatedObject(window, &key, proxy, .OBJC_ASSOCIATION_RETAIN)`, `key` a `nonisolated(unsafe) private var UInt8`), then set `window.delegate = proxy`. For a single-window menu-bar app, prefer `orderOut(nil)` to closing; a macOS 26 report (BAMA notes, not re-tested) says reopening a closed SwiftUI `Window` crashed.

## Hidden-title-bar window

`.hiddenTitleBar` removes the title text. The traffic lights stay, about 28 pt from the top and 20 pt from the left. Keep controls out of that zone. Never hard-code `.padding(.top, 28)`; the safe area already accounts for a toolbar. Fake traffic lights fail WIN-2 ([windows-and-chrome.md](windows-and-chrome.md)).

```swift
import SwiftUI

extension View {
    /// House helper, not SDK. Window material and a clear toolbar need macOS 15.
    @ViewBuilder func clearWindowChrome() -> some View {
        if #available(macOS 15, *) {
            containerBackground(.thinMaterial, for: .window)
                .toolbarBackgroundVisibility(.hidden, for: .windowToolbar)
        } else {
            self
        }
    }
}

```

Apply it as `Window("Main", id: "main") { ContentView().clearWindowChrome() }.windowStyle(.hiddenTitleBar)`. Frames restore per scene id; add `@SceneStorage` for selection and `.restorationBehavior(.disabled)` (15) for HUDs and onboarding. AppKit shell: `setFrameAutosaveName(_:)`.

## QuickPanel

**IMP-7**. A quick-capture or launcher panel is an `NSPanel`. Four details, each from a real failure:

- `.nonactivatingPanel` goes in the init style mask; `styleMask.insert` later can leave the panel activating the app (community report).
- `canBecomeKey` returns `true`. A borderless window returns `false`, so text fields take no typing.
- `hidesOnDeactivate = false`: the app never activates, so close on `resignKey`.
- No `NSApp.activate`: the previous app stays frontmost.

```swift
// house helper: QuickPanel
import SwiftUI
import AppKit

final class QuickPanel: NSPanel {
    init<Content: View>(@ViewBuilder content: () -> Content) {
        super.init(
            contentRect: NSRect(x: 0, y: 0, width: 640, height: 72),
            styleMask: [.nonactivatingPanel, .borderless, .fullSizeContentView], // here, never later
            backing: .buffered, defer: false)
        isFloatingPanel = true   // level .floating
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .ignoresCycle]
        isOpaque = false
        backgroundColor = .clear
        hasShadow = true
        hidesOnDeactivate = false
        isReleasedWhenClosed = false   // keep one instance
        let host = NSHostingView(rootView: content())
        host.sizingOptions = [.intrinsicContentSize]   // grows with content
        contentView = host
    }

    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }
    override func cancelOperation(_ sender: Any?) { close() }   // Escape
    override func resignKey() {
        super.resignKey()
        close()
    }
    func present() {
        center()
        makeKeyAndOrderFront(nil)
    }
}
```

The content view is a plain `TextField` with `@FocusState`, `.task { focused = true }` (the window is not key during the first `onAppear`), `.glassSurface(in: .rect(cornerRadius: 20))` and `.onSubmit` that saves with Undo and closes the panel. Build the panel once at launch (`let panel = QuickPanel { QuickField() }`) and call `present()` from the hotkey: it then appears in the same frame (NAT-6). Return saves and closes; Escape closes (STR-5, [native-feel.md](native-feel.md)). A HUD adds `.titled, .utilityWindow, .hudWindow` to the mask (legacy dark look; draw new HUDs with `glassSurface`). Panel rules: [windows-and-chrome.md](windows-and-chrome.md). Status item panel: [menu-bar-apps.md](menu-bar-apps.md).

## NSHostingView sizing

**IMP-8**. `NSHostingSizingOptions` (macOS 13): `.minSize`, `.intrinsicContentSize`, `.maxSize`, `.standardBounds` (all three, the default), `.preferredContentSize` (controller). With the default, the hosting view pushes the content's min and max size onto the window. That fights a frame you set. A panel that "snaps back" or will not resize: check this first.

| Situation | Set |
|---|---|
| SwiftUI view is the `contentView` of a window you size | `[]` |
| Panel that grows with content | `[.intrinsicContentSize]` |
| `NSHostingController` as sheet or popover content | `.preferredContentSize` |

Set it before assigning `contentView`: `host.sizingOptions = []`. In a custom shell also set `host.safeAreaRegions = []` (13.3). `host.sceneBridgingOptions = [.toolbars, .title]` (14) lets `.toolbar` and `.navigationTitle` in the SwiftUI view drive an AppKit window.

## NSViewRepresentable template

**IMP-9**. Create once in `makeNSView`, diff in `updateNSView`, push AppKit changes back through the coordinator, clean up in `dismantleNSView`. Never write the binding in `updateNSView`: it can loop.

```swift
import SwiftUI
import AppKit

struct SearchField: NSViewRepresentable {
    @Binding var text: String
    var prompt: String

    func makeNSView(context: Context) -> NSSearchField {      // once: static setup only
        let field = NSSearchField()
        field.delegate = context.coordinator
        field.sendsSearchStringImmediately = true
        return field
    }

    func updateNSView(_ field: NSSearchField, context: Context) {  // every update: diff only
        context.coordinator.parent = self
        if field.stringValue != text { field.stringValue = text }
        if field.placeholderString != prompt { field.placeholderString = prompt }
    }

    func makeCoordinator() -> Coordinator { Coordinator(self) }
    static func dismantleNSView(_ field: NSSearchField, coordinator: Coordinator) { field.delegate = nil }

    @MainActor final class Coordinator: NSObject, NSSearchFieldDelegate {
        var parent: SearchField
        init(_ parent: SearchField) { self.parent = parent }
        func controlTextDidChange(_ note: Notification) {
            guard let field = note.object as? NSSearchField else { return }
            parent.text = field.stringValue            // AppKit -> SwiftUI
        }
    }
}
```

Add `sizeThatFits(_:nsView:context:)` (13) for a wrapped `NSScrollView`, or it gets zero or runaway size.

## Tables and outlines

**LST-1** Selection is a `Set<ID>`; actions take the whole set; select the next row after a delete. **LST-2** `sortOrder:` gives header-click sort (a second click reverses); columns resize; title-case noun headers; `.truncationMode(.middle)`; `.alternatingRowBackgrounds()` (14). **LST-3** `primaryAction:` handles double-click and Return; `.onDeleteCommand` handles Delete; test type-select (typing a name prefix) on each OS, custom cells can break it. **LST-5** `Table` up to the low thousands of rows. **LST-6** Selectable rows come from `List` or `Table`.

```swift
import SwiftUI

struct FileRow: Identifiable, Hashable {
    let id = UUID()
    var name: String
    var size: Int64
}

struct FileTable: View {
    @State var rows: [FileRow] = []
    @State private var sort = [KeyPathComparator(\FileRow.name)]
    @State private var selection = Set<FileRow.ID>()

    var body: some View {
        Table(sortedRows, selection: $selection, sortOrder: $sort) {
            TableColumn("Name", value: \.name) { Text($0.name).truncationMode(.middle) }
            TableColumn("Size", value: \.size) { Text($0.size, format: .byteCount(style: .file)) }
        }
        .contextMenu(forSelectionType: FileRow.ID.self) { ids in   // macOS 13; ids = clicked row or selection
            Button("Open") { open(ids) }.disabled(ids.isEmpty)
            Button("Delete", role: .destructive) { delete(ids) }.disabled(ids.isEmpty)
        } primaryAction: { open($0) }                              // double-click or Return
        .onDeleteCommand { delete(selection) }
        .alternatingRowBackgrounds()
    }

    private var sortedRows: [FileRow] { rows.sorted(using: sort) }
    private func open(_ ids: Set<FileRow.ID>) {}
    private func delete(_ ids: Set<FileRow.ID>) {
        guard let first = sortedRows.firstIndex(where: { ids.contains($0.id) }) else { return }
        rows.removeAll { ids.contains($0.id) }
        let rest = sortedRows
        selection = rest.isEmpty ? [] : [rest[min(first, rest.count - 1)].id]   // LST-1
    }
}
```

- Route `delete` through the undo manager ([ux-flows.md](ux-flows.md)). Sort in the model for thousands of rows.
- **LST-4** Outlines remember expanded rows: persist a `Set<ID>` with `@SceneStorage` (via a `RawRepresentable` wrapper) and bind each `DisclosureGroup(isExpanded:)`; in `NSOutlineView` set `autosaveName` and `autosaveExpandedItems = true`. Option-click on a triangle expands all children in `NSOutlineView`; check your SwiftUI outline.
- **LST-5** Use a view-based `NSTableView` (cell reuse, `insertRows`/`removeRows`) for more than a few thousand rows, live feeds, editable cells or column drag-reorder.
- Reported on macOS 26: `Table` leak (FB21850924) and slowdown (FB21860141) with live data; status on 27 unknown.
- **LST-6** Custom rows outside `List` and `Table` get no selection emphasis or menu highlight. Use the real container.

## Text

**IMP-11**. Plain text: `TextField`, `TextEditor`. Code, attachments, decorations, big documents, tokens, find bar below 26: `NSTextView`. Rich `TextEditor` (`AttributedString` + `AttributedTextSelection`) is macOS 26 only. Never read `textView.layoutManager` or `textContainer.layoutManager`: the view drops to TextKit 1 for its lifetime. Use `textLayoutManager` and `setRenderingAttributes(_:for:)` (macOS 12). `NSTextView.scrollableTextView()` is TextKit 2.

```swift
import AppKit

extension NSTextView {
    /// Temporary highlight without touching `layoutManager`.
    func highlight(_ range: NSRange, color: NSColor) {
        guard let layout = textLayoutManager, let content = layout.textContentManager,
              let start = content.location(content.documentRange.location, offsetBy: range.location),
              let end = content.location(start, offsetBy: range.length),
              let textRange = NSTextRange(location: start, end: end) else { return }
        layout.setRenderingAttributes([.backgroundColor: color], for: textRange)
    }
}
```

Put the macOS 26 editor (`TextEditor(text: $rich, selection: $selection)` with `@State` of `AttributedString` and `AttributedTextSelection`) in its own `@available(macOS 26, *)` view and gate the use. System text views give Option-arrow, Control-A/E/K, spelling and Undo Typing for free (NAT-3, [native-feel.md](native-feel.md)).

## Key handling

**IMP-10**. Prefer, in order: `.onKeyPress(_:action:)` (14) on a `.focusable()` view with `.onDeleteCommand`, `.onMoveCommand`, `.onExitCommand`; a `Button` with `.keyboardShortcut` in `Commands`; last, a local event monitor for keys that must work wherever focus is. A monitor sees keys before the responder chain, so pass events through while a text view is editing. Remove every monitor you add.

```swift
import AppKit

@MainActor final class KeyMonitor {
    private var token: Any?
    init(handler: @escaping @MainActor (NSEvent) -> Bool) {
        token = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
            if NSApp.keyWindow?.firstResponder is NSText { return event }   // never steal typing
            return MainActor.assumeIsolated { handler(event) } ? nil : event
        }
    }
    deinit { if let token { NSEvent.removeMonitor(token) } }
}
```

Never bind bare Delete, Return or arrows to a menu `Button` shortcut: it fires while the person types. Command plumbing and shortcut tables: [menus-and-commands.md](menus-and-commands.md).

## AppKit menus

**IMP-12**. SwiftUI has no menu item badge, section header or subtitle. Use `NSMenuItem.badge`, `.sectionHeader(title:)` (14), `.subtitle` (14.4) in an `NSMenu` refreshed from `menuNeedsUpdate(_:)`, or describe the menu in SwiftUI and host it with `NSHostingMenu` (14.4). Rebuilding the SwiftUI menu bar can overwrite `NSApp.mainMenu` edits; re-apply in `menuNeedsUpdate` (community report).

## Activation

**IMP-6**. Since macOS 14 activation is cooperative: `NSApp.activate()` (14) is a request another app may decline. `activate(ignoringOtherApps:)` is deprecated in macOS 27. Call `activate()` only after a user action (hotkey, click, menu item), never at launch or from a timer. A non-activating panel needs none. To hand focus on: `yieldActivation(toApplicationWithBundleIdentifier:)` (14).

On a 13 target branch with `if #available(macOS 14, *) { NSApp.activate() } else { NSApp.activate(ignoringOtherApps: true) }`; on 14+, call `NSApp.activate()` only. Activation-policy switching: [menu-bar-apps.md](menu-bar-apps.md).

## macOS 27 deltas

From Apple's update pages and the docs JSON, 2026-10-28. "(27, verify)" = beta-era; test on a shipping build.

| Change | Min | Effect |
|---|---|---|
| `activate(ignoringOtherApps:)` | deprecated 27.0 | Use `activate()`. Force-activating hotkey apps may be less reliable. |
| `NSMenuItem.preferredImageVisibility` | 27.0 | Menu item images hidden by default for apps linked on 26+; opt in per item. |
| `NSView.cornerConfiguration` | 27.0 | Concentric and capsule corners for custom views; fixed radius below. |
| `@State` becomes a macro | Xcode 27 build | **IMP-14**: class values in `@State` initialize once; re-test `@State var model = Model()` with side effects in `init`. |
| `.toolbarMinimizationBehavior`, `.swipeActionsContainer()`, `NSRefreshController` | 27.0 | Touch idioms. Skip on Mac (NAT-4). |
| AppKit views stop clipping to bounds by default | (27, verify) | Set `clipsToBounds = true` where you relied on clipping. |
| Clipboard-read alert | upcoming | macOS may alert on a read without a paste; read on user action only. |

## Previews and review captures

**IMP-13**. Previews show component states, not window chrome, toolbar, sidebar glass or `NSWindow` tricks. Judge windows from a real capture.

Add `#Preview("Dark") { ContentView().preferredColorScheme(.dark) }` next to the light preview. `dynamicTypeSize` does nothing on macOS: no "large type" preview. Capture a real window with `screencapture -x -o -l <windowID> out.png` (needs the user's OK and Screen Recording; SKILL.md, Safety). In tests use `SCScreenshotManager` (14). `CGWindowListCreateImage` is deprecated in 14 and obsoleted in 15. `ImageRenderer` (13) skips AppKit-backed views: never use it for a window screenshot.

## Gotchas

1. A hidden title bar still has a toolbar zone; content there overlaps the traffic lights.
2. Glass legibility on 27 follows the user's transparency slider (27, verify). Use `.primary` and `.secondary`; test both ends.
3. A window kept for reuse (`isReleasedWhenClosed = false`, held in a static) keeps its SwiftUI view alive after `close()`: `onReceive(timer)` and other periodic refreshes keep firing, and `onDisappear` / `.task` cancellation never run. If the window hosts a refreshing view, drop it on close: `Task { @MainActor [weak self] in for await _ in NotificationCenter.default.notifications(named: NSWindow.willCloseNotification, object: w) { break }; self?.window = nil }`, and restore size and pane with `setFrameAutosaveName` and a stored tab key.
4. After Hide (⌘H) every window reports `isVisible == false`. Track "a window is open" by membership in your own window list (removed on `willClose`), not by `isVisible`, or a hidden form looks closed.

## Sources

Apple docs JSON, read 2026-10-28 (`https://developer.apple.com/tutorials/data/documentation/<path>.json`): `swiftui/scene/windowlevel(_:)`, `swiftui/containerbackgroundplacement/window`, `swiftui/nshostingview/sizingoptions`, `appkit/nsapplication/activate(ignoringotherapps:)`, `appkit/nsview/cornerconfiguration`, `appkit/nsmenuitem/preferredimagevisibility`. `CGWindowListCreateImage`: SDK header `CGWindow.h`.

- SwiftUI and AppKit release notes: https://developer.apple.com/documentation/updates/swiftui , https://developer.apple.com/documentation/updates/appkit
- Michael Tsai, NSHostingView sizing: https://mjtsai.com/blog/2023/08/03/how-nshostingview-determines-its-sizing ; Table bugs: https://mjtsai.com/blog/2026/02/05/tahoe-swiftui-table-bugs/

Parts adapted from BAMA by Dave Ebbelaar (MIT); see THIRD_PARTY_NOTICES.md.
