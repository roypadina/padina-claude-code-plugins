# Demo kit

Renders a short "how it works" screen recording **offscreen** (nothing is shown on the real screen, no clicks, no
`screencapture`): the app's real SwiftUI views composed over a house desktop, encoded to GIF + MP4 + poster.
Files: `DemoKit.swift` (everything), `encode.sh` (frames -> GIF/MP4/WebP). Layout canvas **960x600 pt**, composed at
2560x1600 px, frames downscaled to **1280x800**; MP4 1280x800, GIF 880 px wide / 15 fps. Dark appearance, 30 fps frames.

## API (all in `DemoKit.swift`; `@MainActor`)
- `Demo.size` (960x600 pt), `Demo.barHeight`, `Demo.clock` ("Thu Oct 30 9:41 AM"). Lay out relative to `Demo.size`.
- `Canvas()` -> wallpaper canvas, y-down points; `.image` -> CGImage.
  - `menuBar(app: StatusItem(symbol:text:), appActive:, clock:)` -> the app item's frame (transparent macOS 26 bar).
  - `Canvas.menuFrame(rows, under:)`, `MenuMock.frames(rows)` -> geometry for cursor targets.
  - `menu(rows, under: item, hover: cursorPos, alpha:)`; rows are `MenuMock.Row` (`.item(title, symbol:, key:, submenu:, enabled:)`,
    `.header`, `.separator`). Hover highlights enabled items only. Non-actionable rows (bare `Label`/`Text`) are `enabled: false`.
  - `panel(img, at:, radius:, alpha:)` glass panel; `window(img, at:, radius:)` captured window (16 plain, 26 with toolbar).
  - `cursor(at:, alpha:, press:, pulse:)` the real `NSCursor.arrow`; `CursorPath(start:, moves:, clicks:)` gives
    `.position(t)` (eased glide on a slight arc) and `.click(t)` (dip + ripple).
- `renderView(swiftUIView)` -> transparent dark CGImage; `captureWindow(view, size:, title:)` -> real AppKit title bar,
  active state (coloured traffic lights/controls via private selectors; dev tool only).
- `captureWindow(controller: NSViewController, title:, styleMask:, disabledButtons:)` -> same, for a window built as
  `NSWindow(contentViewController:)`, e.g. Settings = `NSTabViewController` with `tabStyle = .toolbar` whose items are
  `NSHostingController`s (`sizingOptions = .preferredContentSize`). Sizes itself from the controller; minimise/zoom render
  dimmed by default. Recipe: build the controller exactly as the app's SettingsWindow does, then `canvas.window(img, at:, radius: 26)`.
- `DemoClock.now` pins the time for views using `TimelineView` (the kit shadows SwiftUI's with a deterministic shim).
- `Scene(name:, duration:, caption:) { t in ... }` -> `Demo.run(scenes:)` writes `<out>/%04d.png`. Captions are drawn by
  `run` (old fades out 0-0.12 s, new fades in 0.12-0.35 s). 0.2 s crossfades; last 0.2 s dissolves into the first frame.
  `--at 1.5,6.7` previews single instants at 2560x1600. Helpers: `ease`, `easeOut`, `ramp(t, a, b)`.
- `encode.sh <frames> <gif> [mp4] [webp] [poster-frame]`.

## Builder rules (binding)
- **A.** Vendor the kit byte-identical (`cmp DemoKit.swift ${CLAUDE_PLUGIN_ROOT}/skills/finalize-app-release/references/demo-kit/DemoKit.swift`;
  same for `encode.sh`). Never hard-code 1280/800: use `Demo.size`. Use only kit primitives. Kit changes: edit
  `references/demo-kit/` first, then re-vendor.
- **B.** Every on-screen string/state comes from the app's real view files (compile them) or is copied verbatim with a
  `// Source.swift:line` comment. Status text follows the app's own rule at the fake clock. Non-actionable rows `enabled: false`.
  Fake public data only; grep for personal strings.
- **C.** 8-13 s, 4-6 scenes, captions <= 9 words, cursor only while it points at something, every click shows its real result
  within 0.3 s. Run `render.sh` twice (`cmp` equal), GIF <= 4 MB, MP4 <= 800 KB, look at one mid-crossfade frame and the loop
  frame. `render.sh` builds into `${TMPDIR:-/tmp}/<slug>-demo`, never into the repo.

## Vendoring into a repo (`docs/demo/`)
Copy `DemoKit.swift`, `encode.sh`, the app's `scene.swift`, `stubs.swift` (stand-ins for the app types the real view files
reference) and `render.sh`. `render.sh` compiles `DemoKit.swift` + stubs + scene + the app's real view files with `swiftc`, runs the
binary (`-AppleLocale en_US -AppleLanguages "(en)"` for "9:46 AM"-style times), then `encode.sh`. Defaults: kit next to the
script, app sources at `../../Sources/<App>`, GIF at `docs/demo.gif`.

**Settings windows:** toolbar-tab Settings windows are unverified against a real macOS 26 capture: every tab item renders on a
dark rounded box, possibly flattened Liquid Glass. Prefer storyboards that show the app's main flow (status item, menu, panel,
welcome) and use a Settings window only when it is essential to how the app works.

Known limits: glass is blurred wallpaper + tint (no Liquid Glass refraction); no hover/pressed state inside SwiftUI views; materials
sample the wallpaper only, not windows beneath; the captured-window path needs the private `hasKeyAppearance` family of selectors.

## Kit changes after freeze
- 2026-10-30 (v2): `menuBar(…, appName:, menus:)` — `menus` = the frontmost app's menu titles (default Finder's
  File Edit View Go Window Help, so v1 scenes render byte-identical). Use it whenever `appName` is not "Finder"
  (Terminal: Shell Edit View Window Help). Demos published before v2 keep their vendored v1 copy (same output).
