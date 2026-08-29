#!/usr/bin/env python3
"""Translate text between US QWERTY and Israeli SI-1452 Hebrew layouts.

Usage:
    python3 translate.py [--per-word] "<text>"

Default mode: translates the whole string in both directions and scores
plausibility (count of common-word hits).

--per-word mode: tokenizes the input and analyzes each word independently.
For each token, computes both translations and reports which candidate
(original / en_to_he / he_to_en) is most plausible. Also returns a
greedy-reconstructed sentence built by picking the best candidate per word.
This handles mixed Hebrew+English sentences where only SOME words are
garbled because the layout-switch keystroke failed mid-sentence.
"""

import json
import os
import re
import sys
from pathlib import Path

COMMON_HE = {
    "שלום", "את", "של", "על", "אני", "אתה", "זה", "מה", "לא", "כן",
    "היה", "היא", "הוא", "יש", "אין", "כל", "רק", "גם", "או", "אז",
    "איך", "מתי", "איפה", "למה", "מי", "פה", "שם", "תודה", "בבקשה",
    "סליחה", "בוקר", "ערב", "לילה", "טוב", "רע", "גדול", "קטן",
    "כי", "כמה", "עוד", "עד", "כאן", "איש", "כך", "אחד", "אחת",
    "שני", "שתי", "ואני", "ואתה", "ועוד", "ועד", "אבל", "אם",
    "צריך", "רוצה", "יכול", "אפשר", "חבר", "חברה", "בית", "ספר",
    "עבודה", "ילד", "ילדה", "אמא", "אבא", "אח", "אחות", "מים",
    "אוכל", "יום", "שבוע", "חודש", "שנה", "צהריים",
    "מתכון", "תפוח", "אדמה", "לחם", "חלב", "שמן", "מלח", "סוכר",
    "אורז", "פסטה", "ירק", "פרי", "בשר", "עוף", "דג", "ביצה",
    "בוא", "בואי", "תן", "תני", "קח", "קחי", "ראה", "ראי", "שמע",
    "אמר", "אמרה", "הלך", "הלכה", "בא", "באה", "ישב", "ישבה",
    "כותב", "כותבת", "קורא", "קוראת", "אוהב", "אוהבת", "עכשיו",
    "אחרי", "לפני", "תמיד", "אף", "פעם", "מאוד", "ממש", "באמת",
    "מהר", "לאט", "חזק", "חלש", "קר", "חם", "יפה", "מכוער",
    "חדש", "ישן", "נקי", "מלוכלך", "ריק", "מלא", "חצי", "שלם",
}

COMMON_EN = {
    "the", "and", "you", "hello", "what", "when", "where", "this", "that",
    "with", "have", "here", "please", "thanks", "yes", "no", "good", "bad",
    "today", "tomorrow", "for", "are", "was", "were", "will", "can", "not",
    "but", "how", "why", "who", "one", "two", "three", "big", "small",
    "about", "okay", "ok", "from", "into", "like", "love", "want", "need",
    "make", "made", "work", "home", "name", "time", "year", "day", "week",
    "month", "hour", "minute", "second", "morning", "evening", "night",
    "food", "water", "bread", "milk", "salt", "sugar", "rice", "meat",
    "phone", "email", "send", "call", "text", "message", "reply", "now",
    "later", "before", "after", "always", "never", "very", "really",
    "fast", "slow", "hot", "cold", "new", "old", "clean", "dirty",
    "open", "close", "start", "stop", "wait", "go", "come", "see",
    "say", "tell", "ask", "answer", "think", "know", "find", "look",
    "code", "bug", "fix", "test", "build", "run", "deploy", "merge",
    "push", "pull", "commit", "branch", "main", "master", "issue",
}

HEBREW_RE = re.compile(r"[֐-׿]")
LATIN_RE = re.compile(r"[A-Za-z]")
TOKEN_RE = re.compile(r"\S+")
STRIP_PUNCT = ".,!?;:\"'()[]{}׳״…«»"


def split_affixes(token: str) -> tuple:
    """Split token into (prefix_punct, core, suffix_punct)."""
    prefix = ""
    while token and token[0] in STRIP_PUNCT:
        prefix += token[0]
        token = token[1:]
    suffix = ""
    while token and token[-1] in STRIP_PUNCT:
        suffix = token[-1] + suffix
        token = token[:-1]
    return prefix, token, suffix


def find_mapping() -> dict:
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "keyboard-mapping.json",
        Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "")) /
            "skills/keyboard-layout-fix/keyboard-mapping.json",
        Path.cwd() / "keyboard-mapping.json",
        here / "keyboard-mapping.json",
    ]
    for path in candidates:
        if path and path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        "keyboard-mapping.json not found in skill dir, $CLAUDE_PLUGIN_ROOT, or cwd"
    )


def translate(text: str, table: dict) -> str:
    return "".join(table.get(ch, ch) for ch in text)


def classify_script(word: str) -> str:
    has_he = bool(HEBREW_RE.search(word))
    has_lat = bool(LATIN_RE.search(word))
    if has_he and has_lat:
        return "mixed"
    if has_he:
        return "hebrew"
    if has_lat:
        return "latin"
    return "symbol"


def in_common(word: str, lang: str) -> bool:
    stripped = word.strip(STRIP_PUNCT)
    if lang == "he":
        return stripped in COMMON_HE
    return stripped.lower() in COMMON_EN


def score_sentence(text: str, lang: str) -> int:
    return sum(1 for tok in text.split() if in_common(tok, lang))


def analyze_word(word: str, mapping: dict) -> dict:
    """Return analysis for a single token: candidates + plausibility flags.

    Strips leading/trailing punctuation, translates the core, then re-wraps
    so punctuation is preserved as-typed.
    """
    prefix, core, suffix = split_affixes(word)
    en_to_he_core = translate(core, mapping["en_to_he"])
    he_to_en_core = translate(core, mapping["he_to_en"])
    script = classify_script(core)

    def wrap(s: str) -> str:
        return f"{prefix}{s}{suffix}"

    cand = {
        "original": {
            "text": wrap(core),
            "core": core,
            "in_common_he": in_common(core, "he"),
            "in_common_en": in_common(core, "en"),
        },
        "en_to_he": {
            "text": wrap(en_to_he_core),
            "core": en_to_he_core,
            "in_common_he": in_common(en_to_he_core, "he"),
        },
        "he_to_en": {
            "text": wrap(he_to_en_core),
            "core": he_to_en_core,
            "in_common_en": in_common(he_to_en_core, "en"),
        },
    }

    # Decide best candidate per token (greedy):
    # 1. original is recognized in either common list → keep
    # 2. en_to_he produces recognized Hebrew → use it
    # 3. he_to_en produces recognized English → use it
    # 4. fall back to original (low confidence — Claude should judge)
    if cand["original"]["in_common_he"] or cand["original"]["in_common_en"]:
        choice, confidence = "original", "high"
    elif cand["en_to_he"]["in_common_he"]:
        choice, confidence = "en_to_he", "high"
    elif cand["he_to_en"]["in_common_en"]:
        choice, confidence = "he_to_en", "high"
    else:
        choice, confidence = "original", "low"

    return {
        "word": word,
        "core": core,
        "script": script,
        "candidates": cand,
        "choice": choice,
        "confidence": confidence,
        "suggested": cand[choice]["text"],
    }


def per_word_analysis(text: str, mapping: dict) -> dict:
    tokens = TOKEN_RE.findall(text)
    analyses = [analyze_word(tok, mapping) for tok in tokens]

    # Reconstruct sentence preserving original whitespace by re-walking text.
    out_parts = []
    idx = 0
    a_iter = iter(analyses)
    for match in TOKEN_RE.finditer(text):
        start, end = match.span()
        out_parts.append(text[idx:start])
        out_parts.append(next(a_iter)["suggested"])
        idx = end
    out_parts.append(text[idx:])
    reconstructed = "".join(out_parts)

    fixes = sum(1 for a in analyses if a["choice"] != "original")
    return {
        "original": text,
        "reconstructed": reconstructed,
        "fix_count": fixes,
        "words": analyses,
    }


def whole_string_analysis(text: str, mapping: dict) -> dict:
    en_to_he = translate(text, mapping["en_to_he"])
    he_to_en = translate(text, mapping["he_to_en"])
    return {
        "original": text,
        "en_to_he": en_to_he,
        "he_to_en": he_to_en,
        "en_to_he_score": score_sentence(en_to_he, "he"),
        "he_to_en_score": score_sentence(he_to_en, "en"),
    }


def main() -> int:
    args = sys.argv[1:]
    per_word = False
    if args and args[0] == "--per-word":
        per_word = True
        args = args[1:]
    if not args:
        json.dump({"error": "usage: translate.py [--per-word] <text>"}, sys.stdout)
        sys.stdout.write("\n")
        return 1

    text = " ".join(args)
    mapping = find_mapping()
    if per_word:
        result = per_word_analysis(text, mapping)
    else:
        result = {
            **whole_string_analysis(text, mapping),
            "per_word": per_word_analysis(text, mapping),
        }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
