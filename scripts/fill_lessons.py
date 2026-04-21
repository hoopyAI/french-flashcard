"""Batch-fill missing reading/listening sections in books.ts from the B1讲义 docx.

Strategy:
  1. Classify each books.ts lesson's current cards as reading or listening by
     full-text match against the docx (same logic as audit_lessons.py).
  2. For lessons that have only one side, extract the missing side from the
     docx and prepend/append as new cards with section markers. Existing cards
     are left untouched (original IDs, original translations).
  3. For lessons that already have both sides, just insert the two section
     markers at the detected split point.
  4. Re-serialize books.ts preserving the original backtick/template-string
     format. Existing card order is preserved within each side.

Extraction is deliberately conservative: when in doubt, skip. Over-extraction
is worse than under-extraction because the user will have to prune spam;
under-extraction just means a few cards are missing and can be added manually.

Nothing is printed to stdout except a structural summary (counts per lesson);
no passage content leaves the script.
"""
from __future__ import annotations
import io
import re
import sys
from pathlib import Path

import docx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:/Users/racwang/hoopy/french-flashcard")
DOCX = Path(r"C:/Users/racwang/Downloads/B1讲义完整版.pdf+改25.5.31775191233.docx")
BOOKS = ROOT / "src" / "data" / "books.ts"

# ---------- Regexes ----------
LESSON_RE = re.compile(r"(U\d+L\d+)\s*([^-–—]*?)\s*[-–—]\s*(texte\s*[AB]|grammaire|texte\s*\(?\d\)?)", re.I)
TRANS_RE = re.compile(r"^(Transcription\b|听力文本|Transcription\s*听力)", re.I)

# Paragraph-level skip patterns for reading extraction.
# These match paragraph *starts* — a paragraph matching any of these is discarded.
SKIP_RE = re.compile(
    r"^("
    r"知识点|Corrigé|Exercice|Vocabulaire|Prononcez|Devoir|grammaire|"
    r"Observez|Lisez|Dites|Complétez|Répondez|Imaginez|Faites|Présentez|Écoutez|Ecoutez|"
    r"Mettez|Associez|Trouvez|Choisissez|Relevez|Expliquez|Racontez|Classez|Cochez|Indiquez|"
    r"Discutez|Interviewez|Décrivez|Résumez|Comparez|Préparez|Commentez|Cherchez|"
    r"课文讲解|讲解|structure|一、|二、|三、|四、|五、|六、|预习|自主|"
    r"Transcription|听力|Vrai|Faux|"
    r"[a-hA-H][\s.)）、]|[0-9]+[.．、]|\(\d+\)|【"
    r")",
    re.I,
)

# Block-starter patterns that switch us *out* of skip mode. These mark the
# return of reading content after a vocabulary or exercise block.
RESUME_RE = re.compile(r"^(课文讲解|讲解)", re.I)

# Vocab-entry shape: short "word<tab>pos<tab>def" lines with CJK on the right
VOCAB_LINE = re.compile(r"[\u4e00-\u9fff]")


def is_french_prose(t: str) -> bool:
    if len(t) < 15:
        return False
    latin = sum(1 for c in t if c.isalpha() and ord(c) < 0x2E80)
    cjk = sum(1 for c in t if 0x4E00 <= ord(c) <= 0x9FFF)
    # a short line with any CJK is suspicious — probably vocab/note
    if cjk > 0 and len(t) < 40:
        return False
    # too CJK-heavy even if long
    if cjk > latin // 4:
        return False
    return latin > 15


def extract_reading(paragraphs, start: int, end: int) -> list[str]:
    """Extract reading paragraphs from [start..end).

    Skip 知识点 / Corrigé / exercise blocks. Reading returns when 课文讲解 /
    讲解 / Texte markers or a new texte-A sub-heading appears.
    """
    kept: list[str] = []
    mode = "scan"  # scan | skip
    for j in range(start, end):
        t = paragraphs[j].text.strip()
        if not t:
            continue
        # Any heading that starts a new block
        if RESUME_RE.match(t) or re.match(r"^U\d+L\d+\s", t) or t in ("Texte", "Texte A", "Texte B"):
            mode = "scan"
            continue
        if re.match(r"^(知识点|Corrigé|Exercice|Vocabulaire|Devoir)", t):
            mode = "skip"
            continue
        if SKIP_RE.match(t):
            # These are exercise prompts / outline markers / single-letter answers — always skip
            continue
        if mode == "skip":
            # Stay in skip until we hit a prose paragraph that's clearly a reading resume
            # (long, mostly French, no CJK) — this handles cases where 课文讲解 marker is missing
            if len(t) > 60 and is_french_prose(t) and not VOCAB_LINE.search(t):
                mode = "scan"
                kept.append(t)
            continue
        if is_french_prose(t):
            kept.append(t)
    return kept


def extract_listening(paragraphs, trans_idx: int, lesson_end: int) -> list[str]:
    """Listening transcription starts at trans_idx and ends at 知识点 or lesson_end."""
    kept: list[str] = []
    for j in range(trans_idx + 1, lesson_end):
        t = paragraphs[j].text.strip()
        if not t:
            continue
        if re.match(r"^(知识点|Corrigé|Exercice|Vocabulaire|讲解|Reportage diffusé)", t):
            # Reportage source attribution (e.g., "Reportage diffusé sur RTL") marks the *end*.
            # Include it as the last card for context, then stop.
            if t.startswith("Reportage"):
                kept.append(t)
            break
        if SKIP_RE.match(t):
            continue
        if is_french_prose(t):
            kept.append(t)
    return kept


def split_sentences(paragraphs: list[str]) -> list[str]:
    """Turn a list of reading paragraphs into a list of sentence-sized cards."""
    text = " ".join(p.strip() for p in paragraphs if p.strip())
    text = re.sub(r"\s+", " ", text)
    # Protect abbreviations so we don't split on them
    for abbr in ["M.", "Mme.", "Mlle.", "Dr.", "St.", "Ste.", "pp.", "p.", "etc.", "ex.", "cf.", "i.e.", "e.g.", "vs."]:
        text = text.replace(abbr, abbr.replace(".", "\x00"))
    # Split on sentence-final punct followed by space + capital/quote
    sents = re.split(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÿ«\"'“‘\(])", text)
    sents = [s.replace("\x00", ".").strip() for s in sents if s.strip()]
    # Filter tiny fragments
    return [s for s in sents if len(s) >= 8]


# ---------- docx parse ----------

def parse_docx():
    d = docx.Document(str(DOCX))
    paragraphs = d.paragraphs
    N = len(paragraphs)

    headings = []  # (i, lid, sub)
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

    lesson_headings: dict[str, list[tuple[int, str]]] = {}
    for i, lid, sub in headings:
        lesson_headings.setdefault(lid, []).append((i, sub))
    ordered_lids = sorted(
        lesson_headings,
        key=lambda x: (int(re.search(r"U(\d+)", x).group(1)), int(re.search(r"L(\d+)", x).group(1))),
    )

    bounds: dict[str, tuple[int, int]] = {}
    for k, lid in enumerate(ordered_lids):
        this_start = lesson_headings[lid][0][0]
        next_start = lesson_headings[ordered_lids[k + 1]][0][0] if k + 1 < len(ordered_lids) else N
        bounds[lid] = (this_start, next_start)

    result = {}
    for lid in ordered_lids:
        start, end = bounds[lid]
        first_trans = None
        for tp in trans_positions:
            if start <= tp < end:
                first_trans = tp
                break
        reading = extract_reading(paragraphs, start, first_trans if first_trans else end)
        listening = extract_listening(paragraphs, first_trans, end) if first_trans else []
        result[lid] = {
            "reading_paragraphs": reading,
            "listening_paragraphs": listening,
            "reading_cards": split_sentences(reading),
            "listening_cards": split_sentences(listening),
        }
    return result


# ---------- books.ts parse + write ----------

CARD_RE = re.compile(
    r"\{\s*id:\s*`([^`]+)`\s*,\s*front:\s*`([^`]*)`\s*,\s*back:\s*`([^`]*)`\s*\}",
)
LESSON_BLOCK_RE = re.compile(
    r"(\{\s*id:\s*`(u\d+l\d+)`\s*,\s*title:\s*`([^`]+)`\s*,\s*cards:\s*\[)(.*?)(\s*\]\s*,?\s*\})",
    re.S,
)


def parse_books():
    content = BOOKS.read_text(encoding="utf-8")
    lessons = {}
    for m in LESSON_BLOCK_RE.finditer(content):
        lid = m.group(2).upper()
        title = m.group(3)
        cards_raw = m.group(4)
        cards = [(cm.group(1), cm.group(2), cm.group(3)) for cm in CARD_RE.finditer(cards_raw)]
        lessons[lid] = {
            "title": title,
            "cards": cards,
            "match_start": m.start(4),
            "match_end": m.end(4),
        }
    return content, lessons


def normalize(s: str) -> str:
    return re.sub(r"[^\w]+", "", s.lower())


def card_literal(cid: str, front: str, back: str) -> str:
    # Original file uses backticks. Need to escape backtick/${ inside strings.
    def esc(x: str) -> str:
        return x.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    return f"{{ id: `{esc(cid)}`, front: `{esc(front)}`, back: `{esc(back)}` }}"


def classify_existing_cards(cards, rbody_norm: str, lbody_norm: str):
    """Return list of tags per card: 'R'/'L'/'?' + split_idx (first L) + has_section_marker."""
    tags = []
    for cid, front, _back in cards:
        if cid.startswith("s_"):
            tags.append("S")
            continue
        key = normalize(front)[:40]
        if len(key) < 8:
            tags.append("?")
            continue
        r = key in rbody_norm if rbody_norm else False
        l = key in lbody_norm if lbody_norm else False
        if r and not l:
            tags.append("R")
        elif l and not r:
            tags.append("L")
        elif r and l:
            tags.append("B")
        else:
            tags.append("?")
    return tags


def build_new_card_list(lid: str, current_cards, docx_data):
    """Decide what cards go in the lesson after merge.

    Returns (new_cards, action_taken) where new_cards is list of (id,front,back)
    and action_taken is a human-readable string for reporting.
    """
    title = None  # filled by caller
    dx = docx_data.get(lid)
    if not dx:
        return None, "skip (no docx match)"

    rcards_docx = dx["reading_cards"]
    lcards_docx = dx["listening_cards"]
    rbody_norm = normalize(" ".join(dx["reading_paragraphs"]))
    lbody_norm = normalize(" ".join(dx["listening_paragraphs"]))

    # Separate non-marker existing cards
    existing = [(cid, f, b) for cid, f, b in current_cards if not cid.startswith("s_")]
    tags = classify_existing_cards(existing, rbody_norm, lbody_norm)

    # Figure out which side existing cards belong to (majority vote, ignoring ?)
    n_r = tags.count("R") + tags.count("B")  # B = found in both, count as reading-adjacent
    n_l = tags.count("L")

    out: list[tuple[str, str, str]] = []
    action_parts = []

    if n_r and n_l:
        # Existing cards span both. Insert markers at detected split.
        split = next((i for i, t in enumerate(tags) if t == "L"), len(existing))
        out.append(("s_read", "【Lecture · 阅读】", ""))
        out.extend(existing[:split])
        out.append(("s_listen", "【Compréhension orale · 听力】", ""))
        out.extend(existing[split:])
        action_parts.append(f"both→markers (split@{split + 1})")
    elif n_r and not n_l:
        # Existing = reading. Add listening from docx.
        out.append(("s_read", "【Lecture · 阅读】", ""))
        out.extend(existing)
        if lcards_docx:
            out.append(("s_listen", "【Compréhension orale · 听力】", ""))
            for i, text in enumerate(lcards_docx, 1):
                out.append((f"l{i}", text, ""))
            action_parts.append(f"+listening ({len(lcards_docx)})")
        else:
            action_parts.append("reading-only, no docx listening to add")
    elif n_l and not n_r:
        # Existing = listening. Add reading from docx.
        if rcards_docx:
            out.append(("s_read", "【Lecture · 阅读】", ""))
            for i, text in enumerate(rcards_docx, 1):
                out.append((f"r{i}", text, ""))
            out.append(("s_listen", "【Compréhension orale · 听力】", ""))
            out.extend(existing)
            action_parts.append(f"+reading ({len(rcards_docx)})")
        else:
            out.extend(existing)
            action_parts.append("listening-only, no docx reading to add")
    else:
        # No classification — leave as is
        out.extend(existing)
        action_parts.append(f"ambiguous (R={n_r} L={n_l} ?={tags.count('?')}) — untouched")

    return out, "; ".join(action_parts)


def render_cards(cards: list[tuple[str, str, str]]) -> str:
    """Render card list back into the lesson block's `cards: [...]` body, matching original style."""
    lines = []
    for cid, front, back in cards:
        lines.append("          " + card_literal(cid, front, back) + ",")
    return "\n" + "\n".join(lines) + "\n        "


def main():
    docx_data = parse_docx()
    content, lessons = parse_books()

    # Modify content from the end backwards so earlier offsets remain valid
    ordered = sorted(
        lessons.keys(),
        key=lambda x: (int(re.search(r"U(\d+)", x).group(1)), int(re.search(r"L(\d+)", x).group(1))),
    )

    reports = []
    for lid in ordered:
        info = lessons[lid]
        before = len(info["cards"])
        new_cards, action = build_new_card_list(lid, info["cards"], docx_data)
        if new_cards is None:
            reports.append((lid, before, before, action))
            continue
        after = len(new_cards)
        reports.append((lid, before, after, action))
        lessons[lid]["new_cards"] = new_cards

    # Rewrite content: iterate matches in reverse order so offsets stay valid
    for m in reversed(list(LESSON_BLOCK_RE.finditer(content))):
        lid = m.group(2).upper()
        if "new_cards" not in lessons[lid]:
            continue
        new_body = render_cards(lessons[lid]["new_cards"])
        content = content[: m.start(4)] + new_body + content[m.end(4) :]

    BOOKS.write_text(content, encoding="utf-8")

    # Summary report
    print(f"{'lesson':<8} {'before':>7} {'after':>7}  action")
    print("-" * 78)
    for lid, b, a, act in reports:
        delta = f"+{a - b}" if a > b else (str(a - b) if a < b else "±0")
        print(f"{lid:<8} {b:>7} {a:>7} {delta:>4}  {act}")
    total_before = sum(r[1] for r in reports)
    total_after = sum(r[2] for r in reports)
    print("-" * 78)
    print(f"{'TOTAL':<8} {total_before:>7} {total_after:>7}  ({total_after - total_before:+})")


if __name__ == "__main__":
    main()
