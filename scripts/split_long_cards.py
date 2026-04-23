"""Re-split cards whose French front is too long into multiple smaller cards.

Only touches r*/l* cards (our docx-extracted cards). Original c* cards are
left alone — the user designed those and their hand-made Chinese is split
to match.

Splitting rules (applied in order):
  1. Strong: . ! ? … » followed by space + uppercase/open-quote
  2. Medium: ; or : followed by space + uppercase (typically a new thought)
  3. If still too long, split on ": " even without uppercase follow-up
Protected: common abbreviations (M., Mme., etc.), numbered references (n°19).

Each new sub-card inherits the back (translation) field of the original —
that creates temporary duplication but the upcoming zh/en migration will
re-translate anyway.
"""
from __future__ import annotations
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:/Users/racwang/hoopy/french-flashcard")
BOOKS = ROOT / "src" / "data" / "books.ts"

CARD_LINE_RE = re.compile(
    r"^(?P<indent>\s*)\{\s*id:\s*`(?P<cid>[rl]\d+)`\s*,\s*front:\s*`(?P<front>[^`]*)`\s*,\s*back:\s*`(?P<back>[^`]*)`\s*\}(?P<tail>,?\s*)$",
    re.M,
)

LONG_THRESHOLD = 200  # re-split if a card's front exceeds this many chars

# Abbreviations to protect from sentence splitting
ABBREV = [
    "M.", "Mme.", "Mlle.", "Dr.", "St.", "Ste.", "Pr.", "pp.", "p.",
    "etc.", "ex.", "cf.", "i.e.", "e.g.", "vs.", "n°", "N°", "p.ex.",
    "U.S.", "U.K.", "av.", "ap.", "J.-C.",
]


def _protect(text: str) -> str:
    for ab in ABBREV:
        text = text.replace(ab, ab.replace(".", "\x00"))
    # Also protect decimal numbers like "1.5" and time like "20:30"
    text = re.sub(r"(\d)\.(\d)", lambda m: f"{m.group(1)}\x00{m.group(2)}", text)
    text = re.sub(r"(\d):(\d)", lambda m: f"{m.group(1)}\x01{m.group(2)}", text)
    return text


def _unprotect(text: str) -> str:
    return text.replace("\x00", ".").replace("\x01", ":")


def split_front(text: str) -> list[str]:
    """Return sentences from `text`, splitting on common boundaries."""
    t = _protect(text)

    # Pass 1: strong sentence boundaries (. ! ? … » followed by space + capital/quote)
    parts = re.split(r"(?<=[.!?…»])\s+(?=[A-ZÀ-ÿ«\"'“‘(])", t)

    # Pass 2: for each remaining part longer than threshold, try ; and : boundaries
    def refine(p: str) -> list[str]:
        if len(p) <= LONG_THRESHOLD:
            return [p]
        sub = re.split(r"(?<=[;:])\s+(?=[A-ZÀ-ÿ«\"'“‘])", p)
        if len(sub) == 1:
            # Still too long? Try any ; split
            sub = re.split(r"\s*;\s+", p)
        if len(sub) == 1:
            # Try splitting on ". " + lowercase as last resort
            sub = re.split(r"(?<=[.!?])\s+", p)
        return sub

    refined: list[str] = []
    for p in parts:
        refined.extend(refine(p))

    # Cleanup
    out = []
    for s in refined:
        s = _unprotect(s).strip()
        if len(s) >= 8:
            out.append(s)
    return out


def rebuild():
    content = BOOKS.read_text(encoding="utf-8")
    total_long = 0
    total_split_into = 0
    changes: list[tuple[int, int, str]] = []  # (start, end, replacement)

    for m in CARD_LINE_RE.finditer(content):
        cid = m.group("cid")
        front = m.group("front")
        back = m.group("back")
        indent = m.group("indent")
        tail = m.group("tail")
        if len(front) <= LONG_THRESHOLD:
            continue
        sentences = split_front(front)
        if len(sentences) <= 1:
            continue
        total_long += 1
        total_split_into += len(sentences)

        def esc(s: str) -> str:
            return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

        # Re-number the split cards as cid-a, cid-b, cid-c... so they stay distinct
        # while keeping a visible relationship to the original.
        suffix_pool = "abcdefghijklmnop"
        new_lines = []
        for i, sent in enumerate(sentences):
            new_id = f"{cid}-{suffix_pool[i]}" if i < len(suffix_pool) else f"{cid}-{i}"
            # Always emit trailing comma on each card line; tail's original ","
            # (if present) is replaced so we never double up.
            new_lines.append(
                f"{indent}{{ id: `{new_id}`, front: `{esc(sent)}`, back: `{esc(back)}` }},"
            )
        replacement = "\n".join(new_lines)
        changes.append((m.start(), m.end(), replacement))

    # Apply from end to start
    for start, end, repl in sorted(changes, key=lambda x: x[0], reverse=True):
        content = content[:start] + repl + content[end:]

    BOOKS.write_text(content, encoding="utf-8")
    return total_long, total_split_into


def main():
    long_count, pieces = rebuild()
    print(f"Re-split {long_count} long card(s) into {pieces} piece(s)")
    print(f"Average {pieces / long_count:.1f} pieces per card" if long_count else "(nothing to split)")


if __name__ == "__main__":
    main()
