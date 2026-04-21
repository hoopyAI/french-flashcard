"""Audit each lesson: compare books.ts content vs docx reading/listening openings.

Writes a markdown report to .planning/lesson-audit.md. Report keeps excerpts
short (first ~60 chars of openings only) so we can evaluate coverage without
dumping full passages.
"""
from __future__ import annotations
import io
import json
import re
import sys
from pathlib import Path

import docx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:/Users/racwang/hoopy/french-flashcard")
DOCX = Path(r"C:/Users/racwang/Downloads/B1讲义完整版.pdf+改25.5.31775191233.docx")
BOOKS = ROOT / "src" / "data" / "books.ts"
OUT = ROOT / ".planning" / "lesson-audit.md"

LESSON_RE = re.compile(r"(U\d+L\d+)\s*([^-–—]*?)\s*[-–—]\s*(texte\s*[AB]|grammaire|texte\s*\(?\d\)?)", re.I)
# Only match the *actual* transcription section (prefer Latin keyword), not the outline label
TRANS_RE = re.compile(r"^(Transcription\b|听力文本|Transcription\s*听力)", re.I)
# Skip exercise markers, outline labels, directives, and single-letter exercise items
SKIP_RE = re.compile(
    r"^(知识点|Corrigé|Exercice|Vocabulaire|Prononcez|Devoir|grammaire|Observez|Lisez|Dites|Vrai|Faux|Complétez|Répondez|"
    r"课文讲解|structure|texte\s*[AB]|一、|二、|三、|四、|五、|六、|预习|自主|Transcription|听力|"
    r"[a-h]\s+|[0-9]+[.．]|\(\d+\)|Imaginez|Faites|Présentez|Écoutez|Ecoutez|Mettez)",
    re.I,
)
# Anchor to "课文讲解" (text-explanation) which reliably precedes the reading passage
EXPL_ANCHOR_RE = re.compile(r"课文讲解\s*\d?")


def is_french_prose(t: str) -> bool:
    """Heuristic: paragraph contains French words (latin letters + accents), not just cues."""
    if len(t) < 20:
        return False
    # count latin letters vs CJK
    latin = sum(1 for c in t if c.isalpha() and ord(c) < 0x2E80)
    cjk = sum(1 for c in t if 0x4E00 <= ord(c) <= 0x9FFF)
    # reading paragraphs are mostly French; avoid vocab lines like "mot n.m. 含义"
    if cjk > latin // 3:
        return False
    return latin > 15


FULL_TEXT_CACHE: dict[str, str] = {}  # per-lesson normalized full text for fuzzy match


def parse_docx():
    """Return dict: lesson_id -> {reading_open, listen_open, heading_idx, trans_idx}."""
    d = docx.Document(str(DOCX))
    paragraphs = d.paragraphs
    N = len(paragraphs)

    # First pass: find all lesson headings and transcription markers
    headings = []  # (i, lesson_id, subtype)
    trans_positions = []
    for i, p in enumerate(paragraphs):
        t = p.text.strip()
        if not t:
            continue
        m = LESSON_RE.search(t)
        if m:
            headings.append((i, m.group(1).upper(), m.group(3).lower()))
        if TRANS_RE.search(t):
            trans_positions.append(i)

    # For each lesson, find:
    #   - first "texte A" heading index
    #   - next lesson heading (bound)
    #   - within that range, find first French prose that is not a section marker or exercise
    lesson_headings = {}
    for i, lid, sub in headings:
        lesson_headings.setdefault(lid, []).append((i, sub))

    ordered_lids = sorted(
        lesson_headings.keys(),
        key=lambda x: (int(re.search(r"U(\d+)", x).group(1)), int(re.search(r"L(\d+)", x).group(1))),
    )

    # Bounds: next lesson's first heading idx
    bounds = {}
    for k, lid in enumerate(ordered_lids):
        this_start = lesson_headings[lid][0][0]
        next_start = lesson_headings[ordered_lids[k + 1]][0][0] if k + 1 < len(ordered_lids) else N
        bounds[lid] = (this_start, next_start)

    result = {}
    for lid in ordered_lids:
        start, end = bounds[lid]
        headings_in_lesson = lesson_headings[lid]
        reading_open = None
        reading_idx = None
        # Strategy: find "课文讲解" marker within lesson bounds, then the next French prose
        # is the start of the actual reading passage. Exercises use "a/b/c" prompts which
        # we already filter out via SKIP_RE.
        anchor_idx = None
        for j in range(start, end):
            t = paragraphs[j].text.strip()
            if EXPL_ANCHOR_RE.search(t):
                anchor_idx = j
                break
        scan_start = anchor_idx + 1 if anchor_idx is not None else start + 1
        for j in range(scan_start, min(scan_start + 80, end)):
            t = paragraphs[j].text.strip()
            if not t:
                continue
            if SKIP_RE.match(t):
                continue
            if is_french_prose(t):
                reading_open = t
                reading_idx = j
                break
        # Find listening transcription within this lesson's range
        listen_open = None
        listen_idx = None
        for tp in trans_positions:
            if start <= tp < end:
                for j in range(tp + 1, min(tp + 20, end)):
                    t = paragraphs[j].text.strip()
                    if not t:
                        continue
                    if is_french_prose(t):
                        listen_open = t
                        listen_idx = j
                        break
                if listen_open:
                    break

        # Build full-text indexes per section — reading section = [anchor_idx..first trans in lesson]
        # listening section = [trans_idx..end]
        first_trans_in_lesson = None
        for tp in trans_positions:
            if start <= tp < end:
                first_trans_in_lesson = tp
                break
        # Reading body = everything from lesson heading up to the listening transcription
        # (or lesson end). Even if it includes exercise prompts/vocab, the match just needs
        # to find each card's text somewhere — false-positive hits on vocab are acceptable
        # because cards are rarely short enough to collide with vocab entries.
        rend = first_trans_in_lesson if first_trans_in_lesson else end
        reading_body = "\n".join(paragraphs[j].text for j in range(start, rend))
        listen_body = ""
        if first_trans_in_lesson is not None:
            listen_body = "\n".join(paragraphs[j].text for j in range(first_trans_in_lesson, end))
        FULL_TEXT_CACHE[f"{lid}:R"] = normalize(reading_body)
        FULL_TEXT_CACHE[f"{lid}:L"] = normalize(listen_body)

        result[lid] = {
            "heading_idx": start,
            "bounds": (start, end),
            "reading_open": reading_open,
            "reading_idx": reading_idx,
            "listen_open": listen_open,
            "listen_idx": listen_idx,
            "num_texte_a": sum(1 for _, s in headings_in_lesson if "texte a" in s.lower()),
            "has_transcription": first_trans_in_lesson is not None,
            "reading_body_len": len(reading_body),
            "listen_body_len": len(listen_body),
        }
    return result


CARD_RE = re.compile(
    r"\{\s*id:\s*[`\"]([^`\"]+)[`\"]\s*,\s*front:\s*[`\"]([^`\"]*)[`\"]\s*,\s*back:\s*[`\"]([^`\"]*)[`\"]\s*\}",
)
LESSON_BLOCK_RE = re.compile(
    r"\{\s*id:\s*[`\"](u\d+l\d+)[`\"]\s*,\s*title:\s*[`\"]([^`\"]+)[`\"]\s*,\s*cards:\s*\[(.*?)\]\s*,?\s*\}",
    re.S,
)


def parse_books_ts():
    content = BOOKS.read_text(encoding="utf-8")
    result = {}
    for m in LESSON_BLOCK_RE.finditer(content):
        lid = m.group(1).upper()
        title = m.group(2)
        cards_raw = m.group(3)
        cards = [(cm.group(1), cm.group(2), cm.group(3)) for cm in CARD_RE.finditer(cards_raw)]
        result[lid] = {
            "title": title,
            "cards": cards,
            "count": len(cards),
        }
    return result


def normalize(s: str) -> str:
    """Lowercase + strip punctuation/whitespace. No truncation — full text for indexing."""
    s = s.lower()
    s = re.sub(r"[^\w]+", "", s)
    return s


def norm_key(s: str) -> str:
    """Short lookup key (first ~40 chars of normalized text)."""
    return normalize(s)[:40]


def starts_with_match(card_text: str, doc_text: str | None) -> bool:
    if not doc_text:
        return False
    return normalize(card_text) and normalize(doc_text).startswith(normalize(card_text)[:20])


def classify(cards, docx_info, lid):
    """Return a list of status tags based on which docx section each card falls into."""
    status = []
    content_cards = [(cid, f, b) for cid, f, b in cards if not cid.startswith("s_")]
    if not content_cards:
        return ["empty"]

    reading_body = FULL_TEXT_CACHE.get(f"{lid}:R", "")
    listen_body = FULL_TEXT_CACHE.get(f"{lid}:L", "")

    # Classify each card: 'R' if its normalized text appears in reading body, 'L' if in listen, '?' otherwise
    tags_per_card = []
    for _, f, _ in content_cards:
        key = normalize(f)[:20]
        if len(key) < 8:
            tags_per_card.append("?")
            continue
        r_hit = key in reading_body if reading_body else False
        l_hit = key in listen_body if listen_body else False
        if r_hit and not l_hit:
            tags_per_card.append("R")
        elif l_hit and not r_hit:
            tags_per_card.append("L")
        elif r_hit and l_hit:
            tags_per_card.append("B")
        else:
            tags_per_card.append("?")

    n = len(tags_per_card)
    n_r = tags_per_card.count("R")
    n_l = tags_per_card.count("L")
    n_b = tags_per_card.count("B")
    n_u = tags_per_card.count("?")

    # Determine primary structure
    if n_r and n_l:
        # find split point
        split = next((i for i, t in enumerate(tags_per_card) if t == "L"), None)
        status.append(f"reading+listening (split≈card {split + 1 if split is not None else '?'}) R={n_r} L={n_l} ?={n_u}")
    elif n_r and not n_l:
        status.append(f"reading only (R={n_r} ?={n_u})")
    elif n_l and not n_r:
        status.append(f"listening only (L={n_l} ?={n_u})")
    elif n_u == n:
        status.append(f"no docx match ({n} cards)")
    else:
        status.append(f"mixed (R={n_r} L={n_l} B={n_b} ?={n_u})")

    # translation coverage
    translated = sum(1 for _, _, b in content_cards if b.strip())
    status.append(f"zh {translated}/{n}")
    return status


def main():
    docx_data = parse_docx()
    books_data = parse_books_ts()

    all_lids = sorted(
        set(docx_data) | set(books_data),
        key=lambda x: (
            int(re.search(r"U(\d+)", x).group(1)),
            int(re.search(r"L(\d+)", x).group(1)),
        ),
    )

    lines = []
    lines.append("# Lesson content audit")
    lines.append("")
    lines.append("Comparing `src/data/books.ts` against `B1讲义` docx to identify which lessons have reading, listening, both, or neither.")
    lines.append("")
    lines.append("| Lesson | books.ts | docx reading | docx listening | Status |")
    lines.append("| --- | ---: | :---: | :---: | --- |")

    summary = {"both": 0, "reading_only": 0, "listening_only": 0, "unknown": 0, "empty": 0, "missing_from_docx": 0}

    for lid in all_lids:
        bk = books_data.get(lid)
        dx = docx_data.get(lid)
        card_count = bk["count"] if bk else 0
        has_r = "R" if dx and dx["reading_open"] else "-"
        has_l = "L" if dx and dx["listen_open"] else "-"
        if bk:
            tags = classify(bk["cards"], dx, lid)
            status = "; ".join(tags)
        else:
            status = "no books.ts entry"
        if not dx:
            status += " · no docx match"

        # increment counters — order matters: check more specific patterns first
        if "reading+listening" in status:
            summary["both"] += 1
        elif "listening only" in status:
            summary["listening_only"] += 1
        elif "reading only" in status:
            summary["reading_only"] += 1
        elif "empty" in status:
            summary["empty"] += 1
        elif "no docx match" in status:
            summary["missing_from_docx"] += 1
        else:
            summary["unknown"] += 1

        lines.append(f"| {lid} | {card_count} | {has_r} | {has_l} | {status} |")

    lines.append("")
    lines.append("## Summary")
    for k, v in summary.items():
        lines.append(f"- {k}: {v}")
    lines.append(f"- total: {len(all_lids)}")

    lines.append("")
    lines.append("## Per-lesson details")
    for lid in all_lids:
        bk = books_data.get(lid)
        dx = docx_data.get(lid)
        title = bk["title"] if bk else "(no books.ts)"
        lines.append(f"\n### {lid} — {title}")
        lines.append(f"- cards: {bk['count'] if bk else 0}")
        if bk and bk["cards"]:
            content = [(cid, f) for cid, f, _ in bk["cards"] if not cid.startswith("s_")]
            if content:
                lines.append(f"- books.ts first: `{content[0][1][:60]}`")
                lines.append(f"- books.ts last:  `{content[-1][1][:60]}`")
        if dx:
            if dx["reading_open"]:
                lines.append(f"- docx reading opens: `{dx['reading_open'][:60]}` @ para {dx['reading_idx']}")
            else:
                lines.append("- docx reading: **not found**")
            if dx["listen_open"]:
                lines.append(f"- docx listening opens: `{dx['listen_open'][:60]}` @ para {dx['listen_idx']}")
            else:
                lines.append("- docx listening: (none)")
        else:
            lines.append("- no matching heading in docx")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"summary: {json.dumps(summary, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
