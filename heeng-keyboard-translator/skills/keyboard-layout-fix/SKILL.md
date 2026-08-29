---
name: keyboard-layout-fix
description: This skill should be used when the user's message contains text that looks like it was typed with the wrong active keyboard layout (Hebrew vs English) — either the WHOLE message is garbled OR just SOME WORDS inside an otherwise readable sentence are garbled because a layout-switch keystroke failed mid-sentence. Triggers on Latin-letter sequences that don't form English words (e.g. "akuo", "akuo, nv hbun?"), Hebrew-letter sequences that don't form Hebrew words, mixed sentences with one or more nonsensical tokens (e.g. "שלום, akuo חבר"), or inverted-layout sentences where the user alternated and EVERY layout-switch was wrong (e.g. "akuo, ש אםהק כםםג" intending "שלום, I love food"). Also triggers when the user says "wrong layout", "fix my typing", "I typed in the wrong keyboard", "I think keyboard was on hebrew/english", "translate keyboard", or shows confusion about garbled input. Uses bundled keyboard-mapping.json + per-word translator script, then asks via AskUserQuestion to confirm the reconstructed sentence before treating it as the user's actual intent.
---

# Keyboard Layout Fix

Repair text typed with the wrong active layout (US QWERTY vs Israeli SI-1452 Hebrew). Operate **per word**, not just on the whole sentence — many Israeli users mix Hebrew and English in the same sentence and a missed layout-switch leaves only some tokens garbled.

## Scenarios to handle

1. **Whole message garbled** — user thought layout was Hebrew, was actually English (or vice versa). Every token needs translation in one direction.
2. **Some words garbled inside a readable sentence** — layout-switch keystroke failed for a sub-span. Only the broken tokens need translation; the rest stays as-is.
3. **Inverted-layout sentence** — user alternated Heb/Eng on purpose but every switch was inverted: Hebrew-intended words came out English, English-intended words came out Hebrew. Different tokens need translation in DIFFERENT directions inside the same sentence.

The bundled script handles all three uniformly via per-word analysis.

## Trigger checklist

Activate when ANY of the following holds AND the input is not inside a code block / file path / URL / identifier:

- Whole input is gibberish in its dominant script
- Sentence contains at least one token that:
  - Has Latin letters but does NOT form an English word AND would translate to a known Hebrew word
  - Has Hebrew letters but does NOT form a Hebrew word AND would translate to a known English word
- User explicitly mentions wrong-layout typing / fix-my-typing

Skip when input is recognized text in either language with no suspect tokens, OR when only ≤2-char tokens are suspect (too ambiguous).

## Workflow

1. **Translate per word**:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/keyboard-layout-fix/scripts/translate.py" --per-word "<user text>"
   ```
   Script returns JSON:
   - `original` — input verbatim
   - `reconstructed` — sentence rebuilt by picking the best candidate per token
   - `fix_count` — number of tokens changed
   - `words[]` — per-token: `{word, core, script, candidates, choice, confidence, suggested}`

2. **Inspect `fix_count` and per-word `confidence`**:
   - `fix_count == 0` and no `low`-confidence garbled tokens → input is fine, skip skill silently
   - `fix_count > 0` → present the reconstruction to user
   - `fix_count == 0` but tokens have `confidence: low` AND look garbled → still offer, ask user

3. **Print to user in this format**:
   ```
   Detected possible wrong-layout typing.
   Original:        <original>
   Reconstructed:   <reconstructed>
   Per-word fixes:
     - "<word>" → "<suggested>"   (only list tokens where choice != original)
   ```
   For low-confidence garbled tokens that the script left unchanged, also list them with both candidates so the user can decide:
   ```
     - "<word>" (uncertain): could be "<en_to_he.text>" or "<he_to_en.text>"
   ```

4. **Confirm via `AskUserQuestion`**:
   - header: `Layout fix`
   - question: `Use reconstructed text: "<reconstructed>"?`
   - options:
     - `Yes — use reconstruction` → proceed with `reconstructed`
     - `Edit before using` → ask user for the corrected version manually
     - `No — keep original` → proceed with original input
     - (if any token has both directions plausible, include an option to flip that token)

5. **Proceed** with the confirmed text as the user's actual intent. Never silently substitute.

## Examples

| Original | Reconstructed | Fixes |
|---|---|---|
| `akuo` | `שלום` | 1 |
| `שלום, akuo חבר` | `שלום, שלום חבר` | 1 |
| `akuo, vk akun?` | `שלום, vk akun?` (vk + akun? need user judgment) | 1 + 2 uncertain |
| `akuo, ש אםהק כםםג` | `שלום, ש אםהק food` | 2 (heb→en + en→he in same sentence) |
| `hello world` | `hello world` | 0 — skill skips |

## Plausibility scoring

Script uses bundled common-word sets:
- Hebrew (~120 words): שלום, את, של, על, אני, אתה, זה, מה, היה, יש, אין, רק, גם, או, אז, איך, מתי, איפה, למה, מי, תודה, בבקשה, סליחה, בוקר, ערב, לילה, טוב, רע, גדול, קטן, צריך, רוצה, יכול, אפשר, חבר, בית, ספר, עבודה, ילד, אמא, אבא, אח, אחות, מים, אוכל, יום, שבוע, חודש, שנה, …
- English (~110 words): the, and, you, hello, what, when, where, this, that, with, have, please, thanks, yes, no, good, today, tomorrow, want, need, code, bug, fix, push, commit, branch, merge, …

A token is `high` confidence when original OR one translation lands in a common set. Otherwise `low` — let the user judge.

## Boundaries

- Always ask before substituting. Never silently translate.
- Never trigger inside fenced code blocks, file paths, identifiers, URLs.
- Punctuation (`. , ! ? ; : " ' ( ) [ ] { }`) is preserved as-typed — the script translates only the alpha core of each token.
- Hebrew has no letter case; uppercase Latin maps to the same Hebrew letter as lowercase.
- If the user confirms with edits, use the edited text — do not re-translate.

## Bundled resources

- `keyboard-mapping.json` — bidirectional layout map (US QWERTY ↔ Israeli SI-1452)
- `scripts/translate.py` — translator with `--per-word` analysis + plausibility scoring
