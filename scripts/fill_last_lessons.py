"""Fill in the 5 civilisation lessons (U1L4, U3L12, U4L16, U5L20, U11L44) whose
docx headings slipped past the original LESSON_RE because:
  - their titles contain hyphens (télé-réalité, vraies-fausses), or
  - their subtype is bare 'texte' or 'texte（上/中/下）' with full-width parens.

For each target lesson, extract the docx reading body, split into sentences,
dedupe against the current books.ts cards (by normalized front), and append
the missing sentences as new r* cards. A s_read marker is inserted at the
top if not already present. No listening is added — these lessons have no
transcription (every 4th-of-unit lesson is culture-only).
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

TARGETS = {
    "u1l4":   (1040, 1288),
    "u3l12":  (3271, 3503),
    "u4l16":  (4669, 4962),
    "u5l20":  (6396, 6718),
    "u11l44": (12798, 12969),
}

SKIP_RE = re.compile(
    r"^("
    r"知识点|Corrigé|Exercice|Vocabulaire|Prononcez|Devoir|grammaire|讲解|课文讲解|"
    r"Observez|Lisez|Dites|Complétez|Répondez|Imaginez|Faites|Présentez|Écoutez|Ecoutez|"
    r"Mettez|Associez|Trouvez|Choisissez|Relevez|Expliquez|Racontez|Classez|Cochez|Indiquez|"
    r"Discutez|Interviewez|Décrivez|Résumez|Comparez|Préparez|Commentez|Cherchez|"
    r"Repérez|Notez|Identifiez|Formulez|Reformulez|Transformez|Citez|Analysez|Nommez|Recherchez|"
    r"Rédigez|Composez|Retrouvez|Soulignez|Donnez|Employez|Utilisez|Créez|Jouez|Écrivez|"
    r"structure|一、|二、|三、|四、|五、|六、|预习|自主|Transcription|听力|"
    r"Vrai|Faux|document\b|Document\b|"
    r"[a-hA-H][\s.)）、]|[0-9]+[.．、]|\(\d+\)|【|®"
    r")",
    re.I,
)
RESUME_RE = re.compile(r"^(课文讲解|讲解)")


def is_french_prose(t: str) -> bool:
    if len(t) < 15:
        return False
    latin = sum(1 for c in t if c.isalpha() and ord(c) < 0x2E80)
    cjk = sum(1 for c in t if 0x4E00 <= ord(c) <= 0x9FFF)
    if cjk > 0 and len(t) < 40:
        return False
    if cjk > latin // 4:
        return False
    return latin > 15


def extract_reading(paragraphs, start: int, end: int) -> list[str]:
    kept, mode = [], "scan"
    for j in range(start, end):
        t = paragraphs[j].text.strip()
        if not t:
            continue
        if RESUME_RE.match(t) or re.match(r"^U\d+L\d+\s", t) or t.startswith(("Texte", "texte")):
            mode = "scan"
            continue
        if re.match(r"^(知识点|Corrigé|Exercice|Vocabulaire|Devoir)", t):
            mode = "skip"
            continue
        if SKIP_RE.match(t):
            continue
        if mode == "skip":
            if len(t) > 60 and is_french_prose(t):
                mode = "scan"
                kept.append(t)
            continue
        if is_french_prose(t):
            kept.append(t)
    return kept


def split_sentences(paragraphs: list[str]) -> list[str]:
    text = " ".join(p.strip() for p in paragraphs if p.strip())
    text = re.sub(r"\s+", " ", text)
    for abbr in ["M.", "Mme.", "Mlle.", "Dr.", "St.", "Ste.", "pp.", "p.", "etc.", "ex.", "cf.", "i.e.", "e.g.", "vs."]:
        text = text.replace(abbr, abbr.replace(".", "\x00"))
    sents = re.split(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÿ«\"'“‘\(])", text)
    sents = [s.replace("\x00", ".").strip() for s in sents if s.strip()]
    return [s for s in sents if len(s) >= 8]


def norm(s: str) -> str:
    return re.sub(r"[^\w]+", "", s.lower())


CARD_RE = re.compile(
    r"\{\s*id:\s*`([^`]+)`\s*,\s*front:\s*`([^`]*)`\s*,\s*back:\s*`([^`]*)`\s*\}",
)
# Match a lesson block including its cards list; capture the inner cards text
LESSON_BLOCK_RE = re.compile(
    r"(\{\s*id:\s*`(u\d+l\d+)`\s*,\s*title:\s*`[^`]+`\s*,\s*cards:\s*\[)(.*?)(\s*\]\s*,?\s*\})",
    re.S,
)


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def card_literal(cid: str, front: str, back: str) -> str:
    return f"{{ id: `{esc(cid)}`, front: `{esc(front)}`, back: `{esc(back)}` }}"


def main():
    d = docx.Document(str(DOCX))
    content = BOOKS.read_text(encoding="utf-8")

    # Extract per-target new sentences from docx
    per_lesson_new = {}
    for lid, (s, e) in TARGETS.items():
        paragraphs = extract_reading(d.paragraphs, s, e)
        sentences = split_sentences(paragraphs)
        per_lesson_new[lid] = sentences

    # Rebuild per-lesson blocks in books.ts
    def rebuild(m):
        head, lid, body, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        if lid not in TARGETS:
            return m.group(0)
        # Parse existing cards
        existing = [(cm.group(1), cm.group(2), cm.group(3)) for cm in CARD_RE.finditer(body)]
        existing_non_marker = [c for c in existing if not c[0].startswith("s_")]
        existing_keys = {norm(f)[:30] for _, f, _ in existing_non_marker}

        # Build new cards list
        new_cards = []
        rnum = 1
        for sent in per_lesson_new[lid]:
            key = norm(sent)[:30]
            if len(key) < 10:
                continue
            if key in existing_keys:
                continue
            # Avoid dups within new batch
            if any(norm(f)[:30] == key for _, f, _ in new_cards):
                continue
            new_cards.append((f"r{rnum}", sent, ""))
            rnum += 1
            existing_keys.add(key)

        if not new_cards:
            return m.group(0)

        # Final assembly: s_read marker + all existing non-marker cards + new r* cards
        out = [("s_read", "【Lecture · 阅读】", "")]
        out.extend(existing_non_marker)
        out.extend(new_cards)

        # Render
        lines = []
        for cid, front, back in out:
            lines.append("          " + card_literal(cid, front, back) + ",")
        new_body = "\n" + "\n".join(lines) + "\n        "
        return head + new_body + tail

    new_content = LESSON_BLOCK_RE.sub(rebuild, content)
    BOOKS.write_text(new_content, encoding="utf-8")

    # Report
    print(f"{'lesson':<8} {'before':>6} {'new':>5} {'after':>6}")
    print("-" * 32)
    for lid, (s, e) in TARGETS.items():
        # Count new cards added by re-reading
        match = LESSON_BLOCK_RE.search(new_content)
        # Simpler: count r* cards in the new content for each lesson
        pass
    # Re-scan for accuracy
    for lid, (s, e) in TARGETS.items():
        m = re.search(
            rf"\{{\s*id:\s*`{lid}`[^}}]*?cards:\s*\[(.*?)\]\s*,?\s*\}}", new_content, re.S
        )
        if not m:
            continue
        body = m.group(1)
        total = len(CARD_RE.findall(body))
        new_r = sum(1 for cm in CARD_RE.finditer(body) if re.match(r"^r\d+$", cm.group(1)))
        before = total - new_r  # markers + existing
        print(f"{lid:<8} {before:>6} {new_r:>5} {total:>6}")


if __name__ == "__main__":
    main()
