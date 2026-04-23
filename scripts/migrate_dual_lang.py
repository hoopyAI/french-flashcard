"""Migrate books.ts from {id, front, back} to {id, front, zh, en}.

Detects the language of the existing `back` field on each card by CJK
character ratio, then puts the text in the matching slot and leaves the
other slot as an empty string (to be filled by a subsequent translation
pass).

Also updates the Card interface and rewrites the entire data file with
the new schema. After this script, every card object in the file has
zh: string and en: string (either may be "").
"""
from __future__ import annotations
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BOOKS = Path(r"C:/Users/racwang/hoopy/french-flashcard/src/data/books.ts")


def is_cjk_dominant(s: str) -> bool:
    """Return True if >=3 CJK chars AND CJK count >= Latin letter count."""
    cjk = sum(1 for c in s if 0x4E00 <= ord(c) <= 0x9FFF)
    latin = sum(1 for c in s if c.isalpha() and ord(c) < 0x2E80)
    if cjk >= 3 and cjk >= latin:
        return True
    return False


CARD_RE = re.compile(
    r"\{\s*id:\s*`(?P<cid>[^`]+)`\s*,\s*front:\s*`(?P<front>[^`]*)`\s*,\s*back:\s*`(?P<back>[^`]*)`\s*\}",
)


def migrate():
    content = BOOKS.read_text(encoding="utf-8")

    # Update Card interface
    old_iface = (
        "export interface Card {\n"
        "  id: string;\n"
        "  front: string;\n"
        "  back: string;\n"
        "}"
    )
    new_iface = (
        "export interface Card {\n"
        "  id: string;\n"
        "  front: string;\n"
        "  zh: string;\n"
        "  en: string;\n"
        "}"
    )
    if old_iface not in content:
        raise SystemExit("Interface signature not found — did the schema already migrate?")
    content = content.replace(old_iface, new_iface)

    zh_count = en_count = marker_count = 0

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    def repl(m: re.Match[str]) -> str:
        nonlocal zh_count, en_count, marker_count
        cid = m.group("cid")
        front = m.group("front")
        back = m.group("back")

        if cid.startswith("s_"):
            # Section marker — back is always empty by design
            marker_count += 1
            return f"{{ id: `{cid}`, front: `{esc(front)}`, zh: ``, en: `` }}"

        if not back.strip():
            # Empty back (shouldn't happen post-translation, but tolerate)
            return f"{{ id: `{cid}`, front: `{esc(front)}`, zh: ``, en: `` }}"

        if is_cjk_dominant(back):
            zh_count += 1
            return f"{{ id: `{cid}`, front: `{esc(front)}`, zh: `{esc(back)}`, en: `` }}"
        else:
            en_count += 1
            return f"{{ id: `{cid}`, front: `{esc(front)}`, zh: ``, en: `{esc(back)}` }}"

    new_content = CARD_RE.sub(repl, content)
    BOOKS.write_text(new_content, encoding="utf-8")

    print(f"Migrated:")
    print(f"  cards with ZH back → .zh slot: {zh_count}")
    print(f"  cards with EN back → .en slot: {en_count}")
    print(f"  section markers (both empty): {marker_count}")
    print(f"  total: {zh_count + en_count + marker_count}")


if __name__ == "__main__":
    migrate()
