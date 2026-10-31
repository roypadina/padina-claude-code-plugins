# Demo — a short "how it works" clip for every app

Every public Mac app has an 8–13 s looping demo: a GIF in the README and an MP4 on its site page. It is
rendered **offscreen** from the app's real SwiftUI views with fake data, so it stays reproducible and
public-clean. The kit is in [demo-kit/](demo-kit/) (`DemoKit.swift`, `encode.sh`, `README.md` = the API).
Real examples: `docs/demo/` in SmartHiddenBar, Agents Monitor, NtfyBar, and MeetAlert's scene (stubs + real
views; not its render.sh, which still passes the shifting `${MP4:+"$MP4"}` form).

## Rules
- **Never drive the live Mac**: no clicks, no `screencapture`, never launch the installed app. Windows are
  rendered offscreen (`NSHostingView` / `cacheDisplay`), never ordered front. An app-hosted test run needs
  the user's OK first.
- **House look = the kit's**: dark, 960×600 pt layout rendered at 1280×800, generated wallpaper, menu bar
  with the app's own status item, real AppKit window chrome, `MenuMock` menus, eased cursor, caption pill.
  Use kit primitives only and lay out relative to `Demo.size`. Kit change → edit `demo-kit/` here first;
  vendored copies stay as they are until the app's next re-render.
- **Real views, fake data**: compile the app's view files with `swiftc` next to the kit, a `stubs.swift`
  (stand-ins for the app types they reference) and `scene.swift`. A string not from a compiled view gets a
  `// File.swift:line` comment. Status words follow the app's own state machine after every action; rows
  that cannot be clicked are `enabled: false`. Prefer the main flow (status item, menu, panel, welcome); a
  toolbar-tab Settings window only when essential (its look is unverified).
- **Public-clean**: no names, employer, emails, hostnames, topics or home paths. Grep before committing.

## Storyboard (write `docs/demo/storyboard.md` first)
4–6 scenes, 8–13 s, a table of scene / start / duration / what happens / caption. Captions ≤ 9 words, plain
("A panel stays on screen until you act"). Show how it works AND why it is worth installing. Cursor only
while it points at something; every click shows its result within 0.3 s; 0.2 s crossfades; the last frame
dissolves into the first (loops cleanly).

## Outputs
- **Repo**: `docs/demo.gif` (880 px wide, 15 fps, ≤ 4 MB) and `docs/demo/` = `DemoKit.swift` + `encode.sh`
  (byte-identical to `demo-kit/`, check with `cmp`), `scene.swift`, `stubs.swift`, `storyboard.md`,
  `render.sh`. Copy `render.sh` from `docs/demo/render.sh` in SmartHiddenBar or Agents Monitor: it builds
  into `${TMPDIR:-/tmp}/<slug>-demo` (never in the repo, frames are ~400 MB), runs the binary with
  `-AppleLocale en_US -AppleLanguages "(en)"`, pins `POSTER=${POSTER:-<frame>}` on a frame that shows the app
  (never the empty desktop), then `"$KIT/encode.sh" "$BUILD/frames" "$GIF" "${MP4:-}" "${WEBP:-}" "${POSTER:-}"`.
  Keep the quoted empties: the `${MP4:+"$MP4"}` form shifts the positional arguments when MP4 is unset.
- **README hero**, right under the badge block:
  `<img src="docs/demo.gif" alt="<App> in action: <what the clip shows>" width="720">`.
- **Site** (repo `roypadina-apps`): `MP4=<site>/static/screenshots/<slug>/demo.mp4 WEBP=<site>/static/screenshots/<slug>/demo-still.webp ./render.sh`
  writes the GIF, MP4 (1280×800, h264 crf 24, yuv420p, faststart, ≤ 800 KB) and poster from one render.
  Add `"demo": { "video": "screenshots/<slug>/demo.mp4", "poster": "screenshots/<slug>/demo-still.webp", "width": 1280, "height": 800, "alt": "…" }`
  to the app's `data/apps.json` entry (edit the line in place; see SKILL § E2 15a), and
  `h.demoSection({ intro, demo: app.demo, caption })` as the first section of `src/pages/<slug>.mjs`
  (copy `ntfybar.mjs`). `node build.mjs`, then the normal site push.
- A real screen recording (LanGuard: 760×615, no `docs/demo/`) is fine; re-record it by hand, same file names.

## Verify before it ships
`render.sh` twice → `cmp` equal output. Sizes within the limits above. Extract frames with `ffmpeg`
(first, a mid-crossfade, last, poster) and look at them. Then the fable review gate (SKILL § C2).

## Gotchas
- macOS has no `timeout`: wrap `swiftc`, the render and `ffmpeg` as `perl -e 'alarm shift; exec @ARGV' 600 <cmd>`.
- Agents that view images can hang. The builder extracts frames and does not open them; a separate reviewer
  views them (≤ 8, downscaled with `sips -Z 1000`).
- A status symbol with cut-outs (`*.fill`) turns into a blank disc under the kit's `StatusItem`; draw it in
  the scene: monochrome `NSImage(systemSymbolName:)`, `sourceIn` white tint, width reserved (the `glyphSlot` helper in MaccyPlus `docs/demo/scene.swift`).
- Delete the frames only after a successful encode (`set -e`); never commit them.
