# heeng-keyboard-translator

Repairs text typed with the wrong active keyboard layout — US QWERTY vs Israeli SI-1452 Hebrew.

You meant Hebrew, the layout was still English, and `שלום` came out as `akuo`. This plugin notices
and offers the repair before Claude acts on the garbled text.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install heeng-keyboard-translator@padina
```

Needs nothing but Python 3, which macOS already has.

## What makes it useful

It works **per word**, not just on the whole message. The common real-world case isn't a fully
garbled sentence — it's an Israeli developer mixing Hebrew and English where one layout-switch
keystroke didn't land, leaving a couple of broken tokens in an otherwise fine sentence.

| You typed | It reconstructs | Why |
|---|---|---|
| `akuo` | `שלום` | whole message, one direction |
| `שלום, akuo חבר` | `שלום, שלום חבר` | one bad token inside a readable sentence |
| `akuo, ש אםהק כםםג` | `שלום, ש אםהק food` | different tokens need **opposite** directions |
| `hello world` | unchanged | nothing suspect — the skill stays silent |

Every token is translated both ways and scored against bundled common-word sets (140 Hebrew, 123
English). A token is high-confidence when the original or exactly one translation is a real word;
otherwise it is reported as uncertain with both candidates, and you decide.

## How it behaves

1. Runs the bundled translator over your message, per word.
2. If nothing looks garbled, says nothing at all.
3. Otherwise shows the original, the reconstruction, and a per-word list of what changed.
4. Asks — via `AskUserQuestion` — whether to use it, edit it, or keep the original.
5. Proceeds with whatever you confirmed.

**It never substitutes silently.** And it does not fire inside fenced code blocks, file paths, URLs
or identifiers, where a "correction" would be corruption.

## Layout

```
.claude-plugin/plugin.json
skills/keyboard-layout-fix/
  SKILL.md                     triggers, workflow, boundaries
  keyboard-mapping.json        bidirectional US QWERTY ↔ SI-1452 map
  scripts/translate.py         per-word translator + plausibility scoring
```

The script is usable on its own:

```bash
python3 skills/keyboard-layout-fix/scripts/translate.py --per-word "שלום, akuo חבר"
```

It prints JSON: `original`, `reconstructed`, `fix_count`, and a `words[]` array with each token's
candidates, chosen reading and confidence.

## Known limits

- Hebrew has no letter case, so uppercase Latin maps to the same Hebrew letter as lowercase.
- Tokens of two characters or fewer are too ambiguous to call. The script still scores them and
  returns them at `confidence: low` with the original kept; skipping them is a rule in the skill,
  not a filter in the code.
- Only US QWERTY ↔ Israeli SI-1452. Other layout pairs would need a new mapping file.

## License

MIT © Roy Padina
