"""Chunking experiment (unit 3.3): 4 strategies, span-based dual-metric verdict.

Strategies (all cut on the SAME cleaned doc body, so span coordinates apply
uniformly):
  win800_120  historical sliding window (incumbent baseline)
  win400_60   half-size window, half overlap
  win400_0    half-size window, zero overlap (3.2 showed overlap protects
              only 2.3% of spans)
  para600     paragraph aggregation (~600 target, blank-line boundaries)

Metrics per strategy:
  span_completion   fraction of the 518 answer spans fully inside one chunk
                    (pure chunking quality, no retrieval involved)
  docR@10           top-10 chunk docs hit gt_doc_ids (stable across strategies)
  chunkR@10 strict  top-10 contains a chunk fully covering >=1 gt span
                    (empty-GT queries -- span split across every candidate
                    chunk -- drop out of the denominator, counted separately)
  chunkR@10 lenient top-10 chunk overlaps >=1 gt span at all

GT is derived from unit 3.2 span annotations (doc-level coordinates), so the
same annotation asset scores every strategy -- no re-annotation.

All products go to knowledge/eval/local/chunking_exp/ (gitignored): per-
strategy chunk dumps, result.json, report.md. Nothing enters git.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from knowledge.engine import kb_engine as kb  # noqa: E402

LOCAL = REPO_ROOT / "knowledge" / "eval" / "local"
OUT = LOCAL / "chunking_exp"
OUT.mkdir(parents=True, exist_ok=True)


def load_docs() -> list[tuple[str, str, str, str, str, str]]:
    """(doc_id, title, topic, source_url, scope, raw_body) for every corpus doc."""
    docs = []
    for md in sorted(kb.KB_RAW_DIR.glob("*.md")):
        meta, body = kb.parse_frontmatter(md.read_text(encoding="utf-8"))
        docs.append(
            (
                md.stem,
                meta.get("title") or md.stem,
                meta.get("topic") or "general",
                meta.get("source_url") or "",
                meta.get("scope") or "platform",
                body,
            )
        )
    return docs


STRATEGIES: dict[str, str] = {
    "win800_120": "window 800/120 (incumbent)",
    "win400_60": "window 400/60",
    "win400_0": "window 400/0",
    "para600": "paragraph aggregate ~600",
}


def cut(strategy: str, docs) -> list[kb.Chunk]:
    chunks: list[kb.Chunk] = []
    for doc_id, title, topic, url, scope, body in docs:
        if strategy == "win800_120":
            chunks.extend(kb._chunk_body(doc_id, title, topic, url, scope, body))
        elif strategy == "win400_60":
            chunks.extend(kb._chunk_body(doc_id, title, topic, url, scope, body, chunk_size=400, chunk_overlap=60))
        elif strategy == "win400_0":
            chunks.extend(kb._chunk_body(doc_id, title, topic, url, scope, body, chunk_size=400, chunk_overlap=0))
        elif strategy == "para600":
            chunks.extend(kb.para_chunk_body(doc_id, title, topic, url, scope, body))
        else:
            raise ValueError(strategy)
    return chunks


def embed_matrix(embedder, texts: list[str], batch: int = 512) -> np.ndarray:
    vecs: list[list[float]] = []
    for start in range(0, len(texts), batch):
        vecs.extend(embedder.embed(texts[start : start + batch]))
    m = np.asarray(vecs, dtype=np.float32)
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return m / norms


def span_doc_id(item: dict) -> str:
    # every span was anchored to a gt chunk; doc_id = first ::-component
    return item["spans"][0]["chunk_id"].split("::")[0]


def span_metrics(chunks: list[kb.Chunk], spans_data: dict) -> dict:
    """Per-strategy: span completion + per-query GT sets (strict & lenient)."""
    by_doc: dict[str, list[kb.Chunk]] = {}
    for c in chunks:
        by_doc.setdefault(c.doc_id, []).append(c)

    total_spans = 0
    complete_spans = 0
    span_lengths = []
    gt_strict: dict[str, list[str]] = {}
    gt_lenient: dict[str, list[str]] = {}
    for qid, item in spans_data.items():
        doc_id = item["gt_doc_ids"][0] if item.get("gt_doc_ids") else item["spans"][0]["chunk_id"].split("::")[0]
        cands = by_doc.get(doc_id, [])
        strict: set[str] = set()
        lenient: set[str] = set()
        for s in item["spans"]:
            ds, de = s["doc_start"], s["doc_end"]
            total_spans += 1
            span_lengths.append(de - ds)
            fully_inside = False
            for c in cands:
                cs, ce = c.doc_offset, c.doc_offset + c.char_count
                overlap = cs < de and ce > ds  # character-level intersection
                if overlap:
                    lenient.add(c.chunk_id)
                if cs <= ds and ce >= de:
                    fully_inside = True
                    strict.add(c.chunk_id)
            if fully_inside:
                complete_spans += 1
        gt_strict[qid] = sorted(strict)
        gt_lenient[qid] = sorted(lenient)
    return {
        "span_completion": complete_spans / total_spans if total_spans else 0.0,
        "total_spans": total_spans,
        "complete_spans": complete_spans,
        "span_len_median": int(np.median(span_lengths)),
        "span_len_p95": int(np.percentile(span_lengths, 95)),
        "gt_strict": gt_strict,
        "gt_lenient": gt_lenient,
    }


def recall_at_k(sims: np.ndarray, chunks: list[kb.Chunk], queries: list[dict], gt: dict[str, list[str]], k: int = 10) -> dict:
    doc_hits, chunk_hits = [], []
    empty_gt = 0
    per_q = {}
    top_idx = np.argsort(-sims, axis=1)[:, :k]
    for row, q in zip(top_idx, queries):
        qid = q["id"]
        hits = [chunks[i] for i in row]
        top_docs = [c.doc_id for c in hits]
        doc_ok = int(bool(set(top_docs) & set(q["gt_doc_ids"])))
        g = gt.get(qid, [])
        if not g:
            empty_gt += 1
            chunk_ok = None
        else:
            chunk_ok = int(bool(set(c.chunk_id for c in hits) & set(g)))
        doc_hits.append(doc_ok)
        if chunk_ok is not None:
            chunk_hits.append(chunk_ok)
        per_q[qid] = {"docs": top_docs, "chunks": [c.chunk_id for c in hits], "doc_hit": doc_ok, "chunk_hit": chunk_ok}
    n = len(queries)
    n_chunk = len(chunk_hits)
    return {
        "docR": sum(doc_hits) / n,
        "chunkR": sum(chunk_hits) / n_chunk if n_chunk else 0.0,
        "empty_gt": empty_gt,
        "n": n,
        "n_chunk_scored": n_chunk,
        "per_query": per_q,
    }


def main() -> None:
    t0 = time.time()
    docs = load_docs()
    print(f"corpus: {len(docs)} docs")

    spans_data = json.loads((LOCAL / "span_annotations.json").read_text(encoding="utf-8"))["items"]
    dev = {qid: it for qid, it in spans_data.items() if it.get("subset") == "dev"}
    print(f"dev queries with spans: {len(dev)}")

    suite = json.loads((LOCAL / "synthetic_qa.json").read_text(encoding="utf-8"))["items"]
    qmeta = {it["id"]: it for it in suite if it.get("subset") == "dev"}
    queries = [{"id": qid, "gt_doc_ids": it["gt_doc_ids"], "type": it.get("type"), "query": it["question"]} for qid, it in qmeta.items()]
    clean_ids = {qid for qid, it in dev.items() if it.get("clean")}
    print(f"clean: {len(clean_ids)} / dirty: {len(dev) - len(clean_ids)}")

    embedder = kb.get_embedder()
    print("embedding dev queries ...")
    qvecs = embed_matrix(embedder, [q["query"] for q in queries])
    print(f"  qvecs {qvecs.shape} ({time.time() - t0:.0f}s)")

    results = {}
    for strategy, label in STRATEGIES.items():
        t = time.time()
        chunks = cut(strategy, docs)
        # persist chunk dump for case-reading / reproducibility
        dump = OUT / f"chunks_{strategy}.jsonl"
        with dump.open("w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps({"chunk_id": c.chunk_id, "doc_id": c.doc_id, "section": c.section, "doc_offset": c.doc_offset, "char_count": c.char_count, "text": c.text}, ensure_ascii=False) + "\n")

        sm = span_metrics(chunks, dev)
        sizes = [c.char_count for c in chunks]
        by_doc_n = Counter(c.doc_id for c in chunks)

        texts = [f"{c.title} | {c.section} | {c.text}" for c in chunks]
        cvecs = embed_matrix(embedder, texts)
        sims = qvecs @ cvecs.T

        strict = recall_at_k(sims, chunks, queries, sm["gt_strict"])
        lenient = recall_at_k(sims, chunks, queries, sm["gt_lenient"])

        results[strategy] = {
            "label": label,
            "n_chunks": len(chunks),
            "size_median": int(np.median(sizes)),
            "size_p90": int(np.percentile(sizes, 90)),
            "max_doc_chunks": max(by_doc_n.values()),
            "max_doc_id": by_doc_n.most_common(1)[0][0],
            "span_completion": round(sm["span_completion"], 4),
            "complete_spans": f"{sm['complete_spans']}/{sm['total_spans']}",
            "empty_gt_strict": strict["empty_gt"],
            "docR": round(strict["docR"], 4),
            "chunkR_strict": round(strict["chunkR"], 4),
            "chunkR_lenient": round(lenient["chunkR"], 4),
            "per_query_strict": strict["per_query"],
            "per_query_lenient": lenient["per_query"],
        }
        print(
            f"{strategy:<12} chunks={len(chunks):>5} | span_done={sm['span_completion']:.1%} | "
            f"docR={strict['docR']:.1%} | chunkR_s={strict['chunkR']:.1%} | chunkR_l={lenient['chunkR']:.1%} "
            f"| emptyGT={strict['empty_gt']} ({time.time() - t:.0f}s)"
        )

    # clean-only stratification (34 dirty-GT queries excluded)
    for strategy in STRATEGIES:
        for key, ids in (("clean", clean_ids), ("dirty", set(dev) - clean_ids)):
            sel = [q for q in queries if q["id"] in ids]
            if not sel:
                continue
            # recompute on subset via per_query records
            pq = results[strategy]["per_query_strict"]
            d = np.mean([pq[q["id"]]["doc_hit"] for q in sel])
            ch = [pq[q["id"]]["chunk_hit"] for q in sel if pq[q["id"]]["chunk_hit"] is not None]
            results[strategy][f"docR_{key}"] = round(float(d), 4)
            results[strategy][f"chunkR_{key}"] = round(float(np.mean(ch)), 4) if ch else 0.0

    # strip heavy per-query payloads for the json artifact (keep in memory only)
    slim = {k: {kk: vv for kk, vv in v.items() if not kk.startswith("per_query")} for k, v in results.items()}
    (OUT / "result.json").write_text(json.dumps({"strategies": slim, "queries": len(queries)}, ensure_ascii=False, indent=2), encoding="utf-8")
    # per-query full records for case analysis
    (OUT / "per_query.json").write_text(
        json.dumps({s: {"strict": results[s]["per_query_strict"], "lenient": results[s]["per_query_lenient"]} for s in STRATEGIES}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nall done in {time.time() - t0:.0f}s -> {OUT}")


if __name__ == "__main__":
    main()
