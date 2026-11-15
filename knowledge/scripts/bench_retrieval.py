"""Retrieval evaluation -- v7 synthetic suite (unit 2.5).

The old 38-query set (queries.jsonl) is SEALED: author bias + nine rounds of
reuse made v1-v6 numbers dev-set artifacts. This runner consumes the rebuilt
synthetic suite (knowledge/eval/local/synthetic_qa.json) produced by
gen_synthetic_qa.py, with the disciplines that fix v1-v6's flaws:

- chunk-level ground truth (gt_chunk_ids from generation) -> chunk recall/MRR,
  in addition to doc-level recall (which v6's round-robin was isomorphic to)
- Wilson 95% confidence intervals on every rate (n=38 taught us a 100% run
  only proves >=92.1%)
- slice reports: synthetic (simple/reasoning/multi_context/conditional),
  trap (semantic-drift queries avoiding corpus terms), colloquial (vague
  real-user phrasing)
- dev/eval subsets are disjoint; dev is the only set tuning may look at

Method naming: NAME[:param]
    router              raw direct retrieval (arm A baseline)
    wiki:round_robin    arm B, evidence slots rotate across hit pages
    wiki:pool_rerank    arm B, wiki decides pages then pool-chunks reranked
                        by local cosine against the query vector
    fused:rrf           arm C, rank fusion of raw top-k + wiki top-k (v6 shape)
    fused:union_top     arm C, union of raw top10 + wiki top10
    fused:big_pool      arm C, raw top-50 + wiki pool funnel
    fused:quota         arm C, k/2 slots per channel, interleaved

Usage (repo root):
    PYTHONPATH=. python knowledge/scripts/bench_retrieval.py v7dev --subset dev
    PYTHONPATH=. python knowledge/scripts/bench_retrieval.py v7final --subset eval
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

SUITE_PATH = REPO_ROOT / "knowledge" / "eval" / "local" / "synthetic_qa.json"
RESULTS_DIR = REPO_ROOT / "knowledge" / "eval" / "results"

K_VALUES = [5, 10]
LABELS = {
    "router": "A raw 直检 (router)",
    "wiki:round_robin": "B wiki 展开·轮转",
    "wiki:pool_rerank": "B wiki 展开·池内重排",
    "fused:rrf": "C fused·RRF (v6 形态)",
    "fused:union_top": "C fused·top10∪top10",
    "fused:big_pool": "C fused·大池漏斗 (raw50+wiki)",
    "fused:quota": "C fused·配额均分 (5+5)",
}


class CachedEmbedder:
    """Query-embedding cache shared across arms -- same query, one embed call."""

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


def wilson_ci(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = hits / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def load_suite(subset: str) -> list[dict]:
    data = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    items = data["items"]
    if subset != "all":
        items = [it for it in items if it["subset"] == subset]
    return items


def run_method(method: str, q: dict, ctx: dict) -> tuple[list[tuple[kb.Chunk, float]], dict]:
    """Dispatch one method; returns (ranked results, extras like fidelity)."""
    name, _, param = method.partition(":")
    if name in {"keyword", "vector", "hybrid", "router"}:
        return kb.search(name, q["question"], ctx["chunks"], ctx["bm25"], ctx["embedder"], top_k=K_VALUES[-1]), {}
    if name == "wiki":
        results, fid = kb.search_wiki(
            q["question"], ctx["wiki_chunks"], ctx["wiki_bm25"], ctx["embedder"],
            raw_chunks=ctx["chunks"], top_k=K_VALUES[-1],
            expand_strategy=param or "round_robin",
        )
        return results, {"fidelity": fid}
    if name == "fused":
        results = kb.search_fused(
            q["question"], ctx["chunks"], ctx["bm25"], ctx["embedder"],
            ctx["wiki_chunks"], ctx["wiki_bm25"], top_k=K_VALUES[-1],
            pool_construction=param or "rrf",
        )
        return results, {}
    raise ValueError(f"unknown method: {method}")


def evaluate() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag", help="report tag, e.g. v7dev / v7final")
    parser.add_argument("--subset", choices=["dev", "eval", "all"], default="dev")
    parser.add_argument("--methods", default="router,wiki:round_robin,wiki:pool_rerank,fused:rrf,fused:union_top,fused:big_pool,fused:quota")
    args = parser.parse_args()
    tag, subset = args.tag, args.subset
    methods = [m.strip() for m in args.methods.split(",")]

    queries = load_suite(subset)
    print(f"suite: {len(queries)} queries ({subset}) | methods: {methods}")
    slices = Counter(q.get("slice", "synthetic") for q in queries)
    print(f"slices: {dict(slices)}")

    chunks = kb.load_all_chunks()
    bm25 = kb.load_bm25_index(chunks)
    embedder = CachedEmbedder(kb.get_embedder())

    wiki_chunks = wiki_bm25 = None
    if any(m.split(":")[0] in {"wiki", "fused"} for m in methods):
        wiki_chunks = kb.load_wiki_chunks()
        if not wiki_chunks:
            print("wiki layer empty -- run compile_wiki.py + build_kb.py first")
            sys.exit(1)
        wiki_bm25 = kb.BM25Index(wiki_chunks)
        kb.ensure_vector_index(wiki_chunks, embedder, collection=kb._active_collection(wiki=True))
    print(f"raw chunks: {len(chunks)} | wiki pages: {len({c.doc_id for c in wiki_chunks}) if wiki_chunks else 0}")

    ctx = {"chunks": chunks, "bm25": bm25, "embedder": embedder, "wiki_chunks": wiki_chunks, "wiki_bm25": wiki_bm25}

    records: dict[str, list[dict]] = {m: [] for m in methods}
    fidelity = {"refs_total": 0, "refs_exact": 0, "refs_degraded": 0, "refs_failed": 0}
    for qi, q in enumerate(queries):
        for method in methods:
            start = time.perf_counter()
            results, extras = run_method(method, q, ctx)
            elapsed = time.perf_counter() - start
            row = {
                "id": q["id"], "query": q["question"], "slice": q.get("slice", "synthetic"),
                "type": q.get("type", ""),
                "gt_docs": q.get("gt_doc_ids", []), "gt_chunks": q.get("gt_chunk_ids", []),
                "ranked_chunks": [c.chunk_id for c, _ in results],
                "ranked_docs": [c.doc_id for c, _ in results],
                "latency_ms": round(elapsed * 1000, 1),
            }
            if method.startswith("wiki"):
                fid = extras.get("fidelity", {})
                for k, v in fid.items():
                    fidelity[k] = fidelity.get(k, 0) + v
            records[method].append(row)
        print(f"  [{qi + 1}/{len(queries)}] {q['id']} ({q.get('slice', '?')}/{q.get('type', '?')}) done")

    # ---- metrics ----
    def hit_doc(row: dict, k: int) -> bool:
        return any(d in row["gt_docs"] for d in row["ranked_docs"][:k])

    def hit_chunk(row: dict, k: int) -> bool:
        return any(cid in row["gt_chunks"] for cid in row["ranked_chunks"][:k])

    def mrr_doc(row: dict) -> float:
        for pos, d in enumerate(row["ranked_docs"], start=1):
            if d in row["gt_docs"]:
                return 1.0 / pos
        return 0.0

    def mrr_chunk(row: dict) -> float:
        for pos, cid in enumerate(row["ranked_chunks"], start=1):
            if cid in row["gt_chunks"]:
                return 1.0 / pos
        return 0.0

    summary: dict[str, dict] = {}
    for method in methods:
        rows = records[method]
        n = len(rows)
        stats: dict = {"n": n}
        for k in K_VALUES:
            doc_hits = sum(1 for r in rows if hit_doc(r, k))
            lo, hi = wilson_ci(doc_hits, n)
            stats[f"doc_recall@{k}"] = doc_hits / n
            stats[f"doc_recall@{k}_ci"] = (round(lo, 3), round(hi, 3))
        chunk_rows = [r for r in rows if r["gt_chunks"]]
        if chunk_rows:
            for k in K_VALUES:
                ch_hits = sum(1 for r in chunk_rows if hit_chunk(r, k))
                lo, hi = wilson_ci(ch_hits, len(chunk_rows))
                stats[f"chunk_recall@{k}"] = ch_hits / len(chunk_rows)
                stats[f"chunk_recall@{k}_ci"] = (round(lo, 3), round(hi, 3))
            stats["chunk_mrr"] = sum(mrr_chunk(r) for r in chunk_rows) / len(chunk_rows)
        stats["doc_mrr"] = sum(mrr_doc(r) for r in rows) / n
        stats["latency_ms_p50"] = sorted(r["latency_ms"] for r in rows)[n // 2]
        # slice breakdown (doc recall@10 + chunk recall@10 where labels exist)
        stats["slices"] = {}
        for slice_name in {r["slice"] for r in rows}:
            srows = [r for r in rows if r["slice"] == slice_name]
            entry = {"n": len(srows), "doc_recall@10": sum(1 for r in srows if hit_doc(r, 10)) / len(srows)}
            schunk = [r for r in srows if r["gt_chunks"]]
            if schunk:
                entry["chunk_recall@10"] = sum(1 for r in schunk if hit_chunk(r, 10)) / len(schunk)
            stats["slices"][slice_name] = entry
        # synthetic type breakdown
        typerows = [r for r in rows if r["slice"] == "synthetic"]
        stats["types"] = {}
        for tname in {r["type"] for r in typerows}:
            trows = [r for r in typerows if r["type"] == tname]
            entry = {"n": len(trows), "doc_recall@10": sum(1 for r in trows if hit_doc(r, 10)) / len(trows)}
            tchunk = [r for r in trows if r["gt_chunks"]]
            if tchunk:
                entry["chunk_recall@10"] = sum(1 for r in tchunk if hit_chunk(r, 10)) / len(tchunk)
            stats["types"][tname] = entry
        summary[method] = stats

    # ---- report ----
    lines = [
        f"# 检索评测报告 {tag}（合成评测集 v7）",
        "",
        f"- 子集：{subset} | 查询数：{len(queries)}（" + "，".join(f"{k} {v}" for k, v in slices.items()) + "）",
        f"- 语料：{len({c.doc_id for c in chunks})} docs / {len(chunks)} raw chunks | wiki {len({c.doc_id for c in wiki_chunks}) if wiki_chunks else 0} 页",
        "- 指标口径：doc_recall = top-k 命中任一相关 doc；chunk_recall = top-k 命中生成时所用源 chunk（更严格，v6 无法计算）",
        "- 置信区间：Wilson 95%（n 不足 40 时分数上下浮动 ±13pp 属正常）",
        "",
        "## 总览",
        "",
        "| 方案 | doc R@5 | doc R@10 | chunk R@10 | chunk MRR | doc MRR | p50 (ms) |",
        "|---|---|---|---|---|---|---|",
    ]
    for method in methods:
        s = summary[method]
        cr10 = f"{s['chunk_recall@10']:.1%}" if "chunk_recall@10" in s else "—"
        cmrr = f"{s['chunk_mrr']:.3f}" if "chunk_mrr" in s else "—"
        lines.append(
            f"| {LABELS.get(method, method)} | {s['doc_recall@5']:.1%} | {s['doc_recall@10']:.1%} | {cr10} | {cmrr} | {s['doc_mrr']:.3f} | {s['latency_ms_p50']:.0f} |"
        )
    lines += ["", "### Wilson 95% 置信区间（doc R@10 / chunk R@10）", ""]
    for method in methods:
        s = summary[method]
        dlo, dhi = s["doc_recall@10_ci"]
        msg = f"- {LABELS.get(method, method)}: doc R@10 ∈ [{dlo:.1%}, {dhi:.1%}]"
        if "chunk_recall@10_ci" in s:
            clo, chi = s["chunk_recall@10_ci"]
            msg += f" | chunk R@10 ∈ [{clo:.1%}, {chi:.1%}]"
        lines.append(msg)

    lines += ["", "## Slice 分层（doc R@10 / chunk R@10）", "", "| 方案 | " + " | ".join(slices) + " |", "|---|" + "---|" * len(slices)]
    for method in methods:
        s = summary[method]
        cells = []
        for sn in slices:
            e = s["slices"].get(sn, {})
            docv = f"{e.get('doc_recall@10', 0):.0%}"
            chv = f"/{e['chunk_recall@10']:.0%}" if "chunk_recall@10" in e else ""
            cells.append(f"{docv}{chv} (n={e.get('n', 0)})")
        lines.append(f"| {LABELS.get(method, method)} | " + " | ".join(cells) + " |")

    syn_types = sorted({r["type"] for r in records[methods[0]] if r["slice"] == "synthetic"})
    if syn_types:
        lines += ["", "## 演化类型分层（synthetic slice，doc R@10 / chunk R@10）", "", "| 方案 | " + " | ".join(syn_types) + " |", "|---|" + "---|" * len(syn_types)]
        for method in methods:
            s = summary[method]
            cells = []
            for tn in syn_types:
                e = s["types"].get(tn, {})
                docv = f"{e.get('doc_recall@10', 0):.0%}"
                chv = f"/{e['chunk_recall@10']:.0%}" if "chunk_recall@10" in e else ""
                cells.append(f"{docv}{chv} (n={e.get('n', 0)})")
            lines.append(f"| {LABELS.get(method, method)} | " + " | ".join(cells) + " |")

    if fidelity["refs_total"]:
        exact = fidelity["refs_exact"] / fidelity["refs_total"]
        degraded = fidelity["refs_degraded"] / fidelity["refs_total"]
        lines += [
            "", "## Citation fidelity（wiki 系臂）", "",
            f"- source_refs：{fidelity['refs_total']} | exact {exact:.1%} + degraded {degraded:.1%} = 解析率 {(exact + degraded):.1%} | 硬失败 {fidelity['refs_failed']}",
        ]
        summary["_citation_fidelity"] = round(exact + degraded, 4)

    lines += ["", "## 失败案例（top-10 未命中任一相关 doc）", ""]
    for method in methods:
        misses = [r for r in records[method] if not hit_doc(r, K_VALUES[-1])]
        lines.append(f"### {LABELS.get(method, method)}（{len(misses)} 条）")
        lines.append("")
        for r in misses:
            got = list(dict.fromkeys(d.removeprefix("wiki/") for d in r["ranked_docs"]))[:3]
            lines.append(f"- `{r['id']}` [{r['slice']}/{r['type']}] {r['query'][:60]} → 返回: {got}")
        lines.append("")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"report-{tag}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    (RESULTS_DIR / f"raw-{tag}.json").write_text(
        json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print("\n=== 结果 ===")
    for method in methods:
        s = summary[method]
        msg = f"{method:20s} docR@10={s['doc_recall@10']:.1%} (CI {s['doc_recall@10_ci'][0]:.0%}-{s['doc_recall@10_ci'][1]:.0%})"
        if "chunk_recall@10" in s:
            msg += f" chunkR@10={s['chunk_recall@10']:.1%} chunkMRR={s['chunk_mrr']:.3f}"
        print(msg)
    print(f"\nreport -> {out}")


if __name__ == "__main__":
    evaluate()
