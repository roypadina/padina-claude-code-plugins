# Settings window

How to build and structure the Settings window. Explains the SET rules in [rules.md](rules.md).

**When to read this:** before you add or change the Settings window, a settings tab, or a toggle in a settings row. Menu-bar-only apps also read [menu-bar-apps.md](menu-bar-apps.md) (opening Settings). Permission rows: [ux-flows.md](ux-flows.md).

## Contents

- Scene and opening
- Tabs
- Rows and controls
- Sizing
- Focus on open
- Common tabs
- Destructive actions
- Custom AppKit settings window
- Complete example
- Sources

## Scene and opening

**SET-1.** Use the `Settings` scene (macOS 11). SwiftUI adds App > Settings… with Command-Comma (HIG Settings: put the item in the App menu, avoid a toolbar button). Never a sheet, a page in the main window, or a toolbar gear. Document-level options go in the File menu, not here.

- Open it from your own UI with `SettingsLink` or `@Environment(\.openSettings)` (both 14).
- In a menu-bar-only app these fail without a live SwiftUI scene and an activation-policy switch. Reports cover macOS 14 to 26; status on 27 is unknown. Verify on every supported macOS. Use an own window instead (MBX-16): see [Custom AppKit settings window](#custom-appkit-settings-window).
- A custom window is correct only there. In an app with a Dock icon, the `Settings` scene is the default and a custom window is wrong.
- Never call the private `showSettingsWindow:` selector. It stopped working in macOS 14.

## Tabs

**SET-2.** One tab per topic. macOS draws the tabs as icons in the window toolbar, and the window title follows the selected tab. A single pane has no tabs and the title "<App> Settings".

- A topic gets a tab only when it has more than about three rows. Use two to six tabs. More than six topics (a suite of tools): a settings window with a sidebar.
- SwiftUI: `TabView` with `.tabItem { Label("General", systemImage: "gearshape") }` and `.tag`. `Tab(_:systemImage:)` is macOS 15; on a 14 target use `.tabItem`.
- Title the tab with a noun. Labels in the toolbar stay short ("General", "Shortcuts").

| Tab | Holds | Symbol |
|---|---|---|
| General | Startup, menu bar and Dock, default behavior | `gearshape` |
| Appearance | Only app-specific choices (icon style, density). Light/dark and accent follow the system; no picker unless asked | `paintpalette` |
| Shortcuts | Global shortcut, key commands | `keyboard` |
| One per feature | Options of one big feature (Capture, Sync) | the feature's symbol |
| Permissions | Each system permission with state and one button ([ux-flows.md](ux-flows.md)) | `lock.shield` |
| Advanced | Data folder, export, reset, debug | `gearshape.2` |

**SET-3.** Reopen on the last pane. Bind the selection to `@AppStorage` (or `@SceneStorage`). The toolbar is not customizable and always shows the active tab. Minimize and zoom are dimmed: the `Settings` scene does this itself. A custom window sets it by hand (below).

**SET-4.** Changes apply at once. No Save, Apply, OK or Cancel button (house convention; the HIG has no text on it). Use `@AppStorage` for simple values so every view reading a setting updates itself. A value that needs validation: validate on commit and show the error in the footer.

**SET-5.** Few app-wide options, good defaults (HIG Settings).

- Put general, rarely changed options here. View options (sort, filter, show/hide a column) stay in the view or the View menu.
- Never copy a system setting (text size, accent, light/dark, accessibility). Offer a button that opens the System Settings pane instead.
- Do not ask for setup data you can detect (for example the current appearance).

## Rows and controls

**SET-6.** One grouped `Form` per tab (`.formStyle(.grouped)`, macOS 13).

- Group rows in `Section("Name")`. Put help text in the section footer, never in the label.
- Label the setting by its on state, as a statement: "Show in the menu bar", not "Enable menu bar". People infer the off state. Link to a system setting instead of describing where it is.
- `LabeledContent` (13) puts a value or custom control on the trailing edge. Trailing values then line up.
- Use system controls so spacing, focus rings and VoiceOver come free.

**SET-7.** Pick the control by the choice.

| Choice | Control |
|---|---|
| One on/off row in a grouped form | `Toggle` with `.controlSize(.mini)`: a mini switch, whose height matches buttons so rows stay even (HIG Toggles) |
| A master setting that turns a group on | Regular switch |
| A hierarchy of settings (a parent with sub-options) | Checkboxes: `.toggleStyle(.checkbox)` |
| 2 to 5 exclusive choices | Radio group: `.pickerStyle(.radioGroup)` |
| More than 5 choices | Pop-up: `.pickerStyle(.menu)` |
| A single option outside a grouped form | Checkbox |

- Do not swap an existing checkbox for a switch.
- No segmented control in Settings rows. It belongs in toolbars and inspectors.
- Switches, checkboxes and radio buttons go in the window body, never in a toolbar or status bar (TBR-9).

**SET-9.** A setting that cannot apply now is disabled, and the footer says why ("Requires Accessibility access"). A permission row shows the state ("Allowed", "Not allowed") and one button that opens the right System Settings pane. Switches that restore suppressed alerts live in Advanced (MOD-10).

## Sizing

**SET-8.** Each pane sizes to its content.

- Scene: `.windowResizability(.contentSize)`. It is the default for `Settings`, so it is redundant but harmless, and it documents intent.
- Apple's own sample applies `.scenePadding()` and `.frame(maxWidth: 350, minHeight: 100)` to the `TabView`. No fixed Apple width exists.
- A width of 520 pt (house convention) fits a grouped form with labels and trailing controls. Pick one width for all tabs, or the window jumps on every tab change.
- Height follows each pane. A scroll bar appears only when a pane is taller than the screen allows. If a pane is taller than about 640 pt (house convention), split it into two tabs.
- Do not use a fixed height or a hard-coded `.fitsContent()` (not an SDK API).

## Focus on open

A text field, shortcut recorder or button must not open with a focus ring or selected text. Apply `.noInitialFocus()` to the `TabView`. It is a house helper defined in [swiftui-appkit.md](swiftui-appkit.md), not SDK. Test that Tab and Command-Comma still work afterwards. A window whose one job is typing is the exception.

## Common tabs

- **General.** "Open at login" and "Show in the menu bar" toggles. The `SMAppService` code, status handling and `isInserted`/`isVisible` binding are in [menu-bar-apps.md](menu-bar-apps.md). Show the real state: re-read it each time the pane appears, because people change it in System Settings > General > Login Items.
- **Shortcuts.** One row per global shortcut with a recorder, a Clear button and a default. Show a clash or registration failure next to the row (KBD rules in [menus-and-commands.md](menus-and-commands.md)). The system has no recorder control. Use the `KeyboardShortcuts` package (`KeyboardShortcuts.Recorder`) or draw one with an `NSViewRepresentable`; never a plain text field.
- **Permissions.** Reason, live state and one deep link per permission. All details in [ux-flows.md](ux-flows.md).

## Destructive actions

Reset and Delete All go last, in Advanced, in their own section with a footer that says what is lost. Use `role: .destructive`, ending the title with `…` when a confirmation follows. Confirm with an alert (MOD-9), or offer Undo. Never a destructive button as the first row of a pane.

## Custom AppKit settings window

For menu-bar-only apps (MBX-16) and any window that is not the `Settings` scene. Match the scene's conventions:

- Title follows the visible pane ("General"). With one pane: "<App> Settings".
- Dim minimize and zoom: `standardWindowButton(_:)?.isEnabled = false`. Keep `.miniaturizable` in the style mask, or the button vanishes instead of dimming.
- Restore the last pane and the frame (`setFrameAutosaveName`).
- Open it from the status menu's "Settings…" (Command-Comma). Switch activation policy and activate first: [menu-bar-apps.md](menu-bar-apps.md) holds the controller (`SettingsWindow`).

```swift
@MainActor final class SettingsWindowController: NSWindowController {
    convenience init(root: some View) {
        let window = NSWindow(contentViewController: NSHostingController(rootView: root))
        window.styleMask = [.titled, .closable, .miniaturizable]
        window.title = "General"                       // update when the pane changes
        window.setFrameAutosaveName("SettingsWindow")
        window.standardWindowButton(.miniaturizeButton)?.isEnabled = false
        window.standardWindowButton(.zoomButton)?.isEnabled = false
        self.init(window: window)
    }
}
```

## Complete example

Compiles for macOS 14 (no `Tab`, no 15 API). `@AppStorage` keeps the last tab (SET-3) and the values (SET-4).

```swift
struct SettingsRoot: View {
    @AppStorage("settingsTab") private var tab = "general"
    var body: some View {
        TabView(selection: $tab) {
            GeneralPane().tabItem { Label("General", systemImage: "gearshape") }.tag("general")
            AdvancedPane().tabItem { Label("Advanced", systemImage: "gearshape.2") }.tag("advanced")
        }
        .scenePadding()
        .frame(width: 520)                              // house convention
        .noInitialFocus()                               // house helper, swiftui-appkit.md
    }
}

struct GeneralPane: View {
    @AppStorage("showInMenuBar") private var showInMenuBar = true
    @AppStorage("openAtLogin") private var openAtLogin = false
    @AppStorage("sort") private var sort = "date"
    var body: some View {
        Form {
            Section {
                Toggle("Open at login", isOn: $openAtLogin).controlSize(.mini)
                Toggle("Show in the menu bar", isOn: $showInMenuBar).controlSize(.mini)
            } footer: { Text("Turn this off to use the Dock icon only.") }
            Section("Default view") {
                Picker("Sort notes by", selection: $sort) {
                    Text("Date").tag("date"); Text("Title").tag("title")
                }.pickerStyle(.radioGroup)
            }
        }.formStyle(.grouped)
    }
}

struct AdvancedPane: View {
    @State private var confirmReset = false
    var body: some View {
        Form {
            Section {
                Button("Reset All Settings…", role: .destructive) { confirmReset = true }
            } footer: { Text("Restores every setting to its default.") }
        }
        .formStyle(.grouped)
        .confirmationDialog("Reset All Settings?", isPresented: $confirmReset) {
            Button("Reset", role: .destructive) { /* reset */ }
            Button("Cancel", role: .cancel) { }
        }
    }
}

// In the App body:
Settings { SettingsRoot() }.windowResizability(.contentSize)
```

Review each tab in light and dark: no focus ring or selected text on open, no scroll bar unless the pane is tall, no empty band under the last row, labels as statements, trailing values aligned.

## Sources

- HIG: [Settings](https://developer.apple.com/design/human-interface-guidelines/settings), [Toggles](https://developer.apple.com/design/human-interface-guidelines/toggles), [The menu bar](https://developer.apple.com/design/human-interface-guidelines/the-menu-bar), [Alerts](https://developer.apple.com/design/human-interface-guidelines/alerts)
- Docs: [Settings](https://developer.apple.com/documentation/swiftui/settings), [SettingsLink](https://developer.apple.com/documentation/swiftui/settingslink), [openSettings](https://developer.apple.com/documentation/swiftui/environmentvalues/opensettings), [Tab](https://developer.apple.com/documentation/swiftui/tab), [windowResizability(_:)](https://developer.apple.com/documentation/swiftui/scene/windowresizability(_:)), [Form](https://developer.apple.com/documentation/swiftui/form), [standardWindowButton(_:)](https://developer.apple.com/documentation/appkit/nswindow/standardwindowbutton(_:))
- Settings from a menu-bar-only app (community report): https://steipete.me/posts/2025/showing-settings-from-macos-menu-bar-items
- KeyboardShortcuts package: https://github.com/sindresorhus/KeyboardShortcuts
- Parts adapted from BAMA by Dave Ebbelaar (MIT); see THIRD_PARTY_NOTICES.md.
