"""Unit 3.8 supplement: wiki arm on the v8 snapshot -- the wiki生死判据.

3.8 acceptance #5: "wiki 检索价值生死判据有明确答案（n≥30 trap 四象限）".
This runner executes the wiki evidence-expansion arm (wiki:pool_rerank, the
v7 winner) over all 130 v8 queries, reports slice breakdown and the
wiki-x-vector trap quadrant (n=30 trap queries), plus citation fidelity.

Wiki layer uses the current (post-cleaning) wiki collection -- wiki pages are
distilled from source docs, and compile_wiki sources were not affected by the
structural-junk question, but the layer was rebuilt by the 3.6 'after' build
anyway, keeping one corpus generation across the board.

Usage (repo root):
    PYTHONPATH=. python knowledge/scripts/bench_v8_wiki.py
"""

from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

from knowledge.engine import kb_engine as kb  # noqa: E402

SNAP_DIR = REPO_ROOT / "knowledge" / "eval" / "local" / "v8_snapshot"
OUT_DIR = SNAP_DIR
TOP_K = 10


def wilson_ci(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = hits / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def mrr(ranked: list[str], gt: set[str]) -> float:
    for pos, x in enumerate(ranked, start=1):
        if x in gt:
            return 1.0 / pos
    return 0.0


def main() -> None:
    snap = json.loads((SNAP_DIR / "v8_queries.json").read_text(encoding="utf-8"))
    qrels = json.loads((SNAP_DIR / "qrels.json").read_text(encoding="utf-8"))["items"]
    vector_raw = json.loads((SNAP_DIR / "raw-v8-after.json").read_text(encoding="utf-8"))
    vec_by_id = {r["id"]: r for r in vector_raw["records"]["vector"]}

    chunks = [c for c in kb.load_all_chunks() if not kb.is_structural_junk(c)]
    meta = json.loads((kb.KB_INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    if not meta.get("junk_filter"):
        sys.exit("wiki supplement expects the cleaned-corpus generation (meta.junk_filter=true)")

    wiki_chunks = kb.load_wiki_chunks()
    if not wiki_chunks:
        sys.exit("wiki layer empty -- run compile_wiki.py first")
    wiki_bm25 = kb.BM25Index(wiki_chunks)

    class CachedEmbedder(kb.Embedder):
        def __init__(self, inner):
            self._inner = inner
            self._cache = {}

        def embed(self, texts):
            out, missing = [], {}
            for i, t in enumerate(texts):
                if t in self._cache:
                    out.append(self._cache[t])
                else:
                    missing[t] = len(missing)
                    out.append(None)
            if missing:
                vecs = self._inner.embed(list(missing))
                for t, j in missing.items():
                    self._cache[t] = vecs[j]
            return [self._cache[t] if o is None else o for t, o in zip(texts, out)]

    embedder = CachedEmbedder(kb.get_embedder())

    records = []
    fidelity = Counter()
    for qi, it in enumerate(snap["items"]):
        qr = qrels[it["id"]]
        t0 = time.perf_counter()
        results, fid = kb.search_wiki(
            it["question"], wiki_chunks, wiki_bm25, embedder,
            raw_chunks=chunks, top_k=TOP_K, expand_strategy="pool_rerank",
        )
        elapsed = (time.perf_counter() - t0) * 1000
        for k, v in fid.items():
            fidelity[k] += v
        records.append({
            "id": it["id"],
            "slice": it["slice"],
            "gt_docs": it["gt_doc_ids"],
            "strict": qr["strict_chunk_ids"],
            "lenient": qr["relevant_set"],
            "ranked_chunks": [c.chunk_id for c, _ in results],
            "ranked_docs": [c.doc_id for c, _ in results],
            "latency_ms": round(elapsed, 1),
        })
        if (qi + 1) % 40 == 0:
            print(f"  [{qi + 1}/{len(snap['items'])}]")

    def hit(ranked, gt, k):
        return any(x in gt for x in ranked[:k])

    n = len(records)
    s = {"n": n}
    for metric, rkey, gkey in (("doc", "ranked_docs", "gt_docs"), ("lenient", "ranked_chunks", "lenient"), ("strict", "ranked_chunks", "strict")):
        pairs = [(r, set(r[gkey])) for r in records]
        if metric == "strict":
            pairs = [(r, g) for r, g in pairs if g]
        nv = max(len(pairs), 1)
        for k in (5, 10):
            h = sum(1 for r, g in pairs if hit(r[rkey], g, k))
            key = f"{metric}_r@{k}" if metric == "doc" else f"{metric}_chunk_r@{k}"
            s[key] = h / nv
            s[f"{key}_ci"] = tuple(round(v, 3) for v in wilson_ci(h, nv))
        mrr_key = "doc_mrr" if metric == "doc" else f"{metric}_chunk_mrr"
        s[mrr_key] = sum(mrr(r[rkey], g) for r, g in pairs) / nv
    s["latency_p50_ms"] = sorted(r["latency_ms"] for r in records)[n // 2]
    s["slices"] = {}
    for sl in ("planning", "generation", "trap"):
        srows = [r for r in records if r["slice"] == sl]
        if not srows:
            continue
        e = {"n": len(srows), "doc_r@10": sum(1 for r in srows if hit(r["ranked_docs"], set(r["gt_docs"]), 10)) / len(srows)}
        slv = [r for r in srows if r["lenient"]]
        if slv:
            e["lenient_chunk_r@10"] = sum(1 for r in slv if hit(r["ranked_chunks"], set(r["lenient"]), 10)) / len(slv)
        s["slices"][sl] = e

    # wiki x vector trap quadrant (chunk-level, lenient, @10)
    quadrant = Counter()
    for r in records:
        if r["slice"] != "trap" or not r["lenient"]:
            continue
        vh = hit(vec_by_id[r["id"]]["ranked_chunks"], set(r["lenient"]), 10)
        wh = hit(r["ranked_chunks"], set(r["lenient"]), 10)
        quadrant["both" if vh and wh else "wiki_only" if wh else "vector_only" if vh else "neither"] += 1

    (OUT_DIR / "raw-v8-wiki.json").write_text(
        json.dumps({"summary": s, "trap_quadrant": dict(quadrant), "fidelity": dict(fidelity), "records": records},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    print(f"\n=== wiki:pool_rerank on v8 (cleaned corpus) ===")
    dlo, dhi = s["doc_r@10_ci"]
    llo, lhi = s["lenient_chunk_r@10_ci"]
    print(f"docR@10={s['doc_r@10']:.1%} [{dlo:.0%}-{dhi:.0%}] "
          f"lenient_cR@10={s['lenient_chunk_r@10']:.1%} [{llo:.0%}-{lhi:.0%}] "
          f"docMRR={s['doc_mrr']:.3f} p50={s['latency_p50_ms']:.0f}ms")
    for sl, e in s["slices"].items():
        extra = f" lenient_cR@10={e['lenient_chunk_r@10']:.1%}" if "lenient_chunk_r@10" in e else ""
        print(f"  slice {sl:10s} n={e['n']} docR@10={e['doc_r@10']:.0%}{extra}")
    print(f"trap quadrant (n={sum(quadrant.values())}): {dict(quadrant)}")
    print(f"fidelity: {dict(fidelity)}")
    print(f"-> {OUT_DIR / 'raw-v8-wiki.json'}")


if __name__ == "__main__":
    main()
    import knowledge.engine.kb_engine as _kb
    _kb.close_qdrant()  # flush local-mode persistence before exit
