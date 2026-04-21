"""For the 5 lessons missed by the audit, check docx reading coverage vs books.ts."""
import io
import re
import sys
import urllib.request
import json
from pathlib import Path
import docx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DOCX = Path(r"C:/Users/racwang/Downloads/B1讲义完整版.pdf+改25.5.31775191233.docx")
BOUNDS = {
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
    r"Repérez|Notez|Identifiez|Formulez|Transformez|Citez|Analysez|Nommez|Recherchez|"
    r"structure|一、|二、|三、|四、|五、|六、|预习|自主|Transcription|听力|"
    r"Vrai|Faux|document|Document|"
    r"[a-hA-H][\s.)）、]|[0-9]+[.．、]|\(\d+\)|【|®"
    r")",
    re.I,
)


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


def norm(s: str) -> str:
    return re.sub(r"[^\w]+", "", s.lower())


def extract(paragraphs, start: int, end: int) -> list[tuple[int, str]]:
    kept = []
    mode = "scan"
    for j in range(start, end):
        t = paragraphs[j].text.strip()
        if not t:
            continue
        if re.match(r"^(U\d+L\d+)\s", t) or re.match(r"^(Texte|texte)\s*[AB]?", t):
            mode = "scan"
            continue
        if re.match(r"^(知识点|Corrigé|Exercice|Vocabulaire|Devoir|讲解)", t):
            mode = "skip"
            continue
        if SKIP_RE.match(t):
            continue
        if mode == "skip":
            if len(t) > 60 and is_french_prose(t):
                mode = "scan"
                kept.append((j, t))
            continue
        if is_french_prose(t):
            kept.append((j, t))
    return kept


d = docx.Document(str(DOCX))
data = json.loads(urllib.request.urlopen("http://localhost:3001/api/editor").read())

# Build books.ts content index per lesson (normalized fronts)
bk_fronts = {}
for l in data[0]["lessons"]:
    lid = l["id"]
    bk_fronts[lid] = set()
    for c in l["cards"]:
        if c["id"].startswith("s_"):
            continue
        bk_fronts[lid].add(norm(c["front"])[:30])

for lid, (s, e) in BOUNDS.items():
    title = next(l["title"] for l in data[0]["lessons"] if l["id"] == lid)
    bk_count = len([c for c in next(l for l in data[0]["lessons"] if l["id"] == lid)["cards"] if not c["id"].startswith("s_")])
    candidates = extract(d.paragraphs, s, e)
    already = missing = 0
    missing_list = []
    for idx, text in candidates:
        # Does this paragraph's first 30 normalized chars appear in books.ts?
        key = norm(text)[:30]
        if len(key) < 10:
            continue
        found = any(key in bf or bf.startswith(key) for bf in bk_fronts[lid])
        if found:
            already += 1
        else:
            missing += 1
            missing_list.append((idx, text))
    print(f"=== {lid.upper()} {title} ===")
    print(f"  books.ts content cards: {bk_count}")
    print(f"  docx reading candidates: {len(candidates)}")
    print(f"  already in books.ts (match): {already}")
    print(f"  NOT in books.ts: {missing}")
    if missing_list:
        print(f"  sample missing paragraphs (first 5):")
        for idx, txt in missing_list[:5]:
            print(f"    [{idx}] {txt[:100]}")
    print()
