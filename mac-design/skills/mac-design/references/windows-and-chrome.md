# Windows and chrome

Window types, title bar, toolbars, sidebars, inspectors, search, sheets, alerts, popovers, panels. Explains the WIN, TBR, SBR and MOD rules in [rules.md](rules.md).

**When to read this:** before you write or review a scene, toolbar, split view, sheet, alert, popover or panel. Settings window: [settings.md](settings.md). House helpers (`WindowAccessor`, `QuickPanel`): [swiftui-appkit.md](swiftui-appkit.md).

**Contents:** scene types and gates; size, restoration, title bar; tabs, full screen, closing; toolbars; sidebars, inspectors, search; surfaces (sheets, alerts, popovers, panels); sources.

## Scene types and gates

**WIN-1.** Pick the scene first. Give each a stable `id`. Never two scenes for one job.

| Need | Scene | Min macOS |
|---|---|---|
| Many windows of one kind, system tabs, File > New Window | `WindowGroup` | 11 |
| One window, listed in the Window menu, `openWindow(id:)` | `Window` | 13 |
| Palette tied to the active window: floats, hides when inactive, no minimize | `UtilityWindow` | 15 |
| Documents | `DocumentGroup` | 11 |
| Settings, Command-Comma | `Settings` | 11 |
| Status item | `MenuBarExtra` ([menu-bar-apps.md](menu-bar-apps.md)) | 13 |

A `UtilityWindow` reads the selection with `@FocusedValue`; the main scene publishes it with `.focusedSceneValue`.

**Gating scene modifiers on a macOS 14 target.** `@SceneBuilder` accepts `if #available` (`buildLimitedAvailability`). It has no `buildEither`, and `buildOptional` is marked unavailable. So `else` and `if #unavailable` do not compile (checked on the macOS 27 SDK, target 14).

| Situation | Do this |
|---|---|
| Scene exists only on 15+ (`UtilityWindow`, optional welcome window) | `if #available(macOS 15, *) { whole scene }` |
| Scene must exist on 14; a 15 modifier is polish | A plain function returning `some Scene`, one `return` per `#available` branch ([swiftui-appkit.md](swiftui-appkit.md), Scene gates); or set the AppKit equivalent in `WindowAccessor` (`isRestorable`, `level`) |
| `windowMinimizeBehavior`, `windowFullScreenBehavior`, `windowResizeBehavior`, `windowDismissBehavior` (15, View modifiers) | Gate in a `ViewModifier`: `if #available(macOS 15, *) { content.windowFullScreenBehavior(.disabled) } else { content }` |

## Size, restoration, title bar

**WIN-7.** Set a default size and a tested minimum.

- `.defaultSize(width:height:)` and `.defaultPosition(_:)` on the scene (13).
- Minimum: `.frame(minWidth:minHeight:)` on the root view plus `.windowResizability(.contentMinSize)` (13).
- Test at the minimum with sidebar and inspector open. Nothing may overlap or truncate.
- `.windowIdealSize(_:)` (15) sets Zoom's size.

**WIN-8.** Restore UI state, never data. SwiftUI restores frames. AppKit needs `setFrameAutosaveName(_:)` and `isRestorable`. Selection and column visibility: `@SceneStorage` (11), ids and flags only.

**WIN-9.** `.restorationBehavior(.disabled)` for windows that must not return (HUDs, onboarding). `.defaultLaunchBehavior(.presented)` opens a welcome window at launch. Both 15+.

**WIN-2.** Never draw a custom title bar, frame or traffic lights. A fake bar breaks drag, zoom, full screen and hit areas. For no title text use `.windowStyle(.hiddenTitleBar)` (11): the real buttons stay. AppKit: `titlebarAppearsTransparent`, `titleVisibility`, `.fullSizeContentView`.

**WIN-3.** Keep controls clear of the traffic lights. They sit about 20 pt from the left and 28 pt from the top (typical). Inset with the safe area, never `.padding(.top, 28)`. Without a toolbar, `.hiddenTitleBar` content reaches the top edge. Windows share one system corner radius (tighter on macOS 27); never hard-code it.

**WIN-4.** Title the window by its content, under about 15 characters, never the app name. An empty title is fine when content explains itself. Say "window" in UI text, never "scene".

**WIN-5.** A subtitle (`.navigationSubtitle`, 13) shows on every page or none. One that comes and goes changes the toolbar height; BAMA reports an AppKit crash on window reopen from it.

**WIN-6.** Never open a window by default. Reuse the detail pane. Offer Open in New Window in File and the context menu.

## Active windows, tabs, full screen, closing

**WIN-10.** States: main (one per app), key (takes input), inactive. Dim custom chrome when inactive with `@Environment(\.appearsActive)` (10.15). System chrome dims itself. Never dim HUDs or non-activating panels. Put only small facts at the bottom edge (count, free space): people move windows so it goes off-screen.

**WIN-15.** Never float a normal window. `.windowLevel(.floating)` (15) and `NSWindow.level` belong to panels and HUDs.

**WIN-11.** Document-like windows use the system tab bar. `WindowGroup` gives it, with Merge All Windows and Move Tab to New Window. AppKit: `tabbingMode`, `tabbingIdentifier`. File shows Close Tab and Close Window. Never build a tab bar.

**WIN-12.** Main windows enter full screen with View > Enter Full Screen (Control-Command-F). Zoom never does. `.windowToolbarFullScreenVisibility(_:)` (15) sets the toolbar there. AppKit: `collectionBehavior` `.fullScreenPrimary`, `.fullScreenAuxiliary` for panels. Fixed-job windows disable both (gate above).

**WIN-13.** Decide what closing the last window does; do not inherit it. Implement `applicationShouldTerminateAfterLastWindowClosed(_:)`: `true` for document and sidebar apps, `false` for menu-bar-only apps. A Dock click with no windows must reopen the main window: SwiftUI does it for the first scene; in a delegate return `true` from `applicationShouldHandleReopen(_:hasVisibleWindows:)` after you open it.

**WIN-14.** Quit without asking unless typed work would be lost (house convention; the HIG has no text on it).

## Toolbars

**TBR-1.** Three areas. At most three groups in the whole toolbar.

- Leading: sidebar toggle, back/forward, title (not customizable). Center: common controls, first to overflow. Trailing: inspector toggle, search, More menu, primary action (always visible).
- On macOS 26 neighbors share one glass capsule. `ToolbarSpacer(.fixed)` (26) splits groups. `ToolbarSpacer(.flexible)` (26) pushes items apart. `ToolbarItemGroup` keeps a set together. `.sharedBackgroundVisibility(.hidden)` (26) frees one item.
- A fixed spacer goes between a text button and a symbol button. On 14 and 15 use `ToolbarItemGroup` and no spacer.
- `.windowToolbarStyle(.unified)` (11) is the default. Hide it only with a way back: `.toolbarVisibility(.hidden, for: .windowToolbar)` (15).
- Never draw your own toolbar background or divider. macOS 27 uses a uniform frosted toolbar and brings dividers back (27, verify). Leave `.scrollEdgeEffectStyle` (26) on automatic ([design-language.md](design-language.md)).

**TBR-2.** Each item sits over the column it acts on.

| Column | Put here |
|---|---|
| Sidebar | Nothing of yours. The system adds the sidebar toggle |
| Content | Title, subtitle, actions that make or order rows (`.primaryAction`) |
| Detail | Actions on the selection. Plain items start at the column's leading edge: `ToolbarSpacer(.flexible)` first |
| Inspector | One toggle, after `ToolbarSpacer(.flexible)` so it does not jump when the inspector opens |

Put `.toolbar` on the column views. On the `NavigationSplitView` itself, `.primaryAction` lands at the detail's leading edge. Placement changed between macOS 26.0 and 26.2: re-snapshot after OS updates.

**TBR-3.** Borderless monochrome symbols. Write `Button("Title", systemImage:)` so the title shows in the overflow menu, in Icon and Text mode and to VoiceOver. Text only when no symbol fits ("Edit"). `.help` starts with a verb and ends with the shortcut ("Create a note (Command-N)"). Every item also has a menu bar command (MNU-2).

**TBR-4.** At most one prominent action: trailing, alone, only for a completing action (Done, Send). "New" is not one.

**TBR-5.** No custom overflow menu; avoid layouts that overflow by default. `ToolbarContent.visibilityPriority(_:)` is macOS 26.1: `.visibilityPriority(.high)` on must-stay items, applied to the `ToolbarItem`, not the button. A custom item that does not fit is dropped silently, so test at the minimum width with the inspector open and closed.

**TBR-6.** No iOS-only toolbar API on Mac. `ToolbarOverflowMenu` and `.topBarPinnedTrailing` list no macOS availability. `.bottomBar`, `.topBarLeading`, `.topBarTrailing`, `.largeTitle`, `ToolbarRole.navigationStack` do not compile on Mac. `.searchToolbarBehavior(_:)` exists on 26; only `.minimize` is iOS-only.

**TBR-7.** Keep the system sidebar toggle and one inspector toggle. `SidebarCommands()` adds View > Show Sidebar (Control-Command-S); `ToolbarCommands()` adds Show Toolbar and Customize Toolbar (both 11).

**TBR-8.** Apps kept open for hours get a customizable toolbar: `.toolbar(id:)` with `ToolbarItem(id:)` (11) plus `ToolbarCommands()`.

**TBR-9.** No Settings button, switch, checkbox or radio button in a toolbar or status bar. Back and Close are symbols (`chevron.backward`, `xmark`), not words. Status text: `.status` placement (11).

Example for macOS 14 to 26. `Library` is your `@Observable` model. The scene adds `.commands { SidebarCommands(); InspectorCommands(); ToolbarCommands() }`.

```swift
NavigationSplitView {
    FolderList()                                  // no items of your own
} content: {
    NoteList()
        .navigationTitle("Notes").navigationSubtitle("\(library.notes.count) notes")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("New Note", systemImage: "square.and.pencil") { library.addNote() }
                    .help("Create a note (Command-N)")
            }
        }
} detail: {
    NoteEditor().toolbar { DetailToolbar(library: library) }
}
.inspector(isPresented: $library.showInspector) {          // on the split view
    NoteInfo().inspectorColumnWidth(min: 220, ideal: 260, max: 340)
        .toolbar {
            if #available(macOS 26, *) { ToolbarSpacer(.flexible) }   // toggle stays put, open or closed
            ToolbarItem {
                Button("Inspector", systemImage: "sidebar.trailing") { library.showInspector.toggle() }
                    .help("Show or hide the inspector (Control-Command-I)")
            }
        }
}
.searchable(text: $library.query, placement: .toolbar, prompt: "Search all notes")

struct DetailToolbar: ToolbarContent {
    var library: Library
    var body: some ToolbarContent {
        if #available(macOS 26, *) {
            ToolbarSpacer(.flexible)
            ToolbarItem { ShareLink(item: library.query) }
            ToolbarSpacer(.fixed)
            ToolbarItem { flag }
        } else {
            ToolbarItemGroup(placement: .primaryAction) { ShareLink(item: library.query); flag }
        }
    }
    private var flag: some View {
        Button("Flag", systemImage: "flag") { library.toggleFlag() }
            .help("Flag the selected note (Shift-Command-L)")
    }
}

```

AppKit: `NSToolbarItem.isBordered`, `style = .prominent`, `NSTrackingSeparatorToolbarItem`.

## Sidebars, inspectors, search

**SBR-1.** The sidebar lists top-level areas, two levels at most. Deeper data goes in a content column. Disclosure groups for large lists.

**SBR-2.** Visible by default, collapses when narrow, View > Show/Hide Sidebar via `SidebarCommands()`.

**SBR-3.** Never hard-code row height or glyph size. They follow the system sidebar icon size; read `\.sidebarRowSize` (13) to adapt.

**SBR-4.** Sidebar icons take the accent color (HIG Sidebars, 2026-06-08), so they follow a changed system accent. Fixed colors only with meaning.

- On macOS 27 the system sidebar reaches the window edge, with refraction underneath (27, verify). Never add margins, backgrounds or an `NSVisualEffectView` to imitate either look.
- Rich content under a sidebar: `.backgroundExtensionEffect()` (26); skip on 14 and 15. No critical actions at the sidebar bottom.

**SBR-5.** No action rows ("New Folder…") in the sidebar list. Actions go in toolbar and menus (WWDC25-359).

**SBR-6.** Keep the selection highlighted in every pane that leads to the detail. One title above a split view, not per pane. Thin 1 pt divider.

**SBR-7.** `.navigationSplitViewColumnWidth(min:ideal:max:)` (13). Values seen in Apple apps, not published (house convention): sidebar min 180, ideal 220–240, max 300; content min 260. Peer panes (editor and preview): `HSplitView` or `NSSplitViewController`.

**SBR-8.** `.inspector(isPresented:content:)` and `.inspectorColumnWidth(min:ideal:max:)` (14) go on the split view; the framework restores the open state.

- `InspectorCommands()` (14) adds View > Show Inspector (Control-Command-I). HIG Keyboards lists Option-Command-I for an inspector window. Keep the framework command; add no second.
- It shows the current selection and updates with it. No selection: `ContentUnavailableView("No Selection", systemImage: "sidebar.right")`.
- A floating inspector that follows the selection: `UtilityWindow` (15) or `NSPanel`. One that keeps its content is a regular window.

**SBR-9.** One search location, set by scope.

| Scope | Place | API |
|---|---|---|
| Whole window | Trailing toolbar | `.searchable(text:placement: .toolbar)` on the split view |
| Sidebar only | Top of sidebar | `placement: .sidebar` |
| Big multi-section app | A Search item in the sidebar with a results page | own view |

`.searchable` on one column does not move the field over that column on macOS. For a list-only field beside an open inspector use an `NSSearchField` toolbar item.

**SBR-10.** Command-F focuses the field; Option-Command-F also does. `.searchFocused(_:)` is macOS 15; on 14 drive focus in AppKit. Escape clears. Results filter as you type; the subtitle shows the count. No results: `ContentUnavailableView.search(text:)` (14).

## Choosing a surface

**MOD-1.** Take the first row that fits. Lighter is better.

| The feature | Use |
|---|---|
| One value on something on screen | Inline |
| Details of the selection while people keep working | Inspector |
| A few related choices tied to one control | Popover |
| Repeated input while watching the result | Panel |
| One short task that must finish or cancel | Sheet |
| A long or self-contained task | Window |
| A place people come back to | Sidebar page |
| A rare data-destroying action, no undo | Confirmation dialog |
| A problem people must act on now | Alert |

A sheet that grows a second screen or a sidebar wants to be a window.

## Sheets

**MOD-2.** One sheet or popover at a time. No sheet from a sheet, no popover from a popover; nothing over a popover except an alert. A sheet is modal to its parent window only.

**MOD-3.** Sheets: short tasks tied to the window (attach, pick a location, small form). Long tasks: a window. Repeated input with visible results (find and replace): a panel.

**MOD-4.** Cancel plus a verb or Done; never Done alone; never Cancel, Done and Back together. Return runs the trailing default. Escape and Command-Period cancel. `.cancellationAction` and `.confirmationAction` wire this up. The title names the task ("Rename Project"), not "Edit".

Sheet body: a `Form` with `.formStyle(.grouped)` and `.frame(width: 360)` (house convention), `.navigationTitle("Rename Project")`, and a `.toolbar` with `ToolbarItem(placement: .cancellationAction) { Button("Cancel") … }` and `ToolbarItem(placement: .confirmationAction) { Button("Rename") … }` (disable it while the field is empty).

**MOD-5.** Size to content: `.presentationSizing(.fitted)` or `.form` (15). On 14 use a fixed width (house convention: 360 small form, 480 medium, 640 wide). Scroll bars only on overflow. Gate on 14 in a `ViewModifier`.

**MOD-6.** Ask before closing only when typed input would be lost. Tie `.interactiveDismissDisabled(_:)` (12) to that state, never a constant `true`.

## Alerts

**MOD-7.** Only for critical, actionable information. Never at launch, for "Saved" or "Copied", or where Undo covers it. 

**MOD-8.** Anatomy: title, optional text, up to three buttons; macOS adds icon, text field, accessory view, suppression checkbox, Help button.

- Title: what happened and why, two lines at most; never "Error" or a code. Sentence: sentence case and period. Fragment: title case, no period.
- Buttons: one or two words, verbs tied to the text. Never Yes/No. "OK" only when informational. Cancel says "Cancel". Never explain the buttons in the text.

**MOD-9.** Default button trailing (top of a stack), never Cancel. Destructive role and caution icon only for loss the person did not deliberately choose. Empty Trash, chosen on purpose, is not red, so Return works. "Don't Save" on closing a document is not chosen on purpose, so it is destructive.

| Need | SwiftUI | Min | AppKit |
|---|---|---|---|
| Alert | `.alert(_:isPresented:actions:message:)` | 13 | `NSAlert` |
| Choices tied to an intentional action | `.confirmationDialog(_:isPresented:titleVisibility:actions:message:)` | 13 | `NSAlert`, several buttons |
| Caution icon | `.dialogSeverity(.critical)` | 13 | `alertStyle = .critical` |
| Suppression checkbox | `.dialogSuppressionToggle(isSuppressed:)` | 14 | `showsSuppressionButton` |
| Attach to a window | the modifiers above | 13 | `beginSheetModal(for:completionHandler:)` |

```swift
.confirmationDialog("Empty the Trash?", isPresented: $confirmEmpty) {
    Button("Empty Trash") { emptyTrash() }                // chosen on purpose: no destructive role
} message: { Text("You can't undo this action.") }
```

**MOD-10.** Repeating non-critical alerts get a suppression checkbox ("Do not show again", 14) and a Settings switch to restore them (SET-9).

**MOD-11.** Attach alerts to their window. `runModal()` only when no window applies.

AppKit: `NSAlert` with `addButton(withTitle:)` (first = default, trailing) then `beginSheetModal(for: window)`; compare the result to `.alertFirstButtonReturn`.

`alert(_:item:)` and `confirmationDialog(_:item:)` were announced at WWDC26. Their macOS availability is unverified, so avoid them.

## Popovers

**MOD-12.** A few related choices tied to one control; it closes after use.

- The arrow points at the source and never covers it (`.popover(isPresented:attachmentAnchor:arrowEdge:content:)`, 10.15).
- Dismiss on outside click or item pick; multi-select stays open.
- Save the person's work on outside-click close; discard only on explicit Cancel.
- Never a warning in a popover; use an alert.
- Detach into a panel only in AppKit: `NSPopover` plus `NSPopoverDelegate.popoverShouldDetach`. `behavior`: `.transient`, `.semitransient`, `.applicationDefined`.

## Panels and HUDs

**MOD-13.** A panel floats above the active window with controls for the selection (Fonts, Colors, Inspector).

- Short noun title; the menu item says "Show Inspector", not "Show Inspector Panel". Keep the title bar so people can move it.
- No minimize button. Not in the Window menu's list; show/hide lives in View or Window.
- App active: panels come to front. App inactive: they hide (`hidesOnDeactivate`).
- HUD style (`.hudWindow`) only in media apps, when a normal panel would hide essential content and few controls are needed.
- A Spotlight-style quick panel or corner card is another kind: borderless, non-activating, closes on `resignKey`, `hidesOnDeactivate = false`. Code: `QuickPanel` in [swiftui-appkit.md](swiftui-appkit.md).
- Gotcha (verify on a real screen): controls in a non-activating panel of an inactive app may draw the inactive (gray) accent look. Custom button styles are then justified (PRN-5), but they must handle Increase Contrast, focus and hover themselves.

AppKit flags: `.utilityWindow` mask, `isFloatingPanel`, `hidesOnDeactivate`, `becomesKeyOnlyIfNeeded`.

## Sources

- HIG pages under https://developer.apple.com/design/human-interface-guidelines/ : windows, toolbars, sidebars, split-views, sheets, alerts, popovers, panels, search-fields, the-menu-bar
- Docs: [SceneBuilder](https://developer.apple.com/documentation/swiftui/scenebuilder), [UtilityWindow](https://developer.apple.com/documentation/swiftui/utilitywindow), [NSPanel](https://developer.apple.com/documentation/appkit/nspanel), [NSAlert](https://developer.apple.com/documentation/appkit/nsalert)
- WWDC25 sessions: 310 Build an AppKit app with the new design, 323 Build a SwiftUI app with the new design, 356 Get to know the new design system, 359 Design foundations from idea to interface: https://developer.apple.com/videos/play/wwdc2025/<number>/
- WWDC26-102 macOS 27 design changes (session summary; verify on a shipping build).
- Inspector toggle placement across macOS 26: https://developer.apple.com/forums/thread/795561
- Parts adapted from BAMA by Dave Ebbelaar (MIT); see THIRD_PARTY_NOTICES.md.
