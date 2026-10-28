# UX flows

Onboarding, permissions, states, progress, notifications, undo, drag and drop, and writing for a native Mac app. Explains the FLW, UND and DND rules in [rules.md](rules.md).

**When to read this:** you add a first-run flow, a permission, a list or view that can be empty or fail, a notification, an undoable action, a drop target, or any user-facing text. Read only the section you need.

Contents: [Onboarding](#onboarding-and-first-run) · [Permissions](#permissions) · [States](#states) · [Progress](#progress) · [Notifications](#notifications) · [Undo](#undo) · [Drag and drop](#drag-and-drop) · [Copy and Share](#copy-paste-and-share) · [Writing](#writing)

Code compiles with Swift 6 at macOS 14 unless a gate is shown. `AccessState`, `PermissionRow` and `openSystemSettings(_:)` are house code, not SDK. Full HIG text: `hig.sh <topic> --mac`.

## Onboarding and first run

- **FLW-1** Ship no tour, carousel or launch splash. First launch lands in a usable empty state with a visible first action. HIG Onboarding allows a brief splash only as the first page of a required onboarding flow. Teach only what the app adds, never macOS itself.
- **FLW-2** Setup the app cannot work without is short and skippable. A skipped flow never returns; keep it reachable from Help or Settings. No license text, rating prompt or purchase prompt in it.
- **FLW-3** Teach with TipKit tips at the real control (macOS 14+). Call `Tips.configure` once at launch with `.displayFrequency(.daily)`; the default `.immediate` stacks several tips.
- **FLW-4** Never block first use on a download. Show a determinate bar in the content area and let people work.

```swift
import TipKit

struct QuickAddTip: Tip { var title: Text { Text("Add Tasks Faster") } }
// App.init: try? Tips.configure([.displayFrequency(.daily)])
// Control:  Button("Add Task") { … }.popoverTip(QuickAddTip())
```

## Permissions

**FLW-6** Prefer no permission, then a user-driven picker, then a system prompt, then a Settings-only grant.

| Need | Use instead of the broad grant |
|---|---|
| One file or folder | `NSOpenPanel` plus a security-scoped bookmark, not Full Disk Access |
| Pick a window or display | `SCContentSharingPicker` (macOS 14+), not Screen Recording |
| One global shortcut | Carbon hotkey (see [menus-and-commands.md](menus-and-commands.md)), not an event tap |

**FLW-5** Ask when the person first uses the feature, never at launch. Exception: the app's one job needs it. Show the matching state in Settings > Permissions.

### Permission matrix

| Permission | Check (never prompts) | Request | Info.plist key | Settings anchor |
|---|---|---|---|---|
| Accessibility | `AXIsProcessTrusted()` | `AXIsProcessTrustedWithOptions` with prompt option | none | `Privacy_Accessibility` |
| Input Monitoring | `CGPreflightListenEventAccess()` | `CGRequestListenEventAccess()` | none | `Privacy_ListenEvent` |
| Screen Recording | `CGPreflightScreenCaptureAccess()` | `CGRequestScreenCaptureAccess()` | none | `Privacy_ScreenCapture` |
| Full Disk Access | no API | no prompt; link only | none | `Privacy_AllFiles` |
| Files & Folders | per-folder, on access | system prompt on first access | `NSDesktopFolderUsageDescription` and siblings | `Privacy_FilesAndFolders` |
| Automation | `AEDeterminePermissionToAutomateTarget` (10.14) | same call with `askUserIfNeeded: true` | `NSAppleEventsUsageDescription` | `Privacy_Automation` |
| Microphone, Camera | `AVCaptureDevice.authorizationStatus(for:)` | `AVCaptureDevice.requestAccess(for:)` | `NSMicrophoneUsageDescription`, `NSCameraUsageDescription` | `Privacy_Microphone`, `Privacy_Camera` |
| Notifications | `UNUserNotificationCenter.current().notificationSettings()` | `requestAuthorization(options:)` | none | Notifications pane (below) |
| Local Network | no API | first browse prompts | `NSLocalNetworkUsageDescription`, `NSBonjourServices` | pane root only |
| Pasteboard | `NSPasteboard.accessBehavior` (15.4) | system alert on programmatic read | none | `Privacy_Pasteboard` (27, verify) |

The `CG…` calls are macOS 10.15+; `SCContentSharingPicker` is 14.0. Contacts, Calendars, Reminders, Photos, Bluetooth and Speech follow the Microphone pattern.

### Purpose strings and explainers

- **FLW-7** Every protected resource has its usage string in Info.plist. A missing key crashes the app on the request. Write one active sentence in sentence case that says how and why: "Recordings use the microphone to capture your voice." Never "needs access for a better experience".
- **FLW-8** A pre-permission explainer has one button that leads to the system prompt ("Continue"). No Skip, Cancel or "Allow", and never a picture of the system alert. Legal consent is the only exception. Copy order: reason, benefit, what happens without it.

### Settings-only grants

**FLW-9** Accessibility, Input Monitoring and Screen Recording are switched on in System Settings, not in a prompt. Show a row: reason, text state, one button. Call the request API first, or open Settings; never both at once. List every permission in one Settings > Permissions section, each with the state as text plus an icon, never color alone.

**FLW-10** Check with the non-prompting call. Re-check on `NSApplication.didBecomeActiveNotification` and when the view appears. Poll at most once a second, only while the view is visible, and stop at the grant.

```swift
@MainActor @Observable
final class AccessState {                                   // house code
    private(set) var trusted = AXIsProcessTrusted()         // never prompts
    private var watcher: Task<Void, Never>?

    func prompt() {                                         // only from the explainer's one button
        let key = "AXTrustedCheckOptionPrompt" as CFString  // = kAXTrustedCheckOptionPrompt
        trusted = AXIsProcessTrustedWithOptions([key: true] as CFDictionary)
        watch()
    }
    func watch() {                                          // call from .onAppear
        watcher?.cancel()
        watcher = Task { @MainActor in
            while !Task.isCancelled && !trusted {
                try? await Task.sleep(for: .seconds(1))
                trusted = AXIsProcessTrusted()
            }
        }
    }
    func stop() { watcher?.cancel() }                       // .onDisappear
}
```

```swift
struct PermissionRow: View {                                // house code
    let title: String, reason: String, granted: Bool, open: () -> Void
    var body: some View {
        LabeledContent {
            if granted { Label("Allowed", systemImage: "checkmark.circle.fill") }
            else { Button("Open System Settings", action: open) }
        } label: {
            Text(title)
            Text(reason)
        }
    }
}
```

### Deep links

Anchors below were read from the Privacy & Security extension bundle on macOS 27.0.1. That proves the pane knows the name, not that `open` lands there in every app state. macOS 26 and earlier: not re-checked here. Always keep the fallback.

- Base: `x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?<anchor>` (27.0.1).
- Legacy alias: `x-apple.systempreferences:com.apple.preference.security?<anchor>`. The 27.0.1 bundle lists it as `legacyBundleIdentifier`. Try one, then the other, then open System Settings itself.

| Pane | Anchor (27.0.1) |
|---|---|
| Accessibility, Input Monitoring | `Privacy_Accessibility`, `Privacy_ListenEvent` |
| Screen & System Audio Recording | `Privacy_ScreenCapture` |
| Full Disk Access, Files & Folders | `Privacy_AllFiles`, `Privacy_FilesAndFolders` |
| Automation, App Management, Developer Tools | `Privacy_Automation`, `Privacy_AppBundles`, `Privacy_DevTools` |
| Remote Desktop | `Privacy_RemoteDesktop` |
| Microphone, Camera, Speech | `Privacy_Microphone`, `Privacy_Camera`, `Privacy_SpeechRecognition` |
| Location, Contacts, Calendars, Reminders, Photos | `Privacy_LocationServices`, `Privacy_Contacts`, `Privacy_Calendars`, `Privacy_Reminders`, `Privacy_Photos` |
| Bluetooth, Motion, Media | `Privacy_Bluetooth`, `Privacy_Motion`, `Privacy_Media` |
| Notifications | `x-apple.systempreferences:com.apple.Notifications-Settings.extension` (27.0.1, bundle id; no per-app anchor) |
| Login Items & Extensions | `SMAppService.openSystemSettingsLoginItems()` (13.0); pane id `com.apple.LoginItems-Settings.extension` (27.0.1) |
| Local Network | no anchor; open the pane root and add a text hint |

```swift
@MainActor
func openSystemSettings(_ anchor: String? = nil) {          // house code
    let tail = anchor.map { "?\($0)" } ?? ""
    for s in ["x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension\(tail)",
              "x-apple.systempreferences:com.apple.preference.security\(tail)"] {
        if let u = URL(string: s), NSWorkspace.shared.open(u) { return }
    }
    NSWorkspace.shared.open(URL(fileURLWithPath: "/System/Applications/System Settings.app"))
}
```

Add a text line that names where to click; the fallback only opens the app.

### Denied, restart, taps, pasteboard, signing

- **FLW-11** A denied or revoked feature stays visible and disabled, with the reason and "Open System Settings". The system prompt does not reappear. A grant that needs a relaunch shows "Needs restart" and a Restart button. Show it only when the preflight call stays false after the grant. Screen Recording is the usual case (community reports). Severity: `P2`; raise to `P1` when the denied feature is the app's only job.
- **FLW-12** Read `NSPasteboard.general` only on a user paste or action, never on a timer. Since macOS 15.4, `detectPatterns(for:)` and `detectValues(for:)` tell what is on the pasteboard without reading it, and `accessBehavior` reports the person's choice. The SDK header says the General pasteboard asks on programmatic access; macOS may alert the person (27, verify the exact alert).
- **FLW-13** An event tap can hang system input when Accessibility is revoked while a `.defaultTap` runs (Apple Developer Forums, reported on 15, 26 and 27). Prefer no tap, then `.listenOnly`. Stop and release the tap the moment `AXIsProcessTrusted()` turns false.
- macOS 15 re-prompts monthly for the legacy Screen Recording capture path; check current releases. The picker avoids it.
- TCC grants follow the signing identity and path. Sign every dev build with the same stable identity, or each build loses its grants.

## States

**FLW-14** Every view has empty, loading, error, offline and partial states. `ContentUnavailableView` (macOS 14+) covers empty and blocking errors: a label, one line, and the first action as a button. No jokes, no emoji. A search with no results uses `ContentUnavailableView.search(text:)`.

```swift
switch state {
case .loading:
    ProgressView("Loading Tasks…")
case .empty:
    ContentUnavailableView {
        Label("No Tasks", systemImage: "checklist")
    } description: { Text("Tasks you add appear here.") }
      actions: { Button("Add Task", action: add) }
case .failed(let why):
    ContentUnavailableView {
        Label("Unable to Load Tasks", systemImage: "exclamationmark.triangle")
    } description: { Text(why) }
      actions: { Button("Try Again", action: retry) }
case .loaded(let items):
    List(items) { Text($0.title) }
}
```

| State | Design |
|---|---|
| Empty | `ContentUnavailableView` + first action. Never hold critical information in it |
| Loading | Placeholder rows (`.redacted(reason: .placeholder)`, macOS 11+) or cached content first |
| Error (whole view) | `ContentUnavailableView` + Try Again, not an alert |
| Partial | Keep the list; header row "3 items couldn't sync" with "Retry 3 Items". Never drop what worked |
| Offline | One non-modal status line ("Offline. Changes sync when you're back online."); queue the rest. No alert at launch |
| Stale | Keep the data with "Updated 4 minutes ago" while refresh runs or fails |

- **FLW-15** Show cached or placeholder content at once; load in the background.
- **FLW-17** Failures show inline with Retry. An alert is only for important, interrupting information. Do not warn about expected, undoable loss.

## Progress

**FLW-16** Use a determinate bar when the length is known. Never switch from spinner to bar mid-task. Name the verb and the count: "Importing 12 photos…". Offer Cancel when it is safe.

**FLW-18** Never put an error, or the only path to an action, in a timed toast. Every toast is also announced to VoiceOver ([accessibility.md](accessibility.md), A11Y-6). An Undo toast also exists as Edit > Undo.

## Notifications

- **FLW-19** Ask after the first action that benefits ("Remind me"), never at launch. The prompt shows once; later `requestAuthorization` calls only return the status. Keep a Settings row that shows `authorizationStatus` and, when denied, a button to the Notifications pane.
- Alert or Banner is the person's choice (`alertStyle`). A banner is never the only way to act.
- **FLW-20** Set `interruptionLevel` on every notification (macOS 12+): `.passive` for FYI, `.active` default, `.timeSensitive` only for what affects the person now, `.critical` almost never (needs an entitlement). Title says what changed, no app name, no "Open the app to…". At most four actions, short verbs in title case, none named "Open", destructive ones marked `.destructive`.
- If the app should show a banner while frontmost, implement `willPresent`; otherwise macOS shows nothing. In the foreground prefer an in-app cue.
- **FLW-21** Never notify for what is visible, what the person just did, errors that need an in-app alert, or marketing. Dock badge = unread notification count only (`NSApp.dockTile.badgeLabel`), cleared when read.
- `providesAppNotificationSettings` adds a System Settings button; implement `userNotificationCenter(_:openSettingsFor:)` (10.14).
- Menu-bar-only apps need a signed bundle with a stable bundle id, or they never appear in System Settings > Notifications. Test on a signed build.

Call `UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge])` from that first action, and set `content.interruptionLevel = .active` (or another level) on each `UNMutableNotificationContent`.

## Undo

- **UND-1** Prefer Undo to confirmation for common actions, deletes included. Confirm only rare, irreversible loss. The destructive role is for loss the person did not deliberately choose: Empty Trash's confirm button is not red, so Return confirms their own intent.

| Action | Do |
|---|---|
| Common and reversible (delete a row, rename, drop) | Do it, register Undo, name it |
| Rare and irreversible (empty trash, delete account) | Alert: question title with the verb, "Delete" and "Cancel" |

- **UND-2** Edits, deletes, drops, pastes, reorders and renames are undoable, one step per gesture, with a named action ("Undo Rename"). Use `@Environment(\.undoManager)` and `setActionName`. Group related changes with `beginUndoGrouping()` and `endUndoGrouping()`. Register the inverse on the window's manager; a separate `UndoManager` never reaches Edit > Undo.
- **UND-3** After Undo, reveal the item: scroll to it and select it.
- **UND-4** One-click destructive actions in lists and Settings offer Undo in place. No undo depth cap.

```swift
@Environment(\.undoManager) private var undoManager

func add(_ new: [Item]) {
    model.insert(new)                       // new items become the selection
    undoManager?.registerUndo(withTarget: model) { $0.remove(new.map(\.id)) }
    undoManager?.setActionName(new.count == 1 ? "Add Item" : "Add \(new.count) Items")
}
// Reveal: ScrollViewReader + .onChange(of: model.selection) { proxy.scrollTo(id) }
```

A menu-bar-only app has Edit > Undo only while it runs with a regular activation policy and a window ([menu-bar-apps.md](menu-bar-apps.md)).

## Drag and drop

- **DND-1** Support drag and drop where it makes sense, always with a menu or keyboard alternative (Copy and Paste, "Move To…"). Several items drag with a count badge.
- **DND-2** Drag out meaningful data: text, URL or file, never an internal id. Offer representations from highest to lowest fidelity with `Transferable` (macOS 13+): `FileRepresentation`, `DataRepresentation`, `ProxyRepresentation`.
- **DND-3** Create files dragged to Finder lazily with `FileRepresentation` or `NSFilePromiseProvider` (10.12), never at drag start.

```swift
struct NoteFile: Transferable {
    let title: String, body: String
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(exportedContentType: .plainText) { note in
            let url = URL.temporaryDirectory.appending(path: "\(note.title).txt")
            try "\(note.title)\n\n\(note.body)".write(to: url, atomically: true, encoding: .utf8)
            return SentTransferredFile(url)
        }
        ProxyRepresentation(exporting: \.title)     // apps that take no files get text
    }
}
// Row: Text(note.title).draggable(NoteFile(title: note.title, body: note.body))   (macOS 13+)
```

- **DND-4** Move within one container, copy between containers; Option forces copy. Highlight only targets that accept. Invalid drops animate back.
- **DND-5** Dropped content stays selected, and every drop is undoable (Undo code above).
- **DND-6** On macOS 26+ use `dropDestination(for:isEnabled:action:)`, whose action gets `(items, DropSession)` and returns `Void`. The `action:isTargeted:` form is deprecated in the 27.2 SDK; keep it only on the pre-26 path. Also macOS 26: `dropConfiguration(_:)`, `dragConfiguration(_:)` with `DragConfiguration(allowMove: true)`, `onDragSessionUpdated(_:)`, `dragPreviewsFormation(_:)`.

```swift
struct ItemDrop: ViewModifier {
    let add: ([Item]) -> Void
    func body(content: Content) -> some View {
        if #available(macOS 26, *) {
            content.dropDestination(for: Item.self) { items, _ in add(items) }
        } else {
            content.dropDestination(for: Item.self) { items, _ in add(items); return true }
        }
    }
}
```

## Copy, paste and Share

- Copy writes rich and plain types; paste honors Paste and Match Style.
- **DND-7** `ShareLink` (macOS 13+) or `NSSharingServicePicker` goes in File and context menus where it fits, never as the only export.

## Writing

Say "you", never "the user"; "click", never "tap". Cut "we", "Oops", "simply", "just", constant "please", and code words (entity, payload, 404).

- **FLW-22** Buttons and menu items: verb-first, title case ("Create Project"). Add an ellipsis (`…`, U+2026) only when the command asks for more input before it acts. Messages and labels: sentence case. 
- **FLW-23** Errors say what happened, why and what to do, without blame, codes or "Oops". Template: `Unable to <verb> <object>. <Reason>. <Fix>.`

| Before | After |
|---|---|
| OK | Save |
| Oops! Something went wrong. | Unable to save the task. The disk is full. |
| Are you sure? [Yes] [No] | Delete 3 Tasks? [Delete] [Cancel] |
| Loading… | Importing 12 photos… |

- **Alert titles:** a full sentence takes sentence case and a period; a fragment or question takes title case ("Unable to Export", "Delete 3 Tasks?"). Never "Error" or "Warning". The message never explains the buttons. At most three buttons, each a verb; "Cancel" is never the default; "OK" only on information.
- **Settings labels** describe the on state. Skip "Enable".
- **Tooltips** (`.help`, 13+): a verb, then the shortcut in symbols, never the control's name: "Add a task to this list (⌘N)". Sentence case, no period, about 70 characters at most.
- **Plurals:** `Text("^[\(count) task](inflect: true) left")`.

## Sources

- HIG pages (`https://developer.apple.com/design/human-interface-guidelines/<name>`): onboarding, privacy, alerts, notifications, drag-and-drop, undo-and-redo, loading, progress-indicators, writing.
- Apple docs and macOS 27.0 SDK headers (availability): `ContentUnavailableView`, `SCContentSharingPicker`, `NSPasteboard.accessBehavior`, `AEDeterminePermissionToAutomateTarget`, `dropDestination(for:isEnabled:action:)`, `SMAppService`, `Tips.configure`.
- WWDC26-271 Build powerful drag and drop in SwiftUI: https://developer.apple.com/videos/play/wwdc2026/271/
- Event tap hang on Accessibility revoke (Apple Developer Forums, thread 844416): https://developer.apple.com/forums/thread/844416
- Settings anchors: read on disk from `SecurityPrivacyExtension.appex` (`TCCServiceList.plist`, `Info.plist`), macOS 27.0.1.
- Parts adapted from BAMA by Dave Ebbelaar (MIT); see THIRD_PARTY_NOTICES.md.
