"""Sanitize evaluation reports for open-source (unit 6, D1 decision).

Two scrub passes over every knowledge/eval/results/report-*.md:
1. Query-text removal: per-query failure-case lines carry the eval query TEXT,
   which is corpus-derived data (unit 6: eval data ships separately). Keep the
   query ID + what was returned, drop the text:
       - `syn007` [synthetic/multi_context] <text...> -> 返回: [...]   becomes
       - `syn007` -> 返回: [...]
2. Doc-slug aliasing: corpus doc slugs (the corpus list itself) are replaced
   with neutral DOCxx aliases from knowledge/eval/local/doc_alias_map.json
   (gitignored -- the mapping stays local).

Idempotent. Run from repo root:
    python knowledge/scripts/sanitize_reports.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "knowledge" / "eval" / "results"
MAP_PATH = REPO_ROOT / "knowledge" / "eval" / "local" / "doc_alias_map.json"

QUERY_LINE = re.compile(r"^(- `[^`]+`)\s+.*?(→ 返回(?:页)?: .*)$", re.M)

def main() -> None:
    if not MAP_PATH.exists():
        sys.exit(f"missing {MAP_PATH}: run compliance_setup.py first (local-only)")
    alias: dict[str, str] = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    slugs = sorted(alias, key=len, reverse=True)  # longest-first avoids prefix collisions

    reports = sorted(RESULTS.glob("report-*.md"))
    if not reports:
        sys.exit("no report-*.md found")
    for path in reports:
        text = path.read_text(encoding="utf-8")
        n_query, n_slug = 0, 0

        def _scrub_query(m: re.Match) -> str:
            nonlocal n_query
            n_query += 1
            return f"{m.group(1)} {m.group(2)}"

        text = QUERY_LINE.sub(_scrub_query, text)
        for slug in slugs:
            n = text.count(slug)
            if n:
                n_slug += n
                text = text.replace(slug, alias[slug])
        path.write_text(text, encoding="utf-8")
        print(f"{path.name}: query-text scrubbed on {n_query} lines, {n_slug} slug->alias")

    # verification: no slug may survive anywhere in results/
    leftover = {}
    for path in RESULTS.glob("*.md"):
        t = path.read_text(encoding="utf-8")
        found = [s for s in slugs if s in t]
        if found:
            leftover[path.name] = found
    if leftover:
        sys.exit(f"VERIFICATION FAILED, slugs still present: {leftover}")
    print("verification: zero doc slugs remain in knowledge/eval/results/*.md")


if __name__ == "__main__":
    main()
