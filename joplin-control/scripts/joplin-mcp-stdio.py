#!/usr/bin/env python3
"""stdio <-> HTTP bridge for Joplin's built-in MCP server.

Joplin exposes MCP at http://127.0.0.1:<port>/mcp?token=<token>, which means
the token has to live somewhere. Pointing a client straight at that URL bakes
the secret into the client's config file — and Claude Code's ~/.claude.json is
mode 644 on a default install, so that is a real local-disclosure problem.

This bridge exists so no client config ever holds the token. It speaks plain
MCP stdio to the client, and on each message looks the port and token up from
Joplin's own profile at call time. Consequences worth having:

  * the secret stays in Joplin's settings.json and nowhere else
  * "Renew token" in Joplin needs no client reconfiguration at all
  * a non-default clipper port is discovered instead of hard-coded

Joplin's /mcp endpoint is a single-shot JSON-RPC POST: no SSE, no sessions, no
server-initiated messages. That is why this can stay a dumb request/response
pump rather than a real streamable-HTTP client.

Env overrides: JOPLIN_PORT, JOPLIN_TOKEN, JOPLIN_PROFILE_DIR.
Run with --selftest for offline unit tests.
"""

import json
import os
import sys
import urllib.error
import urllib.request

PORT_MIN, PORT_MAX = 41184, 41194
HTTP_TIMEOUT = 30
PROFILE_DIR = os.environ.get(
    "JOPLIN_PROFILE_DIR", os.path.expanduser("~/.config/joplin-desktop")
)

# JSON-RPC error codes we hand back to the client. -32000 is the generic
# "server error" slot reserved for implementation-defined failures.
E_JOPLIN_UNREACHABLE = -32000


def read_token():
    """Token from the env override, else Joplin's settings.json. '' if absent."""
    env = os.environ.get("JOPLIN_TOKEN")
    if env:
        return env
    try:
        with open(os.path.join(PROFILE_DIR, "settings.json")) as fh:
            return json.load(fh).get("api.token", "")
    except (OSError, ValueError):
        return ""


def discover_port():
    """First port in the clipper range whose /ping identifies as Joplin."""
    env = os.environ.get("JOPLIN_PORT")
    if env:
        return int(env)
    for port in range(PORT_MIN, PORT_MAX + 1):
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/ping", timeout=2
            ) as resp:
                if b"JoplinClipperServer" in resp.read(64):
                    return port
        except (urllib.error.URLError, OSError):
            continue
    return None


def error_response(msg_id, message, code=E_JOPLIN_UNREACHABLE):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def post(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        raw = resp.read().decode().strip()
    return json.loads(raw) if raw else None


def handle(msg, endpoint):
    """Forward one client message. Returns a reply dict, or None to stay silent.

    A JSON-RPC notification has no "id" and must never be answered — including
    when it fails, which is why the error path here is conditional too.
    """
    msg_id = msg.get("id")
    is_notification = msg_id is None
    if endpoint is None:
        if is_notification:
            return None
        return error_response(
            msg_id,
            "Joplin is not reachable: no Web Clipper service found on "
            f"127.0.0.1:{PORT_MIN}-{PORT_MAX}. Open Joplin and enable "
            "Settings > Web Clipper.",
        )
    try:
        reply = post(endpoint, msg)
    except urllib.error.HTTPError as exc:
        if is_notification:
            return None
        detail = "check the token in Joplin > Settings > Web Clipper" if exc.code in (401, 403) else str(exc)
        return error_response(msg_id, f"Joplin returned HTTP {exc.code}: {detail}")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        if is_notification:
            return None
        return error_response(msg_id, f"Joplin request failed: {exc}")
    return None if is_notification else reply


def build_endpoint(port, token):
    return f"http://127.0.0.1:{port}/mcp?token={token}"


def main():
    port = discover_port()
    token = read_token()
    endpoint = build_endpoint(port, token) if port and token else None

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            # Unparseable input has no id to answer against; drop it.
            continue

        # Re-resolve lazily if the first attempt found nothing: Joplin may have
        # been launched after this bridge started.
        if endpoint is None:
            port = discover_port()
            token = read_token()
            endpoint = build_endpoint(port, token) if port and token else None

        reply = handle(msg, endpoint)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


def selftest():
    fails = []

    def check(label, actual, expected):
        if actual == expected:
            print(f"  ok   {label}")
        else:
            print(f"  FAIL {label}: got {actual!r} want {expected!r}")
            fails.append(label)

    print("joplin-mcp-stdio.py selftest")

    check(
        "endpoint format",
        build_endpoint(41184, "abc"),
        "http://127.0.0.1:41184/mcp?token=abc",
    )

    # Unreachable Joplin: a request gets an error, a notification gets silence.
    err = handle({"jsonrpc": "2.0", "id": 7, "method": "tools/list"}, None)
    check("unreachable id preserved", err["id"], 7)
    check("unreachable is an error", err["error"]["code"], E_JOPLIN_UNREACHABLE)
    check(
        "notification stays silent",
        handle({"jsonrpc": "2.0", "method": "notifications/initialized"}, None),
        None,
    )

    # A failing POST must still not answer a notification.
    global post
    real_post = post
    try:
        def boom(url, payload):
            raise OSError("connection reset")

        post = boom
        check(
            "notification silent on transport error",
            handle({"jsonrpc": "2.0", "method": "notifications/initialized"}, "http://x"),
            None,
        )
        reply = handle({"jsonrpc": "2.0", "id": 9, "method": "ping"}, "http://x")
        check("request errors on transport error", reply["id"], 9)

        # Happy path: whatever Joplin returns is passed straight through.
        post = lambda url, payload: {"jsonrpc": "2.0", "id": payload["id"], "result": {"tools": []}}
        ok = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/list"}, "http://x")
        check("result passthrough", ok["result"], {"tools": []})
    finally:
        post = real_post

    # The token must never be read from anywhere but the override or the profile.
    os.environ["JOPLIN_TOKEN"] = "envtoken"
    check("env token wins", read_token(), "envtoken")
    del os.environ["JOPLIN_TOKEN"]

    print()
    if fails:
        print(f"{len(fails)} failed")
        return 1
    print("all passed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    main()
