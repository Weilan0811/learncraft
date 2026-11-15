"""Unit 3.5: qrels adjudication side -- turn the v8 snapshot into a scorable eval set.

Pipeline (plan v4.1 section 3.5, six steps):

  1. source GT      -- free: gt_chunk_ids were fixed at 3.4 sampling time.
  2. equivalence    -- per query, keyword BM25 (jieba, kb_engine) pulls top-30
                       candidates; the SOURCE chunks are blindly mixed in; a
                       deepseek judge grades each pair 2/1/0 (SynDL-style
                       relevance assessor, no self-preference: the judge never
                       sees which chunk is the source). Grade-2 chunks join the
                       lenient qrels set (TREC: relevant if any piece is).
                       Source judged <2 => quality flag (generation-side defect).
  3. span overlay   -- verbatim answer spans on SOURCE chunks, same protocol
                       as unit 3.2 (copy-verbatim -> exact find offset).
  4. mechanical     -- field completeness, stage-literal noise in place,
                       term-overlap gradient (L0 > L1 > L2/L3), junk queries.
  5. dev/eval split -- inherited from snapshot (by seed; trap independent).
  6. pool boundary  -- declared in qrels meta: unjudged != irrelevant.

Stages (run one at a time; --all runs pool->judge->spans->validate->review):
    PYTHONPATH=. python knowledge/scripts/build_qrels.py --pool
    PYTHONPATH=. python knowledge/scripts/build_qrels.py --judge [--resume]
    PYTHONPATH=. python knowledge/scripts/build_qrels.py --spans [--resume]
    PYTHONPATH=. python knowledge/scripts/build_qrels.py --validate
    PYTHONPATH=. python knowledge/scripts/build_qrels.py --review
Products -> knowledge/eval/local/v8_snapshot/ (gitignored):
  pool.json / judge_results.json / spans_v8.json / qrels.json /
  validation_report.json / manual_review.html
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "knowledge" / "scripts"))
sys.path.insert(0, str(REPO_ROOT))

from gen_synthetic_qa import DeepSeekClient, read_env_key  # noqa: E402

from knowledge.engine import kb_engine as kb  # noqa: E402

LOCAL = REPO_ROOT / "knowledge" / "eval" / "local"
OUT = LOCAL / "v8_snapshot"
SNAP = OUT / "v8_queries.json"

BM25_TOP_K = 30
POOL_BATCH = 100          # checkpoint cadence for judge calls
JUDGE_WORKERS = 6
MIN_QUESTION_CHARS = 40   # junk interception threshold (planning/generation)
MIN_TRAP_CHARS = 25       # trap questions are bare one-liners

STOPWORDS = set(
    "的了呢吗吧啊呀哦在是和与对于把被为这那有就都不也还很更要你会我能请它他她它们我们你们 "
    "一个一些这个那个什么怎么如何可以应该需要使用进行做出来出的上了下中前后以及但是所以因为如果 "
    "帮我想给写做讲生成输出包含包括通过让使其其中之上之后关于由于并且而且等等之类因此".split()
)

JUDGE_SYSTEM = """你是检索评测的相关性判定员。知识库检索发生在「AI 课件生成」管线中，查询分三种口径，按查询类型标签选用对应判据：

【任务级】（标签：planning）——查询是任务描述（topic + 用户指令 + stage 字面量）。判据：片段是否是与该任务主题相关的实质性知识内容。主题相关且含具体知识（概念、机制、做法、事实、数据）即算 2；**不要**因为片段没有覆盖用户指令里列举的每个具体点而降分——任务级检索的目标是把相关领域的资料喂给规划器，不是找齐列举清单。

【小节级】（标签：generation）——查询 = 任务背景 + 末尾的具体检索目标（小节标题 + 核心消息 + 检索词）。判据：**只按末尾的具体目标判**——片段是否包含实现该目标所需的知识；前面的任务背景只是语境，不是判定对象。

【问句】（无标签或标签：trap）——查询是单句问题。判据：片段是否包含回答该问题的知识。

三级判定（对三种口径统一）：
- 2 = 相关：按对应口径，片段包含所需知识的实质部分（即使只是答案的一部分）
- 1 = 沾边：主题相关但不含能直接使用的具体知识（泛泛提及、目录导航、过渡文字）
- 0 = 无关：按对应口径主题不同或毫无帮助

判定要点：
- 看「知识内容」，不看措辞重合度：片段用不同措辞表达同样的知识也算 2
- 不要求片段是唯一答案：多个片段都提供相关内容是常态，各自独立判定
- 片段来自知识库切分，开头结尾可能不完整，按实际内容判

输出 JSON: {"grade": 2, "reason": "不超过30字的理由"}"""

SPAN_SYSTEM = """你是检索评测集的答案跨度标注员。给定：一个评测查询（带类型标签）、一个知识片段（该查询的目标片段）。

按查询类型选用口径：
- 【任务级】（planning）：判断片段是否提供与任务主题相关的实质知识原文——抽其中支撑该主题的具体知识跨度，不要求它回答用户指令里列举的每个具体点。
- 【小节级】（generation）：查询末尾是该次检索的具体目标——判断片段是否包含实现该目标所需的知识原文。
- 【问句】（trap）：判断片段是否包含回答该问题的知识原文。

若包含：从片段中**逐字抄录**直接对应的知识原文（spans_verbatim）。要求：
- 必须与片段原文逐字一致（程序会用精确字符串匹配定位，改写一个字都匹配失败）
- 每条摘录 ≥15 个字符，取"刚好覆盖该部分知识"的最小完整范围，不要把整个段落都抄进来
- 由多处组成时最多给 3 条摘录
并用 ≤60 字概括这段原文的知识要点（gist）。如实判断，不要迁就：片段不含对应知识时如实输出 is_answer_here=false。

输出 JSON：{"is_answer_here": true, "spans_verbatim": ["..."], "gist": "..."}；不含时 {"is_answer_here": false, "spans_verbatim": [], "gist": "一句话说明片段实际讲什么"}"""


def load_snapshot() -> dict:
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    print(f"snapshot {snap['meta']['version']}: {len(snap['items'])} items")
    return snap


def load_chunks():
    chunks = kb.load_all_chunks()
    print(f"corpus chunks: {len(chunks)}")
    return {c.chunk_id: c for c in chunks}


# ---------------------------------------------------------------- step 2a: pool
def build_pool() -> None:
    snap = load_snapshot()
    chunks_by_id = load_chunks()
    idx = kb.load_bm25_index(list(chunks_by_id.values()))

    pool: dict[str, list] = {}
    for it in snap["items"]:
        qid = it["id"]
        hits = idx.search(it["question"], top_k=BM25_TOP_K, min_rel=0.0)
        rows, seen = [], set()
        for rank, (c, score) in enumerate(hits):
            rows.append({"chunk_id": c.chunk_id, "rank": rank, "bm25": round(score, 4), "is_source": c.chunk_id in it["gt_chunk_ids"]})
            seen.add(c.chunk_id)
        # blindly mix in source chunks the BM25 channel missed
        for cid in it["gt_chunk_ids"]:
            if cid not in seen:
                rows.append({"chunk_id": cid, "rank": -1, "bm25": 0.0, "is_source": True})
        pool[qid] = rows

    n_pairs = sum(len(v) for v in pool.values())
    blind_in = sum(1 for v in pool.values() for r in v if r["is_source"] and r["rank"] < 0)
    in_top = sum(1 for v in pool.values() for r in v if r["is_source"] and r["rank"] >= 0)
    (OUT / "pool.json").write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pool: {len(pool)} queries, {n_pairs} pairs total")
    print(f"source pairs in BM25 top-{BM25_TOP_K}: {in_top}/190 | blind-mixed in (missed by BM25): {blind_in}/190")
    src_ranks = sorted(r["rank"] for v in pool.values() for r in v if r["is_source"] and r["rank"] >= 0)
    if src_ranks:
        print(f"source BM25 ranks (when retrieved): median={src_ranks[len(src_ranks)//2]} top10={sum(1 for r in src_ranks if r < 10)}/{len(src_ranks)}")
        from collections import Counter as _C

        top_docs = _C(chunks_by_id[r["chunk_id"]].doc_id for v in pool.values() for r in v if not r["is_source"])
        print("candidate doc concentration (top 5):", top_docs.most_common(5))
    print(f"-> {OUT / 'pool.json'}")


# ---------------------------------------------------------------- step 2b: judge
QUERY_TYPE_TAG = {
    "planning": "【查询类型：任务级 planning——按任务级口径判】",
    "generation": "【查询类型：小节级 generation——按末尾具体目标判】",
    "trap": "【查询类型：问句 trap——按回答问题判】",
}


def judge_pairs(client: DeepSeekClient, qtext: str, chunk_text: str, qtype: str = "trap") -> dict:
    user = f"{QUERY_TYPE_TAG.get(qtype, QUERY_TYPE_TAG['trap'])}\n\n【检索查询】\n{qtext}\n\n【知识片段】\n{chunk_text}"
    for attempt in range(3):
        try:
            r = client.chat_json(JUDGE_SYSTEM, user, temperature=0.1)
            return {"grade": int(r.get("grade", -1)), "reason": str(r.get("reason", ""))[:60]}
        except Exception as exc:  # noqa: BLE001
            if attempt == 2:
                return {"grade": -1, "reason": f"error: {exc}"[:60]}
            time.sleep(2 * (attempt + 1))
    return {"grade": -1, "reason": "error"}


def run_judge(resume: bool) -> None:
    client = DeepSeekClient()
    snap = load_snapshot()
    chunks_by_id = load_chunks()
    pool = json.loads((OUT / "pool.json").read_text(encoding="utf-8"))
    qtext = {it["id"]: it["question"] for it in snap["items"]}
    qtype = {it["id"]: it["slice"] for it in snap["items"]}

    ckpt_path = OUT / "judge_results.json"
    results: dict[str, dict] = {}
    if resume and ckpt_path.exists():
        results = json.loads(ckpt_path.read_text(encoding="utf-8"))
        print(f"resume: {len(results)} pairs already judged")

    todo = []
    for qid, rows in pool.items():
        for r in rows:
            key = f"{qid}|{r['chunk_id']}"
            if key not in results:
                todo.append((key, qtext[qid], r["chunk_id"], qtype[qid]))
    print(f"judge pairs todo: {len(todo)} (deepseek-chat temp 0.1, {JUDGE_WORKERS} workers, slice-calibrated prompts)")

    t0 = time.time()
    n_done = 0
    with ThreadPoolExecutor(max_workers=JUDGE_WORKERS) as ex:
        futs = {ex.submit(judge_pairs, client, q, chunks_by_id[cid].text, qt): key for key, q, cid, qt in todo}
        for fut in as_completed(futs):
            key = futs[fut]
            results[key] = fut.result()
            n_done += 1
            if n_done % POOL_BATCH == 0:
                ckpt_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
                rate = n_done / (time.time() - t0)
                print(f"  {n_done}/{len(todo)} ({time.time() - t0:.0f}s, {rate:.1f}/s, eta {(len(todo) - n_done) / rate:.0f}s)")
    ckpt_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    from collections import Counter

    grades = Counter(v["grade"] for v in results.values())
    print(f"judge done: {len(results)} pairs in {time.time() - t0:.0f}s | grades: {dict(sorted(grades.items()))}")
    print(f"-> {ckpt_path}")


# ---------------------------------------------------------------- step 3: spans
def run_spans(resume: bool) -> None:
    from annotate_spans import MIN_VERBATIM, resolve_spans  # 3.2 protocol reused verbatim

    snap = load_snapshot()
    chunks_by_id = load_chunks()
    client = DeepSeekClient()

    ckpt_path = OUT / "spans_checkpoint.json"
    annotations: dict[str, dict] = {}
    if resume and ckpt_path.exists():
        annotations = json.loads(ckpt_path.read_text(encoding="utf-8"))
        print(f"resume: {len(annotations)} queries already span-annotated")

    items = [it for it in snap["items"] if it["gt_chunk_ids"]]
    t0 = time.time()
    n_calls = 0
    for i, it in enumerate(items):
        if it["id"] in annotations:
            continue
        spans_all, failed_all, answers_here = [], [], []
        tag = QUERY_TYPE_TAG.get(it["slice"], QUERY_TYPE_TAG["trap"])
        for cid in it["gt_chunk_ids"]:
            chunk = chunks_by_id[cid]
            result = client.chat_json(SPAN_SYSTEM, f"{tag}\n\n【评测查询】\n{it['question']}\n\n【知识片段】\n{chunk.text}", temperature=0.1)
            n_calls += 1
            spans, failed = resolve_spans(chunk, result)
            spans_all.extend(spans)
            failed_all.extend(failed)
            answers_here.append(bool(result.get("is_answer_here")))
        annotations[it["id"]] = {
            "gt_chunk_ids": it["gt_chunk_ids"],
            "spans": spans_all,
            "answer_here_flags": answers_here,
            "clean": all(answers_here) and bool(spans_all),
        }
        if (i + 1) % 20 == 0:
            ckpt_path.write_text(json.dumps(annotations, ensure_ascii=False, indent=1), encoding="utf-8")
            eta = (time.time() - t0) / max(n_calls, 1) * (len(items) * 1.1 - n_calls)
            print(f"  spans {i + 1}/{len(items)} calls={n_calls} eta={eta:.0f}s")
    ckpt_path.write_text(json.dumps(annotations, ensure_ascii=False, indent=1), encoding="utf-8")

    n_spans = sum(len(a["spans"]) for a in annotations.values())
    dirty = [qid for qid, a in annotations.items() if not a["clean"]]
    out = {
        "meta": {
            "created": time.strftime("%Y-%m-%d %H:%M"),
            "model": "deepseek-chat (temp 0.1, verbatim->find offset resolution)",
            "protocol": "identical to unit 3.2 annotate_spans.py (SYSTEM reused)",
            "query_form": "v8 product-shaped queries (_build_query assembled, stage literals included)",
            "doc_offset_basis": "chunk.doc_offset into the cleaned doc body",
        },
        "items": annotations,
    }
    (OUT / "spans_v8.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"spans done: {len(annotations)} queries, {n_calls} calls, {n_spans} spans, {time.time() - t0:.0f}s")
    print(f"dirty sources (span annotation says a source chunk lacks the answer): {len(dirty)}")
    print(f"-> {OUT / 'spans_v8.json'}")


# ---------------------------------------------------------------- step 4: validate + assemble
def _tokenize_zh(text: str) -> set[str]:
    import jieba

    return {w for w in jieba.lcut(text) if len(w) > 1 and w not in STOPWORDS}


def run_validate() -> None:
    snap = load_snapshot()
    chunks_by_id = load_chunks()
    pool = json.loads((OUT / "pool.json").read_text(encoding="utf-8"))
    judge = json.loads((OUT / "judge_results.json").read_text(encoding="utf-8"))
    spans_doc = json.loads((OUT / "spans_v8.json").read_text(encoding="utf-8"))
    spans = spans_doc["items"]

    items = snap["items"]
    problems: list[str] = []

    # -- field completeness
    for it in items:
        if it["slice"] == "generation" and not (it.get("unit_title") and it.get("unit_idx")):
            problems.append(f"{it['id']}: generation missing unit fields")
        if it["slice"] == "planning" and not it.get("user_prompt"):
            problems.append(f"{it['id']}: planning missing user_prompt")
        if not it["gt_chunk_ids"] or not it["gt_doc_ids"]:
            problems.append(f"{it['id']}: missing gt")

    # -- stage literal noise in place (planning/generation only; trap is a bare question)
    for it in items:
        q = it["question"]
        if it["slice"] == "planning" and "planning" not in q:
            problems.append(f"{it['id']}: planning stage literal missing")
        if it["slice"] == "generation" and "generation" not in q:
            problems.append(f"{it['id']}: generation stage literal missing")

    # -- junk interception (trap questions are bare one-liners; lower bar for them)
    junk = [
        it["id"]
        for it in items
        if len(it["question"]) < (MIN_QUESTION_CHARS if it["slice"] != "trap" else MIN_TRAP_CHARS)
    ]
    if junk:
        problems.append(f"junk-length queries: {junk}")

    # -- term-overlap gradient (query tokens vs corpus doc-title bag)
    titles = {}
    for c in chunks_by_id.values():
        if c.doc_id not in titles:
            titles[c.doc_id] = c.title
    title_bag: set[str] = set()
    for t in titles.values():
        title_bag |= _tokenize_zh(t)
    by_level: dict[str, list[float]] = {}
    for it in items:
        qtok = _tokenize_zh(it["question"])
        ov = len(qtok & title_bag) / max(len(qtok), 1)
        by_level.setdefault(it["wording_level"], []).append(ov)
    overlap_grad = {lv: round(sum(v) / len(v), 3) for lv, v in sorted(by_level.items())}

    # -- judge integrity: every pool pair judged; source grades as quality signal
    missing_j = [f"{qid}|{r['chunk_id']}" for qid, rows in pool.items() for r in rows if f"{qid}|{r['chunk_id']}" not in judge]
    if missing_j:
        problems.append(f"pool pairs not judged: {len(missing_j)} (run --judge --resume)")
    src_grades: dict[str, list[int]] = {}
    for it in items:
        gs = [judge.get(f"{it['id']}|{cid}", {}).get("grade", -1) for cid in it["gt_chunk_ids"]]
        src_grades[it["id"]] = gs

    # -- assemble qrels (assessor-filtered: sources judged 0 by the blind judge
    #    are DROPPED from GT and flagged -- corpus junk (LaTeX debris, References
    #    sections) or topic-granularity mismatch from the 3.4 sampler; TREC
    #    convention: assessor verdict outranks the generation-time assumption)
    # -- human audit overlay (manual_review.html verdicts): user overrides outrank
    #    the judge (same TREC logic as source filtering, now for expansions)
    audit = {}
    audit_path = OUT / "audit_results.json"
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        overrides = {f"{o['qid']}|{o['chunk_id']}": o["user_grade"] for o in audit.get("overrides", [])}
        print(f"audit overlay: {len(overrides)} grade overrides from manual review")
    else:
        overrides = {}

    # -- corpus-filter overlay: structural junk (References/TOC/LaTeX debris)
    #    must not stay in GT -- after cleaning they are UNRETRIEVABLE, and any
    #    judge grade-2 on them is the judge's leniency, not real relevance.
    #    Fixed "cleaned-corpus qrels" keeps the before/after AB comparable.
    junk_ids = {c.chunk_id for c in kb.load_all_chunks() if kb.is_structural_junk(c)}
    print(f"corpus filter: {len(junk_ids)} structural-junk chunks in corpus")
    qrels_items = {}
    for it in items:
        qid = it["id"]
        source = list(it["gt_chunk_ids"])
        src_keep, src_drop = [], {}
        for cid in source:
            j = judge.get(f"{qid}|{cid}")
            g = j.get("grade", -1) if j else -1
            g = overrides.get(f"{qid}|{cid}", g)
            if g >= 1:
                src_keep.append(cid)
            else:
                src_drop[cid] = j
        # corpus-filter overlay: junk must not stay in GT (unretrievable after
        # cleaning; judge grade-2 on junk = judge leniency, not relevance)
        filter_dropped = [cid for cid in src_keep if cid in junk_ids]
        src_keep = [cid for cid in src_keep if cid not in junk_ids]
        judged2 = []
        judged_other = {}
        for r in pool.get(qid, []):
            cid = r["chunk_id"]
            if cid in source:
                continue
            g = judge.get(f"{qid}|{cid}", {}).get("grade", -1)
            g = overrides.get(f"{qid}|{cid}", g)
            if g == 2:
                judged2.append(cid)
            elif g in (0, 1):
                judged_other[cid] = g
        judged2_filtered = [cid for cid in judged2 if cid in junk_ids]
        judged2 = [cid for cid in judged2 if cid not in junk_ids]
        relevant_set = list(dict.fromkeys(src_keep + judged2))
        flags = {}
        if src_drop:
            flags["source_dropped_judged0"] = src_drop
        if filter_dropped or judged2_filtered:
            flags["dropped_by_corpus_filter"] = {
                "strict": filter_dropped,
                "expansion": judged2_filtered,
                "note": "unretrievable after structural-junk cleaning; removed from GT in BOTH ab rounds for comparability",
            }
        if not src_keep:
            flags["gt_empty_after_filter"] = True
        # span hygiene measured against KEPT sources only
        kept_spans = [s for s in spans.get(qid, {}).get("spans", []) if s["chunk_id"] in src_keep]
        if src_keep and not kept_spans:
            flags["span_dirty"] = True
        qrels_items[qid] = {
            "subset": it["subset"],
            "slice": it["slice"],
            "wording_level": it["wording_level"],
            "seed_id": it.get("seed_id"),
            "source_chunk_ids": source,
            "strict_chunk_ids": src_keep,
            "relevant_set": relevant_set,
            "judged2_nonsource": judged2,
            "judged_below2_counts": {str(k): v for k, v in sorted(__import__("collections").Counter(judged_other.values()).items())},
            "quality_flags": flags,
            "pool_size": len(pool.get(qid, [])),
        }

    # stats
    from collections import Counter

    n_q = len(qrels_items)
    set_sizes = [len(v["relevant_set"]) for v in qrels_items.values()]
    strict_sizes = [len(v["strict_chunk_ids"]) for v in qrels_items.values()]
    n_flagged = sum(1 for v in qrels_items.values() if v["quality_flags"])
    n_src_bad = sum(1 for v in qrels_items.values() if "source_dropped_judged0" in v["quality_flags"])
    n_empty = sum(1 for v in qrels_items.values() if v["quality_flags"].get("gt_empty_after_filter"))
    n_span_dirty = sum(1 for v in qrels_items.values() if v["quality_flags"].get("span_dirty"))
    add_rate = sum(len(v["judged2_nonsource"]) for v in qrels_items.values()) / n_q
    n_drop_pairs = sum(len(v["quality_flags"].get("source_dropped_judged0", {})) for v in qrels_items.values())

    report = {
        "meta": {
            "created": time.strftime("%Y-%m-%d %H:%M"),
            "snapshot": snap["meta"]["version"],
            "structure_version": snap["meta"]["structure_version"],
        },
        "mechanical_checks": {
            "field_completeness": "PASS" if not any("missing" in p for p in problems) else "FAIL",
            "stage_literals_in_place": "PASS" if not any("literal missing" in p for p in problems) else "FAIL",
            "junk_interception": "PASS" if not junk else f"FAIL {junk}",
            "term_overlap_by_wording": overlap_grad,
            "term_overlap_monotonic": overlap_grad.get("L0", 0) > overlap_grad.get("L1", 0) >= overlap_grad.get("L2", 0),
            "problems": problems,
        },
        "judge_stats": {
            "pairs_judged": len(judge),
            "grade_distribution": dict(sorted(Counter(v["grade"] for v in judge.values()).items())),
            "judge_protocol": "v2 slice-calibrated (planning task-level / generation section-target / trap question); v1 literal protocol invalidated and archived as judge_results_v1_literal.json",
            "source_pairs_total": sum(len(v["strict_chunk_ids"]) + len(v["quality_flags"].get("source_dropped_judged0", {})) for v in qrels_items.values()),
            "source_pairs_dropped_judged0": n_drop_pairs,
            "queries_with_dropped_source": n_src_bad,
            "queries_gt_empty_after_filter": n_empty,
            "span_dirty_queries_kept_sources": n_span_dirty,
            "flagged_queries": n_flagged,
        },
        "qrels_stats": {
            "queries": n_q,
            "relevant_set_size_mean": round(sum(set_sizes) / n_q, 2),
            "relevant_set_size_median": sorted(set_sizes)[n_q // 2],
            "strict_size_mean": round(sum(strict_sizes) / n_q, 2),
            "judge_additions_per_query_mean": round(add_rate, 2),
            "pool_boundary": f"BM25 top-{BM25_TOP_K} + source chunks; unjudged != irrelevant (TREC pooling convention)",
        },
    }
    qrels = {
        "meta": {
            "version": "v8-qrels-20261113",
            "grading": "2=relevant 1=adjacent 0=irrelevant; strict_chunk_ids = source chunks judged>=1 (assessor-filtered); relevant_set = strict U judge-grade-2 (lenient)",
            "judge": "deepseek-chat temp 0.1, blind (source mixed into pool unlabeled), slice-calibrated protocol v2",
            "source_filtering": "sources judged 0 are dropped from GT + flagged (corpus junk / sampler granularity mismatch); review manual_review.html before trusting",
            "pooling": report["qrels_stats"]["pool_boundary"],
            "dual_metric": "strict = strict_chunk_ids; lenient = relevant_set",
            "split_rule": snap["meta"]["split_rule"],
        },
        "items": qrels_items,
    }
    (OUT / "qrels.json").write_text(json.dumps(qrels, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=1)[:2200])
    print(f"flagged queries: {n_flagged}/{n_q}")
    print(f"-> qrels.json, validation_report.json")


# ---------------------------------------------------------------- step 5: manual review page
def run_review() -> None:
    snap = load_snapshot()
    chunks_by_id = load_chunks()
    pool = json.loads((OUT / "pool.json").read_text(encoding="utf-8"))
    judge = json.loads((OUT / "judge_results.json").read_text(encoding="utf-8"))
    qrels = json.loads((OUT / "qrels.json").read_text(encoding="utf-8"))["items"]

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def chunk_text(cid: str) -> str:
        return chunks_by_id[cid].text

    def is_mech_junk(cid: str) -> bool:
        c = chunks_by_id[cid]
        t, sec = c.text, c.section.lower()
        return "lxsvg@" in t or "pgfsys@" in t or "references" in sec or "citation" in sec or "参考文献" in t[:80] or "cited as" in t[:80].lower()

    import random

    rng = random.Random(7)
    picked: list[dict] = []
    # A. source judged 0 and DROPPED from GT -- stratified sample: mechanical junk
    #    (spot-check 4) + contentful disputes (12, forced to include known cases);
    #    the remaining A pairs adopt the judge verdict by default (audit rate
    #    declared in validation_report).
    a_all = []
    for qid, qr in qrels.items():
        for cid, j in (qr["quality_flags"].get("source_dropped_judged0") or {}).items():
            a_all.append({"qid": qid, "chunk_id": cid, "grade": j["grade"], "reason": j["reason"]})
    mech = [a for a in a_all if is_mech_junk(a["chunk_id"])]
    content = [a for a in a_all if not is_mech_junk(a["chunk_id"])]
    for a in rng.sample(mech, min(4, len(mech))):
        picked.append({"group": f"A1-机械垃圾抽查(共{len(mech)}条)", **a, "is_source": True})
    force_first = next((a for a in content if a["qid"] == "v8-seed01-g2"), None)
    if force_first in content:
        content = [a for a in content if a is not force_first]
        content.insert(0, force_first)
    for a in rng.sample(content, min(12, len(content))):
        picked.append({"group": f"A2-内容类争议复核(共{len(content)}条)", **a, "is_source": True})
    # B. judge-grade-2 non-source (equivalence expansion) -- 4 random
    b = [(qid, cid) for qid, qr in qrels.items() for cid in qr["judged2_nonsource"]]
    for qid, cid in rng.sample(b, min(4, len(b))):
        picked.append({"group": "B-等价扩容(判2非源)", "qid": qid, "chunk_id": cid, "grade": 2, "reason": judge[f"{qid}|{cid}"]["reason"], "is_source": False})
    # C. judge-grade-0/1 near-miss (did judge miss relevant content?) -- 4 random
    c_pool = [(qid, r["chunk_id"], judge[f"{qid}|{r['chunk_id']}"]) for qid, rows in pool.items() for r in rows if r["chunk_id"] not in qrels[qid]["source_chunk_ids"] and judge.get(f"{qid}|{r['chunk_id']}", {}).get("grade") in (0, 1)]
    for qid, cid, j in rng.sample(c_pool, min(4, len(c_pool))):
        picked.append({"group": "C-判0/1复核(漏扩检查)", "qid": qid, "chunk_id": cid, "grade": j["grade"], "reason": j["reason"], "is_source": False})
    # D. source judged 2 (sanity: judge agrees with free GT) -- 2 random
    d = [(qid, cid) for qid, it in [(it["id"], it) for it in snap["items"]] for cid in it["gt_chunk_ids"] if judge.get(f"{qid}|{cid}", {}).get("grade") == 2]
    for qid, cid in rng.sample(d, min(2, len(d))):
        picked.append({"group": "D-源判2(应然一致)", "qid": qid, "chunk_id": cid, "grade": 2, "reason": judge[f"{qid}|{cid}"]["reason"], "is_source": True})

    rows_html = []
    for n, p in enumerate(picked):
        it = next(x for x in snap["items"] if x["id"] == p["qid"])
        c = chunks_by_id[p["chunk_id"]]
        rows_html.append(f"""
<div class="case" data-idx="{n}">
  <div class="head"><b>#{n + 1} [{esc(p['group'])}]</b> judge 判定: <b class="g{p['grade']}">{p['grade']}</b> — {esc(p['reason'])} <span class="tag">{'源chunk' if p['is_source'] else '候选chunk'}</span></div>
  <details open><summary>查询 ({esc(it['id'])} · {it['slice']} · {it['wording_level']})</summary><pre class="q">{esc(it['question'])}</pre></details>
  <details><summary>知识片段 ({esc(p['chunk_id'])} · {esc(c.title)} · {esc(c.section)})</summary><pre class="c">{esc(c.text)}</pre></details>
  <div class="verdict">你的判定（依据知识内容，不是措辞）：
    <label><input type="radio" name="v{n}" value="agree" checked> 同意 judge</label>
    <label><input type="radio" name="v{n}" value="disagree2"> 不同意——应判 2（相关）</label>
    <label><input type="radio" name="v{n}" value="disagree1"> 不同意——应判 1（沾边）</label>
    <label><input type="radio" name="v{n}" value="disagree0"> 不同意——应判 0（无关）</label>
  </div>
</div>""")

    html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><title>v8 qrels judge 人工抽验</title><style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;line-height:1.5}}
h1{{font-size:20px}} .case{{border:1px solid #ccc;border-radius:8px;padding:12px;margin:14px 0}}
.head{{background:#f5f5f5;padding:6px 8px;border-radius:4px}} .tag{{float:right;color:#888;font-size:12px}}
pre{{white-space:pre-wrap;background:#fafafa;padding:8px;border-radius:4px;font-size:13px;max-height:320px;overflow:auto}}
.g2{{color:#1a7f37}} .g1{{color:#b26a00}} .g0{{color:#c62828}}
.verdict{{margin-top:8px}} label{{margin-right:14px;white-space:nowrap}}
#done{{position:sticky;top:0;background:#fffbe6;border:1px solid #e0c000;padding:10px;border-radius:6px}}
</style></head><body>
<div id="done"><b>抽验说明</b>：共 {len(picked)} 条分层抽样——A1 机械垃圾抽查 {sum(1 for p in picked if p['group'].startswith('A1'))}/{len(mech)}（乱码/文献节，低争议）、A2 内容类争议复核 {sum(1 for p in picked if p['group'].startswith('A2'))}/{len(content)}（重点：judge 是否错杀）、B 等价扩容抽查、C 漏扩检查、D 源判 2 应然一致。A 组未抽到的条目默认采纳 judge 判定，本次复核结果将折算 judge 一致率写入验证报告。对每条给出你的判定；全部做完后点下面的按钮复制结果发回对话。
<div style="margin-top:8px"><button onclick="copyResult()">复制判定结果</button> <span id="count"></span></div></div>
<h1>v8 qrels judge 人工抽验（单元 3.5 校准）</h1>
{''.join(rows_html)}
<script>
const N = {len(picked)};
function refreshCount() {{
  document.getElementById('count').textContent = '已完成 ' + document.querySelectorAll('input[type=radio]:checked').length + '/' + (N * 1);
}}
document.addEventListener('change', refreshCount);
refreshCount();
function copyResult() {{
  const out = [];
  for (let i = 0; i < N; i++) {{
    const v = document.querySelector(`input[name=v${{i}}]:checked`);
    out.push(`#${{i + 1}}:${{v ? v.value : 'unanswered'}}`);
  }}
  navigator.clipboard.writeText(out.join('\\n')).then(() => alert('已复制，粘贴回对话即可'));
}}
</script></body></html>"""
    path = OUT / "manual_review.html"
    path.write_text(html, encoding="utf-8")

    # audit coverage declared in the validation report
    vr_path = OUT / "validation_report.json"
    vr = json.loads(vr_path.read_text(encoding="utf-8"))
    vr["judge_stats"]["manual_review"] = {
        "cases": len(picked),
        "a1_mechanical_junk": {"sampled": sum(1 for p in picked if p["group"].startswith("A1")), "total": len(mech)},
        "a2_contentful_disputes": {"sampled": sum(1 for p in picked if p["group"].startswith("A2")), "total": len(content)},
        "b_expansion": 4, "c_miss_check": 4, "d_source_agreement": 2,
        "unsampled_a_pairs": "default to judge verdict; agreement rate from this audit calibrates trust",
        "known_issue": "3.4 sampler did not filter References/LaTeX-debris chunks -> junk targets entered GT sampling (v8.1 fix queued)",
    }
    audit_path2 = OUT / "audit_results.json"
    if audit_path2.exists():
        a = json.loads(audit_path2.read_text(encoding="utf-8"))
        vr["judge_stats"]["manual_review"]["user_verdicts"] = {
            "date": a["date"],
            "answers": a["answers"],
            "agreement_rate": f"{sum(1 for v in a['answers'].values() if v == 'agree')}/{len(a['answers'])}",
            "group_agreement": a["group_agreement"],
            "overrides_applied": a["overrides"],
            "conclusion": a["conclusion"],
        }
    vr_path.write_text(json.dumps(vr, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"review page: {len(picked)} cases -> {path} | audit stats written to validation_report.json")


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", action="store_true")
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--spans", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--review", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    if not any([args.pool, args.judge, args.spans, args.validate, args.review, args.all]):
        ap.error("pick a stage (or --all)")
    if args.all:
        args.pool = args.judge = args.spans = args.validate = args.review = True

    if args.pool:
        build_pool()
    if args.judge:
        if not read_env_key("CONTENT_GENERATOR_DEEPSEEK_API_KEY"):
            sys.exit("CONTENT_GENERATOR_DEEPSEEK_API_KEY missing from .env")
        run_judge(args.resume)
    if args.spans:
        if not read_env_key("CONTENT_GENERATOR_DEEPSEEK_API_KEY"):
            sys.exit("CONTENT_GENERATOR_DEEPSEEK_API_KEY missing from .env")
        run_spans(args.resume)
    if args.validate:
        run_validate()
    if args.review:
        run_review()


if __name__ == "__main__":
    main()
