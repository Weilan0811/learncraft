"""Unit 3.6: four-arm retrieval bench on the v8 snapshot (AB corpus-cleaning).

Round A ("before"): full corpus, structural junk (References/TOC/LaTeX debris)
    present in the indexes -- the pre-cleaning state.
Round B ("after"):  junk excluded from the indexes (KB_FILTER_JUNK=1 build_kb).

qrels are FIXED across rounds (cleaned-corpus GT, dropped_by_corpus_filter
flagged in qrels.json), so any metric delta is attributable to the corpus
change alone. BM25 is built in-memory from the round's chunk list (pickle
cache bypassed to avoid stale-round contamination); the vector arm hits the
Qdrant collection built by build_kb.py for that round, cross-checked against
storage meta junk_filter.

Usage (repo root, after building the round's indexes):
    PYTHONPATH=. python knowledge/scripts/bench_v8.py before
    PYTHONPATH=. python knowledge/scripts/bench_v8.py after

Arms: keyword / vector / hybrid / router (kb.search). Metrics per arm:
docR@5/@10 + docMRR (gt_doc_ids from snapshot), chunkR@5/@10 + chunkMRR on
BOTH qrels metrics (strict_chunk_ids / relevant_set). Slice breakdown
(planning/generation/trap) + trap keyword-x-vector quadrant + BM25 top-doc
concentration (leaderboard proxy).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

from knowledge.engine import kb_engine as kb  # noqa: E402

SNAP_DIR = REPO_ROOT / "knowledge" / "eval" / "local" / "v8_snapshot"
OUT_DIR = SNAP_DIR  # gitignored, keeps experimental artifacts out of the repo
K_VALUES = [5, 10]
ARMS = ["keyword", "vector", "hybrid", "router"]


def wilson_ci(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = hits / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


class CachedEmbedder:
    """Query-embedding cache shared across arms (same as bench_retrieval)."""

    def __init__(self, inner: kb.Embedder) -> None:
        self._inner = inner
        self._cache: dict[str, list[float]] = {}

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = [[] for _ in texts]
        missing: dict[str, int] = {}
        for i, t in enumerate(texts):
            if t in self._cache:
                out[i] = self._cache[t]
            elif t not in missing:
                missing[t] = len(missing)
        if missing:
            vecs = self._inner.embed(list(missing))
            for t, j in missing.items():
                self._cache[t] = vecs[j]
        for i, t in enumerate(texts):
            if not out[i]:
                out[i] = self._cache[t]
        return out


def load_round_inputs(round_name: str) -> tuple[list[dict], dict, list[kb.Chunk], dict]:
    snap = json.loads((SNAP_DIR / "v8_queries.json").read_text(encoding="utf-8"))
    qrels = json.loads((SNAP_DIR / "qrels.json").read_text(encoding="utf-8"))["items"]

    chunks_all = kb.load_all_chunks()
    want_filter = round_name == "after"
    if want_filter:
        chunks = [c for c in chunks_all if not kb.is_structural_junk(c)]
    else:
        chunks = list(chunks_all)

    meta = json.loads((kb.KB_INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    if bool(meta.get("junk_filter")) != want_filter:
        sys.exit(
            f"round/ corpus mismatch: meta.junk_filter={meta.get('junk_filter')} "
            f"but round '{round_name}' expects {want_filter}. Run build_kb.py "
            f"({'KB_FILTER_JUNK=0' if not want_filter else 'KB_FILTER_JUNK=1'} --rebuild) first."
        )
    return snap["items"], qrels, chunks, meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("round", choices=["before", "after"])
    args = ap.parse_args()
    rnd = args.round

    items, qrels, chunks, meta = load_round_inputs(rnd)
    print(f"round={rnd} | corpus: {len({c.doc_id for c in chunks})} docs / {len(chunks)} chunks "
          f"(junk_filter={meta.get('junk_filter')})")

    bm25 = kb.BM25Index(chunks)  # in-memory, pickle bypassed
    embedder = CachedEmbedder(kb.get_embedder())
    ctx = {"chunks": chunks, "bm25": bm25, "embedder": embedder}

    records: dict[str, list[dict]] = {m: [] for m in ARMS}
    for qi, it in enumerate(items):
        qr = qrels[it["id"]]
        for arm in ARMS:
            t0 = time.perf_counter()
            results = kb.search(arm, it["question"], ctx["chunks"], ctx["bm25"], ctx["embedder"], top_k=K_VALUES[-1])
            elapsed = (time.perf_counter() - t0) * 1000
            records[arm].append({
                "id": it["id"],
                "slice": it["slice"],
                "wording_level": it["wording_level"],
                "subset": it["subset"],
                "gt_docs": it["gt_doc_ids"],
                "strict": qr["strict_chunk_ids"],
                "lenient": qr["relevant_set"],
                "ranked_chunks": [c.chunk_id for c, _ in results],
                "ranked_docs": [c.doc_id for c, _ in results],
                "latency_ms": round(elapsed, 1),
            })
        if (qi + 1) % 20 == 0:
            print(f"  [{qi + 1}/{len(items)}]")

    # ---- metrics ----
    def mrr(ranked: list[str], gt: set[str]) -> float:
        for pos, x in enumerate(ranked, start=1):
            if x in gt:
                return 1.0 / pos
        return 0.0

    def hit(ranked: list[str], gt: set[str], k: int) -> bool:
        return any(x in gt for x in ranked[:k])

    summary: dict[str, dict] = {}
    for arm in ARMS:
        rows = records[arm]
        n = len(rows)
        s: dict = {"n": n}
        for metric, key in (("doc", "gt_docs"), ("strict", "strict"), ("lenient", "lenient")):
            gts = [set(r[key]) for r in rows]
            if metric == "strict":
                valid = [i for i, g in enumerate(gts) if g]
                rows_v = [rows[i] for i in valid]
                gts = [gts[i] for i in valid]
            else:
                rows_v, gts = rows, gts
            nv = max(len(rows_v), 1)
            for k in K_VALUES:
                if metric == "doc":
                    n_hits = sum(1 for r, g in zip(rows_v, gts) if hit(r["ranked_docs"], g, k))
                    s[f"{metric}_r@{k}"] = n_hits / nv
                    s[f"{metric}_r@{k}_ci"] = tuple(round(v, 3) for v in wilson_ci(n_hits, nv))
                else:
                    n_hits = sum(1 for r, g in zip(rows_v, gts) if hit(r["ranked_chunks"], g, k))
                    s[f"{metric}_chunk_r@{k}"] = n_hits / nv
                    s[f"{metric}_chunk_r@{k}_ci"] = tuple(round(v, 3) for v in wilson_ci(n_hits, nv))
            if metric == "doc":
                s["doc_mrr"] = sum(mrr(r["ranked_docs"], g) for r, g in zip(rows_v, gts)) / nv
            else:
                s[f"{metric}_chunk_mrr"] = sum(mrr(r["ranked_chunks"], g) for r, g in zip(rows_v, gts)) / nv
        s["latency_p50_ms"] = sorted(r["latency_ms"] for r in rows)[n // 2]
        # slice breakdown (lenient chunk R@10 + doc R@10)
        s["slices"] = {}
        for sl in ("planning", "generation", "trap"):
            srows = [r for r in rows if r["slice"] == sl]
            if not srows:
                continue
            e = {"n": len(srows),
                 "doc_r@10": sum(1 for r in srows if hit(r["ranked_docs"], set(r["gt_docs"]), 10)) / len(srows)}
            sl_valid = [r for r in srows if r["lenient"]]
            if sl_valid:
                e["lenient_chunk_r@10"] = sum(1 for r in sl_valid if hit(r["ranked_chunks"], set(r["lenient"]), 10)) / len(sl_valid)
            s["slices"][sl] = e
        # BM25 leaderboard proxy: top doc share of non-GT hits in keyword top-10
        kw = records["keyword"]
        doc_counts = Counter(d for r in kw for d in r["ranked_docs"][:10])
        s["bm25_top_doc_share"] = max(doc_counts.values()) / sum(doc_counts.values())
        summary[arm] = s

    # ---- trap quadrant (chunk-level, lenient, @10) ----
    quadrant = Counter()
    for a, b in zip(records["keyword"], records["vector"]):
        assert a["id"] == b["id"] and a["slice"] == b["slice"]
        if a["slice"] != "trap" or not a["lenient"]:
            continue
        ah = hit(a["ranked_chunks"], set(a["lenient"]), 10)
        bh = hit(b["ranked_chunks"], set(b["lenient"]), 10)
        quadrant["both" if ah and bh else "keyword_only" if ah else "vector_only" if bh else "neither"] += 1

    (OUT_DIR / f"raw-v8-{rnd}.json").write_text(
        json.dumps({"round": rnd, "meta_corpus": {"docs": len({c.doc_id for c in chunks}), "chunks": len(chunks)},
                    "summary": summary, "trap_quadrant": dict(quadrant), "records": records},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    print(f"\n=== round {rnd} ===")
    for arm in ARMS:
        s = summary[arm]
        dlo, dhi = s["doc_r@10_ci"]
        llo, lhi = s["lenient_chunk_r@10_ci"]
        slo, shi = s["strict_chunk_r@10_ci"]
        print(f"{arm:8s} docR@10={s['doc_r@10']:.1%} [{dlo:.0%}-{dhi:.0%}] "
              f"lenient_cR@10={s['lenient_chunk_r@10']:.1%} [{llo:.0%}-{lhi:.0%}] "
              f"strict_cR@10={s['strict_chunk_r@10']:.1%} [{slo:.0%}-{shi:.0%}] "
              f"strict_MRR={s['strict_chunk_mrr']:.3f} p50={s['latency_p50_ms']:.0f}ms")
    print(f"trap quadrant (n={sum(quadrant.values())}): {dict(quadrant)}")
    print(f"-> {OUT_DIR / f'raw-v8-{rnd}.json'}")


if __name__ == "__main__":
    main()
    import knowledge.engine.kb_engine as _kb
    _kb.close_qdrant()  # flush local-mode persistence before exit
