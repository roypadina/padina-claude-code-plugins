# Mac design rules

Master checklist for build and review modes. Each line is checkable on a screenshot or in code; the file after the arrow holds detail, code and sources.

Format: `ID` rule. `severity` · version gate (only when version-specific) · [source] → topic file.

- **Severity** (default; change it with a reason): `P1` broken (inaccessible, data loss, wrong platform behaviour, crash, compile error, dead end). `P2` clearly non-native or confusing. `P3` polish.
- **Sources:** `[HIG <page>]` Human Interface Guidelines · `[WWDCyy-n]` session · `[Docs]` Apple API docs (docs JSON) · `[Forum]` Apple Developer Forums repro · `[Comm]` community repro · `[House]` house convention, never presented as Apple's.
- **Versions:** `macOS 26+` = the API or behaviour starts there.
- **Terms:** status item = the app's menu bar icon. Menu-bar-only app = `LSUIElement`, no Dock icon. Panel = floating auxiliary window (`NSPanel`, `UtilityWindow`). Glass = Liquid Glass.
- IDs never change. A new rule takes the next free number in its area.

## PRN · Principles and hierarchy

- **PRN-1** Write the design plan (archetype, structure, entry points, command map, states, permissions, deployment floor, one feeling) before the first view. `P2` · [House] → native-feel.md
- **PRN-2** Make every screen answer: where am I, what can I do, where can I go; the key item wins a squint test. `P2` · [WWDC25-359] → native-feel.md
- **PRN-3** Cut each feature, control and setting that does not earn people's time. `P3` · [HIG Design principles] → native-feel.md
- **PRN-4** Keep main actions visible; never hide them in one More menu to look minimal. `P2` · [WWDC26-250] → native-feel.md
- **PRN-5** Use stock components first; custom chrome needs a code comment with the reason and keeps menus, keys, text system and accessibility. `P2` · [Comm] → native-feel.md

## STR · Structure, archetype, entry points

- **STR-1** Pick one archetype: sidebar window, single-window/document, menu bar extra, quick-capture panel, or utility/HUD. `P2` · [House] → native-feel.md
- **STR-2** Build from standard structures (`NavigationSplitView`, `.toolbar`, `.searchable`, `.inspector`, `Settings`, `MenuBarExtra`). `P2` · [WWDC25-323] → native-feel.md
- **STR-3** Navigation in the sidebar (none if one level deep), global actions in the toolbar, selection details in an inspector. `P2` · [HIG Sidebars] → native-feel.md
- **STR-4** Design the small entry points first: global shortcut, status item, quick panel, drop on Dock icon, Share, Services. `P3` · [House] → native-feel.md
- **STR-5** Quick-capture panel: one input; a hotkey opens it, Return saves and closes at once (with Undo), Escape closes. `P2` · [House] → native-feel.md
- **STR-6** Offer an automation surface: App Intents, a URL scheme, AppleScript or Services. `P3` · [Comm] → native-feel.md

## NAT · Native feel vs web, Electron, iOS

- **NAT-1** Keep the arrow cursor over buttons and rows; the pointing hand is for links only. `P2` · [Comm] → native-feel.md
- **NAT-2** Use system scrolling and scroll bars; never restyle, hide or re-tune them. `P2` · [HIG Scroll views] → native-feel.md
- **NAT-3** Edit text in system text views so Option-arrow, Control-A/E/K, spelling, text replacement and Undo Typing work. `P2` · [Comm] → native-feel.md
- **NAT-4** No iOS idioms: 44 pt targets, bottom tab bar, floating + button, large titles, hamburger, pull-to-refresh, swipe-only actions. `P2` · [HIG Designing for macOS] → native-feel.md
- **NAT-5** Use native menus, popovers and tooltips (they may extend past the window), never web-drawn ones. `P2` · [Comm] → native-feel.md
- **NAT-6** Show a usable window about 1 s after cold launch; a hotkey panel appears in the same frame (keep it built). `P2` · [Comm] → native-feel.md
- **NAT-7** Wire Print and Export as PDF for document-like content, or remove them; never enabled and dead. `P3` · [Comm] → native-feel.md
- **NAT-8** A web-view surface still gets native menus, keys, IME, context menus and accessibility. `P2` · [Comm] → native-feel.md

## GLS · Liquid Glass and materials

- **GLS-1** Glass only on the navigation and control layer; never on rows, cards or document content. `P2` · macOS 26+ · [HIG Materials] → design-language.md
- **GLS-2** Remove custom backgrounds, scrims and `NSVisualEffectView` behind toolbars, sidebars, inspectors, sheets and popovers. `P2` · macOS 26+ · [WWDC25-310] → design-language.md
- **GLS-3** No glass on glass: apply `glassEffect` to the control, not its subviews; group neighbours in `GlassEffectContainer`. `P2` · macOS 26+ · [WWDC25-356] → design-language.md
- **GLS-4** Regular glass by default; clear glass only over rich media, with a ~35% dark dim over bright media. `P2` · macOS 26+ · [HIG Materials] → design-language.md
- **GLS-5** Tint glass only on the one primary action, and only to carry meaning. `P2` · macOS 26+ · [HIG Color] → design-language.md
- **GLS-6** Interactive glass (`.interactive()`) only on custom controls, sparingly. `P3` · macOS 26+ · [WWDC26-269] → design-language.md
- **GLS-7** Never plan a glass opt-out (`UIDesignRequiresCompatibility`); Xcode 27 builds always get the new design. `P2` · [WWDC26-102] → design-language.md
- **GLS-8** At rest keep text and controls out from under glass; extend art with `backgroundExtensionEffect()`. `P2` · macOS 26+ · [HIG Layout] → design-language.md
- **GLS-9** Separate floating bars from content with the automatic scroll edge effect (one per pane), never a solid band. `P2` · macOS 26+ · [HIG Scroll views] → design-language.md
- **GLS-10** Pick materials by purpose (`.regularMaterial` family, semantic `NSVisualEffectView.Material`), never deprecated `.light`/`.dark`. `P3` · [Docs] → design-language.md
- **GLS-11** Test custom glass at both ends of the transparency setting (26.1 Clear/Tinted, 27 slider), with Reduce Transparency and Increase Contrast. `P2` · macOS 26.1+ · [WWDC26-102] → design-language.md

## CLR · Color, dark mode, contrast

- **CLR-1** Use semantic colors (`.primary`, `.secondary`, `.separator`, `labelColor`); no fixed white, black, gray or hex in chrome or text; never repurpose one. `P2` · [HIG Color] → design-language.md
- **CLR-2** Define custom colors as Color Sets with Any, Dark and High Contrast appearances, or `NSColor(name:dynamicProvider:)`. `P2` · [HIG Color] → design-language.md
- **CLR-3** One accent from the `AccentColor` asset; the user's system accent overrides it unless set to Multicolor. `P3` · [HIG Color] → design-language.md
- **CLR-4** Never show state by color alone: add a shape or a word; honor Differentiate Without Color. `P1` · [HIG Accessibility] → design-language.md
- **CLR-5** Text contrast ≥ 4.5:1 up to 17 pt, ≥ 3:1 at 18 pt or bold, in light, dark and Increase Contrast. `P1` · [HIG Accessibility] → design-language.md
- **CLR-6** Follow the system appearance: no Light/Dark picker by default, no `.preferredColorScheme` outside previews. `P2` · [HIG Dark Mode] → design-language.md
- **CLR-7** Design dark mode as its own palette, not an inversion; check every surface in both modes. `P2` · [HIG Dark Mode] → design-language.md
- **CLR-8** Accent text: deep shade in light, light shade in dark; text on an accent fill uses an on-accent color, not fixed white. `P2` · [House] → design-language.md
- **CLR-9** Never lower contrast on hover or press; text over photos or video sits on a scrim. `P2` · [House] → design-language.md

## TYP · Typography

- **TYP-1** Use macOS text styles (Body 13 pt, Headline bold 13, Callout 12, Subheadline 11, Caption 10); nothing below 10 pt, no iOS sizes. `P2` · [HIG Typography] → design-language.md
- **TYP-2** No Ultralight, Thin or Light weights in interface text. `P2` · [HIG Typography] → design-language.md
- **TYP-3** Never rely on `dynamicTypeSize` (no effect on macOS); reading apps add View > Bigger/Smaller. `P2` · [Docs] → design-language.md
- **TYP-4** Never hand-set tracking or kerning on system text. `P3` · [HIG Typography] → design-language.md
- **TYP-5** `.monospacedDigit()` for changing numbers, `.monospaced()` for code. `P3` · [Docs] → design-language.md
- **TYP-6** Left-align alert and onboarding body text. `P3` · macOS 26+ · [WWDC25-356] → design-language.md
- **TYP-7** Section headers in title case, never typed in all caps. `P3` · macOS 26+ · [Docs] → design-language.md

## LAY · Layout, spacing, shape

- **LAY-1** Size controls with `.controlSize`, never fixed heights; standard controls are ~22–28 pt tall. `P2` · [WWDC25-310] → design-language.md
- **LAY-2** Click targets ≥ 20×20 pt (28×28 default), ~12 pt around bezeled and ~24 pt around borderless controls. `P2` · [HIG Accessibility] → design-language.md
- **LAY-3** Nested corners are concentric (`ConcentricRectangle`, `cornerConfiguration`); fixed radii only on small standalone parts. `P3` · macOS 26+ · [WWDC25-356] → design-language.md
- **LAY-4** Mini–medium controls are rounded rectangles, large ones capsules; dense layouts keep capsules for the standout action. `P3` · macOS 26+ · [WWDC25-356] → design-language.md
- **LAY-5** Never mask window corners or hard-code a window radius; keep content out of corners via the safe area. `P2` · macOS 26+ · [WWDC25-310] → design-language.md
- **LAY-6** Key content top-leading; no controls or critical info on a window's or sidebar's bottom edge. `P2` · [HIG Layout] → design-language.md
- **LAY-7** Take spacing from system containers (`Form`, `Grid`, default stack spacing); any fixed grid is a house convention. `P3` · [House] → design-language.md
- **LAY-8** Line up trailing values, use one date format per view, show each status once per row. `P3` · [House] → design-language.md

## SYM · SF Symbols, toolbar and menu icons

- **SYM-1** SF Symbols or custom symbols for toolbar, sidebar and menu icons, never bitmaps. `P2` · [HIG Icons] → design-language.md
- **SYM-2** Standard symbols for standard actions (Copy `document.on.document`, Rename `pencil`, Delete `trash`, Share `square.and.arrow.up`, More `ellipsis`; full table in the topic file). `P2` · [HIG Icons] → design-language.md
- **SYM-3** Match symbol weight to adjacent text; change emphasis with `imageScale`. `P3` · [HIG SF Symbols] → design-language.md
- **SYM-4** Outline in toolbars, lists and menus; fill for selection or emphasis; slash for unavailable; no custom selected images. `P3` · [HIG SF Symbols] → design-language.md
- **SYM-5** Gate or replace symbols newer than the deployment target (check in the SF Symbols app). `P1` · [HIG SF Symbols] → design-language.md
- **SYM-6** Animate a symbol only to say something, one per region, no loops in lists, none under Reduce Motion. `P3` · macOS 14+ · [HIG SF Symbols] → design-language.md
- **SYM-7** Variable color for levels, hierarchical for depth; no gradient rendering at 11–13 pt; custom symbols from the SF Symbols template. `P3` · [HIG SF Symbols] → design-language.md

## WIN · Windows

- **WIN-1** Pick the scene: `WindowGroup` (many), `Window` (one), `UtilityWindow` (palette, 15+), `DocumentGroup`, `Settings`; stable `id`s. `P2` · macOS 13+ · [Docs] → windows-and-chrome.md
- **WIN-2** Never draw a custom title bar, frame or traffic lights; use `.hiddenTitleBar` with the real buttons. `P1` · [HIG Windows] → windows-and-chrome.md
- **WIN-3** Keep your controls clear of the traffic lights; inset with the safe area, not a fixed padding. `P2` · [HIG Windows] → windows-and-chrome.md
- **WIN-4** Title windows by content (< ~15 characters), never the app name; say "window", never "scene". `P3` · [HIG Windows] → windows-and-chrome.md
- **WIN-5** A subtitle (count, date) shows on every page or none. `P3` · [HIG Toolbars] → windows-and-chrome.md
- **WIN-6** Never open new windows by default; offer Open in New Window in File and context menus. `P2` · [HIG Windows] → windows-and-chrome.md
- **WIN-7** Set `.defaultSize` and a tested minimum (`.frame(minWidth:minHeight:)`, `.contentMinSize`) where nothing overlaps. `P2` · macOS 13+ · [Docs] → windows-and-chrome.md
- **WIN-8** Restore frames, selection and scroll on relaunch (`@SceneStorage`, `setFrameAutosaveName`); UI state only, never data. `P2` · [HIG Launching] → windows-and-chrome.md
- **WIN-9** `.restorationBehavior(.disabled)` for windows that must not return; `.defaultLaunchBehavior(.presented)` for a welcome window. `P3` · macOS 15+ · [Docs] → windows-and-chrome.md
- **WIN-10** Dim custom chrome in inactive windows (`\.appearsActive`); never on HUDs or non-activating panels. `P2` · [Docs] → windows-and-chrome.md
- **WIN-11** System tabs for document-like windows, never a custom tab bar; File has Close Tab and Close Window. `P2` · [HIG The menu bar] → windows-and-chrome.md
- **WIN-12** Main windows enter full screen (Control-Command-F); Zoom never does; fixed-job windows disable resize and full screen (15+ modifiers). `P2` · [HIG The menu bar] → windows-and-chrome.md
- **WIN-13** Decide what closing the last window does; a Dock click with no windows reopens the main window. `P2` · [Docs] → windows-and-chrome.md
- **WIN-14** Quit without asking unless typed work would be lost. `P2` · [House] → windows-and-chrome.md
- **WIN-15** Never float a normal window; floating levels are for panels and HUDs. `P2` · [House] → windows-and-chrome.md

## TBR · Toolbars

- **TBR-1** At most three groups, split with `ToolbarSpacer(.fixed)` (26+); a fixed spacer between text and symbol buttons. `P3` · [HIG Toolbars] → windows-and-chrome.md
- **TBR-2** Each item sits over the column it acts on; nothing of your own over the sidebar; inspector toggle trailing. `P2` · [House] → windows-and-chrome.md
- **TBR-3** Borderless monochrome symbols as `Button("Title", systemImage:)` with a verb-first `.help` ending in the shortcut. `P2` · [HIG Toolbars] → windows-and-chrome.md
- **TBR-4** At most one prominent action, trailing, only for a completing action (Done, Send). `P2` · [HIG Toolbars] → windows-and-chrome.md
- **TBR-5** No custom overflow menu; `.visibilityPriority(.high)` on must-stay items; test at minimum width (unfit items vanish). `P2` · macOS 26.1+ · [Docs] → windows-and-chrome.md
- **TBR-6** No iOS-only toolbar API in macOS targets (`ToolbarOverflowMenu`, `.topBar*`, `.bottomBar`, `.largeTitle`, `.searchToolbarBehavior(.minimize)`). `P1` · [Docs] → windows-and-chrome.md
- **TBR-7** Keep the system sidebar toggle and one inspector toggle; never a second of either. `P2` · [House] → windows-and-chrome.md
- **TBR-8** Customizable toolbar (`.toolbar(id:)` + `ToolbarCommands()`) in apps kept open for hours. `P3` · [HIG Toolbars] → windows-and-chrome.md
- **TBR-9** No Settings button, switch, checkbox or radio button in a toolbar; Back and Close are symbols, not words. `P2` · [HIG Toolbars] → windows-and-chrome.md

## SBR · Sidebars, split views, inspectors, search

- **SBR-1** Sidebar holds top-level areas, at most two levels; deeper data goes in a content column. `P2` · [HIG Sidebars] → windows-and-chrome.md
- **SBR-2** Sidebar visible by default, collapses when narrow, has View > Show/Hide Sidebar (`SidebarCommands()`). `P2` · [HIG Sidebars] → windows-and-chrome.md
- **SBR-3** Never hard-code sidebar row height or glyph size; follow `\.sidebarRowSize`. `P2` · [HIG Sidebars] → windows-and-chrome.md
- **SBR-4** Sidebar icons take the accent color; fixed colors only with meaning. `P3` · [HIG Sidebars] → windows-and-chrome.md
- **SBR-5** No action rows ("New…") in the sidebar list. `P2` · [WWDC25-359] → windows-and-chrome.md
- **SBR-6** Keep the selection highlighted in every pane that leads to the detail. `P2` · [HIG Split views] → windows-and-chrome.md
- **SBR-7** Column widths via `.navigationSplitViewColumnWidth(min:ideal:max:)`; column visibility restored per window. `P3` · macOS 13+ · [Docs] → windows-and-chrome.md
- **SBR-8** Inspector = `.inspector` on the split view + `InspectorCommands()`; it tracks the selection; no second shortcut. `P3` · macOS 14+ · [Docs] → windows-and-chrome.md
- **SBR-9** One search location, placed by scope: trailing toolbar (window), top of sidebar (sidebar), Search item (big apps). `P2` · [HIG Searching] → windows-and-chrome.md
- **SBR-10** Command-F focuses search, Escape clears, results filter live, no results → `ContentUnavailableView.search`. `P2` · macOS 14+ (`searchFocused` 15+) · [HIG Search fields] → windows-and-chrome.md

## MOD · Sheets, alerts, popovers, panels

- **MOD-1** Use the lightest surface: inline, inspector, popover, panel, sheet, window, then alert. `P2` · [House] → windows-and-chrome.md
- **MOD-2** One sheet or popover at a time; never a sheet from a sheet or a popover from a popover. `P2` · [HIG Sheets] → windows-and-chrome.md
- **MOD-3** Sheets for short tasks tied to the window; long tasks get a window, repeated input-and-watch a panel. `P2` · [HIG Sheets] → windows-and-chrome.md
- **MOD-4** Sheets have Cancel plus a verb or Done, never Done alone; Return = default, Escape and Command-Period cancel. `P2` · [HIG Sheets] → windows-and-chrome.md
- **MOD-5** Size sheets and popovers to content (`.presentationSizing(.fitted)`); scroll bars only on overflow. `P3` · macOS 15+ · [HIG Sheets] → windows-and-chrome.md
- **MOD-6** Ask before closing a sheet only when typed input would be lost. `P2` · [House] → windows-and-chrome.md
- **MOD-7** Alerts only for critical, actionable info: never at launch, for "Saved", or for undoable actions. `P2` · [HIG Alerts] → windows-and-chrome.md
- **MOD-8** Alert title says what happened and why (never "Error"); verb buttons, no Yes/No, OK only if informational, Cancel says "Cancel". `P2` · [HIG Alerts] → windows-and-chrome.md
- **MOD-9** Default button trailing, never Cancel; destructive role and caution icon only for loss the person did not choose. `P2` · [HIG Alerts] → windows-and-chrome.md
- **MOD-10** Repeating non-critical alerts get a suppression checkbox and a Settings switch to restore them. `P3` · macOS 14+ · [HIG Alerts] → windows-and-chrome.md
- **MOD-11** Attach alerts to their window (`.alert`, `beginSheetModal(for:)`); `runModal()` only when no window applies. `P3` · [House] → windows-and-chrome.md
- **MOD-12** Popover arrow points at its source; never a warning in a popover; save its work on outside-click close. `P2` · [HIG Popovers] → windows-and-chrome.md
- **MOD-13** Panels: noun title, no minimize, hidden when the app deactivates, not in the Window list; HUD style only in media apps. `P2` · [HIG Panels] → windows-and-chrome.md

## SET · Settings window

- **SET-1** App > Settings… (Command-Comma) opens a `Settings` scene; never a sheet, main-window page or toolbar button (menu-bar-only apps: MBX-16). `P2` · [HIG Settings] → settings.md
- **SET-2** One tab per topic with a toolbar icon, title following the tab; a single pane has no tabs and the title "<App> Settings". `P2` · [HIG Settings] → settings.md
- **SET-3** Reopen on the last pane; non-customizable toolbar; minimize and zoom dimmed. `P3` · [HIG Settings] → settings.md
- **SET-4** Changes apply at once; no Save, Apply or OK button. `P2` · [House] → settings.md
- **SET-5** Few app-wide options; view options stay in the view or View menu; no copies of system settings. `P2` · [HIG Settings] → settings.md
- **SET-6** One grouped `Form` per tab; help text in section footers; labels state the on state, never "Enable…". `P3` · [House] → settings.md
- **SET-7** Mini switches in grouped-form rows, a regular switch only for a master setting; radio group for 2–5 choices, else a pop-up. `P3` · [HIG Toggles] → settings.md
- **SET-8** Each pane sizes to its content (`.windowResizability(.contentSize)`); no fixed Apple width exists. `P3` · [Docs] → settings.md
- **SET-9** Disabled settings say why in the footer; destructive resets sit last, with confirmation or Undo. `P2` · [House] → settings.md

## MNU · Menu bar, commands, context and Dock menus

- **MNU-1** Standard order: App, File, Edit, Format, View, app menus, Window, Help; Window and Help stay even with one window. `P2` · [HIG The menu bar] → menus-and-commands.md
- **MNU-2** Every command is in the menu bar, including every toolbar, context-menu, Dock and hover action. `P2` · [HIG The menu bar] → menus-and-commands.md
- **MNU-3** App menu: About, Settings… (Command-Comma), app items, Services, Hide, Hide Others, Show All, Quit <App>. `P2` · [HIG The menu bar] → menus-and-commands.md
- **MNU-4** File: "New <Noun>", Open…, Open Recent, Close, Duplicate (not Save As), Export As… for other formats. `P3` · [HIG The menu bar] → menus-and-commands.md
- **MNU-5** Keep standard Edit items working; never replace `.pasteboard`, `.undoRedo` or `.textEditing` with an empty group. `P1` · [Docs] → menus-and-commands.md
- **MNU-6** View holds Show/Hide Sidebar, Toolbar, Inspector and Enter Full Screen, labels following state. `P2` · [HIG The menu bar] → menus-and-commands.md
- **MNU-7** Labels: verb-first title case, no articles; "…" (U+2026, not "...") only when more input follows; "Show Fonts", not "Show Fonts Panel". `P3` · [HIG Menus] → menus-and-commands.md
- **MNU-8** Menu bar items that do not apply stay visible and dimmed. `P2` · [HIG Menus] → menus-and-commands.md
- **MNU-9** Command state comes from `.focusedSceneValue` at the window root; no enabled items that do nothing. `P2` · [Docs] → menus-and-commands.md
- **MNU-10** Menu icons sparingly, all or none per group; 27 hides them unless opted in (`.labelStyle(.titleAndIcon)`). `P3` · macOS 27+ · [HIG Menus] → menus-and-commands.md
- **MNU-11** Submenus one level, about five items; Option items one modifier, menu bar only, never the only path. `P3` · [HIG Menus] → menus-and-commands.md
- **MNU-12** Context menus: items for the clicked item only, frequent first, ~3 groups, no shortcuts, inapplicable items hidden. `P2` · [HIG Context menus] → menus-and-commands.md
- **MNU-13** Same context menu on every item of a kind; lists and tables use `.contextMenu(forSelectionType:)`. `P2` · macOS 13+ · [HIG Context menus] → menus-and-commands.md
- **MNU-14** Dock menu (`applicationDockMenu`) with a few plain items when actions are useful from the background. `P3` · [HIG Dock menus] → menus-and-commands.md

## KBD · Keyboard, shortcuts, focus, hotkeys

- **KBD-1** Every frequent command has a shortcut, shown in its menu, its tooltip, and a list in Settings or Help. `P2` · [HIG Keyboards] → menus-and-commands.md
- **KBD-2** Never repurpose a standard or system shortcut, or add a modifier to one for an unrelated command. `P1` · [HIG Keyboards] → menus-and-commands.md
- **KBD-3** Return default, Escape cancel, Command-Period cancel, Delete remove, Space preview, arrows move, Option-Command-F search. `P2` · [HIG Keyboards] → menus-and-commands.md
- **KBD-4** No Option or Shift with punctuation keys; in-app shortcuts use key equivalents, never raw key codes (global hotkeys need key codes). `P3` · [HIG Keyboards] → menus-and-commands.md
- **KBD-5** Every shortcut shows visible feedback in the same frame. `P2` · [House] → menus-and-commands.md
- **KBD-6** Text fields get editing keys first: no Delete/Return/arrow menu shortcuts that fire while typing; monitors pass `NSText` through. `P1` · [Comm] → menus-and-commands.md
- **KBD-7** Global hotkeys are recordable and clearable; default none or Command/Control-based, never Option-only or a system combo. `P2` · [Forum] → menus-and-commands.md
- **KBD-8** Register hotkeys once at launch with `RegisterEventHotKey` or `KeyboardShortcuts`; report registration failure. `P2` · [Comm] → menus-and-commands.md
- **KBD-9** New items take focus; non-typing windows open with no field focused (`noInitialFocus()`, swiftui-appkit.md); typing panels focus their field. `P3` · [House] → menus-and-commands.md

## MBX · Menu-bar (status item) apps

- **MBX-1** A click opens a menu; use a panel only when content needs a list, chart, field or search. `P2` · [HIG The menu bar] → menu-bar-apps.md
- **MBX-2** `NSStatusItem` + popover or panel when it must open from code, handle right-click or keep focus elsewhere. `P2` · macOS 13+ · [Docs] → menu-bar-apps.md
- **MBX-3** `.menu` style holds only menu content (Button, Toggle, Picker, Divider, Menu, Text) and does not refresh while open. `P2` · [Comm] → menu-bar-apps.md
- **MBX-4** Status icon is a template (black and clear) or SF Symbol, sized by the system; never a full-color idle icon. `P2` · [HIG The menu bar] → menu-bar-apps.md
- **MBX-5** Icon states differ by shape (outline, fill, badge, slash), never color alone; `appearsDisabled` for paused. `P2` · [HIG SF Symbols] → menu-bar-apps.md
- **MBX-6** Status button has an accessibility description and a tooltip with name and state. `P1` · [HIG The menu bar] → menu-bar-apps.md
- **MBX-7** Status text is ~4–6 characters with monospaced digits; details go in the menu. `P3` · [Comm] → menu-bar-apps.md
- **MBX-8** The status item is never the only way in: reopening the app from Finder or Spotlight shows its UI; offer a global hotkey too. `P1` · [HIG The menu bar] → menu-bar-apps.md
- **MBX-9** A Settings toggle shows or hides the icon; with `.removalAllowed` the app keeps running (a `MenuBarExtra`-only app quits); stable `autosaveName`. `P2` · [Docs] → menu-bar-apps.md
- **MBX-10** Never detect notch hiding (`isVisible` stays true) or move other apps' items; users can turn icons off in System Settings. `P2` · macOS 26+ · [Forum] → menu-bar-apps.md
- **MBX-11** Status menu: actions, status, then Settings… (Command-Comma), About, and Quit <App> (Command-Q) last. `P2` · [HIG The menu bar] → menu-bar-apps.md
- **MBX-12** A panel-style extra still offers Settings and Quit (gear menu and right-click). `P1` · [House] → menu-bar-apps.md
- **MBX-13** Left click opens the primary UI; right-click and Control-click open a menu (on mouse-up). `P2` · [Comm] → menu-bar-apps.md
- **MBX-14** Handle clicks with the button's target-action (or 27's `expandedInterfaceDelegate`), never a local event monitor. `P2` · [Forum] → menu-bar-apps.md
- **MBX-15** Switch to `.regular` before showing a window and back to `.accessory` after the last closes; test `LSUIElement` from a clean launch. `P2` · [Comm] → menu-bar-apps.md
- **MBX-16** Open Settings via your own window or the hidden-window `openSettings` workaround, never `SettingsLink` in `MenuBarExtra`; verify per macOS. `P1` · macOS 14+ · [Comm] → menu-bar-apps.md
- **MBX-17** Login item via `SMAppService.mainApp`: off by default, user action only, status re-read, `.requiresApproval` handled; toggle in Settings. `P2` · macOS 13+ · [Docs] → menu-bar-apps.md
- **MBX-18** First launch: one small welcome window showing where the icon is, another way in, login item and hotkey. `P2` · [House] → menu-bar-apps.md
- **MBX-19** Refresh at a cadence fit for the data with `Timer.tolerance`, paused in sleep; show data age, never stale values as live. `P2` · [House] → menu-bar-apps.md
- **MBX-20** Animate the icon only during real activity, honor Reduce Motion, no SwiftUI animation in the status item. `P3` · [Forum] → menu-bar-apps.md
- **MBX-21** Offer a `ControlWidget` when the core is one toggle wanted in Control Center or the menu bar. `P3` · macOS 26+ · [Docs] → menu-bar-apps.md

## FLW · Onboarding, permissions, states, notifications, words

- **FLW-1** No tour, carousel or launch splash; first launch lands in a usable empty state with a first action. `P2` · [HIG Onboarding] → ux-flows.md
- **FLW-2** Required setup is short and skippable, never returns once skipped, and has no license, rating or purchase prompt. `P2` · [HIG Onboarding] → ux-flows.md
- **FLW-3** Teach with TipKit tips at the real control, shown daily or less often. `P3` · macOS 14+ · [Docs] → ux-flows.md
- **FLW-4** Never block first use on a download; show determinate progress in place. `P2` · [HIG Onboarding] → ux-flows.md
- **FLW-5** Ask for a permission at first use of its feature, never at launch unless the app's one job needs it. `P1` · [HIG Privacy] → ux-flows.md
- **FLW-6** Ask for the narrowest access: open panel over Full Disk Access, `SCContentSharingPicker` over Screen Recording. `P2` · [HIG Privacy] → ux-flows.md
- **FLW-7** Every protected resource has its Info.plist usage string (missing = crash): one active sentence on how and why. `P1` · [HIG Privacy] → ux-flows.md
- **FLW-8** A pre-permission explainer has one button to the system prompt; no Skip or Cancel, no fake system alert. `P2` · [HIG Privacy] → ux-flows.md
- **FLW-9** Settings-only grants (Accessibility, Input Monitoring, Screen Recording): reason, text state, one deep-linked Open System Settings button; list all in Settings. `P1` · [House] → ux-flows.md
- **FLW-10** Check with non-prompting calls (`AXIsProcessTrusted`, `CGPreflight…`); re-check on activation; poll ≤ 1/s only while visible. `P2` · [Docs] → ux-flows.md
- **FLW-11** Denied features stay visible and disabled with the reason; a grant that needs a relaunch shows a Restart button. `P2` · [Forum] → ux-flows.md
- **FLW-12** Read the pasteboard only on a user paste or action, never on a timer. `P2` · macOS 15.4+ · [Docs] → ux-flows.md
- **FLW-13** Stop event taps when Accessibility trust is lost; prefer `.listenOnly`. `P1` · [Forum] → ux-flows.md
- **FLW-14** Every view has empty, loading, error, offline and partial states; empty = `ContentUnavailableView` + first action. `P2` · macOS 14+ · [HIG Loading] → ux-flows.md
- **FLW-15** Show cached or placeholder content at once and load in the background. `P2` · [HIG Loading] → ux-flows.md
- **FLW-16** Progress is determinate when length is known, never switches type, names verb and count, offers Cancel when safe. `P3` · [HIG Progress indicators] → ux-flows.md
- **FLW-17** Failures show inline with Retry, not an alert; partial failures keep what worked; offline is one status line. `P2` · [HIG Alerts] → ux-flows.md
- **FLW-18** Never put an error or the only path to an action in a timed toast; toasts are announced to VoiceOver. `P1` · [HIG Accessibility] → ux-flows.md
- **FLW-19** Ask for notification permission after the first action that benefits, never at launch. `P2` · [Docs] → ux-flows.md
- **FLW-20** Set `interruptionLevel`; title says what changed, no app name, ≤ 4 verb actions, none named "Open". `P3` · macOS 12+ · [HIG Notifications] → ux-flows.md
- **FLW-21** No notification for what is visible or just done; Dock badge = unread notification count only. `P3` · [HIG Notifications] → ux-flows.md
- **FLW-22** Buttons and menu items: verb-first title case; messages sentence case; "click", never "tap". `P3` · [HIG Writing] → ux-flows.md
- **FLW-23** Errors say what happened, why and what to do; no blame, codes or "Oops". `P2` · [HIG Alerts] → ux-flows.md

## UND · Undo

- **UND-1** Prefer Undo to confirmation for common actions, deletes included; confirm only rare irreversible loss. `P2` · [HIG Undo and redo] → ux-flows.md
- **UND-2** Edits, deletes, drops, pastes, reorders and renames are undoable, one step per gesture, with named actions. `P2` · [HIG Undo and redo] → ux-flows.md
- **UND-3** After Undo, reveal the affected item (scroll to it, select it). `P3` · [HIG Undo and redo] → ux-flows.md
- **UND-4** One-click destructive actions in lists and Settings offer Undo in place; no undo depth cap. `P2` · [HIG Undo and redo] → ux-flows.md

## DND · Drag and drop, pasteboard, share

- **DND-1** Drag and drop where it makes sense, always with a menu or keyboard alternative. `P2` · [HIG Drag and drop] → ux-flows.md
- **DND-2** Drag out meaningful data (text, URL, file), never internal IDs; Copy writes rich and plain types. `P2` · [HIG Drag and drop] → ux-flows.md
- **DND-3** Create files dragged to Finder lazily (`FileRepresentation`, file promises), never at drag start. `P2` · [Docs] → ux-flows.md
- **DND-4** Move within a container, copy between (Option copies); highlight only accepting targets. `P2` · [HIG Drag and drop] → ux-flows.md
- **DND-5** Keep dropped content selected and make every drop undoable. `P2` · [HIG Drag and drop] → ux-flows.md
- **DND-6** On 26+ use `dropDestination(for:isEnabled:action:)`; the `isTargeted:` form (deprecated 27.2 SDK) only on the pre-26 path. `P3` · macOS 26+ · [Docs] → ux-flows.md
- **DND-7** Share (`ShareLink`) in File and context menus where it fits, never the only export. `P3` · [Comm] → ux-flows.md

## LST · Lists, tables, outlines

- **LST-1** Multi-selection everywhere; actions apply to the whole selection; the next row is selected after a delete. `P2` · [House] → swiftui-appkit.md
- **LST-2** Header click sorts (again reverses), columns resize, title-case noun headers, middle truncation, alternating rows. `P2` · [HIG Lists and tables] → swiftui-appkit.md
- **LST-3** Double-click or Return opens (`primaryAction:`), Delete removes (`.onDeleteCommand`), type-select works. `P2` · macOS 13+ · [Docs] → swiftui-appkit.md
- **LST-4** Outlines remember expanded rows; Option-click expands all children. `P3` · [HIG Outline views] → swiftui-appkit.md
- **LST-5** SwiftUI `Table` up to low thousands of rows; `NSTableView`/`NSOutlineView` for large, live or editable data. `P2` · [Comm] → swiftui-appkit.md
- **LST-6** Selectable rows come from `List` or `Table`; custom rows get no selection emphasis or menu highlight. `P3` · [Comm] → swiftui-appkit.md

## A11Y · Accessibility

- **A11Y-1** Label every icon-only control (`Button("Share", systemImage:)` + `.labelStyle(.iconOnly)`). `P1` · [HIG VoiceOver] → accessibility.md
- **A11Y-2** Anything clickable is a `Button`; a tap-gesture view needs the button trait, focus and Space/Return. `P1` · [HIG Accessibility] → accessibility.md
- **A11Y-3** Labels are the visible words without the role; state goes in the value; hints only when needed. `P2` · [HIG VoiceOver] → accessibility.md
- **A11Y-4** Rows read as one element (`children: .combine`) with row and hover actions as named actions. `P2` · [HIG VoiceOver] → accessibility.md
- **A11Y-5** Decorative images hidden; section titles are headers; every window has a unique title. `P3` · [HIG VoiceOver] → accessibility.md
- **A11Y-6** Announce changes without a click (`AccessibilityNotification.Announcement`), at most every 0.3 s. `P2` · macOS 14+ · [WWDC26-220] → accessibility.md
- **A11Y-7** Custom controls have adjustable or named actions; drag-, hover- and gesture-only actions also exist as actions and commands. `P1` · [WWDC26-220] → accessibility.md
- **A11Y-8** With Keyboard navigation on, Tab reaches every control in reading order, Space activates, no focus traps. `P1` · macOS 14+ · [HIG Accessibility] → accessibility.md
- **A11Y-9** Keep the focus ring; `.focusEffectDisabled()` only with an equally visible custom ring. `P1` · macOS 14+ · [Docs] → accessibility.md
- **A11Y-10** Reduce Motion: slides, zooms, parallax and blur transitions become fades; loops stop. `P2` · [HIG Accessibility] → accessibility.md
- **A11Y-11** Reduce Transparency: custom glass and materials get an opaque fallback with equal contrast. `P2` · [HIG Accessibility] → accessibility.md
- **A11Y-12** Custom controls honor Increase Contrast and, on 27, Show Borders (`accessibilityShowBorders`). `P2` · [WWDC26-102] → accessibility.md
- **A11Y-13** `accessibilityInputLabels` when the visible label is long or an icon (Voice Control). `P3` · [Docs] → accessibility.md
- **A11Y-14** Custom `NSView`s expose element, role, label, value and frame, or `NSAccessibilityElement` children. `P1` · [Docs] → accessibility.md
- **A11Y-15** Truncated text shows its full value in a tooltip; photos and video opt out of Smart Invert. `P3` · [Docs] → accessibility.md
- **A11Y-16** Use assistive-technology detection only for small tweaks, never to gate a feature. `P2` · [Docs] → accessibility.md
- **A11Y-17** `performAccessibilityAudit()` in a UI test per main window state, plus manual VoiceOver and keyboard passes. `P3` · macOS 14+ · [Docs] → accessibility.md

## ICN · App, document and menu-bar icons

- **ICN-1** App icon is an Icon Composer `.icon` from square, unmasked, full-bleed 1024×1024 layers. `P2` · macOS 26+ · [HIG App icons] → icons.md
- **ICN-2** One simple idea; no baked shadows or gloss, text, photos, screenshots, UI, Apple hardware or SF Symbols. `P2` · [HIG App icons] → icons.md
- **ICN-3** At most four groups, crisp edges, no thin lines; readable at 16 and 32 px. `P3` · [Docs] → icons.md
- **ICN-4** Default, Dark, Clear and Tinted looks keep the same elements, varying only color. `P2` · macOS 26+ · [HIG App icons] → icons.md
- **ICN-5** No flat-only icon (gray plate on 26) and no second app icon set with the same name. `P2` · macOS 26+ · [Comm] → icons.md
- **ICN-6** Render design generations 26 and 27 when supporting 26; never rely on refraction (no effect before 27). `P3` · Xcode 27+ · [Docs] → icons.md
- **ICN-7** Below a 26 target bundle `Assets.car` and the `AppIcon.icns` fallback with `CFBundleIconName` and `CFBundleIconFile`. `P2` · [Docs] → icons.md
- **ICN-8** `applicationIconImage` or Dock tile views only for temporary state (badge, progress). `P3` · [Docs] → icons.md
- **ICN-9** Document types get a document icon (five sizes, nothing in the top-right fold) or the system default. `P3` · [HIG Icons] → icons.md

## IMP · SwiftUI/AppKit implementation and version gates

- **IMP-1** Read the deployment target first; every newer API sits behind `if #available` with a working fallback. `P1` · [Docs] → swiftui-appkit.md
- **IMP-2** Route glass through one helper (`glassSurface(in:)`) with a material fallback below 26. `P2` · macOS 26+ · [Docs] → swiftui-appkit.md
- **IMP-3** Gate macOS 15 window APIs (`windowLevel`, `WindowDragGesture`, window behavior modifiers) on a 14 target; scene modifiers through a plain `some Scene` function (`@SceneBuilder` has no `else`). `P1` · macOS 15+ · [Docs] → swiftui-appkit.md
- **IMP-4** Reach the `NSWindow` with a `viewDidMoveToWindow` probe (`WindowAccessor`), never `NSApp.windows.first` or async guesses. `P2` · [Docs] → swiftui-appkit.md
- **IMP-5** Never replace `window.delegate` in a SwiftUI app; forward through a proxy. `P1` · [Comm] → swiftui-appkit.md
- **IMP-6** `NSApp.activate()` only after a user action; `activate(ignoringOtherApps:)` is deprecated in 27. `P2` · macOS 14+ · [Docs] → swiftui-appkit.md
- **IMP-7** Quick panel = `NSPanel` with `.nonactivatingPanel` in the init mask, `canBecomeKey` true, Escape and resign-key close it. `P1` · [Comm] → swiftui-appkit.md
- **IMP-8** Set `NSHostingView.sizingOptions` on purpose; the default rewrites the window's min and max size. `P2` · macOS 13+ · [Docs] → swiftui-appkit.md
- **IMP-9** `NSViewRepresentable`: create once, diff in `updateNSView` (no binding writes), clean up in `dismantleNSView`. `P2` · [Docs] → swiftui-appkit.md
- **IMP-10** Prefer `.onKeyPress` and the command modifiers to local event monitors; remove every monitor you add. `P2` · macOS 14+ · [Docs] → swiftui-appkit.md
- **IMP-11** `NSTextView` (TextKit 2, never touch `layoutManager`) for code, attachments or big documents; rich `TextEditor` only on 26+. `P2` · macOS 26+ · [Docs] → swiftui-appkit.md
- **IMP-12** Drop to AppKit for menu item badges, section headers and subtitles (`NSMenuItem`, `NSHostingMenu`). `P3` · macOS 14.4+ · [Docs] → swiftui-appkit.md
- **IMP-13** Capture review shots from real windows (`screencapture -l`); not `ImageRenderer` or `CGWindowListCreateImage`. `P3` · [Docs] → swiftui-appkit.md
- **IMP-14** Re-test `@State` class initialisers with side effects when building with Xcode 27. `P2` · [Docs] → swiftui-appkit.md
