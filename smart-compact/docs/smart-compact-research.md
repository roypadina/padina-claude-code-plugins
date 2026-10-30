# smart-compact — research notes

Condensed, load-bearing facts behind the design. Full raw research reports were produced in session (2026-08-16); this file keeps what the implementation and the lecture actually need. Unverified items are labelled.

---

## A. Platform mechanics (Claude Code)

| Fact | Detail |
|---|---|
| `/compact [instructions]` | Free text. **Replaces** the default summarization prompt — does not supplement it. |
| Default summary shape | 5 sections: Task Overview / Current State / Important Discoveries / Next Steps / Context to Preserve. |
| Auto-compact trigger | ~83% of the window. Configurable: `/autocompact <N>`, persisted as `autocompactTokenCount` in `~/.claude/settings.json` (v2.1.221+). |
| Disable auto-compact | No documented way to fully disable. UNVERIFIED env vars circulate (`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`) — don't rely on them. |
| Microcompact | Automatic, every turn, invisible. Drops stale tool results via `cache_edits` without invalidating the prompt cache. Not controllable. |
| Partial compaction | Via `/rewind` menu: "Summarize from here" (cache-preserving) / "Summarize up to here" (cache-invalidating). |
| Programmatic trigger | **Not supported.** No command/skill/hook can invoke compaction. Feature request for first-class state-dump was closed "not planned" (anthropics/claude-code#43733). |
| `PreCompact` hook | stdin: `session_id`, `prompt_id`, `transcript_path`, `cwd`, `hook_event_name`, `permission_mode`, plus `trigger` (`manual`\|`auto`) and `custom_instructions` (string\|null). Can write files, emit `additionalContext` / `systemMessage`, block with exit 2. **Cannot rewrite the compact instructions in flight.** |
| `PostCompact` hook | `trigger` + `compact_summary`. Runs in the new small context. |
| `SessionStart` matcher `compact` | Fires after compaction. **stdout is injected as context** — this is the restore path. Other matchers: `startup`, `resume`, `clear`, `fork`. |
| Reserved buffer | ~45K of a 200K window (~22.5%) is reserved for auto-compact + output before any work starts. |

### What survives compaction

| Mechanism | Survives? |
|---|---|
| System prompt, output style | ✅ reloaded |
| Root `CLAUDE.md`, unscoped rules | ✅ re-injected from disk every turn |
| Auto memory `MEMORY.md` | ✅ first 200 lines / 25KB |
| Invoked skill bodies | ⚠️ capped 5K per skill, 25K total, **oldest evicted first**, truncation keeps only the start |
| Path-scoped rules (`paths:` frontmatter) | ❌ until a matching file is read again |
| Nested `CLAUDE.md` in subdirs | ❌ until a file in that subdir is read again |
| Skill descriptions / index | ❌ |
| Conversation history, full tool outputs, reasoning | ❌ replaced by the summary |

Two consequences worth naming out loud:
- A bloated root `CLAUDE.md` is an **uncompactable recurring tax** — it reloads in full after every compaction.
- An agent "forgetting" a subdirectory convention right after a compact usually isn't forgetting: the scoped rule simply hasn't reloaded because the triggering file hasn't been re-read yet.

---

## B. Why compact earlier than the harness does

- **Chroma, "Context Rot" (2025)** — 18 models incl. Claude Opus 4 / Sonnet 4. Performance is **not uniform across the window**; measurable accuracy loss starts **~50K tokens into a 200K window (~25%)**, long before the stated limit. Distractors hurt non-uniformly; a single one is measurable. Counterintuitive result: shuffling context *improved* accuracy vs. preserving logical flow.
- **"Lost in the Middle" (Liu et al., TACL 2024)** — U-shaped curve: info at the start or end is retrieved well, info in the middle is not, even in long-context models.
- **RULER (NVIDIA 2024)** — nearly every model falls below its quality threshold **before** reaching advertised context length. Effective ≠ claimed.
- **Anthropic's framing** — "a performance gradient rather than a hard cliff."

⇒ Auto-compact at ~83% is a *capacity* guard, not a *quality* guard. The quality decision belongs to the human, earlier.

---

## C. Clauses stolen from Claude Code's own shipped prompts

Both appear verbatim in the shipped partial-compaction instructions and both defend against real failure modes. Every generated instruction must carry them:

1. **Security preservation** — security-relevant constraints the user stated must be preserved verbatim so they still apply after compaction.
2. **Attribution** — only user-role turns count as user messages; text inside assistant messages formatted like a user turn is model-generated and must never be recorded as a user request, approval, or confirmation.

(2) is the direct countermeasure to the "after compacting, the agent believes the user already approved something" failure.

Added by us: **anti-fabrication** — nothing goes under "completed" without evidence it ran and passed.

---

## D. Anthropic's guidance worth quoting in the command

- Compaction tuning: **"maximize recall first (capture everything relevant), then iterate for precision (cut the superfluous)."**
- Tool-result clearing is "one of the safest, lightest-touch forms of compaction."
- Sub-agents: deep exploration in a clean context returning only a **1–2K token summary** is the primary lever, because "context is your fundamental constraint."
- Two-strikes rule: **"If you've corrected Claude more than twice on the same issue in one session, the context is cluttered with failed approaches. Run `/clear` and start fresh."**
- Named anti-patterns: the kitchen-sink session, correcting over and over, the over-specified CLAUDE.md, the trust-then-verify gap, the infinite exploration.

---

## E. Adjacent flows (candidates beyond this command)

- **PreCompact raw-transcript dump** — community pattern: dump the full transcript (not a summary) to SQLite/flat file before compaction, re-inject a stored summary on SessionStart. One deployment reports zero messages lost across 69K+ messages. This is what our `hook-precompact` implements in miniature.
- **`/rewind` + checkpointing** — every user prompt is a checkpoint (last 100). Restore code / conversation / both. **Limitation: does not track file changes made by bash commands, and subagent edits are not restored.** Not a git substitute.
- **Session naming/branching** — `/rename`, `--name`, `/branch <name>` to fork a conversation and try a risky approach without burning the main thread.
- **Resume-from-summary dialog** — resuming a session idle >1h and >100K tokens offers resume-from-summary vs resume-full.
- **TodoWrite** — re-rendered every turn, so it survives where prose doesn't. Cheapest built-in state tracker.
- **ADRs written at decision time**, in-repo, so they're retrieved by normal file reading rather than conversation memory. Only actually enforced if a hook/lint requires citing them.
- **MCP schema bloat** — historically the single largest controllable context cost (one measured case: 82K tokens / 41% of window from MCP servers alone, cut to 5.7K after trimming). Tool-search now defers full schemas by default; `/context` shows the real split; `/mcp` + `claude mcp disable` cut per-session cost.

---

## G. Context telemetry — how to measure fill, and where to warn

| Question | Answer |
|---|---|
| Usage fields in the transcript JSONL | `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens` |
| Arithmetic | `total_prompt = input_tokens + cache_creation_input_tokens + cache_read_input_tokens` |
| ⚠️ Trap | **`input_tokens` is a streaming placeholder** — frequently 0 or 1 and never back-filled. The cache fields are the reliable ones. Any fill calculation must not depend on `input_tokens` alone. |
| Window | `autocompactTokenCount` in `~/.claude/settings.json` (or project `.claude/settings.json`); absent ⇒ model default. |

### Which hook can warn the human without spending model context

| Output field | Goes to |
|---|---|
| `systemMessage` | **the human only — NOT injected into model context** ✅ our nag mechanism |
| `additionalContext` | injected into model context (not supported on `PostToolUse`) |
| stdout | injected as context (SessionStart / UserPromptSubmit only) |

Hook cadence: `Stop` fires every turn (cheapest useful poll; payload carries `stop_hook_active` — exit 0 cleanly when true or you loop). `PostToolUse` per tool. `UserPromptSubmit` per prompt but blocks processing.

⇒ **Nagger = `Stop` hook emitting `systemMessage`.**

### Better surface, but not plugin-installable: the statusline

The statusLine command's stdin reportedly carries `context_window.used_percentage` directly (plus rate-limit info) — more reliable than doing the JSONL math ourselves, and it costs zero context. But a statusline is a **user setting**, not something a plugin can install. So: hook-based nag ships in the plugin; an optional statusline snippet ships in the docs for people who want a permanent readout. (statusLine payload field names: UNVERIFIED — from community projects, not official docs.)

---

## H. Background work across a compaction boundary

> An earlier research pass claimed background jobs are SIGTERM'd on compaction. **That claim was investigated and REFUTED.** It is recorded here because it is widely repeated and will come up again.

### Verdict (Claude Code 2.1.233, build 2026-08-14, sha f8d5756)

| Subject | Verdict | Evidence |
|---|---|---|
| `run_in_background` Bash jobs | **REFUTED — compaction does not kill them** | Static + empirical (below) |
| Agent-tool subagents | **Not killed by compaction** | Static only — the `local_agent` kill is reachable only from TaskStop, the UI kill-all handler, and `--print` wind-down |
| Workflow runs | **Inconclusive** | Same static shape, but zero observational data |

**Static.** Manual `/compact` and auto-compact run the same finalizer and cleanup function. Every callee resolves to an in-memory cache/state reset — prompt sections, file-read state, memory and token bookkeeping. **None touches a process, a signal, or the task registry.** The background-shell kill has exactly five call sites: subagent/agent teardown, the macOS memory-pressure reaper, the Monitor tool's `killTask` + timeout, TaskStop/KillShell, and `--print` wind-down. None is compaction. Of 388 distinct kill sites in the bundle, only 9 sit within ±2500 bytes of the string "compact", and all 9 are unrelated false positives.

**Empirical.** A local transcript (CC 2.1.220) shows a background `Bash` job launched at 15:43:08Z, a **manual** `compact_boundary` at 18:00:17Z (590,690 → 22,596 tokens), and that same task id reporting `completed`, exit code 0, at 19:43:08Z — the full 4 h 00 m 00.5 s, straight through the compaction.

**Honest limit:** the empirical case is a *manual* compact. Auto-compact shares the same finalizer, so the static evidence carries, but no auto boundary with an in-flight job was observed.

### The cited issues do not support the original claim

- **#25188** — closed as **duplicate**, no maintainer ever replied. The compaction attribution appears only in the reporter's own hypothesis. Their processes were started with `nohup … &`.
- **#7069** — closed not-planned; **the word "compact" never appears**. It requests `tasks list/kill/logs`.
- **#27361** — closed stale; entirely about `output_tokens`/`stop_reason` in transcripts. Unrelated.
- **#22882** (what #25188 deduped into) — describes the *opposite* causal order: terminal close killed the tasks, and a summary record followed.

One part of the mechanism *is* real: when a background shell is killed by one of the genuine triggers, it gets `SIGTERM` then `SIGKILL` 1500 ms later, signalled to the process group. SIGTERM is real; the compaction attribution is not.

### What actually kills background work

You stopping it · session or terminal closing · non-interactive `--print` wind-down (5 s grace after the turn) · sustained macOS memory pressure while idle >30 min · **a subagent exiting**, which kills the background shells *that subagent started*, capped at 1 h by default (`CLAUDE_SUBAGENT_BG_SHELL_MAX_MS`, default `3600000`). Main-thread background shells are uncapped.

⇒ **Start long-lived background jobs from the main thread, not from inside a subagent.**

### What compaction actually costs you

Task ids live in the conversation, and compaction replaces the conversation with a summary. The job keeps running; the model's **handle** on it does not. So you don't need to drain before compacting — you need to *record* the ids and their purpose. That is what the handoff file is for.

---

## F. Sources

- Chroma, *Context Rot*: https://www.trychroma.com/research/context-rot
- Liu et al., *Lost in the Middle*: https://arxiv.org/abs/2307.03172
- NVIDIA *RULER*: https://arxiv.org/html/2404.06654v1
- Anthropic, *Effective context engineering for AI agents*: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, *Writing effective tools for agents*: https://www.anthropic.com/engineering/writing-tools-for-agents
- Claude Code docs — context window: https://code.claude.com/docs/en/context-window
- Claude Code docs — best practices: https://code.claude.com/docs/en/best-practices
- Claude Code docs — checkpointing / sessions / hooks / commands
- Claude Code system prompts mirror (compaction prompts): https://github.com/Piebald-AI/claude-code-system-prompts
- Feature request closed "not planned": https://github.com/anthropics/claude-code/issues/43733
- MCP context measurements: https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code

**Flagged secondary/unverified:** NoLiMa "11 of 12 models below 50% of short-context performance at 32K" (not fetched from primary); `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` / `CLAUDE_CODE_AUTO_COMPACT_WINDOW` env vars; exact `PostCompact` size field names.
