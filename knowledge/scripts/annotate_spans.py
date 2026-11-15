"""Unit 3.2: answer-span annotation -- chunking-independent GT asset.

For each synthetic query, ask DeepSeek to mark the verbatim excerpt(s) of the
gt chunk that directly answer the question, then locate them by exact string
match (LLMs miscount character offsets; they copy text reliably). Spans are
stored BOTH as chunk-internal offsets and doc-level offsets (via
chunk.doc_offset), so any future chunking strategy can be re-scored
(span completeness / span-chunk recall) without re-annotation.

Side output: GT hygiene. is_answer_here=false flags (query, gt_chunk) pairs
where the chunk does NOT actually contain the answer -- candidate dirty GT.

Coverage: the 210 synthetic queries (gt_chunk_ids known). trap/colloquial
entries are doc-level manual labels without a source chunk -- out of scope.

Run during DeepSeek off-peak hours (weeknights >= 18:00, weekends).
    PYTHONPATH=. python knowledge/scripts/annotate_spans.py [--resume]
Output: knowledge/eval/local/span_annotations.json (regenerable, stays local)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "knowledge" / "scripts"))
sys.path.insert(0, str(REPO_ROOT))

from knowledge.engine import kb_engine as kb  # noqa: E402
from gen_synthetic_qa import DeepSeekClient, read_env_key  # noqa: E402

import json  # noqa: E402

SUITE_PATH = REPO_ROOT / "knowledge" / "eval" / "local" / "synthetic_qa.json"
OUT_PATH = REPO_ROOT / "knowledge" / "eval" / "local" / "span_annotations.json"
CHECKPOINT_PATH = REPO_ROOT / "knowledge" / "eval" / "local" / "span_checkpoint.json"

MIN_VERBATIM = 12  # shorter excerpts match too many places; reject

SYSTEM = """你是检索评测集的答案跨度标注员。给定：一个评测问题、它的参考答案、一个知识片段（当前切分下的 chunk）。

任务：
1. 判断该片段是否真的包含"能回答该问题的原文"（is_answer_here）。评测集的 GT 由生成时自动确定，可能存在片段实际不含答案的脏标注——如实判断，不要迁就。
2. 若包含：从片段中**逐字抄录**直接回答问题的原文连续摘录（spans_verbatim）。要求：
   - 必须与片段原文逐字一致（程序会用精确字符串匹配定位，改写一个字都匹配失败）
   - 每条摘录 ≥15 个字符，取"刚好覆盖答案"的最小完整范围，不要把整个段落都抄进来
   - 答案由多处组成时最多给 3 条摘录
3. gist：用 ≤60 字概括这段原文给出的答案要点（供后续蒸馏使用）。

输出 JSON：{"is_answer_here": true, "spans_verbatim": ["..."], "gist": "..."}；不含答案时 {"is_answer_here": false, "spans_verbatim": [], "gist": "一句话说明片段实际讲什么"}"""


def annotate_pair(client: DeepSeekClient, question: str, answer: str, chunk_text: str) -> dict:
    user = (
        f"【评测问题】\n{question}\n\n【参考答案】\n{answer or '（无参考答案，按问题自行判断）'}\n\n"
        f"【知识片段】\n{chunk_text}"
    )
    return client.chat_json(SYSTEM, user, temperature=0.1)


def resolve_spans(chunk: kb.Chunk, result: dict) -> tuple[list[dict], list[str]]:
    """Convert verbatim excerpts to exact offsets. Returns (spans, failed_verbatims)."""
    spans, failed = [], []
    for v in result.get("spans_verbatim", []):
        v = v.strip()
        if len(v) < MIN_VERBATIM:
            failed.append(v[:40])
            continue
        pos = chunk.text.find(v)
        if pos < 0:
            failed.append(v[:40])
            continue
        spans.append(
            {
                "chunk_id": chunk.chunk_id,
                "chunk_start": pos,
                "chunk_end": pos + len(v),
                "doc_start": chunk.doc_offset + pos,
                "doc_end": chunk.doc_offset + pos + len(v),
                "verbatim": v,
                "gist": result.get("gist", ""),
            }
        )
    return spans, failed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if not read_env_key("CONTENT_GENERATOR_DEEPSEEK_API_KEY"):
        sys.exit("CONTENT_GENERATOR_DEEPSEEK_API_KEY missing from .env")

    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))["items"]
    items = [it for it in suite if it.get("gt_chunk_ids")]
    print(f"suite queries with gt_chunk_ids: {len(items)} (trap/colloquial doc-level entries excluded)")

    chunks = kb.load_all_chunks()
    chunk_by_id = {c.chunk_id: c for c in chunks}
    missing = {cid for it in items for cid in it["gt_chunk_ids"] if cid not in chunk_by_id}
    if missing:
        sys.exit(f"gt_chunk_ids not found in current chunking ({len(missing)}): {sorted(missing)[:5]} ...")

    client = DeepSeekClient()
    annotations: dict[str, dict] = {}
    if args.resume and CHECKPOINT_PATH.exists():
        annotations = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        print(f"resuming with {len(annotations)}/{len(items)} annotated")

    t0 = time.time()
    n_calls = 0
    for i, item in enumerate(items):
        if item["id"] in annotations:
            continue
        spans_all, failed_all, answers_here = [], [], []
        for cid in item["gt_chunk_ids"]:
            chunk = chunk_by_id[cid]
            result = annotate_pair(client, item["question"], item.get("answer", ""), chunk.text)
            n_calls += 1
            spans, failed = resolve_spans(chunk, result)
            spans_all.extend(spans)
            failed_all.extend(failed)
            answers_here.append(bool(result.get("is_answer_here")))
            if failed:
                print(f"  [warn] {item['id']} {cid}: verbatim not matched: {failed}")
        annotations[item["id"]] = {
            "question": item["question"],
            "subset": item["subset"],
            "type": item["type"],
            "slice": item.get("slice", "synthetic"),
            "gt_chunk_ids": item["gt_chunk_ids"],
            "gt_doc_ids": item.get("gt_doc_ids", []),
            "spans": spans_all,
            "answer_here_flags": answers_here,
            "clean": all(answers_here) and bool(spans_all),
        }
        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            eta = elapsed / max(n_calls, 1) * (len(items) - i - 1)
            print(f"[{i + 1}/{len(items)}] calls={n_calls} elapsed={elapsed:.0f}s eta={eta:.0f}s")
        if (i + 1) % 20 == 0:
            CHECKPOINT_PATH.write_text(json.dumps(annotations, ensure_ascii=False, indent=1), encoding="utf-8")

    CHECKPOINT_PATH.write_text(json.dumps(annotations, ensure_ascii=False, indent=1), encoding="utf-8")

    dirty = [qid for qid, a in annotations.items() if not a["clean"]]
    no_verbatim = [qid for qid, a in annotations.items() if a["answer_here_flags"] and not a["spans"]]
    out = {
        "meta": {
            "created": time.strftime("%Y-%m-%d %H:%M"),
            "model": "deepseek-chat (temp 0.1, verbatim->find offset resolution)",
            "corpus": "41 docs / 3255 chunks (bge_m3-era)",
            "chunking": f"{kb.CHUNK_SIZE}-char window / {kb.CHUNK_OVERLAP} overlap",
            "doc_offset_basis": "chunk.doc_offset into the cleaned doc body (regex-stripped markdown)",
            "coverage": f"{len(annotations)} synthetic queries; trap/colloquial are doc-level manual labels (no source chunk)",
        },
        "items": annotations,
    }
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    n_spans = sum(len(a["spans"]) for a in annotations.values())
    print(f"\ndone: {len(annotations)} queries, {n_calls} LLM calls, {n_spans} spans resolved, {time.time() - t0:.0f}s")
    print(f"dirty GT (some gt chunk lacks the answer): {len(dirty)} -> {dirty[:10]}")
    print(f"queries where verbatim resolution failed everywhere: {len(no_verbatim)}")
    print(f"asset: {OUT_PATH}")


if __name__ == "__main__":
    main()
