"""Dump all cards with empty `back` field into .planning/to-translate.json
grouped by lesson. Each entry has {lesson_id, cards: [{id, front}]}.
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
OUT = ROOT / ".planning" / "to-translate.json"

content = BOOKS.read_text(encoding="utf-8")

LESSON_RE = re.compile(
    r"\{\s*id:\s*`(u\d+l\d+)`\s*,\s*title:\s*`([^`]+)`\s*,\s*cards:\s*\[(.*?)\]\s*,?\s*\}",
    re.S,
)
CARD_RE = re.compile(
    r"\{\s*id:\s*`([^`]+)`\s*,\s*front:\s*`([^`]*)`\s*,\s*back:\s*`([^`]*)`\s*\}",
)

lessons = []
for m in LESSON_RE.finditer(content):
    lid = m.group(1)
    title = m.group(2)
    cards = []
    for cm in CARD_RE.finditer(m.group(3)):
        cid, front, back = cm.group(1), cm.group(2), cm.group(3)
        if not back.strip() and not cid.startswith("s_"):
            cards.append({"id": cid, "fr": front})
    if cards:
        lessons.append({"lesson": lid, "title": title, "count": len(cards), "cards": cards})

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(lessons, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"wrote {OUT}")
print(f"lessons needing translations: {len(lessons)}")
print(f"total cards to translate: {sum(l['count'] for l in lessons)}")
print()
for l in lessons:
    print(f"  {l['lesson']:<8} {l['count']:>4}  {l['title']}")
