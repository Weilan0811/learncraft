"""Doc-quota rerank experiment (unit 3.3, doc-hegemony treatment).

Mechanism under treatment: top-3 results are often monopolized by chunks of a
a single multi-topic mega doc (~20% of the incumbent index), crowding out
smaller focused docs.

Treatment: greedy per-doc quota over the top-50 candidates -- at most `quota`
chunks per doc may enter the final top-10. Zero cost (index-layer reorder).

Runs on win800_120 (the 3.3 chunking verdict incumbent). Same span-derived GT
as the chunking experiment, so numbers are directly comparable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "knowledge" / "scripts"))

from chunking_experiment import embed_matrix, load_docs, span_metrics  # noqa: E402

from knowledge.engine import kb_engine as kb  # noqa: E402

LOCAL = REPO_ROOT / "knowledge" / "eval" / "local"
OUT = LOCAL / "chunking_exp"


def rerank_quota(order: list[int], doc_ids: list[str], quota: int, k: int = 10) -> list[int]:
    """Greedy scan of a ranked candidate list; at most `quota` chunks per doc."""
    seen: dict[str, int] = {}
    out: list[int] = []
    for i in order:
        d = doc_ids[i]
        if seen.get(d, 0) >= quota:
            continue
        seen[d] = seen.get(d, 0) + 1
        out.append(i)
        if len(out) >= k:
            break
    return out


def main() -> None:
    docs = load_docs()
    chunks = []
    for doc_id, title, topic, url, scope, body in docs:
        chunks.extend(kb._chunk_body(doc_id, title, topic, url, scope, body))
    doc_ids = [c.doc_id for c in chunks]
    print(f"win800_120 chunks: {len(chunks)}")

    spans_data = json.loads((LOCAL / "span_annotations.json").read_text(encoding="utf-8"))["items"]
    dev = {qid: it for qid, it in spans_data.items() if it.get("subset") == "dev"}
    sm = span_metrics(chunks, dev)
    gt = sm["gt_strict"]

    suite = json.loads((LOCAL / "synthetic_qa.json").read_text(encoding="utf-8"))["items"]
    qmeta = {it["id"]: it for it in suite if it.get("subset") == "dev"}
    queries = [{"id": q, "gt_doc_ids": m["gt_doc_ids"], "query": m["question"]} for q, m in qmeta.items()]

    embedder = kb.get_embedder()
    qvecs = embed_matrix(embedder, [q["query"] for q in queries])
    cvecs = embed_matrix(embedder, [f"{c.title} | {c.section} | {c.text}" for c in chunks])
    sims = qvecs @ cvecs.T
    top50 = np.argsort(-sims, axis=1)[:, :50]

    results = {}
    for quota in (99, 3, 2, 1):
        doc_hits, chunk_hits = [], []
        for row, q in zip(top50, queries):
            sel = rerank_quota(list(row), doc_ids, quota if quota < 99 else 10**9)
            top_docs = [doc_ids[i] for i in sel]
            doc_hits.append(int(bool(set(top_docs) & set(q["gt_doc_ids"]))))
            g = gt.get(q["id"], [])
            if g:
                chunk_hits.append(int(bool({chunks[i].chunk_id for i in sel} & set(g))))
        n = len(queries)
        nc = len(chunk_hits)
        label = "no-quota (baseline)" if quota == 99 else f"quota={quota}/doc"
        results[label] = {
            "docR": round(sum(doc_hits) / n, 4),
            "chunkR": round(sum(chunk_hits) / nc, 4),
        }
        print(f"{label:<22} docR={results[label]['docR']:.1%} | chunkR={results[label]['chunkR']:.1%}")

    # clean-only stratification for the best quota arms
    clean_ids = {qid for qid, it in dev.items() if it.get("clean")}
    print(f"\nclean subset n={len(clean_ids)}:")
    for quota in (99, 2, 1):
        doc_hits = []
        for row, q in zip(top50, queries):
            if q["id"] not in clean_ids:
                continue
            sel = rerank_quota(list(row), doc_ids, quota if quota < 99 else 10**9)
            doc_hits.append(int(bool({doc_ids[i] for i in sel} & set(q["gt_doc_ids"]))))
        label = "no-quota" if quota == 99 else f"quota={quota}"
        print(f"  {label:<10} docR={sum(doc_hits) / len(doc_hits):.1%}")

    (OUT / "doc_quota_result.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT / 'doc_quota_result.json'}")


if __name__ == "__main__":
    main()
