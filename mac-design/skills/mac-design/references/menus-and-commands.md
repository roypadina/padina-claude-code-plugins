# Menus, commands and keyboard

Read this when you build or review the menu bar, context menus, the Dock menu, keyboard shortcuts, in-app focus or a global hotkey. Explains MNU-1 to MNU-14 and KBD-1 to KBD-9 in [rules.md](rules.md). Status item menus: [menu-bar-apps.md](menu-bar-apps.md).

Contents: standard menus · labels · icons · SwiftUI commands · AppKit menus · context menus · Dock menu · shortcuts · focus · global hotkeys · sources

## Standard menus (MNU-1 to MNU-6, MNU-8)

**MNU-1** Order: App, File, Edit, Format (text apps), View, your menus (general first, mirroring the app's structure), Window, Help. Keep Window and Help with one window. **MNU-2** Every command is in the menu bar, including each toolbar, context-menu, Dock and hover action: Full Keyboard Access and Help search reach them there.

| Menu | Contents |
|---|---|
| App | About Example (alone in its group), `Settings…` (Command-Comma) with app-config items, Services, Hide, Hide Others, Show All, `Quit Example` (**MNU-3**) |
| File | `New <Noun>` ("New Event", never "New"), `Open…`, Open Recent (names, not paths; Clear Menu), Close, Duplicate (Option: Save As), `Rename…`, `Move To…`, `Export As…` for other formats only (**MNU-4**). Save only for document apps; others autosave |
| Edit | Undo and Redo that name the action ("Undo Add Task": `undoManager?.setActionName`), Cut, Copy, Paste, Paste and Match Style, Delete (never Erase, Clear), Select All, Find. The system adds Dictation and Emoji. Keep Edit in non-document apps (**MNU-5**) |
| View | Show/Hide Sidebar, Toolbar, Inspector, Enter/Exit Full Screen; labels follow state. Keep View with only Full Screen if that is all (**MNU-6**). No window management here |
| Window | Minimize, Zoom, Bring All to Front, then open windows alphabetically. No panels in the list |
| Help | `Example Help`, then a few extras after a separator |

- **MNU-8** An item that does not apply stays visible and dimmed. A submenu stays enabled even when all its items are dimmed.
- Mutating `NSApp.mainMenu` is lost when SwiftUI rebuilds menus (community report). Use it only for what SwiftUI cannot express and re-apply in `menuNeedsUpdate`.
- Menu titles in the bar: one word where you can, title case otherwise (HIG).

## Labels and the ellipsis (MNU-7)

- Verb or verb phrase in title case, no articles: "Add Bookmark", not "Add a Bookmark". "Show Fonts", not "Show Fonts Panel".
- Use the ellipsis character `…` (U+2026), never three periods, and only when the command needs more input before it acts ("Rename…", "Export As…"). A command that acts at once, or shows only a confirmation, gets none.
- A toggled item changes its wording: "Show Map", "Hide Map". Add a verb when the noun is unclear ("Turn Grid On"). A checkmark marks an attribute that is on.
- Submenu when one word repeats in more than two items ("Sort By"). One level, about five items (**MNU-11**).
- Option (dynamic) items: one modifier, menu bar only, never the only path. Not in context or Dock menus.

## Menu icons (MNU-10)

HIG (updated 2026-06-08): use icons sparingly, for key actions, places, devices and visual ideas. All items in a group get an icon or none do. Use the standard symbols for common actions.

On macOS 27, apps linked on macOS 26 or later get no menu item images by default. Opt in per item (macOS 27 for the AppKit property):

```swift
Button { } label: { Label("Export as PDF…", systemImage: "arrow.up.doc") }
    .labelStyle(.titleAndIcon)                 // SwiftUI menus; macOS 11+

let item = NSMenuItem(title: "Export as PDF…", action: nil, keyEquivalent: "")
item.image = NSImage(systemSymbolName: "arrow.up.doc", accessibilityDescription: nil)
if #available(macOS 27, *) { item.preferredImageVisibility = .visible }   // AppKit may still hide it
```

## SwiftUI commands (MNU-5, MNU-9)

`CommandGroup(before:after:replacing:)` takes a `CommandGroupPlacement` (macOS 11): `.appInfo`, `.appSettings`, `.appTermination`, `.systemServices`, `.newItem`, `.saveItem`, `.importExport`, `.printItem`, `.undoRedo`, `.pasteboard`, `.textEditing`, `.textFormatting`, `.sidebar`, `.toolbar`, `.windowSize`, `.windowArrangement`, `.windowList`, `.singleWindowList` (13), `.help`. `CommandMenu` adds a menu.

- Insert `after` or `before` a placement. `replacing` removes system behavior: use it only for a group you re-implement. **MNU-5** Never replace `.pasteboard`, `.undoRedo` or `.textEditing` with an empty group.
- `SidebarCommands()` gives Control-Command-S. `InspectorCommands()` gives Control-Command-I; HIG Keyboards lists Option-Command-I for an inspector window. Keep the framework command and never add a second.
- **MNU-9** State comes from `.focusedSceneValue` at the window root. `.focusedValue` on a leaf goes `nil` when focus leaves that subtree: the usual cause of a menu that stays dimmed. Compiles for macOS 14.

```swift
extension FocusedValues {
    @Entry var library: Library?          // macro (Xcode 16); compiles for older targets
}

struct LibraryWindow: View {
    @State private var library = Library()    // an @Observable class
    var body: some View {
        ContentView()
            .focusedSceneValue(\.library, library)   // window root, not a leaf
    }
}

struct LibraryCommands: Commands {
    @FocusedValue(\.library) private var library: Library?
    var body: some Commands {
        CommandGroup(after: .newItem) {                  // keeps the standard New item
            Button("Duplicate") { library?.duplicate() }
                .keyboardShortcut("d")
                .disabled(library?.selection == nil)    // dim, never hide
        }
        CommandMenu("Library") {
            Button("Rename…") { library?.rename() }.disabled(library == nil)
        }
    }
}
```

- An `@Observable` model also works directly: `.focusedSceneValue(model)` and `@FocusedValue(Model.self)` (macOS 14). `.focusedSceneObject` and `@FocusedObject` (13) serve `ObservableObject`.
- A menu title that changes with state reads a value (`Bool`, `String`) from the focused value. Commands do not re-evaluate on unrelated mutations of an object outside the focused-value channel. A mirror object that copies state into the channel is the fallback.
- A `Window` or `WindowGroup` scene gets Window and Help from the system. Keep them.

## AppKit menus

Use AppKit for what SwiftUI cannot do: badges, section headers, subtitles, rebuild on open. Compiles for macOS 14.

```swift
@MainActor
final class DocController: NSObject, NSMenuItemValidation, NSMenuDelegate {
    var hasSelection = false
    @objc func archive(_ sender: Any?) {}

    func validateMenuItem(_ item: NSMenuItem) -> Bool {       // dims what does not apply
        item.action == #selector(archive(_:)) ? hasSelection : true
    }

    func menuNeedsUpdate(_ menu: NSMenu) {                    // runs right before it opens
        menu.removeAllItems()
        menu.addItem(.sectionHeader(title: "Recent"))         // macOS 14
        let item = NSMenuItem(title: "Archive", action: #selector(archive(_:)), keyEquivalent: "")
        item.target = self
        item.badge = NSMenuItemBadge(count: 3)                // macOS 14
        if #available(macOS 14.4, *) { item.subtitle = "Moves it out of the list" }
        menu.addItem(item)
    }
}
```

`NSHostingMenu(rootView:)` (macOS 14.4) builds an `NSMenu` from SwiftUI views for `NSStatusItem.menu` or a view's `menu`. SwiftUI has no API for subtitle, badge or section header.

## Context menus (MNU-12, MNU-13)

- Items for the clicked item or selection only, most frequent first, about three groups, one submenu level at most.
- No shortcuts shown. Hide inapplicable items (Cut, Copy and Paste may dim). A title only to clarify scope ("3 Items Selected").
- Every item also exists in the menu bar or main UI. Offer the same menu on every item of a kind. Use a context menu or an edit menu on an item, not both.
- Lists and tables use `.contextMenu(forSelectionType:menu:primaryAction:)` (macOS 13) so the menu acts on the selection and `primaryAction` is double-click:

```swift
List(rows, selection: $selection) { Text($0.name) }
    .contextMenu(forSelectionType: Row.ID.self) { ids in
        if !ids.isEmpty { Button("Duplicate") { }; Button("Delete") { } }
    } primaryAction: { ids in /* open */ }
```

Custom rows outside `List` and `Table` get no selection highlight when the menu opens (community): track the target yourself.

## Dock menu (MNU-14)

A few high-value items for when the app is in the background; the system adds open windows. Each item also exists in the menu bar. No dynamic items. SwiftUI has no Dock menu scene. A menu-bar-only app has no Dock icon, so its Dock menu works only while the policy is `.regular`.

```swift
final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDockMenu(_ sender: NSApplication) -> NSMenu? {
        let menu = NSMenu()
        menu.addItem(withTitle: "New Note", action: #selector(newNote), keyEquivalent: "")
        return menu
    }
    @objc private func newNote() { /* same action as File > New Note */ }
}
```

## Shortcuts (KBD-1 to KBD-6)

- **KBD-1** Every frequent command has a shortcut shown in its menu item, in its `.help` tooltip ("Add Task (⌘N)") and in a list in Settings or Help.
- **KBD-2** Never repurpose a standard or system shortcut, and never add a modifier to one for an unrelated command. Shift-Command-V is "Paste as" in HIG, so a clipboard manager should not take it.
- **KBD-3** Standard keys people expect:

| Key | Action |
|---|---|
| Return / Escape | default button / cancel |
| Command-Period | cancel an operation |
| Delete | remove the selection |
| Space | preview (Quick Look) |
| Arrows | move |
| Command-F / Option-Command-F | find / jump to the search field |
| Control-Command-F | enter full screen |
| Control-Command-S / Control-Command-I | show sidebar / inspector (framework commands) |
| Command-Comma / Command-? | Settings / Help |

  System-owned, never reuse: Command-Space, Control-Space, Command-Tab, Command-Grave, Option-Command-Esc, Control-Command-Space, Command-H, Command-M, Command-Q, Command-W.
- **KBD-4** No Option or Shift with punctuation keys: where punctuation sits, and which character Shift gives, change between keyboard layouts. Use `.keyboardShortcut("d")` with a character, never a raw key code. Global hotkeys are the exception: they need key codes.
- **KBD-5** Every shortcut gives visible feedback in the same frame: a panel opens, a HUD flashes, a toggle flips (house convention).
- **KBD-6** Text fields get editing keys first. Do not bind Delete, Return, Space or arrows as menu shortcuts that fire while typing. Prefer `.onKeyPress` (macOS 14), `.onDeleteCommand`, `.onMoveCommand`, `.onExitCommand` on a `.focusable()` view. A local event monitor sees keys before a focused `NSTextView`: use it only for keys that must work anywhere in the app, and pass `NSText` first responders through:

```swift
NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
    if NSApp.keyWindow?.firstResponder is NSText { return event }   // let typing through
    return handle(event) ? nil : event                              // nil swallows the key
}
```

## Keyboard focus in the app (KBD-9)

New items take focus: a new row or note selects its title field. A window you open for browsing opens with no field focused, so no field shows a caret or ring: use `noInitialFocus()` from [swiftui-appkit.md](swiftui-appkit.md) and test that Tab and shortcuts still work. A window you open to type in focuses its field:

```swift
struct QuickAdd: View {
    enum Field { case title, notes }
    @FocusState private var focus: Field?
    @State private var title = ""
    var body: some View {
        TextField("Title", text: $title)
            .focused($focus, equals: .title)
            .onKeyPress(.escape) { focus = nil; return .handled }   // macOS 14
            .defaultFocus($focus, .title)                            // macOS 13
    }
}
```

Use `.focusSection()` (macOS 13) to group controls so arrow keys move between sections. Full keyboard access in custom views: [accessibility.md](accessibility.md).

## Global hotkeys (KBD-7, KBD-8)

| Need | Use | Permission |
|---|---|---|
| One hotkey, recorder UI, App Store | `KeyboardShortcuts` package (third party, macOS 10.15): warns on conflicts, stores in `UserDefaults`, sandbox safe | none |
| Small, first-party | Carbon `RegisterEventHotKey` (`GlobalHotKey` below) | none, works in the sandbox |
| Observe keys, not consume | `NSEvent.addGlobalMonitorForEvents` | Accessibility |
| Consume or rewrite keys | `CGEventTap` | Input Monitoring (listen only) or Accessibility |
| Inside the app only | `.keyboardShortcut` via `CommandGroup` | none |

Neither Carbon nor `KeyboardShortcuts` supports media keys or Caps Lock.

- **KBD-7** Make it recordable and clearable in Settings > Shortcuts. Default to none, or to a Command or Control combination such as Control-Option-Y. Never default to Option-only or Option-Shift-only: macOS 15 broke `RegisterEventHotKey` for them (Apple reported a fix in 15.2; reports stay mixed). Never default to a system combination (KBD-3).
- **KBD-8** Register once at launch (`applicationDidFinishLaunching`), not in `onAppear`, and keep the registration alive. Check the `OSStatus` and tell the user when it fails: `eventHotKeyExistsErr` means another app owns the combination. Show "Shortcut in use" next to the recorder. Registrations normally survive sleep; if users report a dead hotkey after wake, re-register on `NSWorkspace.didWakeNotification` (house convention).

House helper, not SDK. Compiles for macOS 14 (Swift 6):

```swift
import AppKit
import Carbon.HIToolbox

@MainActor
final class GlobalHotKey {
    private static var handler: EventHandlerRef?
    private static var actions: [UInt32: () -> Void] = [:]
    private static var nextID: UInt32 = 1
    private var ref: EventHotKeyRef?
    private let id: UInt32

    /// Returns nil when the system refuses; log the status and surface it in Settings.
    init?(keyCode: Int, modifiers: NSEvent.ModifierFlags, action: @escaping () -> Void) {
        Self.installHandlerOnce()
        id = Self.nextID; Self.nextID += 1
        var carbon: UInt32 = 0
        if modifiers.contains(.command) { carbon |= UInt32(cmdKey) }
        if modifiers.contains(.option)  { carbon |= UInt32(optionKey) }
        if modifiers.contains(.control) { carbon |= UInt32(controlKey) }
        if modifiers.contains(.shift)   { carbon |= UInt32(shiftKey) }
        let status = RegisterEventHotKey(UInt32(keyCode), carbon, EventHotKeyID(signature: 0x4558_4D50, id: id),
                                         GetApplicationEventTarget(), 0, &ref)
        guard status == noErr else { return nil }
        Self.actions[id] = action
    }

    func unregister() {
        if let ref { UnregisterEventHotKey(ref) }
        ref = nil; Self.actions[id] = nil
    }

    private static func installHandlerOnce() {
        guard handler == nil else { return }
        var spec = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        InstallEventHandler(GetApplicationEventTarget(), { _, event, _ in
            var hotKeyID = EventHotKeyID()
            GetEventParameter(event, EventParamName(kEventParamDirectObject), EventParamType(typeEventHotKeyID),
                              nil, MemoryLayout<EventHotKeyID>.size, nil, &hotKeyID)
            MainActor.assumeIsolated { GlobalHotKey.actions[hotKeyID.id]?() }
            return noErr
        }, 1, &spec, nil, &handler)
    }
}
// Launch: hotKey = GlobalHotKey(keyCode: kVK_ANSI_Y, modifiers: [.control, .option]) { togglePanel() }
```

Keep the object in a property (the app delegate). There is no `deinit`: call `unregister()` to free the combination. A recorder stores the key code and modifiers, then unregisters and registers again on change.

## Sources

- HIG, The menu bar; Menus (icons updated 2026-06-08); Context menus; Dock menus; Keyboards (use `hig.sh <topic> --mac`): https://developer.apple.com/design/human-interface-guidelines/the-menu-bar
- CommandGroupPlacement: https://developer.apple.com/documentation/swiftui/commandgroupplacement
- InspectorCommands, SidebarCommands: https://developer.apple.com/documentation/swiftui/inspectorcommands
- `focusedSceneValue(_:_:)`: https://developer.apple.com/documentation/swiftui/view/focusedscenevalue(_:_:)
- NSMenuItem `preferredImageVisibility` (27), `badge`, `subtitle`, `sectionHeader(title:)`: https://developer.apple.com/documentation/appkit/nsmenuitem
- NSHostingMenu: https://developer.apple.com/documentation/swiftui/nshostingmenu
- `contextMenu(forSelectionType:menu:primaryAction:)`: https://developer.apple.com/documentation/swiftui/view/contextmenu(forselectiontype:menu:primaryaction:)
- Forum, Option-only hotkeys on macOS 15: https://developer.apple.com/forums/thread/763878
- KeyboardShortcuts: https://github.com/sindresorhus/KeyboardShortcuts
- WWDC26 session 269 (SwiftUI menu icons on macOS 27).

Parts adapted from BAMA by Dave Ebbelaar (MIT); see THIRD_PARTY_NOTICES.md.
