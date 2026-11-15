"""Absence baseline recorder (unit 2.5.1c).

For every expansion doc, pose 2-3 queries about its core content while the
index still only contains the original 21 pages. Records which existing pages
(or nothing) the queries hit — this is the "document absent" baseline that
unit 3's ingest experiment will later compare against (same queries re-run
after the docs are ingested).

Output: knowledge/eval/local/absence_baseline.json (gitignored — query texts
are ours, but keeping the whole eval dir local is the simpler rule).

Usage (repo root): PYTHONPATH=. python knowledge/scripts/gen_absence_baseline.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from knowledge.engine import kb_engine as kb  # noqa: E402

OUT = REPO_ROOT / "knowledge" / "eval" / "local" / "absence_baseline.json"

# target doc -> queries about ITS core content (asked while it is NOT indexed).
# DATA lives in the local manifest (gitignored) -- the repo ships the pipeline,
# not our eval instance (unit 6 compliance). Regenerate yours for your corpus.
MANIFEST = REPO_ROOT / "knowledge" / "eval" / "local" / "absence_queries.json"
if not MANIFEST.exists():
    sys.exit(f"missing {MANIFEST}: build your own per-doc queries for your corpus "
             f"(schema: {{\"<doc_id>\": [\"query\", ...]}}) and place it there")
QUERIES: dict[str, list[str]] = json.loads(MANIFEST.read_text(encoding="utf-8"))


def main() -> None:
    chunks = kb.load_all_chunks()
    bm25 = kb.load_bm25_index(chunks)
    embedder = kb.get_embedder()

    records = []
    for target, queries in QUERIES.items():
        for q in queries:
            results = kb.search("router", q, chunks, bm25, embedder, top_k=5)
            hit_docs = list(dict.fromkeys(c.doc_id for c, _ in results))
            records.append({
                "target_doc": target,
                "query": q,
                "top5_docs": hit_docs,
                "target_present": target in hit_docs,  # must be False while absent
                "top1": hit_docs[0] if hit_docs else None,
            })
            print(f"  {target[:44]:46s} -> {hit_docs[:2]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"recorded_at": datetime.now().isoformat(timespec="seconds"),
                    "index_state": "pre-expansion pages only (expansion docs fetched but NOT indexed)",
                    "records": records}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"\n{len(records)} baseline queries recorded -> {OUT}")


if __name__ == "__main__":
    main()
