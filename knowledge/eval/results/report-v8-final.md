# 单元 3 终局报告：v8 评测代（清洗后库 × BGE-M3 × 双口径 qrels）

## 0. 口径声明

- 语料：清洗后 2820 chunks（435 条结构垃圾排除索引；chunks.jsonl 与 chunk_id 空间不动）
- qrels：130 条 query，清洗后口径固化（strict 78 / lenient 320 unique；dropped_by_corpus_filter 已 flag）
- judge：deepseek-chat temp0.1 三口径盲判（v1 字面口径作废归档）；人工抽验 26 条，一致率 92.3%
- 池边界：BM25 top-30 + 源盲混；unjudged ≠ irrelevant（TREC pooling 约定）
- n=130，Wilson 95% CI ±8pp：±1.5pp 差异视为噪声

## 1. 四臂基线（doc / chunk 双口径 @10，Wilson 95% CI）

| 臂 | docR@10 | lenient cR@10 | strict cR@10 | strict MRR | p50 ms |
|---|---|---|---|---|---|
| keyword | 31.5% [24%-40%] | 63.1% [55%-71%] | 27.8% [20%-38%] | 0.255 | 50 |
| vector | 69.2% [61%-76%] | 56.9% [48%-65%] | 42.2% [32%-52%] | 0.271 | 52 |
| hybrid | 66.9% [58%-74%] | 67.7% [59%-75%] | 42.2% [32%-52%] | 0.268 | 62 |
| router | 70.8% [62%-78%] | 60.0% [51%-68%] | 43.3% [34%-54%] | 0.260 | 63 |

- BM25 霸榜 proxy：keyword 臂 top-10 单 doc 占比 21.4%
- 清洗 AB 结论：全指标变化 ≤1.6pp（噪声内）——清洗中性，价值在指标之外（用户可见面/语料净化/rerank 候选池）

## 2. trap 分层与 keyword×vector 四象限（lenient chunk@10）

- planning: keyword 94%(n=20) | vector 50%(n=20) | hybrid 89%(n=20) | router 61%(n=20)
- generation: keyword 78%(n=80) | vector 67%(n=80) | hybrid 77%(n=80) | router 70%(n=80)
- trap: keyword 33%(n=30) | vector 67%(n=30) | hybrid 67%(n=30) | router 67%(n=30)

- trap 四象限：{'vector_only': 9, 'keyword_only': 1, 'both': 7, 'neither': 7}（vector-only 9 条：v8 语义漂移题 keyword 几乎全盲，互补性存在但 keyword 侧贡献萎缩）

## 3. wiki 层生死判据（3.8 验收 #5）

- wiki:pool_rerank 全量 130 条：docR@10=64.6%，lenient cR@10=37.7%，p50=492ms（raw vector 52ms 的 ~4 倍）
- trap slice：docR@10=47% / lenient cR@10=29.2%（vector 臂 trap lenient cR@10=66.7%）
- trap 四象限 wiki×vector：{'vector_only': 10, 'both': 6, 'neither': 7, 'wiki_only': 1}
- **判据答案：v8 口径下 wiki 展开臂是净拖累**——wiki_only 仅 1 条 vs vector_only 10 条，且 trap 上 wiki 大幅落后 raw 直检。根因：v8 query 是任务级长拼接（topic+prompt+stage 字面量），与 wiki 概念蒸馏层语义错位；v7 概念式短问句才是 wiki 的主场
- **裁决：wiki 层不进检索主链路**；保留为 citation 导航资产（fidelity 7210 refs 全解析：exact 79.2% + degraded 20.8%，硬失败 0）。v8.1 若做 query 形态改写（为 wiki 通道生成概念式短 query）可重测

## 4. rerank 收益（3.8 验收 #6）

- 候选形态：title | section | text，底座 top-30 → 交叉编码器重排 top-10

| 底座 | strict cR@5（基线→rerank） | strict cR@10 | lenient cR@10 | rerank p50 |
|---|---|---|---|---|
| keyword | 26.7% → 17.8% | 27.8% → 23.3% | 63.1% → 66.2% | 962ms |
| vector | 36.7% → 35.6% | 42.2% → 41.1% | 56.9% → 58.5% | 886ms |
| hybrid | 36.7% → 32.2% | 42.2% → 37.8% | 67.7% → 66.2% | 945ms |
| router | 37.8% → 33.3% | 43.3% → 37.8% | 60.0% → 63.8% | 921ms |

**结论：最大提升仅 -1.1%（噪声带内）——**不进主链路**；排序瓶颈应在 3.4 采样/query 侧解决**

**三轮演进（机制诊断）**：
- v1 默认 max_length=512（query 吃掉 3/4 配额，chunk 被截）: vector strict cR@10 = 28.9%（基线 42.2%）
- v2 max_length=2048（排除截断假设）: vector strict cR@10 = 30.0%（基线 42.2%）
- v3 query-adapter（喂意图段，vector 单臂）: vector strict cR@10 = 37.8%（基线 42.2%）
- 分数分布证据：全长拼接 query 使 sigmoid 饱和（median 0.951，GT 输非 GT 的 margin 中位仅 0.026）；adapter 后恢复（median 0.326），generation slice GT 胜率 1/29 → 7/23——饱和消除但判别力仍不足：GT 与兄弟 chunk 的差异不在词面上，cross-encoder 判不出「论述完整性/位置语义」这类 bi-encoder 已建模的差异
- v8.1 方向：chunk 级粒度精判（更小的 passage 单元喂 reranker）或换指令式 reranker（如 Qwen3-Reranker）；本代不追

## 5. 3.8 验收清单逐条对账

1. **三件套入库** ✅ v8_queries.json(130) / qrels.json / spans_v8.json 固化于 local/v8_snapshot/（gitignore，管线脚本可复现）；术语梯度 L0 0.125 > L1 0.093 > L2 0.068 单调
2. **judge 一致性** ✅ 26 条抽验（≥10），一致率 24/26=92.3%；分歧 #19/#20（judge 扩容偏宽）已修正 + 记录于 audit_results.json；结论：judge 判 0 全对、判 2 偏宽 → strict 主口径
3. **span baseline** ✅ 800/120 滑窗 span 完整率 96.3%；切分横评（800/120 vs 400/60 vs 400/0 vs para600）双指标依据见 3.3
4. **四臂基线** ✅ 本报告 §1（带 CI、双口径）+ trap 分层 §2
5. **wiki 生死判据** ✅ 本报告 §3：trap 净拖累，不进主链路
6. **rerank 收益** ✅ 本报告 §4

## 6. Known issues（v8.1 队列）

- 33 个重复 chunk_id（同 doc 同名 section 撞 idx）——ID 级评测容忍；修复需 chunk_id 空间迁移
- 3.4 采样器未过滤结构垃圾（81 条被踢源根因）——is_structural_junk 已就位，接入采样器待做
- strict GT 均值仅 0.78 条/query（assessor 过滤 + 清洗后），strict 口径统计功效有限——v8.1 采样侧应提高单题源 chunk 数