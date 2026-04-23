"""Dump cards with empty zh or en into .planning/missing-trans.json.

Output format per lesson:
  { lesson, title,
    need_zh: [{id, fr, en}, ...],  # needs Chinese, French+English given as hints
    need_en: [{id, fr, zh}, ...],  # needs English, French+Chinese given as hints
  }

`fr` is always the source. `en`/`zh` are given as hints if present so
translators (or the model filling these) can check consistency across
languages.
"""
from __future__ import annotations
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = Path(r"C:/Users/racwang/hoopy/french-flashcard/.planning/missing-trans.json")


def main():
    d = json.loads(urllib.request.urlopen("http://localhost:3001/api/editor").read())
    result = []
    for book in d:
        for l in book["lessons"]:
            need_zh = []
            need_en = []
            for c in l["cards"]:
                if c["id"].startswith("s_"):
                    continue
                if not c["zh"].strip():
                    need_zh.append({"id": c["id"], "fr": c["front"], "en": c["en"]})
                if not c["en"].strip():
                    need_en.append({"id": c["id"], "fr": c["front"], "zh": c["zh"]})
            if need_zh or need_en:
                result.append({
                    "lesson": l["id"],
                    "title": l["title"],
                    "need_zh_count": len(need_zh),
                    "need_en_count": len(need_en),
                    "need_zh": need_zh,
                    "need_en": need_en,
                })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    total_zh = sum(l["need_zh_count"] for l in result)
    total_en = sum(l["need_en_count"] for l in result)
    print(f"wrote {OUT}")
    print(f"lessons with gaps: {len(result)}")
    print(f"total missing zh: {total_zh}")
    print(f"total missing en: {total_en}")
    print(f"grand total: {total_zh + total_en}\n")

    print(f"{'lesson':<8} {'need_zh':>7} {'need_en':>7}  title")
    for l in result:
        print(f"{l['lesson']:<8} {l['need_zh_count']:>7} {l['need_en_count']:>7}  {l['title']}")


if __name__ == "__main__":
    main()
