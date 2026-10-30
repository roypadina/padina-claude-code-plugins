# smart-compact

`/compact` that keeps what matters, asks nothing, and loses nothing for good.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install smart-compact@padina
```

## The problem

Custom `/compact` instructions **replace** Claude Code's summarizer prompt. Whatever you don't
restate is gone: the reasons behind decisions, what was already tried and failed, the exact next
step, standing rules like "ask before pushing". Auto-compact is worse: it fires mid-thought with
the generic prompt. Once compacted, a detail the summary dropped is gone from the model's view
and it starts guessing.

## What you get

| Piece | When | What it does |
|---|---|---|
| `/smart-compact [free text]` | At a task boundary | Reads the session (no questions), shows the real context fill, writes a handoff file (goal, decisions with reasons, do-not-redo, next step) and copies a tuned `/compact` instruction to the clipboard. Type `/compact `, paste, enter. |
| PreCompact hook | Every compaction, manual or auto | Refreshes the handoff and takes a **full backup of the session**: the transcript gzip-copied, subagent transcripts and tool results hardlinked (under 1 s even for a 700 MB session). |
| SessionStart hook | Right after compaction | Re-injects the handoff (capped at 9,000 chars so Claude Code shows it inline, most important sections first) with an honest age: how long and how many messages before the compaction the notes were written. |
| `search` | When the model misses a detail | `python3 …/smart_compact.py search '<regex>'` — bounded hits (20, short snippets) over the whole session, subagents included; falls back to the backup once the transcript itself is gone. The post-compact context tells the model to use it instead of guessing or grepping tens of MB. |
| Stop hook | Each turn | One-time nudge at 50 / 70 / 85 % context fill, shown to you only (costs the model nothing). |

### Free-text dials

`/smart-compact long haul, minimize, keep the PR number 1234` — dial words are settings, the
rest must survive verbatim:

- **Depth:** `long haul` keeps the research behind decisions and rejected alternatives; a mode
  name (`mid-dev`, `debug-hunt`, `wrap-up`, `review-fix`) picks that keep-list; otherwise it is
  inferred from the last turns.
- **Size:** `minimize` / `short` targets ~3K tokens.
- **In-flight:** background jobs are always recorded by id, since compaction keeps them running
  but loses the model's handle on them.

## Files

Everything lives under `~/.claude/smart-compact/`, owner-only:

```
<session-id>.md                     handoff (re-injected after compaction)
<session-id>.nag                    thresholds already nudged
backups/<session-id>/<UTC>-<trigger>/
    transcript.jsonl.gz             the transcript at the compaction boundary
    subagents/, tool-results/       hardlinks: survive Claude Code deleting the originals
```

The newest backup per session is kept (each one contains the previous); all backups together are
capped at 5 GB, oldest evicted first.

## Settings (environment)

| Variable | Default | Meaning |
|---|---|---|
| `SMART_COMPACT_WINDOW` | `1000000` | Context window, for the fill %. Set `200000` on a 200K model. |
| `SMART_COMPACT_THRESHOLDS` | `50,70,85` | Nudge thresholds, in %. |
| `SMART_COMPACT_MAX_CHARS` | `9000` | Restore cap. Above ~10K chars Claude Code shows the model a 2 KB preview instead. |

## Requirements

Python 3 (standard library only). `pbcopy` for the clipboard (macOS); elsewhere the command
gives you the file path to copy from.

## Notes

- Claude cannot run `/compact` itself; the command stops at the clipboard.
- Self-check: `python3 scripts/smart_compact.py demo` prints `OK`.
- A second copy of this tool ships in another marketplace under a different command name. Both
  can be installed at once: they share `~/.claude/smart-compact/` and each hook event runs once.
