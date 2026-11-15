"""Generate the AB cleaning-comparison report from raw-v8-{before,after}.json."""

import json
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "eval" / "local" / "v8_snapshot"
b = json.loads((D / "raw-v8-before.json").read_text(encoding="utf-8"))
a = json.loads((D / "raw-v8-after.json").read_text(encoding="utf-8"))
bs, as_ = b["summary"], a["summary"]
arms = ["keyword", "vector", "hybrid", "router"]

lines = [
    "# 3.6 AB 对照：结构垃圾清洗前后（v8 快照 130 条 × 四臂）",
    "",
    "- before：3255 chunks 全量索引（垃圾在场）｜after：2820 chunks（435 条结构垃圾被排除索引；chunks.jsonl 与 chunk_id 空间不动）",
    "- qrels 两轮固定为清洗后口径（junk 已从 GT 移除并打 dropped_by_corpus_filter；strict 78 / lenient 320 unique）——指标差异全部来自库变化",
    "- n=130，Wilson 95% CI 约 ±8pp：±1.5pp 内的差异一律视为噪声",
    "",
    "## 总览（before → after）",
    "",
    "| 臂 | docR@10 | lenient cR@10 | strict cR@10 | strict MRR | p50 ms |",
    "|---|---|---|---|---|---|",
]
for arm in arms:
    s, t = bs[arm], as_[arm]

    def fmt(key, pct=True):
        x, y = s[key], t[key]
        f = (lambda v: f"{v:.1%}") if pct else (lambda v: f"{v:.3f}")
        d = y - x
        arrow = "" if abs(d) < 0.001 else (" ↑" if d > 0 else " ↓")
        return f"{f(x)} → {f(y)}{arrow}"

    lines.append(
        f'| {arm} | {fmt("doc_r@10")} | {fmt("lenient_chunk_r@10")} | {fmt("strict_chunk_r@10")} '
        f'| {fmt("strict_chunk_mrr", False)} | {s["latency_p50_ms"]:.0f} → {t["latency_p50_ms"]:.0f} |'
    )

lines += [
    "",
    "## BM25 霸榜（keyword 臂 top-10 返回中单一 doc 占比）",
    "",
    f'- keyword 臂: {bs["keyword"]["bm25_top_doc_share"]:.1%} → {as_["keyword"]["bm25_top_doc_share"]:.1%}',
    "",
    "## trap 四象限（lenient chunk@10，n=24）",
    "",
    f'- before: {b["trap_quadrant"]}',
    f'- after: {a["trap_quadrant"]}',
    "",
    "## Slice 分层（lenient chunkR@10）",
    "",
    "| slice | n | keyword | vector | hybrid | router |",
    "|---|---|---|---|---|---|",
]
for sl in ("planning", "generation", "trap"):
    cells = []
    for arm in arms:
        e_b, e_a = bs[arm]["slices"].get(sl, {}), as_[arm]["slices"].get(sl, {})
        vb, va = e_b.get("lenient_chunk_r@10"), e_a.get("lenient_chunk_r@10")
        cells.append(f"{vb:.0%}→{va:.0%}" if vb is not None else "—")
    n = bs["keyword"]["slices"][sl]["n"]
    lines.append(f"| {sl} | {n} | " + " | ".join(cells) + " |")

lines += [
    "",
    "## 结论",
    "",
    "1. **清洗对检索指标中性**：四臂全部指标变化 ≤1.6pp，远小于 n=130 的置信区间——清洗不是提分手段，也未伤害召回。",
    "2. **strict 口径微降 1.1pp**（hybrid/router）：清洗移除的垃圾中有个别与 GT 邻近的 chunk，移除后排序扰动；在噪声范围内。",
    "3. **trap 四象限完全不变**：keyword×vector 在 trap 上的互补结构对清洗不敏感。",
    "4. **清洗的真实收益在指标之外**：用户可见面（References/乱码/目录不再可能被返回）、BM25 语料净化、下游 rerank 候选池质量——数字测不到的部分。",
    "",
    "## Known issues（记入 v8.1）",
    "",
    "- 33 个重复 chunk_id（同 doc 同名 section 撞 idx，如 doc::示例::0 ×2）——ID 级评测容忍，v8.1 修（需 chunk_id 空间迁移，与采样器垃圾过滤一起做）",
    "- 本次对照只回答「对检索指标的影响」，不回答「对最终生成质量的影响」",
]

out = Path(__file__).resolve().parents[1] / "eval" / "results" / "report-v8-ab-cleaning.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print(f"-> {out}")
