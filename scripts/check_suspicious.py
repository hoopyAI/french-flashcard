"""Scan new (r*/l*) cards in books.ts for extraction garbage patterns."""
import io
import json
import re
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

d = json.loads(urllib.request.urlopen("http://localhost:3001/api/editor").read())
lessons = d[0]["lessons"]

suspicious_patterns = [
    (r"^[a-h][\s.)）、]", "exercise-letter"),
    (r"\bn\.m\.|\bn\.f\.|\badj\.|\bv\.t\.|\bv\.i\.", "vocab-entry"),
    (r"[\u4e00-\u9fff]{4,}", "heavy-cjk"),
    (r"^\d+[.．、]\s", "numbered-start"),
    (r"Corrigé|^Observez|^Lisez|^Exercice", "exercise-marker"),
    (r"^\W*$", "no-alpha"),
]

total_new = 0
total_issues = 0
for l in lessons:
    issues = []
    new_count = 0
    for c in l["cards"]:
        if not (re.match(r"^[rl]\d", c["id"])):
            continue
        new_count += 1
        total_new += 1
        for pat, name in suspicious_patterns:
            if re.search(pat, c["front"]):
                issues.append((c["id"], name, c["front"]))
                total_issues += 1
                break
    if issues:
        print(f"{l['id']}: {len(issues)}/{new_count} suspicious")
        for cid, name, frag in issues[:4]:
            print(f"  {cid} [{name}] {frag[:90]!r}")

print()
print(f"total new cards: {total_new}")
print(f"total suspicious: {total_issues} ({100*total_issues/total_new:.1f}%)" if total_new else "(none)")
