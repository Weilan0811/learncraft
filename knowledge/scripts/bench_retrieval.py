"""Four-way retrieval evaluation over the local KB.

Compares keyword (BM25 baseline mimicking the lab API), vector, hybrid+RRF,
and index-routed hybrid on the annotated query set knowledge/eval/queries.jsonl.
Reports page-level recall@5 / recall@10 / MRR and dumps per-method miss cases.

Usage (repo root):
    python knowledge/scripts/bench_retrieval.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services import kb_engine as kb  # noqa: E402

QUERIES_PATH = REPO_ROOT / "knowledge" / "eval" / "queries.jsonl"
RESULTS_DIR = REPO_ROOT / "knowledge" / "eval" / "results"

METHODS = ["keyword", "vector", "hybrid", "router"]
K_VALUES = [5, 10]


def read_env_key() -> str:
    for line in (REPO_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("CONTENT_GENERATOR_BAILIAN_API_KEY="):
            return line.partition("=")[2].strip()
    return ""


def evaluate() -> None:
    tag = sys.argv[1] if len(sys.argv) > 1 else "v2"
    queries = [json.loads(line) for line in QUERIES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"queries: {len(queries)}")

    chunks = kb.load_all_chunks()
    bm25 = kb.load_bm25_index(chunks)
    embedder = kb.BailianEmbedder(api_key=read_env_key())
    print(f"chunks: {len(chunks)} | strategies: {METHODS}")

    records: dict[str, list[dict]] = {m: [] for m in METHODS}
    for q in queries:
        for method in METHODS:
            start = time.perf_counter()
            results = kb.search(method, q["query"], chunks, bm25, embedder, top_k=K_VALUES[-1])
            elapsed = time.perf_counter() - start
            ranked_docs = [c.doc_id for c, _ in results]
            row = {"id": q["id"], "query": q["query"], "relevant": q["relevant_docs"], "ranked_docs": ranked_docs, "latency_ms": round(elapsed * 1000, 1), "note": q.get("note", "")}
            records[method].append(row)
        print(f"  {q['id']} done")

    report_lines = [f"# 检索方案对比评测报告 {tag}", "", f"- 日期：2026-11-08 | 语料：{len({c.doc_id for c in chunks})} 页 / {len(chunks)} chunks | 评测集：{len(queries)} 条页面级标注", "- 标注口径：top-k 返回 chunk 的 doc_id 命中任一相关页即算召回", ""]
    summary: dict[str, dict[str, float]] = {}
    for method in METHODS:
        rows = records[method]
        stats: dict[str, float] = {}
        for k in K_VALUES:
            hits = sum(1 for r in rows if any(d in r["relevant"] for d in r["ranked_docs"][:k]))
            stats[f"recall@{k}"] = hits / len(rows)
        rr_sum = 0.0
        for r in rows:
            for pos, doc in enumerate(r["ranked_docs"], start=1):
                if doc in r["relevant"]:
                    rr_sum += 1.0 / pos
                    break
        stats["mrr"] = rr_sum / len(rows)
        stats["latency_ms_p50"] = sorted(r["latency_ms"] for r in rows)[len(rows) // 2]
        summary[method] = stats

    report_lines += ["## 总览", "", "| 方案 | recall@5 | recall@10 | MRR | 延迟 p50 (ms) |", "|---|---|---|---|---|"]
    labels = {"keyword": "A 纯关键词 (BM25, baseline)", "vector": "B 纯向量", "hybrid": "C 混合 + RRF (等权)", "router": "D 混合 + query 类型路由 (加权 RRF)"}
    for method in METHODS:
        s = summary[method]
        report_lines.append(f"| {labels[method]} | {s['recall@5']:.1%} | {s['recall@10']:.1%} | {s['mrr']:.3f} | {s['latency_ms_p50']:.0f} |")

    miss_lines = ["", "## 失败案例（top-10 未命中任一相关页）", ""]
    for method in METHODS:
        misses = [r for r in records[method] if not any(d in r["relevant"] for d in r["ranked_docs"])]
        miss_lines.append(f"### {labels[method]}（{len(misses)} 条）")
        miss_lines.append("")
        for r in misses:
            miss_lines.append(f"- `{r['id']}` {r['query']} （{r['note']}）→ 返回页: {list(dict.fromkeys(r['ranked_docs']))[:3]}")
        miss_lines.append("")

    report_lines += miss_lines
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"report-{tag}.md"
    out.write_text("\n".join(report_lines), encoding="utf-8")
    (RESULTS_DIR / f"raw-{tag}.json").write_text(json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n=== 结果 ===")
    for method in METHODS:
        s = summary[method]
        print(f"{method:8s} recall@5={s['recall@5']:.1%} recall@10={s['recall@10']:.1%} mrr={s['mrr']:.3f} p50={s['latency_ms_p50']:.0f}ms")
    print(f"\nreport -> {out}")


if __name__ == "__main__":
    evaluate()
