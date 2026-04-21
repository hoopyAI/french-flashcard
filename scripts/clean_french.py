"""Clean clearly-garbage cards from books.ts.

Two-stage cleanup:
  1. Strip trailing extraction noise (vocab-POS tags, cross-references)
     from within otherwise-legitimate reading cards.
  2. Delete cards that are wholly garbage (section titles, antonym lists,
     CJK-dominant lines, comma-only lists, etc.).

Only touches new cards (id matches r\\d+ or l\\d+). Original content
(c\\d+) and section markers (s_*) are never modified.

Run with --dry-run to preview changes.
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

CARD_LINE_RE = re.compile(
    r"^(?P<indent>\s*)\{\s*id:\s*`(?P<cid>[^`]+)`\s*,\s*front:\s*`(?P<front>[^`]*)`\s*,\s*back:\s*`(?P<back>[^`]*)`\s*\}(?P<tail>,?\s*)$",
    re.M,
)

NEW_CARD_ID = re.compile(r"^[rl]\d+$")

# ---- Strip rules (applied in order; each transforms the front text) ----
STRIP_RULES: list[tuple[str, re.Pattern[str]]] = [
    # Trailing vocab-POS entry: "... word n.m. def [Chinese]"
    # Be conservative: require a sentence-ending char before the stripped part.
    ("tail-vocab-pos", re.compile(
        r"[.!?]\s+\S+\s+(?:n\.\s*m\.|n\.\s*f\.|n\.\s*pr\.|adj\.|adv\.|v\.\s*t\.|v\.\s*i\.|v\.\s*pr\.|conj\.|prép\.|pl\.|loc\.|interj\.)\b.*$"
    )),
    # Trailing cross-reference: "... (texte 2)." or "... (l. 37)."
    ("tail-xref", re.compile(r"\s*\((?:texte|l|ligne|p|para|§)\.?\s*\d+\)\s*\.?\s*$", re.I)),
    # Trailing bracketed cross-reference: "[texte 1]"
    ("tail-xref-bracket", re.compile(r"\s*\[(?:texte|l|ligne|p|para|§)\.?\s*\d+\]\s*\.?\s*$", re.I)),
    # Trailing literal POS marker without word: "... désormais adv."
    ("tail-pos-only", re.compile(r"\s+\S+\s+(?:n\.m\.|n\.f\.|adj\.|adv\.|v\.t\.|v\.i\.|v\.pr\.)\s*$")),
    # Trailing word followed by " : " + French definition (vocab def stuck on reading)
    # Format like "... . bloc : pâté d'immeubles ..."
    # Require a period before the candidate to avoid stripping mid-sentence colons.
    ("tail-colon-def", re.compile(r"\.\s+\b[a-zA-ZÀ-ÿ]{3,}\b\s*:\s+.+$")),
]

# ---- Full-deletion rules (applied to the CLEANED front) ----
def should_delete(front: str) -> list[str]:
    reasons = []
    stripped = front.strip()
    if not re.search(r"[a-zA-ZÀ-ÿ]", stripped):
        reasons.append("no-letters")
    if len(stripped) < 15 and not stripped.endswith("?"):
        reasons.append("too-short")
    # Section headers like "Texte 1 : ..." or "Transcription"
    if re.match(r"^(Texte\s+[AB12]\b|Transcription\b)", stripped):
        reasons.append("section-title")
    # Antonym / equivalence list
    if stripped.count("≠") >= 1:
        reasons.append("antonym-list")
    # Any meaningful CJK in a French card means vocab example contamination.
    # Threshold of 3 chars allows for stray noise (a single CJK char from OCR)
    # while catching embedded translations.
    cjk = sum(1 for c in stripped if 0x4E00 <= ord(c) <= 0x9FFF)
    if cjk > 3:
        reasons.append("cjk-contaminated")
    # Comma list with no sentence-ending punct and 4+ commas
    if re.match(r"^([^,.!?:;]+,\s*){4,}[^,.!?:;]+\s*$", stripped):
        reasons.append("comma-list")
    # Slash list
    if re.match(r"^[^.!?]*(/[^/]+){3,}[^.!?]*$", stripped):
        reasons.append("slash-list")
    # Numbered bullet
    if re.match(r"^[1-9][/.．]\s", stripped):
        reasons.append("numbered-bullet")
    # Card still has mid-text vocab POS marker
    if re.search(r"(?<!\w)(?:n\.\s*m\.|n\.\s*f\.|adj\.|v\.\s*t\.|v\.\s*pr\.|v\.\s*i\.|adv\.|prép\.|conj\.)(?!\w)", stripped):
        reasons.append("mid-vocab-pos")
    # Exercise-prompt directives at start (Lisez, Observez, Faites, etc.)
    if re.match(r"^(Lisez|Observez|Faites|Écoutez|Ecoutez|Dites|Indiquez|Relevez|Associez|Cochez|Complétez|Répondez|Imaginez|Discutez|Présentez|Racontez|Choisissez|Résumez|Mettez|Classez|Cherchez|Décrivez|Expliquez|Comparez|Justifiez|Préparez|Interviewez|Commentez)\b", stripped):
        reasons.append("exercise-prompt")

    # Decision:
    # strong reasons → delete on any
    strong = {"no-letters", "section-title", "antonym-list", "cjk-contaminated", "comma-list", "slash-list", "numbered-bullet", "mid-vocab-pos", "exercise-prompt"}
    if set(reasons) & strong:
        return reasons
    return []


def strip_front(front: str) -> tuple[str, list[str]]:
    """Apply strip rules in order. Return (new_front, applied_tags)."""
    applied = []
    cur = front
    for tag, pat in STRIP_RULES:
        new = pat.sub("", cur).rstrip()
        if new != cur and len(new) >= 15:
            applied.append(tag)
            cur = new
    # Re-add trailing period if we stripped to mid-sentence-end without one
    if cur and cur[-1] not in ".!?»\"'":
        cur = cur + "."
    return cur, applied


def process():
    content = BOOKS.read_text(encoding="utf-8")

    deletions = []  # (cid, front, reasons, start, end_of_line)
    edits = []  # (cid, old_front, new_front, applied_tags, literal_start, literal_end)
    strip_cats = Counter()
    delete_cats = Counter()

    for m in CARD_LINE_RE.finditer(content):
        cid = m.group("cid")
        front = m.group("front")
        back = m.group("back")
        if not NEW_CARD_ID.match(cid):
            continue
        # Stage 1: strip
        cleaned, applied_tags = strip_front(front)
        # Stage 2: decide delete
        reasons = should_delete(cleaned)
        if reasons:
            # Find the newline at end of card line
            line_end = content.find("\n", m.end()) + 1
            if line_end <= 0:
                line_end = m.end()
            deletions.append((cid, front, reasons, m.start(), line_end))
            for r in reasons:
                delete_cats[r] += 1
        elif applied_tags:
            # Only record edit if not being deleted
            edits.append((cid, front, cleaned, applied_tags, m.start("front"), m.end("front")))
            for t in applied_tags:
                strip_cats[t] += 1

    return content, deletions, edits, strip_cats, delete_cats


def write_changes(content: str, deletions, edits):
    # Apply edits first (don't change line lengths enough to mess up offsets IF we do end→start)
    # Combine into one ordered list by start offset, descending.
    all_changes = []
    for cid, front, cleaned, _, fstart, fend in edits:
        # Escape backticks/$
        new = cleaned.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        all_changes.append(("edit", fstart, fend, new))
    for cid, front, reasons, dstart, dend in deletions:
        all_changes.append(("delete", dstart, dend, ""))
    all_changes.sort(key=lambda x: x[1], reverse=True)

    new_content = content
    for kind, start, end, replacement in all_changes:
        if kind == "edit":
            new_content = new_content[:start] + replacement + new_content[end:]
        else:
            new_content = new_content[:start] + new_content[end:]

    BOOKS.write_text(new_content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample", type=int, default=15)
    args = parser.parse_args()

    content, deletions, edits, strip_cats, delete_cats = process()

    print(f"Cards to strip (keep body, trim noise): {len(edits)}")
    for cat, n in strip_cats.most_common():
        print(f"  {cat:<20} {n}")
    print()
    print(f"Cards to delete (wholly garbage): {len(deletions)}")
    for cat, n in delete_cats.most_common():
        print(f"  {cat:<20} {n}")
    print()

    if edits:
        print(f"Sample strips (first {args.sample}):")
        for cid, old, new, tags, _, _ in edits[:args.sample]:
            print(f"  [{cid}] ({','.join(tags)})")
            print(f"    OLD: {old[:90]!r}")
            print(f"    NEW: {new[:90]!r}")
        print()

    if deletions:
        print(f"Sample deletions (first {args.sample}):")
        for cid, front, reasons, _, _ in deletions[:args.sample]:
            print(f"  [{cid}] ({','.join(reasons)}) {front[:90]!r}")

    if args.dry_run:
        print("\n(dry-run — no changes written)")
        return

    write_changes(content, deletions, edits)
    print(f"\n{len(edits)} cards trimmed, {len(deletions)} deleted. File rewritten.")


if __name__ == "__main__":
    main()
