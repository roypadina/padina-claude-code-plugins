# Menu-bar apps (status items)

Read this when you build or review an app whose main entry is a status item. Explains MBX-1 to MBX-22 in [rules.md](rules.md). Code marked "house code" is not SDK.

Contents: decision guide · MenuBarExtra limits · status item + popover · panel variant · clicks · icon, text, states · macOS 26/27 facts · activation policy · Settings · menu order · launch at login · welcome window · data freshness · notifications · ControlWidget · alert-window actions in the menu · test checklist · sources

## Decision guide (MBX-1, MBX-2)

Default to a menu. Move down only for a named feature, and say which.

| Need | Pick | Min macOS |
|---|---|---|
| Toggles, status, a few actions (a VPN toggle, a usage readout) | `MenuBarExtra` with the default `.menu` style, or `NSStatusItem` + `NSMenu` | 13 |
| Lists, a chart, a field or search (a clipboard manager, a meeting list); no open-from-code | `MenuBarExtra` with `.menuBarExtraStyle(.window)` | 13 |
| Same, and it must open from code (hotkey, alert), or needs right-click, custom size, drop on the icon | `NSStatusItem` + `NSPopover` | 10.12 for the item |
| Panel that must not steal focus, show on all Spaces or over full screen | `NSStatusItem` + non-activating `NSPanel` | 10.12 |
| System-managed highlight for a custom window | `NSStatusItem` + `expandedInterfaceDelegate` | 27 |
| One toggle or button, no app UI | `ControlWidget` (Control Center or menu bar) | 26 |

HIG: show a menu, not a popover, unless the content is too complex for one. Let the person decide whether the icon exists (MBX-9). Keep one status item per app: crowded bars drop items.

## MenuBarExtra limits (MBX-3)

- `.menu` holds only `Button`, `Toggle`, `Picker`, `Divider`, `Menu`, `Text`, `Section` headers and non-button `Label` rows. It does not refresh while open (community): never put live data in one.
- No first-party open or close from code (the docs list only `isInserted` initializers). For a hotkey-opened UI use `NSStatusItem`.
- `.window` style: fixed width, bounded height, own `ScrollView`, Escape and close-after-action.
- A menu-bar-only SwiftUI app terminates when the user removes the extra (docs). Keep it alive another way if it has other jobs (MBX-9).
- Shortcuts in a status menu fire only while it is open or the app is active; Command-Q is not global.

### SwiftUI skeleton (macOS 14)

Icon toggle bound to `isInserted`; a delegate that keeps the app alive and reopens the UI. `SettingsWindow` is below.

```swift
@main
struct ExampleApp: App {
    @NSApplicationDelegateAdaptor private var delegate: AppDelegate
    @AppStorage("showMenuBarIcon") private var showIcon = true

    var body: some Scene {
        MenuBarExtra("Example", systemImage: "bolt", isInserted: $showIcon) {
            Button("Settings…") { SettingsWindow.shared.show() }.keyboardShortcut(",")
            Button("Quit Example") { NSApp.terminate(nil) }.keyboardShortcut("q")
        }
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    @MainActor @objc func openSettings() { SettingsWindow.shared.show() }   // status menu action
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        if !flag { Task { @MainActor in SettingsWindow.shared.show() } }   // or your main UI
        return true
    }
}
```

## Status item + popover (MBX-2, MBX-6, MBX-9, MBX-13, MBX-14)

House code, not SDK. Compiles for macOS 14 (Swift 6). Setup, then click handling.

```swift
@MainActor
final class StatusController: NSObject {
    private let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    private let popover = NSPopover()
    private var visibilityObservation: NSKeyValueObservation?
    var onVisibilityChange: ((Bool) -> Void)?       // keep the Settings toggle in sync

    override init() {
        super.init()
        item.autosaveName = "main"                  // position and removal persist
        item.behavior = .removalAllowed             // user can drag it out; the app keeps running
        visibilityObservation = item.observe(\.isVisible) { [weak self] item, _ in
            MainActor.assumeIsolated { self?.onVisibilityChange?(item.isVisible) }
        }
        if let button = item.button {
            button.target = self
            button.action = #selector(clicked(_:))
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }
        popover.behavior = .transient               // closes on outside click
        popover.contentViewController = NSHostingController(rootView: PanelView())
    }

    var isInserted: Bool {                          // bind to the Settings toggle
        get { item.isVisible }
        set { item.isVisible = newValue }
    }
}
```

```swift
extension StatusController {
    @objc private func clicked(_ sender: NSStatusBarButton) {
        let event = NSApp.currentEvent
        if event?.type == .rightMouseUp || event?.modifierFlags.contains(.control) == true {
            showMenu()
        } else {
            togglePopover(from: sender)
        }
    }

    private func togglePopover(from button: NSStatusBarButton) {
        if popover.isShown { popover.performClose(nil); return }
        if #available(macOS 14, *) { NSApp.activate() }     // user action only; a request
        popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
        popover.contentViewController?.view.window?.makeKey()   // text fields need a key window
    }

    private func showMenu() {
        let menu = NSMenu()
        menu.addItem(withTitle: "Settings…", action: #selector(AppDelegate.openSettings), keyEquivalent: ",")
        menu.addItem(.separator())
        menu.addItem(withTitle: "Quit Example", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.menu = menu
        item.button?.performClick(nil)              // opens the menu with the right highlight
        item.menu = nil                             // the next click reaches `clicked` again
    }
}
```

Notes:

- `.removalAllowed` (10.12) fits apps that stay useful without the icon; by default an item is not removable. Use `.terminationOnRemoval` only when quitting is wanted. The app must let the user bring the icon back: a Settings toggle bound to `isInserted`.
- `item.menu` set-then-clear is a community workaround (`popUpStatusItemMenu(_:)` is deprecated). Re-test per macOS.
- Use the button's target-action for clicks (MBX-14), not a local event monitor: Apple engineers say on the forums it is no longer supported on macOS 27 (27, verify).
- Hotkey that opens this UI: KBD-7, KBD-8 in [menus-and-commands.md](menus-and-commands.md).

## Panel variant

For a panel that must not take focus from the frontmost app (a clipboard manager, a HUD), use the non-activating `QuickPanel` in [swiftui-appkit.md](swiftui-appkit.md). Set `.nonactivatingPanel` in the init mask, return `true` from `canBecomeKey`, dismiss on `resignKey` and Escape, and recompute the position on every open. It needs no `NSApp.activate()`.

## Clicks (MBX-13, MBX-14)

- Left click opens the primary UI. Right click and Control-click open a menu with Settings and Quit. Option-click may add extras.
- Send on mouse-up: right-mouse-down leaves the highlight stuck (community).
- Re-test clicks, hover, `highlight(true)`, `occlusionState` and drop-on-icon on each new macOS: forum reports show breakage on macOS 27 betas.

### macOS 27 expanded interface (27, verify)

`expandedInterfaceDelegate` (macOS 27) lets the system own click, highlight and keyboard navigation for a custom window. It is not called for items with a `menu`. Gate it; keep target-action for older systems. Compiles for macOS 27.

```swift
@available(macOS 27, *)
@MainActor
final class ExpandedUI: NSObject, @MainActor NSStatusItemExpandedInterfaceDelegate {
    private let panel: NSWindow
    init(panel: NSWindow, item: NSStatusItem) {
        self.panel = panel
        super.init()
        item.expandedInterfaceDelegate = self
    }
    func statusItem(_ statusItem: NSStatusItem, didBegin session: NSStatusItemExpandedInterfaceSession) {
        guard let frame = statusItem.button?.window?.frame else { return }
        panel.setFrameTopLeftPoint(NSPoint(x: frame.minX, y: frame.minY))
        panel.makeKeyAndOrderFront(nil)
    }
    func statusItemDidEndExpandedInterfaceSession(_ statusItem: NSStatusItem, animated: Bool) {
        panel.orderOut(nil)
    }
}
```

Close from code with `statusItem.expandedInterfaceSession?.cancel()`. Betas reported suppressed animation and no toggle on a second click (27, verify).

## Icon, text and states (MBX-4, MBX-5, MBX-6, MBX-7, MBX-20)

Drawing, template rules and symbol configuration: [icons.md](icons.md).

- **MBX-4** Template image (`isTemplate = true`) or SF Symbol; the system tints it. Never a full-color idle icon. HIG: the bar is 24 pt (`NSStatusBar.thickness` docs say 22): never hard-code a height; let the button size the image. 16 to 18 pt glyphs are community lore.
- **MBX-5** States differ by shape, never color alone. Idle: outline (`bolt`). Active: `.fill`. Attention: badge symbol (`bolt.badge.exclamationmark`). Error: another symbol (`bolt.slash`). Paused: same glyph with `button.appearsDisabled = true` (10.10), not a hand-faded image. A colored badge makes it non-template.
- **MBX-6** Give the button an accessibility label and a tooltip with name and state ("Example: paused"). Set both in one `setState(_:)` function with the image.
- **MBX-7** Status text: 4 to 6 characters, `.monospacedDigit()` ("42%", not "CPU 42 %"). Width can push the item out on a notched Mac. Details go in the menu.
- **MBX-20** Animate only during real activity (sync, recording): swap template images at 1 to 2 fps, or use an SF Symbol effect. Honor Reduce Motion (`NSWorkspace.shared.accessibilityDisplayShouldReduceMotion`, 10.12). No SwiftUI animation in a status item: stutter reported since macOS 26.

## macOS 26/27 menu bar facts (MBX-9, MBX-10)

- **Allow in the Menu Bar.** From macOS 26 people switch each app's icon in System Settings > Menu Bar. No API reads it. Apple DTS: use `behavior = .removalAllowed` and KVO on `isVisible`.
- **No notch detection.** `isVisible` stays true when the item is crowded out or under the notch; `occlusionState` was unreliable on macOS 27 betas. The app must work with an invisible icon: hotkey, relaunch opens the UI, notifications (MBX-8, MBX-10). Add a Settings hint: "Icon missing? Check System Settings > Menu Bar."
- Never move, hide or enumerate other apps' items.
- **Menu icons on 27.** Status menus hide item images by default for apps linked on 26 or later. Opt in per item with `NSMenuItem.preferredImageVisibility = .visible` (27) or `.labelStyle(.titleAndIcon)`. Keep icons for state, places and devices. See MNU-10 in [menus-and-commands.md](menus-and-commands.md).

## Activation policy and windows (MBX-8, MBX-15)

Set `LSUIElement` to `YES` in Info.plist for a menu-bar-only app (clean launch needed; an Xcode stop and run can mislead). The policy is `.accessory`: no Dock icon, no menu bar, no Command-Tab entry. A window shown that way gets poor focus, and text fields may ignore Command-C and Command-V without an Edit menu. So:

1. Before a real window (Settings, welcome, main): `setActivationPolicy(.regular)`, then `NSApp.activate()`, then `makeKeyAndOrderFront(nil)`.
2. When the last such window closes: `setActivationPolicy(.accessory)`. Popovers and panels do not count.
3. Activate only on a user action (click, hotkey), never at launch or on a timer.

- `activate(ignoringOtherApps:)` is deprecated in macOS 27. Since macOS 14 activation is cooperative and `activate()` (14) is a request: gate it on a 13 target ([swiftui-appkit.md](swiftui-appkit.md)). Offer a Dock icon only as an explicit setting.
- A relaunch from Finder sends a reopen event: implement `applicationShouldHandleReopen(_:hasVisibleWindows:)` to open the primary UI (MBX-8). A Dock menu exists only while the policy is `.regular`.
- Return `false` from `applicationShouldTerminateAfterLastWindowClosed`. To keep one main window, hide it with `orderOut(nil)` from a window delegate: close-then-reopen of a SwiftUI `Window` crashed AppKit on macOS 26 (community, one source).

## Settings from a menu-bar-only app (MBX-16)

Normal apps use the `Settings` scene ([settings.md](settings.md)). In a menu-bar-only app `SettingsLink` and `openSettings` (macOS 14) are unreliable: they need a live scene and a policy switch. Reports cover macOS 14 to 26; 27 unknown. Verify per macOS.

Default: open your own window, with Settings conventions (title follows the selected pane, closable, tabs as toolbar icons; see [settings.md](settings.md)). Host the panes in an `NSTabViewController` with `tabStyle = .toolbar`. A SwiftUI `TabView` inside a plain `NSWindow` draws in-window tabs and breaks SET-2. House code, not SDK. Compiles for macOS 14.

```swift
@MainActor
final class SettingsTabs: NSTabViewController {
    override func tabView(_ tabView: NSTabView, didSelect tabViewItem: NSTabViewItem?) {
        super.tabView(tabView, didSelect: tabViewItem)
        view.window?.title = tabViewItem?.label ?? "Settings"   // title follows the pane
    }
}

@MainActor
final class SettingsWindow: NSObject, NSWindowDelegate {
    static let shared = SettingsWindow()
    private var window: NSWindow?

    private func add(_ tabs: NSTabViewController, _ label: String, _ symbol: String, _ pane: some View) {
        let host = NSHostingController(rootView: pane)
        host.sizingOptions = .preferredContentSize      // window follows the pane (SET-8)
        host.title = label
        let item = NSTabViewItem(viewController: host)
        item.label = label
        item.image = NSImage(systemSymbolName: symbol, accessibilityDescription: label)
        tabs.addTabViewItem(item)
    }

    func show() {
        if window == nil {
            let tabs = SettingsTabs()
            tabs.tabStyle = .toolbar                    // icons in the toolbar (SET-2)
            add(tabs, "General", "gearshape", GeneralPane())
            add(tabs, "Advanced", "gearshape.2", AdvancedPane())
            let w = NSWindow(contentViewController: tabs)
            w.styleMask = [.titled, .closable, .miniaturizable]   // keep .miniaturizable so the button dims
            w.title = "General"
            w.isReleasedWhenClosed = false
            w.standardWindowButton(.miniaturizeButton)?.isEnabled = false
            w.standardWindowButton(.zoomButton)?.isEnabled = false
            w.setFrameAutosaveName("SettingsWindow")
            w.delegate = self
            w.center()
            window = w
        }
        NSApp.setActivationPolicy(.regular)             // Dock icon, menu bar, focus
        if #available(macOS 14, *) { NSApp.activate() } else { NSApp.activate(ignoringOtherApps: true) }
        window?.makeKeyAndOrderFront(nil)
    }

    func windowWillClose(_ notification: Notification) {
        let closing = notification.object as? NSWindow
        let others = NSApp.windows.contains { $0 !== closing && $0.isVisible && $0.canBecomeMain }
        if !others { NSApp.setActivationPolicy(.accessory) }
    }
}
```

Each pane gets its own height (SET-8): grouped forms have no intrinsic height.

Call it from the status menu and the panel's More menu. Keeping the `Settings` scene needs the community hidden-window workaround (Sources, steipete): a 1 by 1 `Window(id: "hidden")` declared before `MenuBarExtra` and `Settings`, which switches to `.regular`, waits about 100 ms, calls `openSettings`, then orders the `com.apple.SwiftUI.Settings` window front. Timing dependent: prefer the own window.

## Menu order, Quit, About (MBX-11, MBX-12)

- **MBX-11** Order: actions, separator, status, separator, `Settings…` (Command-Comma), `About Example`, separator, `Quit Example` (Command-Q) last. Short app name (16 characters or fewer), no version in About. Open About with `NSApp.activate()` then `NSApp.orderFrontStandardAboutPanel(nil)`.
- **MBX-12** A panel-style extra still needs Settings and Quit: a More menu (`ellipsis.circle`, SYM-2) in the panel plus the right-click menu, with the same items (house convention). A gear (`gearshape`) means Settings: use it only for a button that opens Settings directly, never for a menu of mixed actions. A panel with no Quit is a defect.
- While the policy is `.regular` the app has a menu bar: give it App (Settings…), Edit, Window and Help so text keys work.

## Launch at login (MBX-17)

Use `SMAppService.mainApp` (macOS 13). Off by default, changed only by a user action, never at launch. Put the toggle in Settings > General, labeled "Open at Login"; do not hide it in onboarding. Re-read `status` when the view appears and when the app becomes active: the user can change it in System Settings > General > Login Items. House code. Compiles for macOS 14.

```swift
import SwiftUI
import ServiceManagement

struct LaunchAtLoginToggle: View {
    @State private var status = SMAppService.mainApp.status

    var body: some View {
        Group {
            Toggle("Open at Login", isOn: Binding(
                get: { status == .enabled },
                set: { on in
                    do { if on { try SMAppService.mainApp.register() } else { try SMAppService.mainApp.unregister() } }
                    catch { /* log it */ }
                    status = SMAppService.mainApp.status
                }))
            if status == .requiresApproval {
                Text("Allow Example in System Settings > General > Login Items.")
                    .font(.caption).foregroundStyle(.secondary)
                Button("Open Login Items…") { SMAppService.openSystemSettingsLoginItems() }
            }
            if status == .notFound { Text("Move Example to Applications first.").font(.caption) }
        }
        .onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)) { _ in
            status = SMAppService.mainApp.status    // the user may change it in System Settings
        }
    }
}
```

- `.requiresApproval`: toggle off, a "Needs approval" note, and a button calling `SMAppService.openSystemSettingsLoginItems()` (13). `.notFound` often means the app runs from a disk image or build folder.
- `LaunchAtLogin-Modern` (third party) wraps this as `LaunchAtLogin.Toggle()`.

## First-run welcome window (MBX-18)

On first launch show one small welcome window (house convention; policy steps as above; `.accessory` again on "Done"). 

- Show where the icon is (screenshot or arrow) and name it.
- Offer: "Show in the Menu Bar", "Open at Login", a hotkey recorder.
- Say how to open the app without the icon: hotkey, relaunch from Applications, Dock menu if any (MBX-8, MBX-10).
- Permissions: one at a time, at first use ([ux-flows.md](ux-flows.md)).

## Data freshness (MBX-19)

- Match cadence to data: a usage readout every 30 to 60 s; observe `NWPathMonitor` instead of polling network state.
- Set `Timer.tolerance` (about 10% of the interval). Pause timers on sleep (`NSWorkspace.willSleepNotification`) and when nothing visible needs them.
- On panel open refresh, showing the previous value with a spinner, not a blank.
- Show age ("Updated 2 min ago"). Older than two cycles: mark the icon and say why. Never show an old number as live.

## Notifications from a menu-bar-only app

Only for a state change the person cannot see, never to repeat the icon. Ask for authorization when the feature is first enabled; tapping opens the panel. `UNUserNotificationCenter` (10.14) works from an accessory app run as a built `.app` with a stable bundle id (community; test it). More: [ux-flows.md](ux-flows.md).

## ControlWidget (MBX-21)

When the core of the app is one toggle or button, offer a `ControlWidget` (macOS 26, WidgetKit controls). People place it in Control Center or as a menu bar item. It needs a widget extension. It complements a status item and does not replace the app's other entry points.

## Actions on floating windows (MBX-22)

Every action on a floating panel or alert window (Join, Snooze, Dismiss…) is also an item in the status menu, so keyboard-only and VoiceOver users can act without reaching the window. Enable or disable the items with the state of the window (dimmed when nothing is pending). Compare the window's button titles with the menu items (review.md, MNU-2 parity).

## Test checklist

On a clean launch, notched display, crowded bar:

- Icon reads in light, dark and tinted bars; states differ by shape; tooltip and VoiceOver give name and state (MBX-4 to MBX-6).
- Left click opens the UI, right and Control-click the menu, Escape closes a popover (MBX-13). Menu ends Settings…, About, Quit; a panel has Settings and Quit (MBX-11, MBX-12).
- Every action on a floating window also sits in the status menu (MBX-22).
- Settings opens in front; the Dock icon shows while it is open, then goes (MBX-15, MBX-16).
- Drag the icon out or turn it off in System Settings > Menu Bar: the app lives, the toggle shows off, you can still reach it (MBX-8 to 10).
- Launch at login: on, off, requires approval (MBX-17). Reduce Motion: no animation (MBX-20).
- Grep: no `activate(ignoringOtherApps`, no `SettingsLink` in a `MenuBarExtra`, no `register()` at launch.

## Sources

- HIG, The menu bar (menu bar extras, 24 pt, menu not popover, Dock menu): https://developer.apple.com/design/human-interface-guidelines/the-menu-bar
- MenuBarExtra: https://developer.apple.com/documentation/swiftui/menubarextra
- NSStatusItem: https://developer.apple.com/documentation/appkit/nsstatusitem
- NSMenuItem `preferredImageVisibility`: https://developer.apple.com/documentation/appkit/nsmenuitem/preferredimagevisibility
- macOS 27 release notes: https://developer.apple.com/documentation/macos-release-notes/macos-27-release-notes
- NSApplication `activate()`: https://developer.apple.com/documentation/appkit/nsapplication/activate()
- SMAppService: https://developer.apple.com/documentation/servicemanagement/smappservice
- Forum, DTS on Allow in the Menu Bar: https://developer.apple.com/forums/thread/788101
- Forum, status items on macOS 27 betas: https://developer.apple.com/forums/thread/836113 , https://developer.apple.com/forums/thread/832823
- Steipete, Settings from menu bar items: https://steipete.me/posts/2025/showing-settings-from-macos-menu-bar-items
- LaunchAtLogin-Modern: https://github.com/sindresorhus/LaunchAtLogin-Modern

Parts adapted from BAMA by Dave Ebbelaar (MIT); see THIRD_PARTY_NOTICES.md.
