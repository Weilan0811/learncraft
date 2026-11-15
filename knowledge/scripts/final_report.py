"""Unit 3.8: final acceptance report for unit 3 (v8 evaluation generation).

Pulls every produced number into one report:
- 3.5 qrels adjudication (audit rate, strict/lenient duality, pool boundary)
- 3.6 cleaned-corpus four-arm baseline with Wilson CI + cleaning AB verdict
- 3.8 supplement: wiki arm + trap quadrant (wiki value-of-existence verdict)
- 3.7 rerank numbers if raw-v8-rerank.json exists (else marked PENDING)

Usage: python knowledge/scripts/final_report.py
"""

import json
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "eval" / "local" / "v8_snapshot"
OUT = Path(__file__).resolve().parents[1] / "eval" / "local" / "v8_snapshot" / "report-v8-final.md"

qrels = json.loads((D / "qrels.json").read_text(encoding="utf-8"))
audit = json.loads((D / "audit_results.json").read_text(encoding="utf-8"))
after = json.loads((D / "raw-v8-after.json").read_text(encoding="utf-8"))
wiki = json.loads((D / "raw-v8-wiki.json").read_text(encoding="utf-8"))
vr = json.loads((D / "validation_report.json").read_text(encoding="utf-8"))
rerank_path = D / "raw-v8-rerank.json"
rerank = json.loads(rerank_path.read_text(encoding="utf-8")) if rerank_path.exists() else None

arms = ["keyword", "vector", "hybrid", "router"]
s = after["summary"]
L = []

L += [
    "# 单元 3 终局报告：v8 评测代（清洗后库 × BGE-M3 × 双口径 qrels）",
    "",
    "## 0. 口径声明",
    "",
    "- 语料：清洗后 2820 chunks（435 条结构垃圾排除索引；chunks.jsonl 与 chunk_id 空间不动）",
    "- qrels：130 条 query，清洗后口径固化（strict 78 / lenient 320 unique；dropped_by_corpus_filter 已 flag）",
    "- judge：deepseek-chat temp0.1 三口径盲判（v1 字面口径作废归档）；人工抽验 26 条，一致率 92.3%",
    "- 池边界：BM25 top-30 + 源盲混；unjudged ≠ irrelevant（TREC pooling 约定）",
    "- n=130，Wilson 95% CI ±8pp：±1.5pp 差异视为噪声",
    "",
    "## 1. 四臂基线（doc / chunk 双口径 @10，Wilson 95% CI）",
    "",
    "| 臂 | docR@10 | lenient cR@10 | strict cR@10 | strict MRR | p50 ms |",
    "|---|---|---|---|---|---|",
]
for arm in arms:
    x = s[arm]
    d, le, st = x["doc_r@10_ci"], x["lenient_chunk_r@10_ci"], x["strict_chunk_r@10_ci"]
    L.append(f"| {arm} | {x['doc_r@10']:.1%} [{d[0]:.0%}-{d[1]:.0%}] | {x['lenient_chunk_r@10']:.1%} [{le[0]:.0%}-{le[1]:.0%}] "
             f"| {x['strict_chunk_r@10']:.1%} [{st[0]:.0%}-{st[1]:.0%}] | {x['strict_chunk_mrr']:.3f} | {x['latency_p50_ms']:.0f} |")

L += [
    "",
    f"- BM25 霸榜 proxy：keyword 臂 top-10 单 doc 占比 {s['keyword']['bm25_top_doc_share']:.1%}",
    "- 清洗 AB 结论：全指标变化 ≤1.6pp（噪声内）——清洗中性，价值在指标之外（用户可见面/语料净化/rerank 候选池）",
    "",
    "## 2. trap 分层与 keyword×vector 四象限（lenient chunk@10）",
    "",
]
for sl in ("planning", "generation", "trap"):
    cells = []
    for arm in arms:
        e = s[arm]["slices"].get(sl, {})
        cells.append(f"{e.get('lenient_chunk_r@10', 0):.0%}(n={e.get('n', 0)})")
    L.append(f"- {sl}: " + " | ".join(f"{a} {c}" for a, c in zip(arms, cells)))
L += [
    "",
    f"- trap 四象限：{after['trap_quadrant']}（vector-only 9 条：v8 语义漂移题 keyword 几乎全盲，互补性存在但 keyword 侧贡献萎缩）",
    "",
    "## 3. wiki 层生死判据（3.8 验收 #5）",
    "",
]
w = wiki["summary"]
L += [
    f"- wiki:pool_rerank 全量 130 条：docR@10={w['doc_r@10']:.1%}，lenient cR@10={w['lenient_chunk_r@10']:.1%}，p50={w['latency_p50_ms']:.0f}ms（raw vector {s['vector']['latency_p50_ms']:.0f}ms 的 ~4 倍）",
    f"- trap slice：docR@10={w['slices']['trap']['doc_r@10']:.0%} / lenient cR@10={w['slices']['trap'].get('lenient_chunk_r@10', 0):.1%}（vector 臂 trap lenient cR@10={s['vector']['slices']['trap']['lenient_chunk_r@10']:.1%}）",
    f"- trap 四象限 wiki×vector：{wiki['trap_quadrant']}",
    "- **判据答案：v8 口径下 wiki 展开臂是净拖累**——wiki_only 仅 1 条 vs vector_only 10 条，且 trap 上 wiki 大幅落后 raw 直检。根因：v8 query 是任务级长拼接（topic+prompt+stage 字面量），与 wiki 概念蒸馏层语义错位；v7 概念式短问句才是 wiki 的主场",
    "- **裁决：wiki 层不进检索主链路**；保留为 citation 导航资产（fidelity 7210 refs 全解析：exact 79.2% + degraded 20.8%，硬失败 0）。v8.1 若做 query 形态改写（为 wiki 通道生成概念式短 query）可重测",
    "",
    "## 4. rerank 收益（3.8 验收 #6）",
    "",
]
if rerank:
    rs = rerank["summary"]
    L += [
        f"- 候选形态：{rerank['candidate_form']}，底座 top-{rerank['candidate_k']} → 交叉编码器重排 top-{rerank['final_k']}",
        "",
        "| 底座 | strict cR@5（基线→rerank） | strict cR@10 | lenient cR@10 | rerank p50 |",
        "|---|---|---|---|---|",
    ]
    for arm in arms:
        r = rs[arm]
        b = s[arm]
        L.append(f"| {arm} | {b['strict_chunk_r@5']:.1%} → {r['strict_chunk_r@5']:.1%} "
                 f"| {b['strict_chunk_r@10']:.1%} → {r['strict_chunk_r@10']:.1%} "
                 f"| {b['lenient_chunk_r@10']:.1%} → {r['lenient_chunk_r@10']:.1%} "
                 f"| {r['rerank_p50_ms']:.0f}ms |")
    # verdict
    best = max(rs, key=lambda a: rs[a]["strict_chunk_r@10"])
    gain = rs[best]["strict_chunk_r@10"] - s[best]["strict_chunk_r@10"]
    if gain >= 0.05:
        verdict = f"rerank 在 {best} 底座上 strict cR@10 提升 {gain:.1%}（超出噪声带），且 p50={rs[best]['rerank_p50_ms']:.0f}ms——**进主链路**（挂在 {best} 之后）"
    elif gain <= 0.02:
        verdict = f"最大提升仅 {gain:.1%}（噪声带内）——**不进主链路**；排序瓶颈应在 3.4 采样/query 侧解决"
    else:
        verdict = f"提升 {gain:.1%} 处于临界带（2-5pp），p50={rs[best]['rerank_p50_ms']:.0f}ms——**视延迟预算裁决**，建议 generation 阶段挂载（体验敏感度低）"
    L += ["", f"**结论：{verdict}**"]

    # three-run evidence chain (mechanism diagnosis)
    timeline = []
    for fname, label in (
        ("raw-v8-rerank-v1-truncated512.json", "v1 默认 max_length=512（query 吃掉 3/4 配额，chunk 被截）"),
        ("raw-v8-rerank-v2-fulllength2048.json", "v2 max_length=2048（排除截断假设）"),
        ("raw-v8-rerank-v3-adapter-vector.json", "v3 query-adapter（喂意图段，vector 单臂）"),
    ):
        p = D / fname
        if p.exists():
            v = json.loads(p.read_text(encoding="utf-8"))["summary"].get("vector", {})
            if v:
                timeline.append(f"- {label}: vector strict cR@10 = {v.get('strict_chunk_r@10', 0):.1%}（基线 42.2%）")
    L += [
        "",
        "**三轮演进（机制诊断）**：",
        *timeline,
        "- 分数分布证据：全长拼接 query 使 sigmoid 饱和（median 0.951，GT 输非 GT 的 margin 中位仅 0.026）；adapter 后恢复（median 0.326），generation slice GT 胜率 1/29 → 7/23——饱和消除但判别力仍不足：GT 与兄弟 chunk 的差异不在词面上，cross-encoder 判不出「论述完整性/位置语义」这类 bi-encoder 已建模的差异",
        "- v8.1 方向：chunk 级粒度精判（更小的 passage 单元喂 reranker）或换指令式 reranker（如 Qwen3-Reranker）；本代不追",
    ]
else:
    L += ["- PENDING：raw-v8-rerank.json 不存在（模型未下载）。下载 BAAI/bge-reranker-v2-m3 到 .models/bge-reranker-v2-m3 后运行 bench_v8_rerank.py，重跑本脚本"]

L += [
    "",
    "## 5. 3.8 验收清单逐条对账",
    "",
    "1. **三件套入库** ✅ v8_queries.json(130) / qrels.json / spans_v8.json 固化于 local/v8_snapshot/（gitignore，管线脚本可复现）；术语梯度 L0 0.125 > L1 0.093 > L2 0.068 单调",
    "2. **judge 一致性** ✅ 26 条抽验（≥10），一致率 24/26=92.3%；分歧 #19/#20（judge 扩容偏宽）已修正 + 记录于 audit_results.json；结论：judge 判 0 全对、判 2 偏宽 → strict 主口径",
    "3. **span baseline** ✅ 800/120 滑窗 span 完整率 96.3%；切分横评（800/120 vs 400/60 vs 400/0 vs para600）双指标依据见 3.3",
    "4. **四臂基线** ✅ 本报告 §1（带 CI、双口径）+ trap 分层 §2",
    "5. **wiki 生死判据** ✅ 本报告 §3：trap 净拖累，不进主链路",
    "6. **rerank 收益** " + ("✅ 本报告 §4" if rerank else "⏳ 等模型"),
    "",
    "## 6. Known issues（v8.1 队列）",
    "",
    "- 33 个重复 chunk_id（同 doc 同名 section 撞 idx）——ID 级评测容忍；修复需 chunk_id 空间迁移",
    "- 3.4 采样器未过滤结构垃圾（81 条被踢源根因）——is_structural_junk 已就位，接入采样器待做",
    "- strict GT 均值仅 0.78 条/query（assessor 过滤 + 清洗后），strict 口径统计功效有限——v8.1 采样侧应提高单题源 chunk 数",
]

OUT.write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
print(f"\n-> {OUT}")
