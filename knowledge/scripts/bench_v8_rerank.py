"""Unit 3.7: chunk-level rerank on the v8 snapshot (bge-reranker-v2-m3, local).

Question (plan 3.7): "召回了但排不上去的正确答案，rerank 能把它推进 top-k 吗？
代价是什么？" -- closes the loop on 3.3's finding that all misses were RANKING
problems (sibling crowding 47% / lone-candidate 38% / double-doc squeeze 15%),
against the 3.6 cleaned-corpus baseline (strict cR@10 = 42.2% best arm).

Design: four bases (keyword / vector / hybrid / router) each fetch top-30
candidates, then the cross-encoder rescues the ordering. Candidate text is
contextualized ({title} | {section} | {text}) -- same form the embedder sees.

Model path resolution (same convention as unit 3.1):
    BGE_RERANKER_PATH env -> <worktree>/.models/bge-reranker-v2-m3 -> repo root

Usage (repo root, after the model is downloaded):
    PYTHONPATH=. python knowledge/scripts/bench_v8_rerank.py
Output: raw-v8-rerank.json + stdout comparison table.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

from knowledge.engine import kb_engine as kb  # noqa: E402

SNAP_DIR = REPO_ROOT / "knowledge" / "eval" / "local" / "v8_snapshot"
OUT_DIR = SNAP_DIR
CAND_K = 30   # candidates fetched per base before rerank
FINAL_K = 10  # final ranking depth
BASES = ["keyword", "vector", "hybrid", "router"]
# FlagReranker default max_length=512 (query gets 3/4 of it) truncates our
# ~300-char task-level queries + 800-char chunks -- the first run (max_length
# default) DEMOTED GT out of top-10 in 17/130 vector queries because the
# cross-encoder never saw chunk mid/body. v2-m3 supports 8K positions.
MAX_LENGTH = 2048


def resolve_reranker_path() -> Path:
    env = __import__("os").environ.get("BGE_RERANKER_PATH")
    if env:
        p = Path(env)
        if p.exists():
            return p
    here = Path(__file__).resolve().parents[1].parent  # worktree root
    for base in (
        here / ".models" / "bge-reranker-v2-m3",
        here.parent.parent / ".models" / "bge-reranker-v2-m3",  # main repo root (where bge-m3 also lives)
    ):
        if base.exists():
            return base
    sys.exit("bge-reranker-v2-m3 not found: set BGE_RERANKER_PATH or download to .models/bge-reranker-v2-m3 "
             "(HuggingFace BAAI/bge-reranker-v2-m3)")


def load_reranker():
    from FlagEmbedding import FlagReranker

    path = resolve_reranker_path()
    t0 = time.perf_counter()
    model = FlagReranker(str(path), use_fp16=True)
    print(f"reranker loaded from {path} in {time.perf_counter() - t0:.1f}s")
    return model


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


def rerank_query(it: dict) -> str:
    """Query adapter for the cross-encoder.

    v8 ``question`` is a retrieval-side concatenation (topic + user_prompt +
    stage literal + system prompt + section hint, median 293 chars) -- OOD for
    bge-reranker-v2-m3, which scores everything near 1.0 on it (sigmoid
    saturation; generation slice 1 win / 29 loss vs GT). The adapter feeds the
    scorer the INTENT, not the raw concatenation:
      generation -> topic line + unit_title (~30 chars)
      planning   -> topic + user_prompt (drop the trailing 'planning' literal)
      trap       -> verbatim (already a short natural question)
    Retrieval still uses the full question; only the scorer sees the adapted form.
    """
    q = it["question"]
    lines = [ln for ln in q.splitlines() if ln.strip()]
    if it["slice"] == "generation":
        return f"{lines[0]}\n{it.get('unit_title', '')}".strip()
    if it["slice"] == "planning":
        return "\n".join(ln for ln in lines if ln.strip().lower() != "planning").strip()
    return q


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bases", default=",".join(BASES))
    ap.add_argument("--adapt-query", action="store_true",
                    help="feed the cross-encoder the intent-adapter query instead of the raw concatenation")
    args = ap.parse_args()
    bases = [b.strip() for b in args.bases.split(",")]

    snap = json.loads((SNAP_DIR / "v8_queries.json").read_text(encoding="utf-8"))
    qrels = json.loads((SNAP_DIR / "qrels.json").read_text(encoding="utf-8"))["items"]

    chunks = [c for c in kb.load_all_chunks() if not kb.is_structural_junk(c)]
    meta = json.loads((kb.KB_INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    if not meta.get("junk_filter"):
        sys.exit("rerank bench expects the cleaned-corpus generation (meta.junk_filter=true); run build_kb.py --rebuild")

    bm25 = kb.BM25Index(chunks)
    embedder = CachedEmbedder(kb.get_embedder())
    reranker = load_reranker()
    ctx = {"chunks": chunks, "bm25": bm25, "embedder": embedder}

    def rerank(query: str, cands: list[kb.Chunk]) -> tuple[list[tuple[kb.Chunk, float]], list[float]]:
        pairs = [[query, f"{c.title} | {c.section} | {c.text}"] for c in cands]
        scores = reranker.compute_score(pairs, normalize=True, max_length=MAX_LENGTH)
        scored = sorted(zip(cands, scores), key=lambda x: x[1], reverse=True)
        return scored[:FINAL_K], list(scores)

    records: dict[str, list[dict]] = {b: [] for b in bases}
    rerank_latency: dict[str, list[float]] = {b: [] for b in bases}
    for qi, it in enumerate(snap["items"]):
        qr = qrels[it["id"]]
        for base in bases:
            t0 = time.perf_counter()
            cands = kb.search(base, it["question"], ctx["chunks"], ctx["bm25"], ctx["embedder"], top_k=CAND_K)
            t1 = time.perf_counter()
            q_for_scorer = rerank_query(it) if args.adapt_query else it["question"]
            results, all_scores = rerank(q_for_scorer, [c for c, _ in cands])
            rerank_latency[base].append((time.perf_counter() - t1) * 1000)
            cand_ids = [c.chunk_id for c, _ in cands]
            strict_set = set(qr["strict_chunk_ids"])
            gt_diag = [
                {"cid": cid, "base_pos": cand_ids.index(cid), "rr_score": round(all_scores[cand_ids.index(cid)], 4)}
                for cid in qr["strict_chunk_ids"] if cid in cand_ids
            ]
            records[base].append({
                "id": it["id"], "slice": it["slice"],
                "gt_docs": it["gt_doc_ids"],
                "strict": qr["strict_chunk_ids"], "lenient": qr["relevant_set"],
                "ranked_chunks": [c.chunk_id for c, _ in results],
                "ranked_docs": [c.doc_id for c, _ in results],
                "rr_scores": [round(s, 4) for _, s in results],
                "gt_in_cands": gt_diag,
                "base_latency_ms": round((t1 - t0) * 1000, 1),
                "rerank_latency_ms": round(rerank_latency[base][-1], 1),
            })
        if (qi + 1) % 20 == 0:
            print(f"  [{qi + 1}/{len(snap['items'])}]")

    def wilson_ci(hits: int, n: int, z: float = 1.96):
        p = hits / n
        denom = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denom
        half = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / denom
        return (round(max(0.0, center - half), 3), round(min(1.0, center + half), 3))

    def hit(ranked, gt, k):
        return any(x in gt for x in ranked[:k])

    def mrr(ranked, gt):
        for pos, x in enumerate(ranked, start=1):
            if x in gt:
                return 1.0 / pos
        return 0.0

    summary = {}
    for base in bases:
        rows = records[base]
        s = {"n": len(rows)}
        for metric, rkey, gkey in (("doc", "ranked_docs", "gt_docs"), ("lenient", "ranked_chunks", "lenient"), ("strict", "ranked_chunks", "strict")):
            pairs = [(r, set(r[gkey])) for r in rows]
            if metric == "strict":
                pairs = [(r, g) for r, g in pairs if g]
            nv = max(len(pairs), 1)
            for k in (5, 10):
                h = sum(1 for r, g in pairs if hit(r[rkey], g, k))
                key = f"{metric}_r@{k}" if metric == "doc" else f"{metric}_chunk_r@{k}"
                s[key] = h / nv
                s[f"{key}_ci"] = wilson_ci(h, nv)
            mrr_key = "doc_mrr" if metric == "doc" else f"{metric}_chunk_mrr"
            s[mrr_key] = sum(mrr(r[rkey], g) for r, g in pairs) / nv
        s["rerank_p50_ms"] = sorted(rerank_latency[base])[len(rows) // 2]
        s["base_p50_ms"] = sorted(r["base_latency_ms"] for r in rows)[len(rows) // 2]
        s["slices"] = {}
        for sl in ("planning", "generation", "trap"):
            srows = [r for r in rows if r["slice"] == sl]
            if srows:
                s["slices"][sl] = {
                    "n": len(srows),
                    "lenient_chunk_r@10": sum(1 for r in srows if hit(r["ranked_chunks"], set(r["lenient"]), 10)) / len(srows),
                }
        summary[base] = s

    baseline = json.loads((SNAP_DIR / "raw-v8-after.json").read_text(encoding="utf-8"))["summary"]

    out_name = "raw-v8-rerank-adapted.json" if args.adapt_query else "raw-v8-rerank.json"
    (OUT_DIR / out_name).write_text(
        json.dumps({"summary": summary, "records": records, "candidate_k": CAND_K, "final_k": FINAL_K,
                    "candidate_form": "title | section | text", "max_length": MAX_LENGTH,
                    "adapt_query": bool(args.adapt_query)},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    print(f"\n=== rerank ({CAND_K}-cand cross-encoder{' + query-adapter' if args.adapt_query else ''}) vs 3.6 baseline ===")
    print(f"{'arm':12s} {'strict cR@5':>16s} {'strict cR@10':>16s} {'lenient cR@10':>16s} {'rerank p50':>12s}")
    for base in bases:
        s, b = summary[base], baseline[base]
        print(f"{base:12s} {b['strict_chunk_r@5']:.1%}→{s['strict_chunk_r@5']:.1%} "
              f"{b['strict_chunk_r@10']:.1%}→{s['strict_chunk_r@10']:.1%} "
              f"{b['lenient_chunk_r@10']:.1%}→{s['lenient_chunk_r@10']:.1%} "
              f"{s['rerank_p50_ms']:.0f}ms")
    print(f"-> {OUT_DIR / out_name}")


if __name__ == "__main__":
    main()
    import knowledge.engine.kb_engine as _kb
    _kb.close_qdrant()  # flush local-mode persistence before exit
