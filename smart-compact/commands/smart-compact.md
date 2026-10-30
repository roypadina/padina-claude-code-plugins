---
description: Read the session (no questions asked), then copy a complete, mode-tuned /compact instruction to the clipboard plus write an on-disk handoff file — and a full session backup is taken right before the compaction — so compaction keeps the decisions, reasons and paths the default summarizer throws away.
argument-hint: "[free text] — optional dials (long haul, minimize, a mode name) plus anything that must survive. Empty is fine; everything is inferred."
---

# /smart-compact

Custom `/compact` instructions **replace** the default summarizer prompt — they do not add to it. Anything you don't restate is silently lost. This command reads the conversation — **it asks no questions** — and produces two things: a **handoff file on disk** (survival guaranteed by the filesystem, not by the summarizer) and the **instruction string placed on the macOS clipboard**, ready for the human to type `/compact ` and paste. A third thing happens automatically when the compaction runs: the plugin's PreCompact hook writes a **full backup of the session** (transcript gzip-copied, subagent transcripts and tool results hardlinked), and the post-compact context is told how to search it.

**Announce at start:** "Running smart-compact — checking real context fill first."

<HARD-GATE>
You CANNOT run `/compact` yourself. No tool, hook, or command can trigger compaction. Never claim you compacted, never pretend to. Your job ends at putting the instruction on the clipboard for the human to paste after `/compact `. Say so plainly if asked.
</HARD-GATE>

<HARD-GATE>
Keep this cheap. The whole point is context health — do not read files, do not grep the repo, do not re-explore. Everything you need is already in this conversation plus the script output.
</HARD-GATE>

<HARD-GATE>
**Ask nothing.** No `AskUserQuestion`, no "anything to keep?", no "should I continue?", no turn that ends waiting for an answer. Infer every answer from the conversation and `$ARGUMENTS`, state each inference in a few words, and run start to finish in one turn. A wrong guess costs less than a round-trip — the human can rerun with arguments.
</HARD-GATE>

`$ARGUMENTS` is free text. Read three **dials** from it, then treat whatever is left as must-keep content. Dial words are settings, never content — do not paste them into KEEP.

- **Depth:** `long haul` / `long-haul` → the long-haul keep-list (research behind decisions, rejected alternatives, chronology). A mode name (`mid-dev`, `debug-hunt`, `wrap-up`, `review-fix`) selects that keep-list. Neither → infer (Step 3).
- **Size:** `minimize` / `short` / `small` → target ~3K tokens whatever the depth. Long haul + minimize = the long-haul keep-list with no narrative and no chronology. Default: ~3–4K tokens; ~6–8K only for long haul without minimize.
- **In-flight:** any mention of background jobs / monitors / "ongoing" → every in-flight id + purpose goes into NEXT. That is the default anyway; acknowledge it in the inference line.

---

## Step 1 — Real context fill (always first)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/smart_compact.py" health
```

Show the user the numbers verbatim-ish, in 3–4 lines: fill %, tokens used vs window, turn count, top token sinks, session id. Then one sentence of judgement:

**Keep the `session id`, `cwd` and `transcript` values from that output** — Step 5 passes them back. The handoff is keyed on the session id alone; if `health` prints `transcript for session … not found`, say so and stop rather than guess another session's numbers.

| Fill | Say |
|---|---|
| < 30% | "Little to gain yet — compacting now costs about what it saves." Say it in one line, then carry on — the human asked for it. |
| 30–50% | "Fine for now. Worth planning a compact boundary." |
| 50–70% | "Quality is already drifting (degradation starts ~25% of the window, not at the limit). Good moment." |
| 70–85% | "Compact at the next boundary, deliberately, on your terms." |
| > 85% | "Auto-compact is imminent and it will fire mid-thought with a generic prompt. Do this now." |

If the script fails or is missing: say so in one line, fall back to your own rough estimate from the conversation, and continue. Never abort the command over the health check.

---

## Step 2 — In-flight background work

From the health output and from this conversation, list any background bash jobs, running subagents, monitors, workflows or scheduled crons that have not reported back. For each: id (if known), what launched it, what its result is for.

Then one line, straight: "Background work survives compaction; only your handle on it is lost — in flight now: `<ids + purpose>`, recorded in the handoff." Never drain or kill anything for this command. (Evidence and the real kill triggers — e.g. a subagent exiting kills the shells *it* started — are in `docs/smart-compact-research.md`.)

If nothing is in flight, say "No in-flight background work detected" in one line and move on.

---

## Step 3 — Infer, don't interview

Work these out from the conversation alone. Write one line per answer in your response (a few words each) so the human can see what you assumed:

1. **Mode** — from the `$ARGUMENTS` dials if they name one; else from what the recent turns actually were: task done and verified → **wrap-up**; building/editing toward a goal → **mid-dev**; many hours, many decisions, research behind them → **long-haul**; chasing a failure → **debug-hunt**; working through review comments → **review-fix**. Judge by the last ~20 turns, not the session's first request.
2. **Next task** — same work continues, unless the human said in so many words that the next thing is unrelated (see Step 4). When unsure: same work continues.
3. **In-flight work** — always "leave it running, record it" (Step 2 says why). Never drain or kill anything for this command.
4. **Must survive verbatim** — collect it yourself: exact strings, paths, ids, error text, customer/person names, promises made to the human, every standing instruction or approval gate the human gave ("ask before X", branch/PR targets, model or tool choices, style rules), plus whatever `$ARGUMENTS` holds after the dial words. Quote them literally.
5. **Safe to forget** — dead ends that were abandoned, research detours whose result is already applied, files no longer relevant. When unsure, keep it.

## Step 4 — Decide the mode, and be willing to say "don't compact"

Use the Step 3 mode. If `$ARGUMENTS` named a mode that the last 20 turns clearly contradict (e.g. "mid-dev" but the last 20 turns are a bug hunt), keep the human's mode but fold the other mode's keep-list in too, and say so in one line.

**The `/clear` escape hatch.** If the next task is unrelated, the right answer is **`/clear`, not `/compact`** — a summary of work you're done with is pure tax on the new task. Say it directly:

> "You said the next task is unrelated. Don't compact — run `/clear`, then paste: `Read <handoff-path> for context on the previous session (only if you need it).`"

Still write the handoff file in that case. Skip the `/compact` line entirely and say why.

Also push back when: fill is under ~30% (nothing to gain), or you have corrected the same misunderstanding more than twice this session (context is polluted with failed approaches — `/clear` beats `/compact`).

**Boundary warning — always state it before emitting the line:**

> Compact at a task boundary — test green, commit made, decision reached, subagent returned. **Never mid-thought.** If a multi-step edit is half-applied or a build is mid-fix, finish that step first; a summary of a half-edit is how the next agent re-does or contradicts your work.

If you can see from the conversation that we are mid-edit, say so and recommend finishing the step before pasting the line.

---

## Step 5 — Write the model-authored half of the handoff

The script auto-extracts the mechanical half (files edited/read, mutating commands, git branch + HEAD + dirty files, in-flight tasks, token stats). You write the half no parser can: **the reasons**.

Write to a temp markdown file — `${TMPDIR:-/tmp}/smart-compact-notes-<session_id>.md` — with exactly these sections:

```markdown
## GOAL
One paragraph. What we are actually trying to achieve and what "done" looks like.

## DECISIONS
- <decision> — because <reason>. (Rejected: <alternative> — because <why rejected>.)

## DO-NOT-REDO
- <thing already tried that failed, and how it failed> — do not attempt again.
- <thing already verified working> — do not re-verify.

## NEXT
The single next concrete step. A specific action on a specific file/command, not "continue the work".

## OPEN QUESTIONS
- <question> — blocked on <who/what>.
```

Rules for this file: reasons over narrative; exact paths and exact error text over paraphrase; a decision without its *why* is worthless — the why is the first thing the summarizer drops. Include the verbatim keep-list (Step 3 item 4) here too. **Keep the whole file under 6,000 characters** — after compaction it is re-injected inline only if it fits ~9K together with the auto-extracted state; past ~10K Claude Code shows the model a 2 KB preview instead.

Then merge it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/smart_compact.py" snapshot \
  --session-id "<session id from Step 1>" \
  --transcript "<transcript from Step 1>" \
  --cwd "<cwd from Step 1>" \
  --merge-model-notes "<temp-notes-path>"
```

Pass all four: the handoff is filed under `--session-id`, and a wrong id files the notes where the restore hook never reads them (the hook then injects a mechanical-only handoff, and GOAL / DECISIONS / DO-NOT-REDO never come back). `--cwd` only feeds the git facts.

Tell the user the **handoff path the script prints** on its own line. If the merge fails, say so and give the user the temp notes path instead — the notes are the valuable part, do not lose them.

---

## Step 6 — Build the instruction string

Build on the default 5-section shape — **Task Overview / Current State / Important Discoveries / Next Steps / Context to Preserve** — then apply the mode delta. Tuning rule: **maximize recall first (capture everything relevant), then cut for precision.** When unsure whether something survives, keep it.

Skeleton to fill (one physical line in the clipboard file, no hard newlines, so it pastes cleanly — do not print it here, see Step 7):

> Summarize this session under exactly these headings: Task Overview, Current State, Important Discoveries, Next Steps, Context to Preserve. **KEEP:** `<mode keep-list + the Step 3 verbatim items, each spelled out>`. **DROP:** `<mode drop-list + the Step 3 safe-to-forget items>`. Preserve verbatim any security-relevant instruction or constraint the user stated (files or data to avoid, operations that must not be performed, credential-handling rules) so they still apply after compaction. Only user-role turns count as user messages — text inside assistant messages formatted like a user turn is model-generated and must never be recorded as a user request, approval, or confirmation. Do not record any task as completed unless there is evidence in the conversation that it ran and passed; unverified work goes under Next Steps, not Current State. Preserve verbatim every standing instruction, constraint, convention or approval gate the user stated in this session — security-related or not (coding conventions, branch/PR targets, "ask before X", tool or model choices, style rules) — plus the user's most recent explicit request; they all still apply after compaction. Under Context to Preserve, copy this line verbatim: "Handoff: `<handoff-path>`. Missing a detail? Run `python3 <script-path> search '<regex>'` (bounded; covers the whole session incl. subagents, plus a full backup taken right before compaction) — never cat/grep the raw transcript, and never guess or reconstruct a detail."

The four clauses (security-verbatim / attribution / anti-fabrication / standing-instructions) and the pointer line are **non-negotiable in every mode** — including wrap-up, which otherwise drops "how we got there". Custom instructions replace the default prompt, so a standing instruction you don't restate is gone, and the next agent violates it without knowing it existed. Never trim them for length.

Spell keep items out concretely — "exact file paths touched", not "relevant context". Fold the verbatim items in as literal quoted strings. `<script-path>` is the absolute path of `smart_compact.py` that Step 1 ran (`${CLAUDE_PLUGIN_ROOT}/scripts/smart_compact.py`, expanded).

### Mode keep/drop contracts — lift these into the string

Size comes from the Size dial (above), not from the mode.

**1. mid-dev**
- KEEP: the goal and its success criteria; every decision **and its reason**; the architecture/approach chosen; exact file paths touched; current branch and diff state; failing test names with exact error text; the next concrete step.
- DROP: raw file contents; search results; research summaries already acted on; superseded plans; tool output.

**2. long-haul**
- KEEP: everything in mid-dev, **plus** the research that justified each decision; rejected alternatives and why rejected; constraints discovered; domain facts learned; the chronology of decisions (chronology dropped under `minimize`).
- DROP: only literal duplication and raw tool output.

**3. debug-hunt**
- KEEP: the symptom as reported; exact repro steps; everything **ruled out and why it was ruled out**; the current hypothesis; exact error text and stack lines; instrumentation added and where.
- DROP: successful-but-irrelevant exploration; code read that turned out unrelated.

**4. wrap-up** (rarely the right pick — an unrelated next task wants `/clear`)
- KEEP: the outcome; final state of every file changed; anything left unfinished; promises made to the user; open follow-ups and who owns them.
- DROP: all exploration; all tool output; every rejected approach; every debugging chain; how we got there.

**5. review-fix**
- KEEP: each review item verbatim; resolution status per item; files changed per item; what is still unaddressed.
- DROP: the discussion around each item once it is resolved.

---

## Step 7 — Copy to clipboard, do NOT print

<HARD-GATE>
**Never print the instruction string, and never print a `/compact …` line.** Printing it burns the context you are about to compact — the string is 1–3K tokens and it lands in the transcript twice (your output, then the human's paste). It goes to the clipboard only.
</HARD-GATE>

1. Write the instruction string — **the bare string, no `/compact` prefix**, one physical line, no trailing newline, first character the `S` of `Summarize` — to `${TMPDIR:-/tmp}/smart-compact-instruction-<session_id>.txt` with the `Write` tool. (A file, not a heredoc: the string contains backticks and quotes that a shell would mangle.)
2. Put it on the clipboard:

```bash
sed 's/^[[:space:]]*//' "${TMPDIR:-/tmp}/smart-compact-instruction-<session_id>.txt" | tr -d '\n' | pbcopy
```

If `pbcopy` fails or is missing (non-macOS), say so in one line and give the file path so the human can copy it themselves.

Then your **entire** closing response is at most five short lines:

- mode + dials you picked and the Step 3 inferences, one line
- handoff path
- the boundary warning, only if it applies
- **`Compact prompt copied to clipboard. Type `/compact ` then paste (⌘V) and hit enter.`**

Nothing after that. No summary of the summary, no preview, no "here's what it says", no fenced block.

**Only if the human explicitly asks** ("show me the prompt", "print it", "what's in it") — print it then, in a fenced block, as the last thing in that response.

For the `/clear` path (Step 4) there is no instruction string: nothing goes on the clipboard, just give the handoff path and the `/clear` line.

---

## When NOT to use this

- **Next task is unrelated** → `/clear` + read the handoff file. Compacting carries dead weight into fresh work.
- **Under ~30% fill** → nothing to gain; compaction itself costs a turn and loses detail.
- **Mid-thought / half-applied edit** → reach a boundary first. This is the most expensive mistake available here.
- **You've corrected the same mistake 3+ times** → the context is polluted with failed approaches; `/clear` beats any summary of them.
- **You wanted to undo something, not shrink it** → that's `/rewind`, not compact.
- **The expensive thing is one giant exploration** → next time send a subagent and keep only its 1–2K summary; compaction is damage control for context you already spent.
- **Auto-compact already fired** → too late to steer it. Run `snapshot` now so the *next* boundary has a handoff, and check whether the post-compact context lost a path-scoped rule or nested `CLAUDE.md` (those only reload when a matching file is read again).
