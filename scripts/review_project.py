"""Full-project health review — scans books.ts + src/ for common issues.

Checks data integrity (empty fronts/backs, dup ids, orphan markers, lang
mix) and reports flags. Does not modify anything. Prints counts only,
never full card content, to keep the review concise.
"""
from __future__ import annotations
import io
import re
import sys
import urllib.request
import json
from collections import defaultdict, Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

d = json.loads(urllib.request.urlopen("http://localhost:3001/api/editor").read())

issues: list[tuple[str, str]] = []  # (severity, message)

def flag(sev: str, msg: str):
    issues.append((sev, msg))

def is_cjk(ch: str) -> bool:
    return 0x4E00 <= ord(ch) <= 0x9FFF

# --- Per-lesson structural checks ---
for book in d:
    for l in book["lessons"]:
        lid = l["id"]
        cards = l["cards"]
        content = [c for c in cards if not c["id"].startswith("s_")]
        markers = [c for c in cards if c["id"].startswith("s_")]

        # Duplicate IDs within lesson
        id_counts = Counter(c["id"] for c in cards)
        dupes = [i for i, n in id_counts.items() if n > 1]
        if dupes:
            flag("HIGH", f"{lid}: duplicate IDs: {dupes}")

        # Marker sanity
        read_cards = [c for c in content if c.get("section") is None]  # not useful — section isn't in API
        # section info is only in the client. Use marker position as proxy.
        # Expected: at most 1 s_read and 1 s_listen
        marker_counts = Counter(c["id"] for c in markers)
        if marker_counts.get("s_read", 0) > 1:
            flag("MED", f"{lid}: multiple s_read markers")
        if marker_counts.get("s_listen", 0) > 1:
            flag("MED", f"{lid}: multiple s_listen markers")

        # Empty fronts
        empty_fronts = [c["id"] for c in content if not c["front"].strip()]
        if empty_fronts:
            flag("HIGH", f"{lid}: empty front on {len(empty_fronts)} card(s): {empty_fronts[:5]}")

        # Empty backs on content cards
        empty_backs = [c["id"] for c in content if not c["back"].strip()]
        if empty_backs:
            flag("HIGH", f"{lid}: empty back on {len(empty_backs)} card(s): {empty_backs[:5]}")

        # Very short cards (likely fragments)
        tiny = [c["id"] for c in content if len(c["front"].strip()) < 8]
        if tiny:
            flag("LOW", f"{lid}: {len(tiny)} very short (<8 char) card(s): {tiny[:3]}")

        # Very long cards (overflow risk)
        huge = [c["id"] for c in content if len(c["front"]) > 350]
        if huge:
            flag("LOW", f"{lid}: {len(huge)} very long (>350 char) card(s): {huge[:3]}")

        # Lang mix in card.front (French): should be Latin-dominant; CJK in front = garbage
        for c in content:
            cjk = sum(1 for ch in c["front"] if is_cjk(ch))
            if cjk > 2:
                flag("MED", f"{lid}/{c['id']}: {cjk} CJK chars in French front")

        # Lang in card.back: should be translation (CN or EN), not another French sentence
        for c in content:
            back = c["back"].strip()
            if not back:
                continue
            cjk = sum(1 for ch in back if is_cjk(ch))
            latin = sum(1 for ch in back if ch.isalpha() and ord(ch) < 0x2E80)
            # If back is mostly latin AND not short, it's English translation — OK
            # If back is mostly CJK — Chinese translation OK
            # If back has French-specific diacritics with zero CJK and no typical English words, MIGHT be stray French
            # skip this check for now, too noisy

        # Translation language consistency per lesson (CN vs EN)
        cn_backs = sum(1 for c in content if any(is_cjk(ch) for ch in c["back"]))
        en_backs = sum(1 for c in content if c["back"].strip() and not any(is_cjk(ch) for ch in c["back"]))
        if cn_backs > 0 and en_backs > 0:
            flag("INFO", f"{lid}: mixed translation languages — {cn_backs} ZH + {en_backs} EN cards")

        # Marker vs content mismatch: if lesson has s_read but no r-prefix cards → weird
        # (new r* and l* are only added when the extractor ran; the original cards are c*)
        has_r_marker = any(c["id"] == "s_read" for c in markers)
        has_l_marker = any(c["id"] == "s_listen" for c in markers)
        # An r_marker without any real content following it would be weird
        # Walk positions
        section = None
        per_section_count = {"reading": 0, "listening": 0, None: 0}
        for c in cards:
            if c["id"] == "s_read":
                section = "reading"
                continue
            if c["id"] == "s_listen":
                section = "listening"
                continue
            if c["id"].startswith("s_"):
                continue
            per_section_count[section] += 1
        if has_r_marker and per_section_count["reading"] == 0:
            flag("MED", f"{lid}: s_read marker but 0 reading cards after it")
        if has_l_marker and per_section_count["listening"] == 0:
            flag("MED", f"{lid}: s_listen marker but 0 listening cards after it")
        if not has_r_marker and not has_l_marker and len(content) > 0:
            flag("INFO", f"{lid}: no section markers (reading/listening undivided) — {len(content)} cards")

print("=" * 60)
print("PROJECT HEALTH REVIEW")
print("=" * 60)

by_sev = defaultdict(list)
for sev, msg in issues:
    by_sev[sev].append(msg)

for sev in ["HIGH", "MED", "LOW", "INFO"]:
    if by_sev[sev]:
        print(f"\n[{sev}] {len(by_sev[sev])} issue(s):")
        for msg in by_sev[sev][:40]:
            print(f"  - {msg}")
        if len(by_sev[sev]) > 40:
            print(f"  ... +{len(by_sev[sev]) - 40} more")

# Totals
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
total_cards = sum(len(l["cards"]) for b in d for l in b["lessons"])
total_content = sum(
    1 for b in d for l in b["lessons"] for c in l["cards"]
    if not c["id"].startswith("s_")
)
total_markers = total_cards - total_content
print(f"Lessons: {sum(len(b['lessons']) for b in d)}")
print(f"Total cards: {total_cards} ({total_content} content + {total_markers} markers)")
print(f"Issues — HIGH: {len(by_sev['HIGH'])}, MED: {len(by_sev['MED'])}, LOW: {len(by_sev['LOW'])}, INFO: {len(by_sev['INFO'])}")
