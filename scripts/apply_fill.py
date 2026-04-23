"""Apply fill-in translations from .planning/fill-trans.json to books.ts.

Input shape (partial — contains only the cards you want to fill):
  {
    "u1l1": {
      "c1": { "en": "English ..." },
      "c2": { "zh": "中文 ..." },
      "c3": { "en": "...", "zh": "..." }
    },
    ...
  }

For each card, only *empty* slots in books.ts are filled; existing values
are never overwritten. Reports per-lesson fill counts.
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
FILL = ROOT / ".planning" / "fill-trans.json"

LESSON_BLOCK_RE = re.compile(
    r"(\{\s*id:\s*`(u\d+l\d+)`\s*,\s*title:\s*`[^`]+`\s*,\s*cards:\s*\[)(.*?)(\s*\]\s*,?\s*\})",
    re.S,
)
CARD_RE = re.compile(
    r"(\{\s*id:\s*`)(?P<cid>[^`]+)(`\s*,\s*front:\s*`)(?P<front>[^`]*)(`\s*,\s*zh:\s*`)(?P<zh>[^`]*)(`\s*,\s*en:\s*`)(?P<en>[^`]*)(`\s*\})",
    re.S,
)


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def main():
    if not FILL.exists():
        sys.exit(f"no fill file at {FILL}")
    fills = json.loads(FILL.read_text(encoding="utf-8"))
    content = BOOKS.read_text(encoding="utf-8")

    per_lesson_zh: dict[str, int] = {}
    per_lesson_en: dict[str, int] = {}
    per_lesson_skipped: dict[str, int] = {}

    def rewrite_block(m: re.Match[str]) -> str:
        head, lid, body, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        lesson_fills = fills.get(lid)
        if not lesson_fills:
            return m.group(0)

        zh_filled = 0
        en_filled = 0
        skipped = 0

        def rewrite_card(cm: re.Match[str]) -> str:
            nonlocal zh_filled, en_filled, skipped
            cid = cm.group("cid")
            front = cm.group("front")
            zh = cm.group("zh")
            en = cm.group("en")
            new = lesson_fills.get(cid)
            if not new:
                return cm.group(0)
            if "zh" in new and new["zh"].strip() and not zh.strip():
                zh = new["zh"]
                zh_filled += 1
            if "en" in new and new["en"].strip() and not en.strip():
                en = new["en"]
                en_filled += 1
            if "zh" in new and new["zh"].strip() and cm.group("zh").strip():
                skipped += 1
            if "en" in new and new["en"].strip() and cm.group("en").strip():
                skipped += 1
            return f"{{ id: `{cid}`, front: `{esc(front)}`, zh: `{esc(zh)}`, en: `{esc(en)}` }}"

        new_body = CARD_RE.sub(rewrite_card, body)
        per_lesson_zh[lid] = zh_filled
        per_lesson_en[lid] = en_filled
        per_lesson_skipped[lid] = skipped
        return head + new_body + tail

    new_content = LESSON_BLOCK_RE.sub(rewrite_block, content)
    BOOKS.write_text(new_content, encoding="utf-8")

    total_zh = sum(per_lesson_zh.values())
    total_en = sum(per_lesson_en.values())
    total_skip = sum(per_lesson_skipped.values())
    print(f"Filled {total_zh} zh slots, {total_en} en slots")
    if total_skip:
        print(f"Skipped {total_skip} slots that already had content (not overwritten)")
    for lid in sorted(per_lesson_zh):
        if per_lesson_zh[lid] or per_lesson_en[lid]:
            print(f"  {lid:<8}  +{per_lesson_zh[lid]} zh  +{per_lesson_en[lid]} en")


if __name__ == "__main__":
    main()
