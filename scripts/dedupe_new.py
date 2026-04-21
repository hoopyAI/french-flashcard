"""Remove duplicate new cards (r*/l*) within each lesson.

Duplicates are counted by normalized French text. First occurrence kept,
later duplicates removed. Only touches new cards; original c* cards and
s_* markers are never touched.

Run with --dry-run to preview.
"""
from __future__ import annotations
import argparse
import io
import re
import sys
from pathlib import Path
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:/Users/racwang/hoopy/french-flashcard")
BOOKS = ROOT / "src" / "data" / "books.ts"

LESSON_RE = re.compile(
    r"\{\s*id:\s*`(u\d+l\d+)`\s*,\s*title:\s*`([^`]+)`\s*,\s*cards:\s*\[(.*?)\]\s*,?\s*\}",
    re.S,
)
CARD_LINE_RE = re.compile(
    r"^(\s*)\{\s*id:\s*`([^`]+)`\s*,\s*front:\s*`([^`]*)`\s*,\s*back:\s*`([^`]*)`\s*\}(,?\s*)$",
    re.M,
)

NEW_ID = re.compile(r"^[rl]\d+$")


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w]+", "", s)
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    content = BOOKS.read_text(encoding="utf-8")

    # Identify per-lesson card ranges
    # For each lesson, scan its cards in order; track seen normalized-front keys.
    # If a new card duplicates a prior card (in same lesson), mark for deletion.

    deletions = []  # list of (lesson_id, cid, front, start, end_of_line_in_full_content)

    for lm in LESSON_RE.finditer(content):
        lid = lm.group(1)
        cards_block_start = lm.start(3)
        cards_block_end = lm.end(3)
        cards_block = content[cards_block_start:cards_block_end]
        seen: set[str] = set()
        for cm in CARD_LINE_RE.finditer(cards_block):
            cid = cm.group(2)
            front = cm.group(3)
            key = norm(front)
            if not NEW_ID.match(cid):
                # Original card — seed the seen set so new cards mirroring originals are dropped too
                seen.add(key)
                continue
            if key in seen:
                abs_start = cards_block_start + cm.start()
                abs_end = cards_block_start + cm.end()
                line_end = content.find("\n", abs_end) + 1
                if line_end <= 0:
                    line_end = abs_end
                deletions.append((lid, cid, front, abs_start, line_end))
            else:
                seen.add(key)

    # Group by lesson for reporting
    per_lesson = Counter(d[0] for d in deletions)

    print(f"Duplicate cards to remove: {len(deletions)}")
    for lid, n in per_lesson.most_common():
        print(f"  {lid:<8} {n}")

    print("\nSample duplicates (first 10):")
    for lid, cid, front, _, _ in deletions[:10]:
        print(f"  {lid}/{cid}: {front[:90]!r}")

    if args.dry_run:
        print("\n(dry-run)")
        return

    # Apply from end to start
    deletions.sort(key=lambda x: x[3], reverse=True)
    new_content = content
    for _, _, _, start, end in deletions:
        new_content = new_content[:start] + new_content[end:]

    BOOKS.write_text(new_content, encoding="utf-8")
    print(f"\nRemoved {len(deletions)} duplicates. File rewritten.")


if __name__ == "__main__":
    main()
