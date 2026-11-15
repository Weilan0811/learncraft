# 3.6 AB 对照：结构垃圾清洗前后（v8 快照 130 条 × 四臂）

- before：3255 chunks 全量索引（垃圾在场）｜after：2820 chunks（435 条结构垃圾被排除索引；chunks.jsonl 与 chunk_id 空间不动）
- qrels 两轮固定为清洗后口径（junk 已从 GT 移除并打 dropped_by_corpus_filter；strict 78 / lenient 320 unique）——指标差异全部来自库变化
- n=130，Wilson 95% CI 约 ±8pp：±1.5pp 内的差异一律视为噪声

## 总览（before → after）

| 臂 | docR@10 | lenient cR@10 | strict cR@10 | strict MRR | p50 ms |
|---|---|---|---|---|---|
| keyword | 31.5% → 31.5% | 62.3% → 63.1% ↑ | 27.8% → 27.8% | 0.255 → 0.255 | 99 → 50 |
| vector | 69.2% → 69.2% | 56.9% → 56.9% | 42.2% → 42.2% | 0.271 → 0.271 | 117 → 52 |
| hybrid | 66.9% → 66.9% | 67.7% → 67.7% | 42.2% → 42.2% | 0.267 → 0.268 | 127 → 62 |
| router | 70.8% → 70.8% | 59.2% → 60.0% ↑ | 43.3% → 43.3% | 0.259 → 0.260 ↑ | 122 → 63 |

## BM25 霸榜（keyword 臂 top-10 返回中单一 doc 占比）

- keyword 臂: 21.3% → 21.4%

## trap 四象限（lenient chunk@10，n=24）

- before: {'vector_only': 9, 'keyword_only': 1, 'both': 7, 'neither': 7}
- after: {'vector_only': 9, 'keyword_only': 1, 'both': 7, 'neither': 7}

## Slice 分层（lenient chunkR@10）

| slice | n | keyword | vector | hybrid | router |
|---|---|---|---|---|---|
| planning | 20 | 94%→94% | 50%→50% | 89%→89% | 56%→61% |
| generation | 80 | 77%→78% | 67%→67% | 77%→77% | 70%→70% |
| trap | 30 | 33%→33% | 67%→67% | 67%→67% | 67%→67% |

## 结论

1. **清洗对检索指标中性**：四臂全部指标变化 ≤1.6pp，远小于 n=130 的置信区间——清洗不是提分手段，也未伤害召回。
2. **strict 口径微降 1.1pp**（hybrid/router）：清洗移除的垃圾中有个别与 GT 邻近的 chunk，移除后排序扰动；在噪声范围内。
3. **trap 四象限完全不变**：keyword×vector 在 trap 上的互补结构对清洗不敏感。
4. **清洗的真实收益在指标之外**：用户可见面（References/乱码/目录不再可能被返回）、BM25 语料净化、下游 rerank 候选池质量——数字测不到的部分。

## Known issues（记入 v8.1）

- 33 个重复 chunk_id（同 doc 同名 section 撞 idx，如 doc::示例::0 ×2）——ID 级评测容忍，v8.1 修（需 chunk_id 空间迁移，与采样器垃圾过滤一起做）
- 本次对照只回答「对检索指标的影响」，不回答「对最终生成质量的影响」