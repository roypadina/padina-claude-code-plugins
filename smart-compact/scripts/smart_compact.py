#!/usr/bin/env python3
"""smart_compact.py — the single script behind /smart-compact.

Python 3 standard library ONLY. No network. Writes only inside the state dir.

Subcommands
  health             context-health report for a session transcript
  snapshot           (re)write the handoff file from the transcript (+ model notes)
  search             search a session's full backup (or live transcript) — bounded, readable hits
  hook-precompact    PreCompact hook: refresh handoff, FULL session backup, warn on auto-compact
  hook-sessionstart  SessionStart hook: re-inject the handoff after a compact/resume
  hook-nag           per-turn hook: one-time nudge when a fill threshold is crossed
  demo               assert-based self-check; prints OK

State layout (root overridable with SMART_COMPACT_HOME, used by demo/tests):
  ~/.claude/smart-compact/<project-slug>/<session_id>.md          handoff
  ~/.claude/smart-compact/<project-slug>/<session_id>.nag         thresholds already fired
  ~/.claude/smart-compact/<project-slug>/backups/<sid>/<UTC>-<trigger>/   full gzip copy of the
        session taken right before each compaction: transcript.jsonl.gz + subagents/ + tool-results/
        (last 3 per session, none older than 90 days)
  ~/.claude/smart-compact/.claims/                                 dedupe markers (see claim())

Hook contract notes (verified, see docs/smart-compact-research.md):
  * `systemMessage` in hook JSON is shown to the HUMAN and never enters model context.
    That is the nag channel — it is the least context-costly option available to a hook.
    (`reason` would be model-visible on Stop; `additionalContext` always is. Neither is used
    by hook-nag on purpose.)
  * SessionStart stdout IS injected as context — that is the restore path, and the only
    place this script prints prose on purpose.
  * Every hook subcommand is wrapped: on any unexpected failure it prints nothing and exits 0.
    A broken hook must never break the session.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- constants

# Command name + env prefix. Two plugins ship this file under different command names; only
# these two values and the prose naming them differ. Both share the default state dir — see
# claim().
CMD = "/smart-compact"
ENV = "SMART_COMPACT_"

# Most important first: rendered in this order, and truncation eats from the tail.
SECTIONS = [
    "GOAL", "NEXT", "DO-NOT-REDO", "DECISIONS",
    "IN-FLIGHT", "STATE", "FILES", "OPEN QUESTIONS",
]
AUTO_SECTIONS = {"STATE", "FILES", "IN-FLIGHT"}          # regenerated every snapshot
MODEL_SECTIONS = [s for s in SECTIONS if s not in AUTO_SECTIONS]
PLACEHOLDER = f"_(not written — run `{CMD}`)_"

DEFAULT_WINDOW = 1_000_000      # 1M context is the norm; 200K users set SMART_COMPACT_WINDOW
DEFAULT_THRESHOLDS = [50, 70, 85]
# Claude Code persists hook output above ~10K chars to a file and shows the model a 2 KB
# preview, which it never follows up (usage data: 24 of 39 restores cut). Stay inline.
DEFAULT_MAX_CHARS = 9_000
KEEP_BACKUPS = 1                # per session; the transcript is append-only, so the newest is a superset
BACKUP_CAP_BYTES = 5 << 30      # all backups together; oldest evicted first
STALE_AFTER_MIN = 90            # model notes older than this (or ...
STALE_AFTER_TURNS = 30          # ... this many assistant messages) before compaction: verify first
CHARS_PER_TOKEN = 4             # crude, only used for "token sink" estimates

SECRET_RE = re.compile(r"\bsecurity\s|\s-w\b|token|secret|passw|bearer\s|api[_-]?key", re.I)
# Commands worth remembering because they changed state somewhere.
MUTATING_RE = re.compile(
    r"\b(git\s+(commit|push|rebase|merge|reset|revert|checkout\s+-b|switch\s+-c|tag|worktree|stash)"
    r"|dotnet\s+ef|migrate|alembic|kubectl\s+(apply|delete|rollout|scale)|helm\s+(install|upgrade)"
    r"|terraform\s+(apply|destroy)|docker\s+push|npm\s+publish|gh\s+(pr|release)\s+create"
    r"|rm\s+-rf)\b"
)
# One id + everything up to the next id, so a status is attributed to ITS task and not to
# every task mentioned in the same record.
TASK_BLOCK_RE = re.compile(r"<task-id>\s*([^<\s]+)\s*</task-id>(.*?)(?=<task-id>|\Z)", re.S)
TASK_STATUS_RE = re.compile(r"<status>\s*([^<]*)\s*</status>")
BG_ID_RE = re.compile(r"background with ID:\s*`?([A-Za-z0-9_-]+)`?")


# ---------------------------------------------------------------- small utils

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def state_root() -> Path:
    override = os.environ.get(ENV + "HOME")
    if override:
        return Path(override)
    return Path.home() / ".claude" / "smart-compact"


# Keyed on the session id alone. Older versions used a cwd slug dir, which drifted with
# every `cd` and stranded the model notes where the restore never looked.
def handoff_path(session_id: str) -> Path:
    state_root().mkdir(parents=True, exist_ok=True)
    return state_root() / f"{safe_id(session_id)}.md"


def nag_path(session_id: str) -> Path:
    state_root().mkdir(parents=True, exist_ok=True)
    return state_root() / f"{safe_id(session_id)}.nag"


def _header_value(header_lines: list[str], key: str) -> str | None:
    for line in header_lines:
        m = re.match(rf"^\s*-\s*{re.escape(key)}:\s*(\S+)\s*$", line)
        if m:
            return m.group(1)
    return None


def safe_id(session_id: str | None) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", session_id or "unknown") or "unknown"


def thresholds_from_env() -> list[int]:
    raw = os.environ.get(ENV + "THRESHOLDS", "")
    out = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            try:
                v = int(float(part))
            except ValueError:
                continue
            if 0 < v <= 100:
                out.append(v)
    return sorted(set(out)) or list(DEFAULT_THRESHOLDS)


def max_chars_from_env() -> int:
    try:
        v = int(os.environ.get(ENV + "MAX_CHARS", "") or DEFAULT_MAX_CHARS)
        return v if v > 200 else DEFAULT_MAX_CHARS
    except ValueError:
        return DEFAULT_MAX_CHARS


# ---------------------------------------------------------------- transcript IO

def iter_records(path: str | Path):
    """Stream a JSONL transcript. Malformed lines are skipped, never fatal."""
    try:
        f = open(path, "r", encoding="utf-8", errors="replace")
    except OSError:
        return
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if isinstance(rec, dict):
                yield rec


def tail_lines(path: str | Path, want_bytes: int = 262_144, cap: int = 8_388_608):
    """Read the tail of a file and return complete lines, newest last.

    Doubles the read window until at least one full line is captured or the cap is hit.
    Avoids a full forward parse just to find the last usage record.
    """
    try:
        size = os.path.getsize(path)
    except OSError:
        return []
    chunk = min(want_bytes, cap)
    while True:
        start = max(0, size - chunk)
        try:
            with open(path, "rb") as f:
                f.seek(start)
                data = f.read()
        except OSError:
            return []
        text = data.decode("utf-8", errors="replace")
        lines = text.split("\n")
        if start > 0 and lines:
            lines = lines[1:]           # first line is probably partial
        lines = [ln for ln in lines if ln.strip()]
        if lines or start == 0 or chunk >= cap:
            return lines
        chunk = min(chunk * 4, cap)


def _usage_of(rec: dict) -> dict | None:
    """Return message.usage for a *real* main-thread assistant record, else None."""
    if rec.get("type") != "assistant":
        return None
    if rec.get("isSidechain"):          # subagent branch — different context window
        return None
    msg = rec.get("message")
    if not isinstance(msg, dict):
        return None
    if msg.get("model") == "<synthetic>":   # no-op records carry an all-zero usage
        return None
    usage = msg.get("usage")
    if not isinstance(usage, dict):
        return None
    if not any(isinstance(usage.get(k), int) for k in
               ("input_tokens", "cache_read_input_tokens",
                "cache_creation_input_tokens", "output_tokens")):
        return None
    return usage


def last_usage(path: str | Path) -> tuple[dict | None, str | None]:
    """(usage, model) from the last real assistant record. Tail-first, forward fallback."""
    for line in reversed(tail_lines(path)):
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if not isinstance(rec, dict):
            continue
        u = _usage_of(rec)
        if u is not None:
            return u, (rec.get("message") or {}).get("model")
    found = (None, None)
    for rec in iter_records(path):
        u = _usage_of(rec)
        if u is not None:
            found = (u, (rec.get("message") or {}).get("model"))
    return found


# ---------------------------------------------------------------- fill maths

def _settings_paths(cwd: str | None = None) -> list[Path]:
    """User settings first, then the project's — research doc lists both as valid."""
    out = [Path.home() / ".claude" / "settings.json",
           Path.home() / ".claude" / "settings.local.json"]
    if cwd:
        out += [Path(cwd) / ".claude" / "settings.json",
                Path(cwd) / ".claude" / "settings.local.json"]
    return out


def _settings_dicts(cwd: str | None = None):
    for p in _settings_paths(cwd):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            yield data


def read_settings_window(cwd: str | None = None) -> int | None:
    """`autocompactTokenCount`, if the user ever ran /autocompact <N>.

    Never observed set on this machine — treat as usually absent and validate hard.
    """
    for data in _settings_dicts(cwd):
        v = data.get("autocompactTokenCount")
        if isinstance(v, (int, float)) and 10_000 <= v <= 5_000_000:
            return int(v)
    return None


def context_window(model: str | None = None, used: int = 0,
                   cwd: str | None = None) -> tuple[int, str]:
    """(window_tokens, where-it-came-from).

    Env override, then `autocompactTokenCount`, then 1M. No model-id sniffing: the
    transcript strips the `[1m]` suffix and settings.json misses `--model` and extra
    CLAUDE_CONFIG_DIR profiles, so guessing was wrong more often than the default.
    `model` and `used` are unused, kept so callers need no change.
    """
    try:
        forced = int(os.environ.get(ENV + "WINDOW") or 0)
    except ValueError:
        forced = 0
    if 10_000 <= forced <= 5_000_000:
        return forced, ENV + "WINDOW"
    explicit = read_settings_window(cwd)
    if explicit:
        return explicit, "autocompactTokenCount (settings.json)"
    return DEFAULT_WINDOW, f"default 1M (set {ENV}WINDOW=200000 for a 200K model)"


def used_tokens(usage: dict | None) -> int:
    """Prompt tokens currently in the window.

    input + cache_creation + cache_read — the same formula the statusLine's
    `context_window.used_percentage` is documented to use. output_tokens is
    deliberately excluded (it lands in the NEXT turn's cache figures).
    This is an estimate, not harness ground truth.
    """
    if not usage:
        return 0
    total = 0
    for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
        v = usage.get(k)
        if isinstance(v, (int, float)):
            total += int(v)
    return total


def fill_percent(used: int, window: int) -> float:
    return round((used / window) * 100.0, 1) if window else 0.0


def verdict_for(pct: float, thresholds: list[int]) -> str:
    if not thresholds:
        return "OK"
    if pct >= thresholds[-1]:
        return "compact now"
    if pct >= thresholds[0]:
        return "compact soon"
    return "OK"


def newly_crossed(pct: float, already: list[int], thresholds: list[int]) -> list[int]:
    return [t for t in thresholds if pct >= t and t not in already]


# ---------------------------------------------------------------- transcript scan

def scan_transcript(path: str | Path) -> dict:
    """One forward streaming pass. Feature-detects tool names; unknown tools are ignored."""
    written: list[str] = []
    read_files: list[str] = []
    commands: list[str] = []
    sinks: dict[str, int] = {}
    bg_launch: dict[str, dict] = {}       # tool_use_id -> {command, description}
    bg_tasks: dict[str, dict] = {}        # background task id -> info
    bg_resolved: dict[str, str] = {}      # task id -> status
    tool_names: dict[str, str] = {}       # tool_use_id -> tool name
    user_turns = assistant_turns = 0
    first_ts = last_ts = None
    usage = None
    model = None

    for rec in iter_records(path):
        ts = rec.get("timestamp")
        if isinstance(ts, str):
            first_ts = first_ts or ts
            last_ts = ts
        rtype = rec.get("type")
        msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
        content = msg.get("content")

        # Task-completion notifications land in TWO shapes: inside `message.content` on a
        # `user` record, and (far more often, measured on a real 25MB transcript) on the
        # TOP-LEVEL `content` of a `queue-operation` record. Read both, regardless of type,
        # or finished jobs are reported as still in flight.
        top = rec.get("content")
        if isinstance(top, str) and "<task-id>" in top:
            _parse_task_notifications(top, bg_resolved)

        if rtype == "assistant":
            assistant_turns += 1
            u = _usage_of(rec)
            if u is not None:
                usage, model = u, msg.get("model")
        elif rtype == "user":
            # task-notification records carry a plain-string content
            if isinstance(content, str) and "<task-id>" in content:
                _parse_task_notifications(content, bg_resolved)
            if isinstance(content, str) and "<task-id>" not in content:
                user_turns += 1
            elif isinstance(content, list) and not any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content
            ):
                user_turns += 1

        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "tool_use":
                    name = block.get("name") or "?"
                    inp = block.get("input") if isinstance(block.get("input"), dict) else {}
                    tuid = block.get("id")
                    if tuid:
                        tool_names[tuid] = name
                    sinks[name] = sinks.get(name, 0) + _blob_len(inp)
                    fp = inp.get("file_path") or inp.get("notebook_path")
                    if isinstance(fp, str):
                        if name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                            _push(written, fp)
                        elif name == "Read":
                            _push(read_files, fp)
                    cmd = inp.get("command")
                    if isinstance(cmd, str) and MUTATING_RE.search(cmd):
                        _push(commands, cmd.strip().replace("\n", " ")[:200])
                    if inp.get("run_in_background") is True and tuid:
                        bg_launch[tuid] = {
                            "command": (inp.get("command") or inp.get("prompt") or "")[:200],
                            "description": (inp.get("description") or "")[:200],
                            "tool": name,
                        }
                elif btype == "tool_result":
                    tuid = block.get("tool_use_id")
                    sinks[tool_names.get(tuid, "tool_result")] = (
                        sinks.get(tool_names.get(tuid, "tool_result"), 0) + _blob_len(block)
                    )
                    if tuid in bg_launch:
                        tid = _background_id(rec, block)
                        info = dict(bg_launch[tuid])
                        info["tool_use_id"] = tuid
                        bg_tasks[tid or f"unknown:{tuid}"] = info
                elif btype in ("text", "thinking"):
                    sinks["conversation text"] = sinks.get("conversation text", 0) + _blob_len(block)
        elif isinstance(content, str):
            sinks["conversation text"] = sinks.get("conversation text", 0) + len(content)

    pending = {tid: info for tid, info in bg_tasks.items()
               if not tid.startswith("unknown:") and tid not in bg_resolved}
    pending.update({tid: info for tid, info in bg_tasks.items() if tid.startswith("unknown:")})

    return {
        "files_written": written,
        "files_read": read_files,
        "commands": commands,
        "sinks": sinks,
        "background_pending": pending,
        "background_resolved": bg_resolved,
        "user_turns": user_turns,
        "assistant_turns": assistant_turns,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "usage": usage,
        "model": model,
    }


def _parse_task_notifications(raw: str, into: dict[str, str]) -> None:
    """Record `<task-id>X</task-id> … <status>S</status>` pairs, status matched per id block."""
    for m in TASK_BLOCK_RE.finditer(raw):
        sm = TASK_STATUS_RE.search(m.group(2))
        into[m.group(1)] = (sm.group(1).strip() if sm else "resolved") or "resolved"


def _push(lst: list[str], value: str, cap: int = 400) -> None:
    if value not in lst and len(lst) < cap:
        lst.append(value)


def _blob_len(obj) -> int:
    try:
        return len(json.dumps(obj, default=str))
    except Exception:
        return 0


def _background_id(rec: dict, block: dict) -> str | None:
    tur = rec.get("toolUseResult")
    if isinstance(tur, dict):
        tid = tur.get("backgroundTaskId")
        if isinstance(tid, str) and tid:
            return tid
    text = block.get("content")
    if isinstance(text, list):
        text = " ".join(str(b.get("text", "")) for b in text if isinstance(b, dict))
    if isinstance(text, str):
        m = BG_ID_RE.search(text)
        if m:
            return m.group(1)
    return None


def git_info(cwd: str | None) -> dict:
    """Read-only git facts. Any failure yields {}."""
    if not cwd or not os.path.isdir(cwd):
        return {}
    out = {}
    for key, args in (
        ("branch", ["rev-parse", "--abbrev-ref", "HEAD"]),
        ("head", ["rev-parse", "--short", "HEAD"]),
        ("dirty", ["status", "--porcelain"]),
    ):
        try:
            r = subprocess.run(["git", "-C", cwd] + args, capture_output=True,
                               text=True, timeout=5)
        except Exception:
            continue
        if r.returncode == 0:
            out[key] = r.stdout.strip()
    if "dirty" in out:
        files = [ln[3:] for ln in out["dirty"].splitlines() if len(ln) > 3][:20]
        out["dirty"] = files
    return out


# ---------------------------------------------------------------- handoff file

def parse_handoff(text: str) -> tuple[list[str], dict[str, str]]:
    """Split a handoff markdown into (header lines, {SECTION: body})."""
    header: list[str] = []
    bodies: dict[str, str] = {}
    current = None
    buf: list[str] = []
    known = {s.upper(): s for s in SECTIONS}
    for line in (text or "").splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m and m.group(1).strip().upper() in known:
            if current:
                bodies[current] = "\n".join(buf).strip()
            current = known[m.group(1).strip().upper()]
            buf = []
            continue
        (buf if current else header).append(line)
    if current:
        bodies[current] = "\n".join(buf).strip()
    return header, bodies


def render_handoff(meta: dict, bodies: dict[str, str]) -> str:
    lines = [
        "# Smart-compact handoff",
        "",
        f"- session: `{meta.get('session_id', 'unknown')}`",
        f"- project: `{meta.get('cwd', '')}`",
        f"- updated: {meta.get('updated', _now())}",
        f"- turns: {meta.get('turns', 0)}",
    ]
    if meta.get("notes"):           # when the model last wrote GOAL/NEXT/…, and at which turn
        lines += [f"- notes: {meta['notes']}", f"- notes-turns: {meta.get('notes_turns', 0)}"]
    lines.append("")
    for name in SECTIONS:
        body = (bodies.get(name) or "").strip() or PLACEHOLDER
        lines.append(f"## {name}")
        lines.append("")
        lines.append(body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def has_model_content(bodies: dict[str, str]) -> bool:
    for name in MODEL_SECTIONS:
        body = (bodies.get(name) or "").strip()
        if body and body != PLACEHOLDER:
            return True
    return False


def auto_bodies(scan: dict, cwd: str | None, window_info: tuple[int, str]) -> dict[str, str]:
    window, source = window_info
    used = used_tokens(scan.get("usage"))
    pct = fill_percent(used, window)
    git = git_info(cwd)

    state = [
        f"- context: ~{used:,} / {window:,} tokens ({pct}% — estimate, {source})",
        f"- turns: {scan['user_turns']} user / {scan['assistant_turns']} assistant",
    ]
    if scan.get("first_ts") or scan.get("last_ts"):
        state.append(f"- span: {scan.get('first_ts') or '?'} → {scan.get('last_ts') or '?'}")
    if git.get("branch"):
        state.append(f"- git: `{git['branch']}` @ `{git.get('head', '?')}`")
    if git.get("dirty"):
        state.append("- dirty files: " + ", ".join(f"`{f}`" for f in git["dirty"]))
    elif "dirty" in git:
        state.append("- working tree clean")
    if scan["commands"]:
        state.append("- state-changing commands run (last 8):")
        state += [f"  - `{c[:120]}`" if not SECRET_RE.search(c)
                  else "  - <redacted: the command touched a credential>"
                  for c in scan["commands"][-8:]]

    files = []
    if scan["files_written"]:
        files.append("Written / edited:")
        files += [f"- `{f}`" for f in scan["files_written"][:30]]

    inflight = []
    for tid, info in scan["background_pending"].items():
        label = tid.split(":", 1)[1] if tid.startswith("unknown:") else tid
        note = " (id unknown — check `/tasks`)" if tid.startswith("unknown:") else ""
        desc = info.get("description") or info.get("command") or info.get("tool") or "?"
        inflight.append(f"- `{label}`{note} — {desc}")
    if inflight:
        inflight.insert(0, "Still running at snapshot time. Compaction does NOT kill these "
                           "(verified — research §H); what it destroys is the model's handle "
                           "on them, since task ids live in the replaced conversation. They "
                           "are listed here so they stay addressable. Re-check output files "
                           "(and `/tasks`) rather than the model's memory:")

    return {
        "STATE": "\n".join(state),
        "FILES": "\n".join(files),
        "IN-FLIGHT": "\n".join(inflight),
    }


def write_snapshot(transcript: str | None, session_id: str, cwd: str | None,
                   model_notes: str | None = None) -> Path:
    scan = (scan_transcript(transcript) if transcript and os.path.exists(transcript)
            else _empty_scan())
    path = handoff_path(session_id)

    # Fold in copies older versions left under cwd-slug dirs (oldest first, so the newest
    # wins per section): that is where the notes of a drifted session are stranded.
    head: list[str] = []
    bodies: dict[str, str] = {}
    legacy = sorted(state_root().glob(f"*/{safe_id(session_id)}.md"), key=lambda f: f.stat().st_mtime)
    for f in legacy + ([path] if path.exists() else []):
        try:
            h, b = parse_handoff(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        head = h
        bodies.update({k: v for k, v in b.items() if (v or "").strip() not in ("", PLACEHOLDER)})
    notes_at = _header_value(head, "notes")
    notes_turns = _header_value(head, "notes-turns")

    if model_notes:
        notes_at, notes_turns = _now(), scan["assistant_turns"]
        _, notes = parse_handoff(model_notes)
        if not notes:                       # fragment with no headings → treat as GOAL prose
            notes = {"GOAL": model_notes.strip()}
        for name in MODEL_SECTIONS:
            body = (notes.get(name) or "").strip()
            if body and body != PLACEHOLDER:
                bodies[name] = body

    bodies.update(auto_bodies(scan, cwd, context_window(
        scan.get("model"), used_tokens(scan.get("usage")), cwd)))
    text = render_handoff({"session_id": session_id, "cwd": cwd or "", "updated": _now(),
                           "turns": scan["assistant_turns"], "notes": notes_at,
                           "notes_turns": notes_turns}, bodies)
    path.write_text(text, encoding="utf-8")
    return path


def _empty_scan() -> dict:
    return {
        "files_written": [], "files_read": [], "commands": [], "sinks": {},
        "background_pending": {}, "background_resolved": {},
        "user_turns": 0, "assistant_turns": 0,
        "first_ts": None, "last_ts": None, "usage": None, "model": None,
    }


# ---------------------------------------------------------------- capped render

def render_capped(bodies: dict[str, str], max_chars: int, header: str = "") -> str:
    """Render the handoff under a hard char cap, dropping least-important sections first."""
    work = {n: (bodies.get(n) or "").strip() for n in SECTIONS}
    work = {n: ("" if b == PLACEHOLDER else b) for n, b in work.items()}
    # No single section may starve the rest: real notes put whole reports under GOAL.
    third = max(200, max_chars // 3)
    work = {n: (b if len(b) <= third else b[:third].rstrip() + "\n… [truncated]")
            for n, b in work.items()}
    drop_order = list(reversed(SECTIONS))

    def build() -> str:
        out = [header] if header else []
        for name in SECTIONS:
            if work.get(name):
                out.append(f"## {name}\n\n{work[name]}\n")
        return "\n".join(out).strip() + "\n"

    text = build()
    for _ in range(len(SECTIONS) * 3):
        if len(text) <= max_chars:
            break
        target = next((n for n in drop_order if work.get(n)), None)
        if target is None:
            break
        over = len(text) - max_chars
        body = work[target]
        keep = len(body) - over - 24
        if keep > 120:
            work[target] = body[:keep].rstrip() + "\n… [truncated]"
        else:
            work[target] = ""
        text = build()
    return text[:max_chars]


# ---------------------------------------------------------------- transcript discovery

def find_transcript(cwd: str | None, session_id: str | None = None) -> str | None:
    """This session's .jsonl under <config dir>/projects.

    Claude Code exports the live session id as CLAUDE_CODE_SESSION_ID: with it, find
    <session_id>.jsonl in ANY project dir, and never guess. Without it, newest-by-mtime in
    the cwd's project dir (walking up parents) — a guess that is regularly a parallel
    session, so callers should pass the id.
    """
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "projects"
    sid = (session_id or os.environ.get("CLAUDE_CODE_SESSION_ID") or "").strip()
    if sid:
        hits = [f for f in base.glob(f"*/{safe_id(sid)}.jsonl") if f.is_file()]
        return str(max(hits, key=lambda f: f.stat().st_mtime)) if hits else None
    p = Path(os.path.normpath(cwd or os.getcwd()))
    for cand in [p] + list(p.parents):
        d = base / re.sub(r"[^A-Za-z0-9]", "-", str(cand))
        if not d.is_dir():
            continue
        files = sorted((f for f in d.glob("*.jsonl") if f.is_file()),
                       key=lambda f: f.stat().st_mtime, reverse=True)
        if files:
            return str(files[0])
    return None


def resolve_transcript(arg: str | None, cwd: str | None) -> str | None:
    if arg and os.path.exists(arg):
        return arg
    return find_transcript(cwd)


# ---------------------------------------------------------------- subcommand: health

def cmd_health(args) -> int:
    cwd = args.cwd or os.getcwd()
    transcript = resolve_transcript(args.transcript, cwd)
    if not transcript:
        sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
        msg = (f"transcript for session {sid} not found — pass --transcript PATH" if sid
               else "no transcript found — pass --transcript PATH")
        print(json.dumps({"error": msg}) if args.json else msg)
        return 1

    scan = scan_transcript(transcript)
    used = used_tokens(scan.get("usage"))
    window, source = context_window(scan.get("model"), used, cwd)
    pct = fill_percent(used, window)
    # The transcript filename stem IS the session id (one sessionId per file). Printing it
    # is what lets `snapshot --session-id` key the handoff the way the hooks read it back.
    session_id = Path(transcript).stem
    thresholds = thresholds_from_env()
    verdict = verdict_for(pct, thresholds)

    sinks = sorted(scan["sinks"].items(), key=lambda kv: kv[1], reverse=True)[:6]
    sinks = [(name, chars // CHARS_PER_TOKEN) for name, chars in sinks if chars > 0]

    if args.json:
        print(json.dumps({
            "transcript": transcript,
            "session_id": session_id,
            "cwd": cwd,
            "model": scan.get("model"),
            "used_tokens": used,
            "window": window,
            "window_source": source,
            "fill_percent": pct,
            "user_turns": scan["user_turns"],
            "assistant_turns": scan["assistant_turns"],
            "top_sinks": [{"source": n, "approx_tokens": t} for n, t in sinks],
            "background_pending": list(scan["background_pending"].keys()),
            "files_written": scan["files_written"][:50],
            "verdict": verdict,
            "note": "used = input + cache_creation + cache_read (estimate, not harness ground truth)",
        }, indent=2))
        return 0

    bar_len = 30
    filled = min(bar_len, int(round(pct / 100 * bar_len)))
    print("context health")
    print(f"  session id : {session_id}")
    print(f"  cwd        : {cwd}")
    print(f"  transcript : {transcript}")
    print(f"  model      : {scan.get('model') or 'unknown'}")
    print(f"  used       : ~{used:,} tokens  (estimate: input + cache_creation + cache_read)")
    print(f"  window     : {window:,}  ({source})")
    print(f"  fill       : {pct}%  [{'#' * filled}{'.' * (bar_len - filled)}]")
    print(f"  turns      : {scan['user_turns']} user / {scan['assistant_turns']} assistant")
    if sinks:
        print("  top sinks  : (approx, by transcript bytes)")
        for name, tok in sinks:
            print(f"      {name:<22} ~{tok:,} tok")
    if scan["background_pending"]:
        print(f"  in-flight  : {len(scan['background_pending'])} background task(s) — "
              "compaction won't kill them, but record the ids (the handle is what's lost)")
    print(f"verdict: {verdict}")
    if verdict != "OK":
        print(f"  → run {CMD} (compact at a task boundary, never mid-edit)")
    return 0


# ---------------------------------------------------------------- subcommand: snapshot

def cmd_snapshot(args) -> int:
    cwd = args.cwd or os.getcwd()
    transcript = resolve_transcript(args.transcript, cwd)
    session_id = args.session_id or (Path(transcript).stem if transcript else "unknown")
    notes = None
    if args.merge_model_notes:
        try:
            notes = Path(args.merge_model_notes).read_text(encoding="utf-8")
        except OSError as e:
            print(f"could not read --merge-model-notes: {e}", file=sys.stderr)
    path = write_snapshot(transcript, session_id, cwd, notes)
    print(str(path))
    return 0


# ---------------------------------------------------------------- subcommand: search

def _record_texts(rec: dict):
    """(label, text) pairs worth searching in one transcript record."""
    rtype = rec.get("type") or "?"
    if rtype.startswith("api-request"):
        return      # request plumbing: re-sent copies of the system prompt and history (noise)
    if rtype == "attachment":       # hook output, queued user prompts, notifications, reminders
        att = rec.get("attachment") if isinstance(rec.get("attachment"), dict) else {}
        shown = rec.get("rendered")
        yield f"attachment/{att.get('type')}", (
            "\n".join(str(x.get("content", "")) for x in shown if isinstance(x, dict))
            if isinstance(shown, list) else json.dumps(att, ensure_ascii=False))
        return
    msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
    content = msg.get("content", rec.get("content", rec.get("summary")))
    if isinstance(content, str):
        yield rtype, content
        return
    for b in content if isinstance(content, list) else []:
        if not isinstance(b, dict):
            continue
        t = b.get("type")
        if t == "text":
            yield rtype, b.get("text") or ""
        elif t == "thinking":
            yield f"{rtype}/thinking", b.get("thinking") or ""
        elif t == "tool_use":
            yield f"tool_use {b.get('name')}", json.dumps(b.get("input"), ensure_ascii=False)
        elif t == "tool_result":
            c = b.get("content")
            if isinstance(c, list):
                c = "\n".join(str(x.get("text", "")) for x in c if isinstance(x, dict))
            yield "tool_result", c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)


def search_files(files: list[Path], rx: re.Pattern, base: Path | None, limit: int,
                 width: int = 140):
    """Yield one short line per hit and finally the total hit count (an int)."""
    hits = 0
    for f in files:
        name = str(f.relative_to(base)) if base else str(f)
        jsonl = f.name.endswith((".jsonl", ".jsonl.gz"))
        try:
            fh = (gzip.open if f.suffix == ".gz" else open)(f, "rt", encoding="utf-8",
                                                           errors="replace")
        except OSError:
            continue
        with fh:
            for n, line in enumerate(fh, 1):
                pairs = [("text", line)]
                ts = ""
                if jsonl:
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    if not isinstance(rec, dict):
                        continue
                    ts = (rec.get("timestamp") or "")[:19]
                    pairs = list(_record_texts(rec))
                for label, text in pairs:
                    m = rx.search(text or "")
                    if not m:
                        continue
                    hits += 1
                    if hits <= limit:
                        lo, hi = max(0, m.start() - width), m.end() + width
                        snip = re.sub(r"\s+", " ", text[lo:hi]).strip()
                        yield (f"{name}:{n} {ts} [{label}] "
                               f"{'…' if lo else ''}{snip}{'…' if hi < len(text) else ''}")
    yield hits


def cmd_search(args) -> int:
    try:
        rx = re.compile(args.pattern, re.I)
    except re.error as e:
        print(f"bad regex: {e}")
        return 1
    if args.file:
        files, base = [Path(args.file)], None
    else:
        sid = args.session_id or os.environ.get("CLAUDE_CODE_SESSION_ID") or ""
        if not sid:                     # guessing picks a parallel session: refuse instead
            print("no session id — run inside Claude Code, or pass --session-id / --file")
            return 1
        live = find_transcript(args.cwd, sid)
        if live:                        # the live transcript is append-only: a superset
            base = Path(live).parent
            files = [Path(live)] + _text_files(Path(live).with_suffix(""))
            print(f"searching live session {live} (+ subagents, tool results)")
        else:
            backups = find_backups(sid)
            if not backups:
                print(f"session {sid}: no live transcript and no backup")
                return 1
            base = backups[-1]
            files = sorted(_text_files(base), key=lambda f: (not f.name.startswith("transcript."),
                                                              str(f)))
            print(f"live transcript is gone — searching backup {base}")
    total = 0
    for out in search_files(files, rx, base, args.max):
        if isinstance(out, int):
            total = out
        else:
            print(out)
    if total > args.max:
        print(f"… {total - args.max} more hit(s) not shown — narrow the regex or raise --max")
    print(f"{total} hit(s)")
    return 0


BINARY = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip"}


def _text_files(d: Path) -> list[Path]:
    return (sorted(f for f in d.rglob("*") if f.is_file() and f.suffix.lower() not in BINARY)
            if d.is_dir() else [])


def search_hint() -> str:
    return (f"Missing a detail? Run `python3 '{Path(__file__).resolve()}' search '<regex>'` — "
            "bounded (20 hits, short snippets, request plumbing skipped), covering this whole "
            "session incl. subagents and tool results, with a full backup taken right before "
            "compaction. Do not Read/cat/grep the transcript yourself: tens of MB of duplicated "
            "request blobs would flood this fresh context. Example: `search 'PR #?\\d+|RD-\\d+'`.\n")


# ---------------------------------------------------------------- hook bodies
# Each returns the string to print on stdout (or None). Wrappers below guarantee exit 0.

def claim(kind: str, session_id: str, transcript: str | None) -> bool:
    """True for the first caller of one hook event, False for any duplicate.

    Two plugins ship this script and share the default state dir (an ENV + "HOME" override
    moves only one copy's root and so disables this). Their hook command strings are
    identical before `${CLAUDE_PLUGIN_ROOT}` expands, and Claude Code 2.1.314 ran only one of
    them with both plugins loaded (E2E, 2026-10-30) — this is the net for when it runs both,
    in parallel. The transcript size keys the event: every later event sees a bigger file. Assumed, not verified: the harness appends nothing between the two launches of
    one event (they start within milliseconds) — if it did, both copies would act, which is
    the pre-dedupe behaviour, not a loss.
    """
    try:
        size = os.path.getsize(transcript) if transcript else 0
    except OSError:
        size = 0
    d = state_root() / ".claims"
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.close(os.open(d / f"{safe_id(session_id)}.{kind}.{size}",
                         os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return False
    cutoff = time.time() - 86_400
    for f in d.iterdir():
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            pass
    return True


def backup_session(transcript: str | None, session_id: str,
                   trigger: str = "") -> tuple[Path, int, int, int] | None:
    """FULL backup of the session right before compaction: (dir, gz bytes, linked, evicted).

    The main transcript is gzip-copied: a snapshot at the compaction boundary. Everything in
    the sibling `<session_id>/` dir (subagents/, tool-results/ — up to ~700 MB) is HARDLINKED:
    no bytes, no time, and the content survives Claude Code deleting the original
    (`cleanupPeriodDays`), because unlinking one name keeps the inode.
    shortcut: a hardlink follows later appends/rewrites of the same inode; side files are
    write-once or append-only, so that is fine — copy them if that ever changes.
    Written to `<dir>.partial` and renamed, so a hook timeout never leaves a backup that
    looks complete. Owner-only (umask 077): transcripts can hold secrets.
    """
    if not transcript or not os.path.isfile(transcript):
        return None
    root = state_root() / "backups" / safe_id(session_id)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = root / f"{stamp}-{re.sub(r'[^a-z]+', '', trigger.lower()) or 'manual'}"
    n = 1
    while dest.exists() or dest.with_name(dest.name + ".partial").exists():
        n += 1
        dest = dest.with_name(f"{dest.name.split('~')[0]}~{n}")
    tmp = dest.with_name(dest.name + ".partial")
    files = 0
    old_umask = os.umask(0o077)
    try:
        tmp.mkdir(parents=True)
        with open(transcript, "rb") as fi, gzip.open(tmp / "transcript.jsonl.gz", "wb",
                                                     compresslevel=1) as fo:
            shutil.copyfileobj(fi, fo, 1 << 20)
        side = Path(transcript).with_suffix("")
        for src in (sorted(side.rglob("*")) if side.is_dir() else []):
            if not src.is_file():
                continue
            out = tmp / src.relative_to(side)
            out.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(src, out)
            except OSError:             # other filesystem / no link support: real copy
                try:
                    shutil.copy2(src, out)
                except OSError:
                    continue            # vanished mid-backup: keep the rest
            files += 1
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    finally:
        os.umask(old_umask)
    tmp.rename(dest)
    total = (dest / "transcript.jsonl.gz").stat().st_size
    return dest, total, files, prune_backups(root, dest)


def _own_bytes(d: Path) -> int:
    """Bytes only this backup holds: a hardlink whose original still exists costs nothing."""
    total = 0
    for f in d.rglob("*"):
        try:
            st = f.stat()
        except OSError:
            continue
        if f.is_file() and st.st_nlink == 1:
            total += st.st_size
    return total


def prune_backups(session_root: Path, keep: Path) -> int:
    """Newest KEEP_BACKUPS per session, then the global BACKUP_CAP_BYTES, oldest first."""
    done = sorted(p for p in session_root.iterdir() if not p.name.endswith(".partial"))
    for old in done[:-KEEP_BACKUPS]:
        shutil.rmtree(old, ignore_errors=True)
    for p in session_root.glob("*.partial"):           # left by a hook that timed out
        if p.stat().st_mtime < time.time() - 3600:
            shutil.rmtree(p, ignore_errors=True)
    every = sorted((p for p in state_root().glob("backups/*/*")
                    if p.is_dir() and not p.name.endswith(".partial")), key=lambda p: p.name)
    sizes = {p: _own_bytes(p) for p in every}
    used, evicted = sum(sizes.values()), 0
    for p in every:
        if used <= BACKUP_CAP_BYTES:
            break
        if p != keep:
            shutil.rmtree(p, ignore_errors=True)
            used -= sizes[p]
            evicted += 1
    return evicted


def find_backups(session_id: str) -> list[Path]:
    """Completed backups of a session, oldest first."""
    return sorted((p for p in state_root().glob(f"backups/{safe_id(session_id)}/*")
                   if p.is_dir() and not p.name.endswith(".partial")), key=lambda p: p.name)


def hook_precompact_body(payload: dict) -> str:
    cwd = payload.get("cwd") or os.getcwd()
    session_id = payload.get("session_id") or "unknown"
    transcript = payload.get("transcript_path")
    trigger = (payload.get("trigger") or "").lower()
    if not claim("precompact", session_id, transcript):
        return json.dumps({})           # the other installed copy already handled this event

    # A compaction is the definitive context reset: forget which thresholds already nagged,
    # so the next climb toward the wall warns again instead of staying silent forever.
    # First, so a slow backup that hits the hook timeout cannot skip it.
    try:
        nag_path(session_id).unlink()
    except OSError:
        pass
    path = write_snapshot(transcript, session_id, cwd, None)
    try:
        saved = backup_session(transcript, session_id, trigger)
        backup_msg = (f"💾 Full session backup → {saved[0]} (transcript {saved[1] / 1e6:.1f} MB "
                      f"gzip + {saved[2]} subagent/tool-result files hardlinked)" if saved
                      else "⚠ No session backup: transcript not found.")
        if saved and saved[3]:
            backup_msg += (f" ({saved[3]} oldest backup(s) evicted to stay under "
                           f"{BACKUP_CAP_BYTES >> 30} GB.)")
    except Exception as e:              # never let a full disk block the compaction
        backup_msg = f"⚠ Session backup FAILED ({type(e).__name__}: {e}) — compaction goes ahead."

    _, bodies = parse_handoff(path.read_text(encoding="utf-8"))
    steered = has_model_content(bodies)

    # `background_tasks` is documented only on Stop/SubagentStop, but read it if it shows up.
    bg = payload.get("background_tasks")

    out: dict = {"systemMessage": backup_msg}
    if trigger == "auto" and not steered:
        warn = (
            f"⚠ Unsteered AUTO-compact just fired — you did not run {CMD}, "
            "so the summarizer chose what to keep. An auto-extracted handoff was written to "
            f"{path} (files touched, state, in-flight work), but the goal, decisions and "
            f"'do not redo' list were never captured. Next time run {CMD} at a "
            "task boundary. Consider raising the nag thresholds "
            f"({ENV}THRESHOLDS)."
        )
        if isinstance(bg, list) and bg:
            warn += f" {len(bg)} background task(s) were in flight — verify their output files."
        out["systemMessage"] = warn + "\n" + backup_msg
    return json.dumps(out)


def hook_sessionstart_body(payload: dict) -> str | None:
    if (payload.get("source") or "").lower() != "compact":
        return None
    session_id = payload.get("session_id") or "unknown"
    path = handoff_path(session_id)
    if not path.exists():
        return None
    head, bodies = parse_handoff(path.read_text(encoding="utf-8"))
    if not any((bodies.get(n) or "").strip() not in ("", PLACEHOLDER) for n in SECTIONS):
        return None
    if not claim("sessionstart", session_id, payload.get("transcript_path")):
        return None                     # the other installed copy already injected it
    return render_capped(bodies, max_chars_from_env(),
                         _recovered_header(head, has_model_content(bodies)))


def _age_minutes(stamp: str | None) -> float | None:
    """Minutes since a `%Y-%m-%dT%H:%M:%SZ` stamp, or None if missing/unreadable."""
    try:
        t = datetime.strptime(stamp or "", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return max(0.0, (datetime.now(timezone.utc) - t).total_seconds() / 60.0)


def _recovered_header(header_lines: list[str], has_notes: bool) -> str:
    title = f"# Recovered handoff ({CMD[1:]})\n\n" + search_hint() + "\n"
    if not has_notes:
        return title + ("Auto-extracted at compaction only — no GOAL, DECISIONS, DO-NOT-REDO or "
                        "NEXT were recorded, so do not infer them from this file. STATE, FILES "
                        "and IN-FLIGHT are facts read from the transcript.\n")
    age = _age_minutes(_header_value(header_lines, "notes"))
    try:
        turns = (int(_header_value(header_lines, "turns") or "")
                 - int(_header_value(header_lines, "notes-turns") or ""))
    except ValueError:
        turns = None
    when = ("at an unknown time" if age is None else
            f"{int(age)} min" if age < 60 else f"{age / 60:.1f} h")
    if turns is not None and age is not None:
        when += f" and {turns} assistant messages"
    stale = age is None or age >= STALE_AFTER_MIN or (turns or 0) >= STALE_AFTER_TURNS
    trust = (
        "Work went on after they were written: NEXT and STATE may be out of date — check them "
        "against the summary above before acting. DO-NOT-REDO and DECISIONS stay binding."
        if stale else
        "Where they disagree with the summary above, this file is authoritative."
    )
    return title + (
        f"Model notes (GOAL, NEXT, DO-NOT-REDO, DECISIONS) were written {when} before this "
        f"compaction; STATE, FILES and IN-FLIGHT were refreshed at compaction. {trust} "
        "Do not redo work listed under DO-NOT-REDO.\n"
    )


def _write_nag(path: Path, crossed: list[int], pct: float) -> None:
    try:
        path.write_text(json.dumps({"crossed": sorted(set(crossed)), "pct": pct, "at": _now()}),
                        encoding="utf-8")
    except OSError:
        pass


def hook_nag_body(payload: dict) -> str | None:
    if payload.get("stop_hook_active"):
        return None                     # already inside a stop-hook loop; stay out of it
    cwd = payload.get("cwd") or os.getcwd()
    session_id = payload.get("session_id") or "unknown"
    transcript = payload.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        return None

    usage, model = last_usage(transcript)
    if not usage:
        return None
    used = used_tokens(usage)
    window, _ = context_window(model, used, cwd)
    pct = fill_percent(used, window)
    thresholds = thresholds_from_env()

    npath = nag_path(session_id)
    already: list[int] = []
    if npath.exists():
        try:
            data = json.loads(npath.read_text(encoding="utf-8"))
            already = [int(x) for x in data.get("crossed", []) if isinstance(x, (int, float))]
        except Exception:
            already = []
    # A compaction keeps the same session id AND the same transcript file, so this state
    # survives it. Drop (and persist the drop of) thresholds the context has since fallen
    # back below, or the nagger goes permanently silent after the first compaction — in
    # exactly the long sessions that compact several times, which is the whole point of
    # the feature. hook-precompact clears the file outright; this self-heals every other
    # context drop too.
    pruned = [t for t in already if t <= pct]

    fresh = newly_crossed(pct, pruned, thresholds)
    if not fresh:
        if pruned != already:
            _write_nag(npath, pruned, pct)
        return None
    _write_nag(npath, pruned + fresh, pct)
    top = fresh[-1]
    if not claim(f"nag{top}", session_id, transcript):
        return None
    if top >= thresholds[-1]:
        msg = (f"🔴 Context {pct}% full — auto-compact is close, and it will pick what to keep. "
               f"Run {CMD} NOW, at the next clean boundary.")
    elif top >= thresholds[0] and len(thresholds) > 1 and top >= thresholds[1]:
        msg = (f"🟠 Context {pct}% full — plan a compaction boundary (test green / commit made). "
               f"Run {CMD}.")
    else:
        msg = (f"🟡 Context {pct}% full — output quality already drifts around here, long before "
               f"the window fills. Run {CMD} at the next task boundary.")
    # systemMessage: shown to the human, never added to model context.
    return json.dumps({"systemMessage": msg})


def run_hook(fn) -> int:
    """Read stdin JSON, run a hook body, print its output. Never fails the session."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
        out = fn(payload)
        if out:
            sys.stdout.write(out if out.endswith("\n") else out + "\n")
    except Exception:
        pass                            # broken hook must never break the session
    return 0


# ---------------------------------------------------------------- demo

def _demo_transcript(path: Path) -> None:
    def a(blocks, usage=None, model="claude-opus-5"):
        msg = {"role": "assistant", "model": model, "content": blocks}
        if usage is not None:
            msg["usage"] = usage
        return {"type": "assistant", "isSidechain": False, "timestamp": "2026-08-16T10:00:00Z",
                "message": msg}

    def u(content, tool_use_result=None, origin=None):
        rec = {"type": "user", "timestamp": "2026-08-16T10:00:01Z",
               "message": {"role": "user", "content": content}}
        if tool_use_result is not None:
            rec["toolUseResult"] = tool_use_result
        if origin is not None:
            rec["origin"] = origin
        return rec

    lines = [
        u("build the thing"),
        a([{"type": "tool_use", "id": "t1", "name": "Write",
            "input": {"file_path": "/tmp/a.py", "content": "x"}}]),
        u([{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]),
        a([{"type": "tool_use", "id": "t2", "name": "Edit",
            "input": {"file_path": "/tmp/b.py", "old_string": "a", "new_string": "b"}}]),
        a([{"type": "tool_use", "id": "t3", "name": "Read",
            "input": {"file_path": "/tmp/c.py", "offset": 1, "limit": 10}}]),
        a([{"type": "tool_use", "id": "t4", "name": "Bash",
            "input": {"command": "git commit -m 'x'", "description": "commit"}}]),
        a([{"type": "tool_use", "id": "t5", "name": "Bash",
            "input": {"command": "sleep 100", "description": "long job",
                      "run_in_background": True}}]),
        u([{"type": "tool_result", "tool_use_id": "t5", "content": "Command running in background"}],
          tool_use_result={"backgroundTaskId": "bg123"}),
        a([{"type": "tool_use", "id": "t6", "name": "Bash",
            "input": {"command": "sleep 5", "description": "short job",
                      "run_in_background": True}}]),
        u([{"type": "tool_result", "tool_use_id": "t6", "content": "started"}],
          tool_use_result={"backgroundTaskId": "bg999"}),
        u("<task-notification>\n<task-id>bg999</task-id>\n<status>completed</status>\n"
          "</task-notification>", origin={"kind": "task-notification"}),
        a([{"type": "tool_use", "id": "t7", "name": "Bash",
            "input": {"command": "sleep 7", "description": "queued job",
                      "run_in_background": True}}]),
        u([{"type": "tool_result", "tool_use_id": "t7", "content": "started"}],
          tool_use_result={"backgroundTaskId": "bg777"}),
        # The common real shape: notification on the TOP-LEVEL content of a non-user record.
        {"type": "queue-operation", "timestamp": "2026-08-16T10:00:02Z",
         "content": "<task-notification>\n<task-id>bg777</task-id>\n"
                    "<status>completed</status>\n</task-notification>"},
        a([{"type": "text", "text": "done"}],
          usage={"input_tokens": 5, "cache_creation_input_tokens": 10000,
                 "cache_read_input_tokens": 90000, "output_tokens": 500}),
        a([{"type": "text", "text": "No response requested."}],
          usage={"input_tokens": 0, "cache_creation_input_tokens": 0,
                 "cache_read_input_tokens": 0, "output_tokens": 0},
          model="<synthetic>"),
    ]
    with open(path, "w", encoding="utf-8") as f:
        for rec in lines:
            f.write(json.dumps(rec) + "\n")
        f.write("{not json at all\n")            # malformed line must be tolerated
        f.write("\n")


def cmd_demo(_args=None) -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        os.environ[ENV + "HOME"] = str(tmp / "state")
        os.environ.pop(ENV + "THRESHOLDS", None)
        os.environ.pop(ENV + "MAX_CHARS", None)
        os.environ.pop(ENV + "WINDOW", None)
        tpath = tmp / "session.jsonl"
        _demo_transcript(tpath)

        def reset_claims():         # each demo step stands for a new hook event
            shutil.rmtree(state_root() / ".claims", ignore_errors=True)

        assert claim("x", "s", str(tpath)) and not claim("x", "s", str(tpath))

        # --- parsing -------------------------------------------------------
        scan = scan_transcript(tpath)
        assert scan["files_written"] == ["/tmp/a.py", "/tmp/b.py"], scan["files_written"]
        assert scan["files_read"] == ["/tmp/c.py"], scan["files_read"]
        assert any("git commit" in c for c in scan["commands"]), scan["commands"]
        assert "bg123" in scan["background_pending"], scan["background_pending"]
        assert "bg999" not in scan["background_pending"], scan["background_pending"]
        assert scan["background_resolved"].get("bg999") == "completed", scan["background_resolved"]
        # completion seen only on a top-level `content` field of a non-user record
        assert "bg777" not in scan["background_pending"], scan["background_pending"]
        assert scan["background_resolved"].get("bg777") == "completed", scan["background_resolved"]
        assert scan["user_turns"] == 1, scan["user_turns"]
        assert scan["model"] == "claude-opus-5", scan["model"]   # synthetic record ignored

        # status is attributed per task-id block, not "first status wins for every id"
        parsed: dict[str, str] = {}
        _parse_task_notifications("<task-id>x1</task-id><status>failed</status>"
                                  "<task-id>x2</task-id><status>completed</status>", parsed)
        assert parsed == {"x1": "failed", "x2": "completed"}, parsed

        # --- fill arithmetic ----------------------------------------------
        usage, model = last_usage(tpath)
        assert usage == scan["usage"], (usage, scan["usage"])
        assert model == "claude-opus-5", model
        used = used_tokens(usage)
        assert used == 100_005, used                              # output_tokens excluded
        assert fill_percent(used, 200_000) == 50.0
        real_home = os.environ.get("HOME")
        os.environ["HOME"] = str(tmp / "fakehome")   # no settings.json at all
        try:
            assert context_window("claude-opus-5", 100_005)[0] == 1_000_000
            assert context_window("claude-opus-5")[0] == 1_000_000   # no `[1m]` needed
            # project-level settings are read, not just the user's
            proj = tmp / "projcfg" / ".claude"
            proj.mkdir(parents=True, exist_ok=True)
            (proj / "settings.json").write_text('{"autocompactTokenCount": 123456}',
                                                encoding="utf-8")
            assert context_window("claude-opus-5", 0, str(tmp / "projcfg"))[0] == 123_456
        finally:
            if real_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = real_home
        # pin a 200K window so the rest of the demo is hermetic and exercises the override
        os.environ[ENV + "WINDOW"] = "200000"
        assert context_window("claude-opus-5[1m]") == (200_000, ENV + "WINDOW")
        assert verdict_for(10, DEFAULT_THRESHOLDS) == "OK"
        assert verdict_for(55, DEFAULT_THRESHOLDS) == "compact soon"
        assert verdict_for(90, DEFAULT_THRESHOLDS) == "compact now"

        # --- threshold crossing, pure -------------------------------------
        assert newly_crossed(50.0, [], DEFAULT_THRESHOLDS) == [50]
        assert newly_crossed(50.0, [50], DEFAULT_THRESHOLDS) == []
        assert newly_crossed(86.0, [50], DEFAULT_THRESHOLDS) == [70, 85]

        # --- threshold crossing, end-to-end (fires at most once) ----------
        payload = {"cwd": str(tmp / "proj"), "session_id": "sess1",
                   "transcript_path": str(tpath)}
        (tmp / "proj").mkdir(exist_ok=True)
        first = hook_nag_body(payload)
        assert first and "systemMessage" in first, first
        assert "50" in json.loads(first)["systemMessage"]
        second = hook_nag_body(payload)
        assert second is None, second                             # does not fire twice
        assert hook_nag_body(dict(payload, stop_hook_active=True)) is None

        # ...but it DOES fire again after the context drops and climbs back (post-compaction).
        low = tmp / "low.jsonl"
        low.write_text(json.dumps({
            "type": "assistant", "isSidechain": False,
            "message": {"role": "assistant", "model": "claude-opus-5",
                        "usage": {"input_tokens": 1, "cache_creation_input_tokens": 0,
                                  "cache_read_input_tokens": 10_000, "output_tokens": 1}},
        }) + "\n", encoding="utf-8")
        assert hook_nag_body(dict(payload, transcript_path=str(low))) is None   # 5% — prunes
        with open(tpath, "a", encoding="utf-8") as f:   # a later turn: the transcript grew
            f.write("{}\n")
        again = hook_nag_body(payload)                                          # back to 50%
        assert again and "50" in json.loads(again)["systemMessage"], again

        # --- snapshot + model-note merge ----------------------------------
        notes = tmp / "notes.md"
        notes.write_text("## GOAL\n\nShip the widget.\n\n## NEXT\n\nRun the tests.\n",
                         encoding="utf-8")
        hpath = write_snapshot(str(tpath), "sess1", str(tmp / "proj"),
                               notes.read_text(encoding="utf-8"))
        text = hpath.read_text(encoding="utf-8")
        _, bodies = parse_handoff(text)
        assert bodies["GOAL"] == "Ship the widget."
        assert bodies["NEXT"] == "Run the tests."
        assert "/tmp/a.py" in bodies["FILES"]
        assert "bg123" in bodies["IN-FLIGHT"]
        assert "50.0%" in bodies["STATE"], bodies["STATE"]
        assert [s for s in SECTIONS if f"## {s}" in text] == SECTIONS   # fixed order preserved
        assert has_model_content(bodies)

        # re-snapshot without notes keeps model sections
        hpath2 = write_snapshot(str(tpath), "sess1", str(tmp / "proj"), None)
        head2, bodies2 = parse_handoff(hpath2.read_text(encoding="utf-8"))
        assert bodies2["GOAL"] == "Ship the widget."
        assert _header_value(head2, "notes") and _header_value(head2, "notes-turns")  # kept
        assert hpath2.parent == state_root()                       # keyed on session id only

        # notes stranded in old cwd-slug dirs are folded in, newest wins per section
        for slug, goal in (("OldRepo", "legacy goal"), ("OtherRepo", PLACEHOLDER)):
            (state_root() / slug).mkdir(exist_ok=True)
            (state_root() / slug / "sess4.md").write_text(
                f"# h\n\n## GOAL\n\n{goal}\n\n## NEXT\n\nlegacy next\n", encoding="utf-8")
            time.sleep(0.01)
        _, b4 = parse_handoff(write_snapshot(str(tpath), "sess4", None).read_text("utf-8"))
        assert b4["GOAL"] == "legacy goal" and b4["NEXT"] == "legacy next", b4

        # --- truncation ordering ------------------------------------------
        big = {n: (n + " body ") * 200 for n in SECTIONS}
        big["GOAL"] = "keep me: ship the widget"
        capped = render_capped(big, 600, "# hdr\n")
        assert len(capped) <= 600, len(capped)
        assert "keep me: ship the widget" in capped
        assert "OPEN QUESTIONS body" not in capped                # least important dropped first
        assert "GOAL" in capped
        full = render_capped(big, 100_000, "# hdr\n")
        assert "OPEN QUESTIONS body" in full
        tiny = render_capped(big, 250, "# hdr\n")
        assert len(tiny) <= 250
        hog = render_capped({"GOAL": "g" * 20_000, "NEXT": "run the tests"}, 9_000)
        assert "run the tests" in hog and len(hog) <= 9_000      # a huge GOAL cannot evict NEXT

        # --- sessionstart gating ------------------------------------------
        assert hook_sessionstart_body({"source": "startup", "cwd": str(tmp / "proj"),
                                       "session_id": "sess1"}) is None
        out = hook_sessionstart_body({"source": "compact", "cwd": str(tmp / "proj"),
                                      "session_id": "sess1"})
        assert out and "Ship the widget." in out, out
        assert "Recovered handoff" in out
        # fresh handoff claims authority; a stale one downgrades to "verify first"
        assert "authoritative" in out and " search " in out, out
        assert out.index(" search ") < out.index("## GOAL")         # the search line comes first
        assert len(out) <= DEFAULT_MAX_CHARS < 10_000              # stays under the persist limit
        assert _age_minutes("2020-01-01T00:00:00Z") > 1000
        assert _age_minutes("not-a-date") is None and _age_minutes(None) is None
        old = _recovered_header(["- notes: 2020-01-01T00:00:00Z", "- turns: 5",
                                 "- notes-turns: 1"], True)
        assert "out of date" in old and "authoritative" not in old, old
        busy = _recovered_header([f"- notes: {_now()}", "- turns: 90", "- notes-turns: 10"], True)
        assert "80 assistant messages" in busy and "out of date" in busy, busy
        assert "unknown time" in _recovered_header(["- notes: garbage"], True)
        mech = _recovered_header([], False)
        assert "do not infer" in mech and "DO-NOT-REDO." not in mech, mech
        assert hook_sessionstart_body({"source": "compact", "cwd": str(tmp / "proj"),
                                       "session_id": "nope"}) is None
        # a second installed copy of this hook, same event: stays silent
        assert hook_sessionstart_body({"source": "compact", "cwd": str(tmp / "proj"),
                                       "session_id": "sess1"}) is None
        reset_claims()
        os.environ[ENV + "MAX_CHARS"] = "400"
        short = hook_sessionstart_body({"source": "compact", "cwd": str(tmp / "proj"),
                                        "session_id": "sess1"})
        assert short is not None and len(short) <= 400, len(short or "")
        os.environ.pop(ENV + "MAX_CHARS")

        # --- precompact: full backup, rotation, dedupe, unsteered warning --
        side = tmp / "session" / "subagents"           # the transcript's sibling session dir
        side.mkdir(parents=True)
        (side / "agent-1.jsonl").write_text(json.dumps(
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "subagent found the needle-42 value"}]}}) + "\n",
            encoding="utf-8")
        pre = {"cwd": str(tmp / "proj"), "session_id": "sess1",
               "transcript_path": str(tpath), "trigger": "auto"}
        res = json.loads(hook_precompact_body(pre))
        assert "AUTO-compact" not in res["systemMessage"], res   # steered: notes already exist
        assert "Full session backup" in res["systemMessage"], res
        assert "+ 1 subagent/tool-result files" in res["systemMessage"], res
        assert json.loads(hook_precompact_body(pre)) == {}       # duplicate hook copy: no-op
        bdir = find_backups("sess1")[-1]
        assert bdir.name.endswith("-auto"), bdir
        with gzip.open(bdir / "transcript.jsonl.gz", "rb") as f:
            assert f.read() == tpath.read_bytes()                 # byte-identical full copy
        linked = bdir / "subagents" / "agent-1.jsonl"
        assert linked.stat().st_ino == (side / "agent-1.jsonl").stat().st_ino   # hardlink
        assert _own_bytes(bdir) == (bdir / "transcript.jsonl.gz").stat().st_size
        (side / "agent-1.jsonl").unlink()                         # Claude deletes the original…
        assert "needle-42" in linked.read_text(encoding="utf-8")  # …the backup still has it
        os.link(linked, side / "agent-1.jsonl")
        assert (bdir / "transcript.jsonl.gz").stat().st_mode & 0o077 == 0     # owner-only
        assert bdir.stat().st_mode & 0o077 == 0
        reset_claims()
        pre2 = dict(pre, session_id="sess2")
        res2 = json.loads(hook_precompact_body(pre2))
        assert "AUTO-compact" in res2["systemMessage"] and "backup" in res2["systemMessage"], res2
        reset_claims()
        res3 = json.loads(hook_precompact_body(dict(pre2, trigger="manual")))
        assert "AUTO-compact" not in res3["systemMessage"], res3
        for _ in range(5):
            reset_claims()
            hook_precompact_body(pre2)
        assert len(find_backups("sess2")) == KEEP_BACKUPS, find_backups("sess2")
        assert not list(state_root().glob("backups/*/*.partial"))
        reset_claims()
        missing = json.loads(hook_precompact_body(dict(pre, session_id="sess3",
                                                       transcript_path=str(tmp / "nope"))))
        assert "No session backup" in missing["systemMessage"], missing

        # sessionstart now points the model at the backup and the search command
        reset_claims()
        ss = hook_sessionstart_body({"source": "compact", "cwd": str(tmp / "proj"),
                                     "session_id": "sess1"})
        assert ss and " search " in ss, ss

        # the global size cap evicts the oldest backups, never the one just written
        cap = BACKUP_CAP_BYTES
        globals()["BACKUP_CAP_BYTES"] = 1
        try:
            reset_claims()
            capped_res = json.loads(hook_precompact_body(dict(pre, session_id="sess5")))
        finally:
            globals()["BACKUP_CAP_BYTES"] = cap
        assert "evicted" in capped_res["systemMessage"], capped_res
        assert not find_backups("sess2") and len(find_backups("sess5")) == 1
        reset_claims()
        hook_precompact_body(pre)                                 # sess1 backup again for search
        bdir = find_backups("sess1")[-1]

        # --- search: the backup, subagents included, bounded ----------------
        lines = list(search_files(_text_files(bdir), re.compile("needle-\\d+", re.I), bdir, 20))
        assert lines[-1] == 1 and "subagents/agent-1.jsonl" in lines[0], lines
        lines = list(search_files([bdir / "transcript.jsonl.gz"], re.compile("git commit"),
                                  bdir, 20))
        assert lines[-1] >= 1 and "tool_use Bash" in lines[0], lines
        lines = list(search_files([bdir / "transcript.jsonl.gz"], re.compile("."), bdir, 2))
        assert len(lines) == 3 and lines[-1] > 2, lines           # 2 shown + the total
        # precompact clears the nag state so the next climb warns again
        assert not nag_path("sess1").exists()

        # --- robustness: garbage in, no crash ------------------------------
        assert scan_transcript(tmp / "missing.jsonl")["files_written"] == []
        assert last_usage(tmp / "missing.jsonl") == (None, None)
        assert hook_nag_body({}) is None
        assert hook_sessionstart_body({}) is None
        empty = tmp / "empty.jsonl"
        empty.write_text("", encoding="utf-8")
        assert last_usage(empty) == (None, None)
        junk = tmp / "junk.jsonl"
        junk.write_text("nope\n[]\n{}\n", encoding="utf-8")
        assert scan_transcript(junk)["assistant_turns"] == 0

        # --- transcript discovery picks THIS session, not the newest file ---
        saved_env = {k: os.environ.get(k) for k in ("HOME", "CLAUDE_CODE_SESSION_ID",
                                                    "CLAUDE_CONFIG_DIR")}
        os.environ.pop("CLAUDE_CONFIG_DIR", None)
        try:
            fake_home = tmp / "home"
            work = tmp / "work"
            work.mkdir(exist_ok=True)
            pdir = fake_home / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(work))
            pdir.mkdir(parents=True, exist_ok=True)
            mine = pdir / "sess-mine.jsonl"
            other = pdir / "sess-other.jsonl"
            mine.write_text("{}\n", encoding="utf-8")
            other.write_text("{}\n", encoding="utf-8")
            os.utime(mine, (1, 1))                       # a parallel session wrote more recently
            os.environ["HOME"] = str(fake_home)
            os.environ["CLAUDE_CODE_SESSION_ID"] = "sess-mine"
            assert find_transcript(str(work)) == str(mine), find_transcript(str(work))
            assert find_transcript(str(tmp)) == str(mine)        # any cwd: found by id alone
            del os.environ["CLAUDE_CODE_SESSION_ID"]
            assert find_transcript(str(work)) == str(other)      # no id: newest by mtime
            os.environ["CLAUDE_CODE_SESSION_ID"] = "sess-gone"   # id known, no file: never guess
            assert find_transcript(str(work)) is None

            # search: live transcript + its side dir first; the backup once the live one is gone
            (pdir / "sess-mine" / "subagents").mkdir(parents=True)
            (pdir / "sess-mine" / "subagents" / "a.jsonl").write_text(json.dumps(
                {"type": "user", "message": {"content": "live-needle here"}}) + "\n",
                encoding="utf-8")
            import contextlib
            import io

            def run_search(sid, pattern):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = cmd_search(argparse.Namespace(pattern=pattern, file=None,
                                                       session_id=sid, cwd=None, max=5))
                return rc, buf.getvalue()

            rc, txt = run_search("sess-mine", "live-needle")
            assert rc == 0 and "searching live session" in txt and "1 hit(s)" in txt, txt
            rc, txt = run_search("sess1", "needle-42")
            assert rc == 0 and "searching backup" in txt and "1 hit(s)" in txt, txt
            assert run_search("sess-none", "x")[0] == 1
            os.environ.pop("CLAUDE_CODE_SESSION_ID")
            assert run_search("", "x")[0] == 1                  # no id at all: refuse, no guess
        finally:
            for k, v in saved_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    print("OK")
    return 0


# ---------------------------------------------------------------- main

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="smart_compact.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")

    h = sub.add_parser("health")
    h.add_argument("--transcript")
    h.add_argument("--cwd")
    h.add_argument("--json", action="store_true")

    s = sub.add_parser("snapshot")
    s.add_argument("--transcript")
    s.add_argument("--session-id")
    s.add_argument("--cwd")
    s.add_argument("--merge-model-notes")

    q = sub.add_parser("search", help="search a session's full backup (default: the newest)")
    q.add_argument("pattern", help="Python regex, case-insensitive")
    q.add_argument("--session-id", help="default: $CLAUDE_CODE_SESSION_ID")
    q.add_argument("--file", help="search this .jsonl / .gz / text file instead")
    q.add_argument("--cwd", help="for the live-transcript fallback")
    q.add_argument("--max", type=int, default=20, help="hits to print (default 20)")

    for name in ("hook-precompact", "hook-sessionstart", "hook-nag", "demo"):
        sub.add_parser(name)

    args = p.parse_args(argv)
    if args.cmd == "health":
        return cmd_health(args)
    if args.cmd == "snapshot":
        return cmd_snapshot(args)
    if args.cmd == "search":
        return cmd_search(args)
    if args.cmd == "hook-precompact":
        return run_hook(hook_precompact_body)
    if args.cmd == "hook-sessionstart":
        return run_hook(hook_sessionstart_body)
    if args.cmd == "hook-nag":
        return run_hook(hook_nag_body)
    if args.cmd == "demo":
        return cmd_demo(args)
    p.print_help()
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
