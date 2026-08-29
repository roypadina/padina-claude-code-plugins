# cmux Browser Automation

The browser panel is a WKWebView surface. Drive it with the `cmux browser` subcommand family or the
`browser.*` socket methods.

## Stable Agent Loop

```
1. Open / target a browser surface     → cmux browser open <url>
2. Verify navigation                   → cmux browser <surface> get url
3. Wait for a ready state              → cmux browser <surface> wait --load-state complete
4. Interactive snapshot for refs       → cmux browser <surface> snapshot --interactive
5. Act with refs (e1, e2, …)           → cmux browser <surface> click e3 --snapshot-after
6. Re-snapshot after every change
```

Refs from `snapshot --interactive` (`e1`, `e2`, …) are **per-snapshot** — re-snapshot after any DOM
or navigation change, or the ref goes stale.

## Opening Surfaces

```bash
SURF=$(cmux --json browser open https://example.com | jq -r '.surface_ref // .surface')

cmux browser open-split https://news.ycombinator.com
cmux browser open https://example.com --workspace workspace:2 --window window:1 --json
```

`open` / `open-split` / `new` default to `$CMUX_WORKSPACE_ID` and `--focus false`.

Two-step pattern when the URL flakily fails to load on creation:

```bash
SURF=$(cmux --json browser open about:blank | jq -r '.surface_ref')
cmux browser "$SURF" navigate https://example.com --snapshot-after
```

## Navigation

```bash
cmux browser "$SURF" navigate https://example.org/docs --snapshot-after
cmux browser "$SURF" back
cmux browser "$SURF" forward
cmux browser "$SURF" reload --snapshot-after
cmux browser "$SURF" url
```

## Waiting

```bash
cmux browser "$SURF" wait --load-state complete --timeout-ms 15000
cmux browser "$SURF" wait --selector "#checkout"
cmux browser "$SURF" wait --text "Order confirmed"
cmux browser "$SURF" wait --url-contains "/dashboard" --timeout-ms 15000
cmux browser "$SURF" wait --function "document.readyState === 'complete'" --timeout-ms 10000
```

If `get url` is empty or `about:blank`, navigate first — do not wait on a page that has not started
loading.

## Snapshots and Reads

```bash
cmux browser "$SURF" snapshot --interactive
cmux browser "$SURF" snapshot --interactive --compact
cmux browser "$SURF" snapshot --selector "#main" --max-depth 6
cmux browser "$SURF" screenshot --out /tmp/page.png

cmux browser "$SURF" get url
cmux browser "$SURF" get title
cmux browser "$SURF" get text  body
cmux browser "$SURF" get html  body
cmux browser "$SURF" get value "#email"
cmux browser "$SURF" get attr  "#link" href
cmux browser "$SURF" get count "li.item"
cmux browser "$SURF" get box   "#button"
cmux browser "$SURF" get styles "#header" --property color
```

## Interaction

```bash
cmux browser "$SURF" click e3 --snapshot-after
cmux browser "$SURF" dblclick e3
cmux browser "$SURF" hover e3
cmux browser "$SURF" focus e3
cmux browser "$SURF" check e3
cmux browser "$SURF" uncheck e3
cmux browser "$SURF" scroll-into-view e3

cmux browser "$SURF" type "#search" "query"
cmux browser "$SURF" fill "#email" "ops@example.com" --snapshot-after
cmux browser "$SURF" fill "#email" ""                 # empty == clear the input

cmux browser "$SURF" press   Enter
cmux browser "$SURF" keydown Shift
cmux browser "$SURF" keyup   Shift
cmux browser "$SURF" select "#country" "US"
cmux browser "$SURF" scroll --dy 800
cmux browser "$SURF" scroll --selector "#list" --dx 200
```

CSS selectors and `eN` refs both work wherever a selector is expected. Named keys follow the
Playwright/W3C names; `Space`, `Spacebar` and `space` all emit DOM key `" "` with code `Space`, while
`--key ' '` passes the raw DOM key.

## Finding Elements Beyond CSS

```bash
cmux browser "$SURF" find role button --name "Submit"
cmux browser "$SURF" find text "Sign in"
cmux browser "$SURF" find label "Email"
cmux browser "$SURF" find placeholder "Search…"
cmux browser "$SURF" find alt "company logo"
cmux browser "$SURF" find title "Edit"
cmux browser "$SURF" find testid "checkout-button"
cmux browser "$SURF" find first "li"
cmux browser "$SURF" find last  "li"
cmux browser "$SURF" find nth 2 "li"
```

`find role` takes the role as the positional and the accessible name via `--name` (add `--exact` for
an exact match). The text-ish finders take `--exact` too.

## State and Predicates

```bash
cmux browser "$SURF" is visible "#modal"
cmux browser "$SURF" is enabled "#submit"
cmux browser "$SURF" is checked "#agree"
```

## JavaScript

```bash
cmux browser "$SURF" eval "document.title"
cmux browser "$SURF" eval --script "JSON.stringify(performance.timing)"

cmux browser "$SURF" addinitscript "window.__test = true;"   # before any page load
cmux browser "$SURF" addscript "document.body.style.background='red'"
cmux browser "$SURF" addstyle  "body { font-family: monospace; }"
```

## Frames, Dialogs, Downloads

```bash
cmux browser "$SURF" frame main
cmux browser "$SURF" frame "#iframe-id"

cmux browser "$SURF" dialog accept "yes"
cmux browser "$SURF" dialog dismiss

cmux browser "$SURF" download wait --path ~/Downloads --timeout-ms 30000
```

## Profiles, Cookies, Storage, Tabs

```bash
cmux browser profiles list
cmux browser profiles add work
cmux browser profiles rename work corporate
cmux browser profiles delete corporate
cmux browser profiles clear work

cmux browser cookies get   example.com
cmux browser cookies set   '{"name":"sid","value":"abc","domain":".example.com"}'
cmux browser cookies clear example.com

cmux browser storage local   get "key"
cmux browser storage local   set "key" "val"
cmux browser storage local   clear
cmux browser storage session get "key"

cmux browser tab list
cmux browser tab new "https://example.com"
cmux browser tab switch 2
cmux browser tab close 2
```

`cmux browser import` pulls cookies and profiles out of an installed browser
(`--from <browser> [--profile <name>] [--all-profiles] [--to-profile <name>] [--domain <domain>]`).

## Persistent Auth

```bash
cmux browser "$SURF" state save ~/.config/cmux-auth/site.json    # after logging in once

# later, in a fresh surface
SURF=$(cmux --json browser open https://example.com/login | jq -r '.surface_ref')
cmux browser "$SURF" state load ~/.config/cmux-auth/site.json
cmux browser "$SURF" navigate https://example.com/dashboard
```

Those files hold live session cookies. Keep them out of any repository.

## Viewport, Network, Recording

```bash
cmux browser "$SURF" viewport 390 844      # exact CSS-pixel emulation, 1…4096
cmux browser "$SURF" viewport reset        # back to native pane sizing
cmux browser "$SURF" geolocation 32.08 34.78
cmux browser "$SURF" offline true
cmux browser "$SURF" trace start /tmp/trace
cmux browser "$SURF" screencast start
cmux browser "$SURF" network route "**/api/**" --abort
cmux browser "$SURF" network requests
cmux browser "$SURF" input mouse …
```

`viewport` aspect-fits the page inside the existing pane without resizing it; an oversized
viewport-plus-zoom combination returns structured render-limit details.

**Caveat:** WKWebView does not expose the Chrome DevTools Protocol, so some of this group has
historically returned `not_supported` depending on the build. `viewport` is documented as working in
0.64.22; treat `offline`, `trace`, `screencast`, `network route/unroute` and the raw `input` family
as **verify-before-you-rely-on-it** — run the one you need once and read the response.

## Debugging

```bash
cmux browser "$SURF" console list
cmux browser "$SURF" console clear
cmux browser "$SURF" errors list
cmux browser "$SURF" highlight "#problem-element"
cmux browser "$SURF" identify

cmux disable-browser        # turn the cmux browser off globally
cmux browser-status
cmux enable-browser
```

## Troubleshooting

### `js_error` on snapshot or eval

Some pages break the snapshot / eval scripts. Fall back to:

```bash
cmux browser "$SURF" get url
cmux browser "$SURF" get text body
cmux browser "$SURF" get html body
```

Still failing? Navigate to a simpler intermediate page on the same origin and retry from there.

### Stale `eN` refs

The DOM mutated between the snapshot and the action. Re-snapshot with `--interactive`, and use
`--snapshot-after` on anything that changes the DOM.

### The page never reaches `complete`

Some SPAs never fire the load event after the first paint. Switch to `--load-state interactive`,
`--selector`, `--text`, or `--function`.
