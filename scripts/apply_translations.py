"""Apply English translations from .planning/translations.json to books.ts.

The translations file is a flat map: {"lesson_id": {"card_id": "English"}}.
Only updates cards with empty `back`. Never overwrites existing translations.

Report prints per-lesson fill counts.
"""
from __future__ import annotations
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:/Users/racwang/hoopy/french-flashcard")
BOOKS = ROOT / "src" / "data" / "books.ts"
TRANSLATIONS = ROOT / ".planning" / "translations.json"

LESSON_RE = re.compile(
    r"(\{\s*id:\s*`(u\d+l\d+)`\s*,\s*title:\s*`[^`]+`\s*,\s*cards:\s*\[)(.*?)(\s*\]\s*,?\s*\})",
    re.S,
)
CARD_RE = re.compile(
    r"\{\s*id:\s*`([^`]+)`\s*,\s*front:\s*`([^`]*)`\s*,\s*back:\s*`([^`]*)`\s*\}",
)


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def main():
    translations = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))
    content = BOOKS.read_text(encoding="utf-8")

    filled_per_lesson = {}
    skipped_per_lesson = {}
    missing_keys = []

    def rebuild_cards_block(cards_text: str, lid: str) -> str:
        filled = 0
        skipped = 0

        def replace_card(m):
            nonlocal filled, skipped
            cid, front, back = m.group(1), m.group(2), m.group(3)
            if back.strip():
                return m.group(0)
            t = translations.get(lid, {}).get(cid)
            if not t:
                skipped += 1
                return m.group(0)
            filled += 1
            return f"{{ id: `{cid}`, front: `{esc(front)}`, back: `{esc(t)}` }}"

        new_block = CARD_RE.sub(replace_card, cards_text)
        filled_per_lesson[lid] = filled
        skipped_per_lesson[lid] = skipped
        return new_block

    def replace_lesson(m):
        lid = m.group(2)
        pre, body, post = m.group(1), m.group(3), m.group(4)
        new_body = rebuild_cards_block(body, lid)
        return pre + new_body + post

    new_content = LESSON_RE.sub(replace_lesson, content)

    # Sanity: warn if translations.json has IDs not present in books.ts
    for lid, card_map in translations.items():
        for cid in card_map:
            # Look for the id in content — if not present, the translation was unused
            if f"id: `{cid}`" not in new_content:
                missing_keys.append(f"{lid}/{cid}")

    BOOKS.write_text(new_content, encoding="utf-8")

    total_filled = sum(filled_per_lesson.values())
    print(f"Filled: {total_filled} cards")
    for lid in sorted(filled_per_lesson):
        f = filled_per_lesson[lid]
        s = skipped_per_lesson[lid]
        if f or s:
            print(f"  {lid:<8} filled={f:<4} still empty={s}")
    if missing_keys:
        print(f"\nUnused translation keys ({len(missing_keys)}):")
        for k in missing_keys[:20]:
            print(f"  {k}")


if __name__ == "__main__":
    main()
