"""Extract French→Chinese translation pairs from the TAXI docx and fill
empty `back` fields in books.ts.

The TAXI docx has ~573 bilingual paragraphs where French example sentences
are immediately followed by their Chinese translations (as part of vocab
and grammar notes). We scan each paragraph, split on the French→Chinese
transition, collect (fr, zh) pairs into a dictionary keyed by a normalized
French fragment, then look up each untranslated card in books.ts.

OCR errors in the TAXI docx ("decouvert", "grace", "parle") mean exact
matching won't work. We use a stripped/lowercased/ascii-folded key and a
prefix match of the first ~40 chars.
"""
from __future__ import annotations
import io
import re
import sys
import unicodedata
from pathlib import Path

import docx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:/Users/racwang/hoopy/french-flashcard")
TAXI = Path(r"C:/Users/racwang/Downloads/【TAXI】你好！法语+31775227168.docx")
BOOKS = ROOT / "src" / "data" / "books.ts"

CJK_RANGE = r"\u4e00-\u9fff"
CJK_PUNCT = r"\u3000-\u303f\uff00-\uffef，。！？、；：""''（）《》…"


def fold(s: str) -> str:
    """Strip accents, lowercase, remove non-word chars. Helps match past OCR artefacts."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    # Common OCR corruptions to ignore
    s = s.replace("0", "o").replace("1", "l").replace("ô", "o")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def split_pairs(text: str) -> list[tuple[str, str]]:
    """Walk a bilingual paragraph and emit (fr, zh) pairs.

    Algorithm: cut the string into runs of same-script characters. French runs
    separated by Chinese runs are paired: the French run ending just before a
    Chinese run is the source; the following Chinese run is its translation.
    """
    pairs = []
    # Tokenize: alternating FR chunks and ZH chunks
    tokens = re.findall(
        rf"([a-zA-ZÀ-ÿ'"
        rf"\s,.!?;:«»\"()\-\d]+|["
        rf"{CJK_RANGE}{CJK_PUNCT}]+)",
        text,
    )
    i = 0
    while i < len(tokens):
        tok = tokens[i].strip()
        # Is this token French (has latin letters)?
        if re.search(r"[a-zA-Z]", tok) and not re.search(rf"[{CJK_RANGE}]", tok):
            # Look for an adjacent Chinese token
            if i + 1 < len(tokens) and re.search(rf"[{CJK_RANGE}]", tokens[i + 1]):
                fr = tok
                zh = tokens[i + 1].strip()
                # split multi-sentence FR into last sentence only (more targeted)
                # keep only the sentence closest to the ZH
                m = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÿ])", fr)
                fr_last = m[-1].strip() if m else fr
                if len(fr_last) >= 8 and len(zh) >= 2:
                    pairs.append((fr_last, zh))
                i += 2
                continue
        i += 1
    return pairs


def build_dict() -> dict[str, str]:
    d = docx.Document(str(TAXI))
    raw_pairs = []
    for p in d.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        latin = sum(1 for c in t if c.isalpha() and ord(c) < 0x2E80)
        cjk = sum(1 for c in t if 0x4E00 <= ord(c) <= 0x9FFF)
        if latin < 10 or cjk < 3:
            continue
        raw_pairs.extend(split_pairs(t))

    # Build dict: keyed by folded first 40 chars of French
    out: dict[str, str] = {}
    collisions = 0
    for fr, zh in raw_pairs:
        # Strip trailing Chinese punctuation from zh (so it's clean)
        zh = re.sub(rf"^[{CJK_PUNCT}\s]+|[{CJK_PUNCT}\s]+$", "", zh).strip()
        if not zh:
            continue
        key = fold(fr)[:40]
        if len(key) < 10:
            continue
        if key in out and out[key] != zh:
            collisions += 1
            # keep the longer translation
            if len(zh) > len(out[key]):
                out[key] = zh
        else:
            out[key] = zh
    print(f"built dictionary: {len(out)} unique keys, {collisions} key collisions")
    return out


CARD_RE = re.compile(
    r"\{\s*id:\s*`([^`]+)`\s*,\s*front:\s*`([^`]*)`\s*,\s*back:\s*`([^`]*)`\s*\}",
)


def rewrite_books(translation_dict: dict[str, str]) -> tuple[int, int, int]:
    content = BOOKS.read_text(encoding="utf-8")
    filled = 0
    partial = 0
    total_empty = 0

    def repl(match):
        nonlocal filled, partial, total_empty
        cid, front, back = match.group(1), match.group(2), match.group(3)
        if back.strip():
            return match.group(0)
        total_empty += 1
        key = fold(front)[:40]
        if len(key) < 10:
            return match.group(0)
        # Try exact prefix match
        zh = translation_dict.get(key)
        if not zh:
            # Try fuzzier: any dict key that is a prefix of ours, or we are a prefix of
            for k, v in translation_dict.items():
                if k[:25] and (key.startswith(k[:25]) or k.startswith(key[:25])):
                    zh = v
                    partial += 1
                    break
        if not zh:
            return match.group(0)
        filled += 1
        # Escape backticks/$ in zh
        zh_esc = zh.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        # Rebuild the literal preserving original spacing
        return f"{{ id: `{cid}`, front: `{front}`, back: `{zh_esc}` }}"

    new_content = CARD_RE.sub(repl, content)
    BOOKS.write_text(new_content, encoding="utf-8")
    return filled, partial, total_empty


def main():
    td = build_dict()
    filled, partial, empty = rewrite_books(td)
    print(f"empty cards scanned: {empty}")
    print(f"filled: {filled} ({100*filled/empty:.1f}%)" if empty else "(no empty cards)")
    print(f"  of which prefix-fuzzy: {partial}")


if __name__ == "__main__":
    main()
