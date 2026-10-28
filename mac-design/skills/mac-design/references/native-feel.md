# Native feel: principles, archetypes, entry points

Read this at the start of design mode, when you pick an archetype or entry points, when you write the design plan, or when an app "feels like the web" or "feels like iOS". It explains PRN-1 to PRN-5, STR-1 to STR-6 and NAT-1 to NAT-8.

Contents: Principles as a review lens · Hierarchy · The design plan · Archetypes · Entry points · Quick capture · The Mac-native checklist · Web and Electron symptoms · iOS-isms · Custom chrome · Automation surface · Lessons from other apps · Sources.

## Principles as a review lens

Apple restored its design principles in the HIG on 2026-06-08 (`hig.sh design-principles`). Ask the question on every screen. Details in the HIG; these are paraphrases.

| Principle | Ask | Rules |
|---|---|---|
| Purpose | What does this feature earn from the person's time and trust? | PRN-3 |
| Agency | Can they go their own way, skip, undo, leave? | UND-1, FLW-1 |
| Responsibility | Is every permission and data use explained at the moment of need? | FLW-5, FLW-8 |
| Familiarity | Does a standard part do this already? | STR-2, PRN-5 |
| Flexibility | Do keyboard, pointer, VoiceOver and resizing all work? | KBD-1, A11Y-8 |
| Simplicity | Is hierarchy from order, space and contrast, not from hiding? | PRN-2, PRN-4 |
| Craft | Is every edge aligned, every response instant, every state designed? | NAT-6, FLW-14 |
| Delight | Does everything serve the one feeling in the plan? | PRN-1 |

## Hierarchy

**PRN-2**. Every screen answers three questions at a glance: Where am I? What can I do? Where can I go? Squint test: blur a screenshot until text is unreadable. The most important element must still stand out. If two things compete, demote one.

**PRN-3**. Cut each feature, control and setting that does not earn the person's time. Ask "what is the least UI that lets the content stand out?" A control nobody uses costs attention on every screen.

**PRN-4**. Keep main actions visible. Simple is not minimal: hiding the main actions in one More menu looks clean and is harder to use. A button that is used daily sits in the toolbar with a title or `.help`, plus a menu item.

## The design plan

**PRN-1**. Write the plan before the first view (SKILL.md lists the eight items). If the repo has `docs/DESIGN.md` or a design section in `docs/BRIEF.md`, put it there; else show it in chat and wait for a yes. One line each. Worked example for a generic notes app:

| Item | Entry |
|---|---|
| Archetype | Sidebar window, plus a quick-capture panel |
| Information architecture | Sidebar: All Notes, Folders, Tags (two levels at most). Content: note list. Detail: editor. |
| Entry points | Main window; global hotkey opens the capture panel; Share extension; drop text on the Dock icon; Shortcuts action "Add Note" |
| Command map | New Note: File, Command-N, toolbar, empty-state button. Delete: Edit, Command-Delete, context menu. Find: Edit, Command-F, toolbar search. |
| States | Empty folder: `ContentUnavailableView` with "New Note". Loading: cached list at once. Error: inline Retry. Offline: one status line. |
| Permissions | None at launch. Notifications only after the first reminder is set. |
| Deployment floor | macOS 14. Glass through `glassSurface`; rich `TextEditor` on 26 with an `NSTextView` fallback. |
| The one feeling | Calm: no badges, no animation beyond selection, quiet empty states. |

Then check the plan against PRN, STR and MOD-1 in rules.md.

## Archetypes

**STR-1**. Pick one main archetype; add at most one small entry point.

| Archetype | Use when | Skeleton | Detail |
|---|---|---|---|
| Sidebar window | People browse collections and edit items | `WindowGroup` + `NavigationSplitView` + `Settings` | [windows-and-chrome.md](windows-and-chrome.md) |
| Single-window or document | One canvas or one document per window | `Window` or `DocumentGroup` + `Settings` | [windows-and-chrome.md](windows-and-chrome.md) |
| Menu bar extra, menu style | A few toggles, a readout, some actions | `MenuBarExtra` `.menu` + `Settings` | [menu-bar-apps.md](menu-bar-apps.md) |
| Menu bar extra, panel style | A list, search, field or chart | `NSStatusItem` + panel | [menu-bar-apps.md](menu-bar-apps.md) |
| Quick-capture panel | One frequent input from anywhere | hotkey + `QuickPanel` | [swiftui-appkit.md](swiftui-appkit.md) |
| Utility or HUD | Floating controls for the active window | `UtilityWindow` (15) or `NSPanel` | [windows-and-chrome.md](windows-and-chrome.md) |

**STR-2**. Build from standard structures: `NavigationSplitView`, `.toolbar`, `.searchable`, `.inspector`, `Settings`, `MenuBarExtra`. **STR-3**. Navigation goes in the sidebar (no sidebar if navigation is one level deep), global actions in the toolbar, details of the selection in an inspector or the detail column.

Sidebar window:

```swift
@main struct NotesApp: App {
    var body: some Scene {
        WindowGroup("Notes", id: "main") {
            NavigationSplitView {
                SidebarView()
            } content: {
                ListView()
            } detail: {
                DetailView()
            }
        }
        .commands {
            SidebarCommands()
            InspectorCommands()    // macOS 14; only with an inspector
            ToolbarCommands()
        }
        Settings { SettingsView() }
    }
}
```

Menu bar extra, menu style (a status toggle; a menu-bar-only app opens Settings through its own window, MBX-16):

```swift
@main struct StatusApp: App {
    @State private var connected = false
    var body: some Scene {
        MenuBarExtra("Status", systemImage: connected ? "lock.fill" : "lock.open") {
            Toggle("Connected", isOn: $connected)
            Divider()
            Button("Settings…") { /* own window: menu-bar-apps.md */ }.keyboardShortcut(",")
            Button("Quit") { NSApplication.shared.terminate(nil) }.keyboardShortcut("q")
        }
        .menuBarExtraStyle(.menu)
        Settings { SettingsView() }
    }
}
```

Utility window (macOS 15; below it, use `NSPanel`): `UtilityWindow("Palette", id: "palette") { PaletteView() }`, declared in a Scene marked `@available(macOS 15, *)`. The skeletons were type-checked at a macOS 14 target with stub views. The `Quick-capture panel` and `panel-style extra` archetypes have no scene: the app delegate owns an AppKit panel.

## Entry points

**STR-4**. A Mac app is used through small entry points. Design them before the main window: a global shortcut, the status item, a quick panel, a file or text drop on the Dock icon, Share, Services, Shortcuts actions. A to-do app lives in its quick-add panel. Each entry point must work with no main window open, and must land in the same model as the main UI. Rules for the pieces: KBD-7 and KBD-8 in [menus-and-commands.md](menus-and-commands.md); MBX-8 in [menu-bar-apps.md](menu-bar-apps.md).

## Quick capture

**STR-5**. One input. A hotkey opens the panel. Return saves and closes at once and shows the result (optimistic UI); offer Undo, not a spinner. Escape closes. Buttons, if any, show their shortcuts. The panel keeps the previous app frontmost. Code, the four panel details and the non-activating pattern: `QuickPanel` in [swiftui-appkit.md](swiftui-appkit.md). Save in the background; if saving can fail, show the failure inline in the main window and via a notification, never in the vanished panel.

## The Mac-native checklist

A native framework does not make an app Mac-like. These are behavior tests: pass or fail by use. Tags point to the rule.

| # | Check | Rule |
|---|---|---|
| 1 | Cold launch shows a usable window in about 1 s; a hotkey panel appears in the same frame | NAT-6 |
| 2 | Local search updates on every keystroke, no spinner | SBR-10 |
| 3 | Every toolbar and panel action is also in the menu bar | MNU-2 |
| 4 | Standard menus present, Window and Help even with one window | MNU-1 |
| 5 | In text fields: Option-arrows move by word, Command-arrows to line ends, Control-A/E/K work, Option-Delete deletes a word, Command-Z undoes typing | NAT-3, KBD-6 |
| 6 | Spelling, autocorrect and text replacement work | NAT-3 |
| 7 | Right-click shows a context menu on every item and on text | MNU-12 |
| 8 | Services lists the app's actions where they apply | STR-6 |
| 9 | Control-Command-F and the green button behave; Window menu has Minimize and Zoom | WIN-12 |
| 10 | Space previews the selected file or file-like item | KBD-3 |
| 11 | Quit and relaunch restores window, Space, selection and scroll | WIN-8 |
| 12 | Command-N opens a new window; tabs merge; Command-` cycles | WIN-6, WIN-11 |
| 13 | A dragged-out item becomes a real file or text; files dropped on the Dock icon open | DND-2, DND-3 |
| 14 | Print and Export as PDF work for document-like content, or are absent | NAT-7 |
| 15 | The app can be driven: App Intents, URL scheme or AppleScript | STR-6 |
| 16 | Cursor stays an arrow over buttons and rows | NAT-1 |
| 17 | System scroll physics and scroll bars; Page Up, Page Down, Home, End scroll lists | NAT-2 |
| 18 | The first click on an inactive window acts; the title bar drags everywhere expected | none |
| 19 | VoiceOver reads every control; Tab reaches every control | A11Y-1, A11Y-8 |
| 20 | Dark, Increase Contrast and Reduce Transparency stay legible | CLR-5, A11Y-11 |
| 21 | Settings open with Command-Comma and apply at once | SET-1, SET-4 |
| 22 | The icon is a full layered squircle, legible in all appearances | ICN-1, ICN-4 |

**NAT-1**. Keep the arrow cursor over buttons and rows; the pointing hand is for links only. **NAT-2**. Never restyle, hide or re-tune scroll bars or scrolling. **NAT-3**. Edit text in system text views. **NAT-5**. Menus, popovers and tooltips are native windows that may extend past the window; a web-drawn one is clipped. **NAT-6**. Cold launch about 1 s is a rule of thumb, not an Apple number: measure on a base-model Mac. **NAT-7**. Wire Print and Export as PDF for document-like content, or remove the items; never leave them enabled and dead.

## Web and Electron symptoms

Find these in a screenshot or by use. Fix by using the system part, not by patching.

| Symptom | Why wrong | Fix | Rule |
|---|---|---|---|
| Custom title bar with web buttons, misplaced traffic lights | Breaks drag, double-click zoom, full screen, corner radius | Real titlebar or toolbar; `.hiddenTitleBar` | none |
| Menu bar has only Quit; Settings is a submenu | Menus are the contract for discovery and keys | Full standard menus, Command-Comma | MNU-1, SET-1 |
| Pointer hand on buttons, hover highlight on whole rows | Web convention | Arrow cursor | NAT-1 |
| Thin custom scroll bars, no rubber-band, wrong momentum | Scroll feel is part of "Mac" | `ScrollView`, `NSScrollView` | NAT-2 |
| No word or line selection, no Services, spelling or replacement | Not the AppKit text system | `TextField`, `TextEditor`, `NSTextView`; bridge it in a web view | NAT-3, NAT-8 |
| App shortcuts steal Option-arrow or Control-A/E/K | Editing keys must reach the field first | Let the field consume them; test | KBD-6 |
| Shortcuts break on non-US keyboards | Raw key codes or punctuation with modifiers | Key equivalents | KBD-4 |
| Menus and tooltips clipped to the window | Web menus cannot leave the window | `Menu`, `NSMenu`, popovers | NAT-5 |
| No context menu, or a web one | Mac users right-click everything | `.contextMenu` | MNU-12 |
| Catalyst sidebar not a source list; no Page Up, Page Down | Catalyst does not rebuild AppKit behavior | `NavigationSplitView`; keyboard scroll audit | STR-2 |
| No AppleScript, Shortcuts, Services or URL scheme | Closed to Mac automation | At least App Intents plus a URL scheme | STR-6 |
| A web view for every pane, always loaded | Memory and launch cost | Native shell; pre-warm only the launch surface | NAT-6 |

**NAT-8**. A web-view surface still gets native menus, keys, input methods, context menus and accessibility. If you go hybrid, you own that work.

## iOS-isms

**NAT-4**. No iOS idioms on the Mac.

| Symptom | Fix |
|---|---|
| 44 pt targets, large pill buttons | `.controlSize`; standard 22–28 pt controls (LAY-1) |
| Hamburger or "More" for everything | Menu bar plus toolbar (PRN-4) |
| Bottom tab bar | Sidebar or a top segmented control |
| Full-screen modal for a small task | Sheet sized to content, popover or inspector (MOD-1, MOD-3) |
| Swipe-only row actions | Context menu, toolbar and shortcut; swipe is a bonus |
| Large titles | Window title in the title bar (WIN-4) |
| Pull to refresh | Command-R, a menu item, a toolbar button |
| Floating "+" button | Toolbar button, File > New, Command-N |
| Share sheet as the only export | Export in File, drag out, Share (DND-7) |
| Back buttons in nav stacks everywhere | One window with split views; documents in separate windows |

## Custom chrome

**PRN-5**. Use stock components first. Stock UI is the baseline, not a duty: a custom toolbar or control is fine when it makes the app clearly better at its one job (a quick-add field, a calendar grid). Opinion: pick a position per app. A restrained app adopts the system look; a custom-chrome app may drop `NSToolbar`.

What must stay, even with custom chrome:

- A code comment with the reason.
- Real menus with the shortcuts, Settings on Command-Comma, standard Edit behavior.
- The system text system (NAT-3), system scrolling (NAT-2) and real traffic lights (WIN-2).
- Accessibility: labels, Tab order, focus ring, Reduce Motion and Transparency (A11Y rules).
- System spacing, fonts and concentric corners (LAY-3).

Never replace a system component because it looks plain. Replace it for a measured reason.

## Automation surface

**STR-6**. Offer at least one: App Intents, a URL scheme, AppleScript or Services. Intents double as UI: they appear in Shortcuts and Spotlight.

```swift
import AppIntents

struct AddNote: AppIntent {                      // macOS 13
    static let title: LocalizedStringResource = "Add Note"
    @Parameter(title: "Text") var text: String

    func perform() async throws -> some IntentResult {
        // save through the same model the UI uses
        return .result()
    }
}

struct NotesShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(intent: AddNote(), phrases: ["Add a note in \(.applicationName)"],
                    shortTitle: "Add Note", systemImageName: "square.and.pencil")
    }
}
```

- URL scheme: declare it in `CFBundleURLTypes`, handle it with `.onOpenURL { url in … }` (macOS 11). Validate the host and every parameter; any app can send the URL.
- AppleScript: set `NSAppleScriptEnabled` and ship a `.sdef` dictionary.
- Services: add `NSServices` entries to Info.plist and a handler method; select text in another app and your action appears in Services.

## Lessons from other apps

Facts are cited; opinions are labelled. Only public third-party apps.

- **Raycast** (launcher). Fact: a native shell with web content; the window is kept ordered front at alpha 0 so it shows instantly; popovers and tooltips are real native windows; Settings opens in a separate window. Lesson: keep one panel alive and update its content off-screen. Trade-off stated by the makers: inactive windows are torn down to save memory, so cold open is slower. Opinion (reviewers): web views risk native feel.
- **Things** (to-dos). Fact: a global Quick Entry that works with the app closed and autofills a link from the front app; Shortcuts actions can prefill a to-do. Opinion (Brent Simmons): its custom toolbar is acceptable because the app is excellent.
- **CleanShot** (screenshots). Fact: a floating overlay after each capture that drags into any app; the latest capture is auto-copied; it asks for two permissions. Lesson: request the minimum, at the moment of need.
- **Nova** (editor). Fact (MacStories review): an icon-grid Settings window where changes apply at once, a standard file sidebar and context menus, preview tabs. Contrast drawn by the reviewer: editors that hide Preferences in a submenu.
- **iStat Menus** (menu bar monitor). Fact: its macOS 26 update fixed a menu bar vertical offset and shipped a layered icon with a mono variant. Lesson: retest status item baseline and icon appearances on every new macOS.
- **Linear** (web and desktop). Fact: the instant feel comes from a local-first sync engine, not from chrome. Lesson: render from local state, apply edits optimistically, sync after (FLW-15).
- **Arc**. Opinion (reviewers): a new navigation model had a steep learning curve. Lesson: do not invent navigation when the standard sidebar does the job.
- **Position on stock UI** (opinion): Brent Simmons and John Gruber argue stock macOS 26 UI is not worth adopting blindly. This file's position: use stock parts by default, and keep the behaviors (keys, menus, text, accessibility) when you do not.

## Sources

- HIG, Design principles: `hig.sh design-principles --mac`; Designing for macOS: `hig.sh designing-for-macos --mac`
- Raycast, technical deep dive: https://www.raycast.com/blog/a-technical-deep-dive-into-the-new-raycast
- Brent Simmons, Proxyman (Mac-assed): https://inessential.com/2020/03/19/proxyman ; stock Mac UI, via Daring Fireball: https://daringfireball.net/linked/2026/09/25/brent-simmons-stock-mac-ui
- Daring Fireball, Mac-assed Mac apps: https://daringfireball.net/linked/2020/03/20/mac-assed-mac-apps ; Sketch on native: https://daringfireball.net/2020/11/sketch_mac_app_mac_apps ; Catalyst two months in: https://daringfireball.net/2019/12/catalyst_two_months_in
- MacStories, Nova review: https://www.macstories.net/reviews/nova-review-panics-code-editor-demonstrates-why-mac-like-design-matters/ ; Things 3.17 Shortcuts: https://www.macstories.net/reviews/things-3-17-overhauls-the-apps-shortcuts-actions/
- Cultured Code, Shortcuts actions: https://www.culturedcode.com/things/help/shortcuts-actions/
- Efficient.app, CleanShot: https://efficient.app/apps/cleanshot
- Bjango, iStat Menus version history: https://weather.bjango.com/mac/istatmenus/versionhistory
- Linear, scaling the sync engine: https://linear.app/blog/scaling-the-linear-sync-engine
- Michael Tsai, Liquid Glass disbelief: https://mjtsai.com/blog/2025/12/29/liquid-glass-disbelief
- Tyler Hall, Half-assed Mac apps: https://tyler.io/?p=1435
- App Intents docs: `appintents/appintent`, `appintents/appshortcutsprovider` (macOS 13), `swiftui/utilitywindow` (macOS 15), `swiftui/inspectorcommands` (macOS 14), via the Apple docs JSON, 2026-10-28.

Parts adapted from BAMA by Dave Ebbelaar (MIT); see THIRD_PARTY_NOTICES.md.
