#!/usr/bin/env python3
"""Inventory and repair cmux workspaces that run Claude Code sessions.

Reads cmux's own persisted session file (the one it writes for
"Restore Previous Launch") plus the live topology, and reports or
rebuilds any workspace whose Claude pane did not come back.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SESSION_JSON = Path.home() / "Library/Application Support/cmux/session-com.cmuxterm.app.json"
PREVIOUS_JSON = SESSION_JSON.with_name("session-com.cmuxterm.app-previous.json")
DEFAULT_CONFIG_DIR = Path.home() / ".claude"
RESUME_RE = re.compile(r"--resume\s+([0-9a-f-]{36})")
TREE_RE = re.compile(
    r"^(?P<indent>[\s│├└─]*)(?P<kind>workspace|pane|surface)\s+"
    r"(?P<ref>\w+:\d+)\s+(?P<uuid>[0-9A-F-]{36})(?P<rest>.*)$"
)


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True).stdout


# ---------- Claude Code profiles ----------
#
# Claude Code keeps its state in ~/.claude unless CLAUDE_CONFIG_DIR points
# elsewhere. People who run several accounts on one machine have several such
# directories — and often symlink the heavy `projects/` tree so the transcripts
# are shared. Dedupe on the RESOLVED projects path so a symlinked profile is not
# scanned twice.

def project_dirs():
    """Every distinct transcript directory on this machine, newest-first order irrelevant."""
    candidates = []
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    if env:
        candidates += [Path(p).expanduser() for p in env.split(":") if p]
    candidates.append(DEFAULT_CONFIG_DIR)
    candidates += sorted(Path.home().glob(".claude*"))

    seen, dirs = set(), []
    for config_dir in candidates:
        projects = config_dir / "projects"
        if not projects.is_dir():
            continue
        key = projects.resolve()
        if key in seen:
            continue
        seen.add(key)
        dirs.append(projects)
    return dirs or [DEFAULT_CONFIG_DIR / "projects"]


PROJECT_DIRS = project_dirs()


def profile_label(config_dir):
    """Human name for the profile a pane was launched under."""
    if not config_dir:
        return "default"
    path = Path(config_dir).expanduser()
    if path.resolve() == DEFAULT_CONFIG_DIR.resolve():
        return "default"
    return path.name.lstrip(".") or str(path)


# ---------- live topology ----------

def live_tree():
    """[{ref, uuid, title, surfaces:[{ref, uuid, title, tty}]}] for the running app."""
    out = sh("cmux", "tree", "--all", "--id-format", "both")
    workspaces, current = [], None
    for line in out.splitlines():
        m = TREE_RE.match(line)
        if not m:
            continue
        kind, rest = m.group("kind"), m.group("rest")
        title = (re.search(r'"([^"]*)"', rest) or [None, ""])[1]
        if kind == "workspace":
            current = {"ref": m.group("ref"), "uuid": m.group("uuid"), "title": title, "surfaces": []}
            workspaces.append(current)
        elif kind == "surface" and current is not None:
            tty = (re.search(r"tty=(\S+)", rest) or [None, None])[1]
            current["surfaces"].append(
                {"ref": m.group("ref"), "uuid": m.group("uuid"), "title": title, "tty": tty}
            )
    return workspaces


def tty_claude(tty):
    """(pid, session_id) of the claude process on a tty, or (None, None)."""
    if not tty:
        return None, None
    for line in sh("ps", "-t", tty, "-o", "pid=,command=").splitlines():
        pid, _, cmd = line.strip().partition(" ")
        if "/claude" not in cmd.split(" ")[0]:
            continue
        m = RESUME_RE.search(cmd)
        return pid, (m.group(1) if m else None)
    return None, None


# ---------- saved session ----------

def saved_workspaces(path=SESSION_JSON):
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    result = []
    for window in data.get("windows", []):
        for w in window.get("tabManager", {}).get("workspaces", []):
            panels = []
            for p in w.get("panels", []):
                term = p.get("terminal") or {}
                agent = term.get("agent") or {}
                binding = term.get("resumeBinding") or {}
                if not (agent or binding):
                    continue
                env = binding.get("environment") or agent.get("launchCommand", {}).get("environment") or {}
                panels.append({
                    "uuid": p.get("id"),
                    "kind": agent.get("kind") or binding.get("kind"),
                    "session_id": agent.get("sessionId") or binding.get("checkpointId"),
                    "cwd": binding.get("cwd") or agent.get("workingDirectory") or p.get("directory"),
                    "mode": agent.get("permissionMode") or binding.get("permissionMode"),
                    "config_dir": env.get("CLAUDE_CONFIG_DIR"),
                    "auto_resume": binding.get("autoResume"),
                })
            result.append({
                "uuid": w.get("workspaceId"),
                "title": w.get("customTitle") or w.get("processTitle") or "(untitled)",
                "cwd": w.get("currentDirectory"),
                "panels": panels,
            })
    return result


# ---------- transcripts ----------

def transcript(session_id):
    if not session_id:
        return None
    for projects in PROJECT_DIRS:
        hits = list(projects.glob(f"*/{session_id}.jsonl"))
        if hits:
            return hits[0]
    return None


def encoded(path):
    return re.sub(r"[/.]", "-", path or "")


def resume_cmd(panel):
    cmd = "claude"
    if panel.get("config_dir"):
        cmd = f"CLAUDE_CONFIG_DIR={panel['config_dir']} {cmd}"
    cmd += f" --resume {panel['session_id']}"
    if panel.get("mode"):
        cmd += f" --permission-mode {panel['mode']}"
    return cmd


# ---------- commands ----------

def cmd_list(args):
    saved = {w["uuid"]: w for w in saved_workspaces()}
    rows = []
    for w in live_tree():
        s = saved.get(w["uuid"], {})
        panels = {p["uuid"]: p for p in s.get("panels", [])}
        for surface in w["surfaces"]:
            pid, live_sid = tty_claude(surface["tty"])
            panel = panels.get(surface["uuid"], {})
            sid = live_sid or panel.get("session_id")
            t = transcript(sid)
            rows.append({
                "workspace": w["ref"], "workspace_uuid": w["uuid"],
                "title": w["title"] or s.get("title", ""),
                "surface": surface["ref"], "surface_uuid": surface["uuid"],
                "surface_title": surface["title"], "tty": surface["tty"],
                "pid": pid, "running": bool(pid), "session_id": sid,
                "cwd": panel.get("cwd"), "config_dir": panel.get("config_dir"),
                "mode": panel.get("mode"),
                "resume": resume_cmd({**panel, "session_id": sid}) if sid else None,
                "transcript": str(t) if t else None,
            })

    if args.json:
        print(json.dumps(rows, indent=2))
        return
    out = render(rows)
    if args.output:
        Path(args.output).expanduser().write_text(out)
        print(f"wrote {args.output}")
    else:
        print(out)


def render(rows):
    lines = [f"# cmux Claude sessions ({len(rows)} panes)", ""]
    for r in rows:
        head = r["title"] or r["surface_title"]
        lines.append(f"## {head}  ({r['workspace']})")
        lines.append(f"- workspace UUID: `{r['workspace_uuid']}`")
        lines.append(f"- pane: `{r['surface']}` \"{r['surface_title']}\" · tty {r['tty']}")
        lines.append(f"- claude: {'running pid ' + r['pid'] if r['running'] else 'NOT RUNNING'}")
        if r["cwd"]:
            lines.append(f"- cwd: `{r['cwd']}`")
        lines.append(f"- profile: {profile_label(r['config_dir'])}")
        if r["session_id"]:
            lines.append(f"- session: `{r['session_id']}`")
            lines.append(f"- resume: `{r['resume']}`")
        lines.append("")
    return "\n".join(lines)


def cmd_check(args):
    source = Path(args.session_file).expanduser() if args.session_file else SESSION_JSON
    saved = saved_workspaces(source)
    live = live_tree()
    live_ws = {w["uuid"] for w in live}
    problems = {"missing_workspaces": [], "dead_panes": [], "warnings": []}

    for w in saved:
        if w["uuid"] in live_ws or not w["panels"]:
            continue
        problems["missing_workspaces"].append(w)

    saved_by_uuid = {w["uuid"]: w for w in saved}
    for w in live:
        panels = {p["uuid"]: p for p in saved_by_uuid.get(w["uuid"], {}).get("panels", [])}
        for surface in w["surfaces"]:
            pid, _ = tty_claude(surface["tty"])
            panel = panels.get(surface["uuid"])
            if pid or not panel or not panel.get("session_id"):
                continue
            problems["dead_panes"].append({"workspace": w, "surface": surface, "panel": panel})

    for w in saved:
        for p in w["panels"]:
            if not p["session_id"]:
                continue
            t = transcript(p["session_id"])
            if t is None:
                problems["warnings"].append(
                    f"{w['title']}: no transcript on disk for session {p['session_id']}"
                )
            elif t.parent.name != encoded(p["cwd"]):
                problems["warnings"].append(
                    f"{w['title']}: transcript lives in {t.parent.name} but resume cwd is "
                    f"{p['cwd']} — `--resume` may not find it from there"
                )

    if args.json:
        print(json.dumps(problems, indent=2, default=str))
        return

    mw, dp = problems["missing_workspaces"], problems["dead_panes"]
    if not mw and not dp:
        print("All saved Claude workspaces are live with a running agent.")
    for w in mw:
        sids = ", ".join(p["session_id"] or "?" for p in w["panels"])
        print(f"MISSING workspace  {w['title']}  ({w['uuid']})  sessions: {sids}")
    for d in dp:
        print(f"DEAD pane          {d['workspace']['title']}  {d['surface']['ref']}  "
              f"session {d['panel']['session_id']}")
    for warn in problems["warnings"]:
        print(f"warning            {warn}")
    if mw or dp:
        print("\nRebuild with: cmux-sessions.py restore   (add --dry-run first)")


def cmd_restore(args):
    source = Path(args.session_file).expanduser() if args.session_file else SESSION_JSON
    live = live_tree()
    live_ws = {w["uuid"] for w in live}
    saved = saved_workspaces(source)

    targets = [w for w in saved if w["uuid"] not in live_ws and w["panels"]]
    if args.match:
        needle = args.match.lower()
        targets = [w for w in targets if needle in w["title"].lower()]
    if not targets and not args.match:
        print("Nothing missing.")

    for w in targets:
        first, *extra = w["panels"]
        if not first.get("session_id"):
            print(f"skip {w['title']}: no session id saved")
            continue
        out = run(["cmux", "new-workspace", "--name", w["title"],
                   "--cwd", first["cwd"] or w["cwd"],
                   "--command", resume_cmd(first), "--focus", "false"], args.dry_run)
        ws_ref = ref_from(out, "workspace")
        for p in extra:
            if not p.get("session_id"):
                continue
            if args.dry_run or not ws_ref:
                print(f"  [extra pane] split {ws_ref or w['title']} and run: {resume_cmd(p)}")
                continue
            split = run(["cmux", "new-split", "right", "--workspace", ws_ref, "--focus", "false"], False)
            surface = ref_from(split, "surface")
            if not surface:
                print(f"  could not split for extra pane; run manually: {resume_cmd(p)}")
                continue
            run(["cmux", "send", "--workspace", ws_ref, "--surface", surface, resume_cmd(p)], False)
            run(["cmux", "send-key", "--workspace", ws_ref, "--surface", surface, "enter"], False)

    # panes that exist but lost their agent
    saved_by_uuid = {w["uuid"]: w for w in saved}
    for w in live:
        panels = {p["uuid"]: p for p in saved_by_uuid.get(w["uuid"], {}).get("panels", [])}
        for surface in w["surfaces"]:
            if args.match and args.match.lower() not in (w["title"] or "").lower():
                continue
            pid, _ = tty_claude(surface["tty"])
            panel = panels.get(surface["uuid"])
            if pid or not panel or not panel.get("session_id"):
                continue
            run(["cmux", "send", "--workspace", w["ref"], "--surface", surface["ref"],
                 resume_cmd(panel)], args.dry_run)
            run(["cmux", "send-key", "--workspace", w["ref"], "--surface", surface["ref"],
                 "enter"], args.dry_run)


def run(cmd, dry):
    printable = " ".join(f"'{c}'" if " " in c else c for c in cmd)
    if dry:
        print(f"[dry-run] {printable}")
        return ""
    print(printable)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode:
        print(f"  FAILED: {result.stderr.strip() or result.stdout.strip()}", file=sys.stderr)
    return result.stdout


def ref_from(output, kind):
    """cmux prints `OK workspace:17` / `OK surface:19 workspace:17`."""
    m = re.search(rf"\b({kind}:\d+)\b", output or "")
    return m.group(1) if m else None


def self_check():
    assert encoded("/Users/x/Code/foo.bar") == "-Users-x-Code-foo-bar"
    assert encoded(None) == ""

    assert profile_label(None) == "default"
    assert profile_label(str(DEFAULT_CONFIG_DIR)) == "default"
    assert profile_label("~/.claude-work2") == "claude-work2"
    assert profile_label("/opt/claude-alt") == "claude-alt"

    assert resume_cmd({"session_id": "abc"}) == "claude --resume abc"
    assert resume_cmd({"session_id": "abc", "mode": "auto"}) == \
        "claude --resume abc --permission-mode auto"
    assert resume_cmd({"session_id": "abc", "config_dir": "/c", "mode": "auto"}) == \
        "CLAUDE_CONFIG_DIR=/c claude --resume abc --permission-mode auto"

    assert ref_from("OK surface:19 workspace:17", "workspace") == "workspace:17"
    assert ref_from("OK surface:19 workspace:17", "surface") == "surface:19"
    assert ref_from("nothing here", "surface") is None

    # Symlinked profiles must not be scanned (and reported) twice.
    resolved = [p.resolve() for p in PROJECT_DIRS]
    assert len(resolved) == len(set(resolved)), f"duplicate transcript dirs: {resolved}"

    line = "  ├─ surface surface:7 1A2B3C4D-0000-0000-0000-00000000000F \"agent\" tty=ttys004"
    m = TREE_RE.match(line)
    assert m and m.group("ref") == "surface:7" and "tty=ttys004" in m.group("rest")

    print(f"cmux-sessions self-check OK ({len(PROJECT_DIRS)} transcript dir(s))")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-check", action="store_true", help="run the built-in assertions and exit")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("list", help="inventory every live Claude pane")
    p.add_argument("--json", action="store_true")
    p.add_argument("-o", "--output", help="write the markdown report to a file")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("check", help="find workspaces/panes that did not come back")
    p.add_argument("--json", action="store_true")
    p.add_argument("--session-file", help=f"read a different saved session (default {SESSION_JSON.name}; "
                                          f"use {PREVIOUS_JSON.name} to recover the launch before this one)")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("restore", help="recreate missing workspaces and revive dead panes")
    p.add_argument("--match", help="only workspaces whose title contains this substring")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--session-file", help="read a different saved session (see `check --session-file`)")
    p.set_defaults(func=cmd_restore)

    args = ap.parse_args()
    if args.self_check:
        self_check()
        return
    if not args.cmd:
        ap.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
