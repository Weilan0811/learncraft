# 检索评测报告 v7final（合成评测集 v7）

- 子集：eval | 查询数：82（synthetic 67，trap 10，colloquial 5）
- 语料：41 docs / 3255 raw chunks | wiki 50 页
- 指标口径：doc_recall = top-k 命中任一相关 doc；chunk_recall = top-k 命中生成时所用源 chunk（更严格，v6 无法计算）
- 置信区间：Wilson 95%（n 不足 40 时分数上下浮动 ±13pp 属正常）

## 总览

| 方案 | doc R@5 | doc R@10 | chunk R@10 | chunk MRR | doc MRR | p50 (ms) |
|---|---|---|---|---|---|---|
| A raw 直检 (router) | 76.8% | 86.6% | 68.7% | 0.362 | 0.560 | 598 |
| B wiki 展开·轮转 | 56.1% | 78.0% | 0.0% | 0.000 | 0.303 | 311 |
| B wiki 展开·池内重排 | 62.2% | 65.9% | 49.3% | 0.283 | 0.517 | 743 |
| C fused·RRF (v6 形态) | 70.7% | 85.4% | 53.7% | 0.229 | 0.497 | 642 |
| C fused·top10∪top10 | 76.8% | 86.6% | 68.7% | 0.362 | 0.560 | 639 |
| C fused·大池漏斗 (raw50+wiki) | 65.9% | 84.1% | 53.7% | 0.166 | 0.419 | 642 |
| C fused·配额均分 (5+5) | 69.5% | 85.4% | 53.7% | 0.298 | 0.527 | 643 |

### Wilson 95% 置信区间（doc R@10 / chunk R@10）

- A raw 直检 (router): doc R@10 ∈ [77.6%, 92.3%] | chunk R@10 ∈ [56.8%, 78.5%]
- B wiki 展开·轮转: doc R@10 ∈ [67.9%, 85.6%] | chunk R@10 ∈ [0.0%, 5.4%]
- B wiki 展开·池内重排: doc R@10 ∈ [55.1%, 75.2%] | chunk R@10 ∈ [37.7%, 60.9%]
- C fused·RRF (v6 形态): doc R@10 ∈ [76.1%, 91.4%] | chunk R@10 ∈ [41.9%, 65.1%]
- C fused·top10∪top10: doc R@10 ∈ [77.6%, 92.3%] | chunk R@10 ∈ [56.8%, 78.5%]
- C fused·大池漏斗 (raw50+wiki): doc R@10 ∈ [74.7%, 90.5%] | chunk R@10 ∈ [41.9%, 65.1%]
- C fused·配额均分 (5+5): doc R@10 ∈ [76.1%, 91.4%] | chunk R@10 ∈ [41.9%, 65.1%]

## Slice 分层（doc R@10 / chunk R@10）

| 方案 | synthetic | trap | colloquial |
|---|---|---|---|
| A raw 直检 (router) | 87%/69% (n=67) | 90% (n=10) | 80% (n=5) |
| B wiki 展开·轮转 | 75%/0% (n=67) | 100% (n=10) | 80% (n=5) |
| B wiki 展开·池内重排 | 64%/49% (n=67) | 80% (n=10) | 60% (n=5) |
| C fused·RRF (v6 形态) | 87%/54% (n=67) | 80% (n=10) | 80% (n=5) |
| C fused·top10∪top10 | 87%/69% (n=67) | 90% (n=10) | 80% (n=5) |
| C fused·大池漏斗 (raw50+wiki) | 85%/54% (n=67) | 80% (n=10) | 80% (n=5) |
| C fused·配额均分 (5+5) | 87%/54% (n=67) | 80% (n=10) | 80% (n=5) |

## 演化类型分层（synthetic slice，doc R@10 / chunk R@10）

| 方案 | conditional | multi_context | reasoning | simple |
|---|---|---|---|---|
| A raw 直检 (router) | 80%/40% (n=5) | 87%/65% (n=31) | 57%/43% (n=7) | 96%/88% (n=24) |
| B wiki 展开·轮转 | 60%/0% (n=5) | 74%/0% (n=31) | 86%/0% (n=7) | 75%/0% (n=24) |
| B wiki 展开·池内重排 | 80%/40% (n=5) | 65%/45% (n=31) | 57%/43% (n=7) | 62%/58% (n=24) |
| C fused·RRF (v6 形态) | 80%/20% (n=5) | 90%/58% (n=31) | 71%/29% (n=7) | 88%/62% (n=24) |
| C fused·top10∪top10 | 80%/40% (n=5) | 87%/65% (n=31) | 57%/43% (n=7) | 96%/88% (n=24) |
| C fused·大池漏斗 (raw50+wiki) | 80%/20% (n=5) | 90%/58% (n=31) | 57%/29% (n=7) | 88%/62% (n=24) |
| C fused·配额均分 (5+5) | 80%/20% (n=5) | 90%/58% (n=31) | 71%/29% (n=7) | 88%/62% (n=24) |

## Citation fidelity（wiki 系臂）

- source_refs：9652 | exact 80.1% + degraded 19.9% = 解析率 100.0% | 硬失败 0

## 失败案例（top-10 未命中任一相关 doc）

### A raw 直检 (router)（11 条）

- `syn025` → 返回: ['DOC05', 'DOC22', 'DOC30']
- `syn058` → 返回: ['DOC05', 'DOC04', 'DOC31']
- `syn067` → 返回: ['DOC05', 'DOC04']
- `syn071` → 返回: ['DOC04', 'DOC15', 'DOC05']
- `syn083` → 返回: ['DOC15', 'DOC32', 'DOC07']
- `syn105` → 返回: ['DOC34', 'DOC22', 'DOC10']
- `syn120` → 返回: ['DOC28', 'DOC25', 'DOC41']
- `syn196` → 返回: ['DOC30', 'DOC32', 'DOC08']
- `syn210` → 返回: ['DOC05', 'DOC04', 'DOC30']
- `trap03` → 返回: ['DOC26', 'DOC28', 'DOC25']
- `col04` → 返回: ['DOC08', 'DOC28', 'DOC25']

### B wiki 展开·轮转（18 条）

- `syn006` → 返回: ['DOC13', 'DOC08', 'DOC41']
- `syn030` → 返回: ['DOC13', 'DOC08', 'DOC28']
- `syn042` → 返回: ['DOC41', 'DOC13', 'DOC28']
- `syn044` → 返回: ['DOC26', 'DOC41', 'DOC31']
- `syn058` → 返回: ['DOC05', 'DOC13', 'DOC25']
- `syn071` → 返回: ['DOC15', 'DOC04', 'DOC05']
- `syn086` → 返回: ['DOC41', 'DOC13', 'DOC09']
- `syn105` → 返回: ['DOC13', 'DOC08', 'DOC23']
- `syn109` → 返回: ['DOC08', 'DOC31', 'DOC29']
- `syn128` → 返回: ['DOC32', 'DOC33', 'DOC30']
- `syn130` → 返回: ['DOC41', 'DOC13', 'DOC18']
- `syn138` → 返回: ['DOC25', 'DOC13', 'DOC31']
- `syn140` → 返回: ['DOC41', 'DOC28', 'DOC13']
- `syn144` → 返回: ['DOC13', 'DOC30', 'DOC25']
- `syn150` → 返回: ['DOC31', 'DOC06', 'DOC32']
- `syn170` → 返回: ['DOC05', 'DOC18', 'DOC31']
- `syn210` → 返回: ['DOC05', 'DOC08', 'DOC15']
- `col04` → 返回: ['DOC13', 'DOC22', 'DOC07']

### B wiki 展开·池内重排（28 条）

- `syn006` → 返回: ['DOC16', 'DOC08', 'DOC31']
- `syn014` → 返回: ['DOC28', 'DOC27', 'DOC26']
- `syn025` → 返回: ['DOC21', 'DOC22', 'DOC09']
- `syn042` → 返回: ['DOC28', 'DOC41', 'DOC09']
- `syn044` → 返回: ['DOC15', 'DOC40', 'DOC28']
- `syn058` → 返回: ['DOC31', 'DOC32', 'DOC34']
- `syn067` → 返回: ['DOC05', 'DOC04', 'DOC06']
- `syn071` → 返回: ['DOC04', 'DOC05', 'DOC15']
- `syn086` → 返回: ['DOC41', 'DOC08', 'DOC06']
- `syn120` → 返回: ['DOC28', 'DOC27']
- `syn128` → 返回: ['DOC32', 'DOC33', 'DOC06']
- `syn130` → 返回: ['DOC22', 'DOC21', 'DOC32']
- `syn136` → 返回: ['DOC27', 'DOC13', 'DOC08']
- `syn138` → 返回: ['DOC16', 'DOC28', 'DOC13']
- `syn140` → 返回: ['DOC28', 'DOC15', 'DOC41']
- `syn144` → 返回: ['DOC28', 'DOC41', 'DOC37']
- `syn150` → 返回: ['DOC28', 'DOC14', 'DOC23']
- `syn158` → 返回: ['DOC08', 'DOC33']
- `syn170` → 返回: ['DOC39', 'DOC35', 'DOC36']
- `syn192` → 返回: ['DOC28', 'DOC27', 'DOC13']
- `syn196` → 返回: ['DOC30', 'DOC08']
- `syn210` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn213` → 返回: ['DOC32', 'DOC34']
- `syn214` → 返回: ['DOC14', 'DOC38', 'DOC07']
- `trap07` → 返回: ['DOC31', 'DOC13', 'DOC21']
- `trap10` → 返回: ['DOC13', 'DOC31', 'DOC03']
- `col02` → 返回: ['DOC17', 'DOC35', 'DOC32']
- `col04` → 返回: ['DOC28', 'DOC08', 'DOC22']

### C fused·RRF (v6 形态)（12 条）

- `syn025` → 返回: ['DOC05', 'DOC22', 'DOC30']
- `syn058` → 返回: ['DOC05', 'DOC04', 'DOC13']
- `syn071` → 返回: ['DOC04', 'DOC15', 'DOC05']
- `syn105` → 返回: ['DOC34', 'DOC13', 'DOC08']
- `syn130` → 返回: ['DOC22', 'DOC20', 'DOC41']
- `syn140` → 返回: ['DOC41', 'DOC09', 'DOC28']
- `syn144` → 返回: ['DOC28', 'DOC13', 'DOC25']
- `syn196` → 返回: ['DOC30', 'DOC13', 'DOC32']
- `syn210` → 返回: ['DOC05', 'DOC08', 'DOC04']
- `trap02` → 返回: ['DOC41', 'DOC09', 'DOC25']
- `trap10` → 返回: ['DOC13', 'DOC19', 'DOC31']
- `col04` → 返回: ['DOC28', 'DOC08', 'DOC13']

### C fused·top10∪top10（11 条）

- `syn025` → 返回: ['DOC05', 'DOC22', 'DOC30']
- `syn058` → 返回: ['DOC05', 'DOC04', 'DOC31']
- `syn067` → 返回: ['DOC05', 'DOC04']
- `syn071` → 返回: ['DOC04', 'DOC15', 'DOC05']
- `syn083` → 返回: ['DOC15', 'DOC32', 'DOC07']
- `syn105` → 返回: ['DOC34', 'DOC22', 'DOC10']
- `syn120` → 返回: ['DOC28', 'DOC25', 'DOC41']
- `syn196` → 返回: ['DOC30', 'DOC32', 'DOC08']
- `syn210` → 返回: ['DOC05', 'DOC04', 'DOC30']
- `trap03` → 返回: ['DOC26', 'DOC28', 'DOC25']
- `col04` → 返回: ['DOC08', 'DOC28', 'DOC25']

### C fused·大池漏斗 (raw50+wiki)（13 条）

- `syn025` → 返回: ['DOC05', 'DOC22', 'DOC30']
- `syn058` → 返回: ['DOC05', 'DOC04', 'DOC13']
- `syn071` → 返回: ['DOC04', 'DOC15', 'DOC05']
- `syn105` → 返回: ['DOC13', 'DOC34', 'DOC08']
- `syn120` → 返回: ['DOC27', 'DOC28', 'DOC09']
- `syn130` → 返回: ['DOC22', 'DOC41', 'DOC20']
- `syn140` → 返回: ['DOC41', 'DOC09', 'DOC05']
- `syn144` → 返回: ['DOC28', 'DOC25', 'DOC13']
- `syn196` → 返回: ['DOC13', 'DOC30', 'DOC32']
- `syn210` → 返回: ['DOC04', 'DOC05', 'DOC08']
- `trap02` → 返回: ['DOC41', 'DOC25', 'DOC28']
- `trap10` → 返回: ['DOC13', 'DOC19', 'DOC31']
- `col04` → 返回: ['DOC28', 'DOC08', 'DOC13']

### C fused·配额均分 (5+5)（12 条）

- `syn025` → 返回: ['DOC05', 'DOC22', 'DOC30']
- `syn058` → 返回: ['DOC05', 'DOC04', 'DOC13']
- `syn071` → 返回: ['DOC04', 'DOC15', 'DOC05']
- `syn105` → 返回: ['DOC34', 'DOC13', 'DOC08']
- `syn130` → 返回: ['DOC20', 'DOC41', 'DOC22']
- `syn140` → 返回: ['DOC28', 'DOC41', 'DOC24']
- `syn144` → 返回: ['DOC28', 'DOC13', 'DOC25']
- `syn196` → 返回: ['DOC30', 'DOC13', 'DOC32']
- `syn210` → 返回: ['DOC05', 'DOC08', 'DOC04']
- `trap02` → 返回: ['DOC09', 'DOC41', 'DOC25']
- `trap10` → 返回: ['DOC13', 'DOC19', 'DOC31']
- `col04` → 返回: ['DOC08', 'DOC13', 'DOC28']

## 终局结论（v7final）

**本代裁决：raw 直检（router）全面最优，编译层检索增益不成立。**

- 主战场（synthetic, n=67）：router docR@10=87% / chunkR@10≈69%，高于全部 wiki 臂与 fused 构造；v6 的"wiki 臂 100% 超 raw"确认是旧测试集作者偏差 + 指标同构的产物（幻觉证伪）
- 轮转展开的 chunkR@10=0%（dev 7.7%）：其"每页均匀代表"策略与 chunk 级命中完全脱钩——排序不是拼接，是证据集配额分配，但配额不等于命中
- 唯一正向信号：**trap slice（语义漂移对抗 query, n=10）上 wiki:round_robin 100% vs router 90%**——编译层的概念归一在"术语规避"型 query 上留下了方向正确的火种；但 n=10 的 Wilson CI 宽达 ±25pp，不构成显著证据，下代评测需扩充对抗题库
- 机制归因（dev 诊断）：① wiki 层页级命中率天花板 ≈72% < router 77.6%；② degraded 锚（20.7%）doc 级展开污染证据池；③ wiki 证据与 raw top-10 平均重叠 0.4/10，fused 的 raw 优先截断使其全部出局

**结论定性**：在本语料规模（41 docs）与当前编译协议下，LLM Wiki 层的检索价值定位应从"召回增强"转向知识管理与 citation 证据链（fidelity 100% 解析）。若重启检索方向：混合路由（对抗型 query 走 wiki 层 / term 型走 raw）或编译协议以可检索性为目标重设计，均属新方法，需新的 dev 迭代与新的 eval 快照（合成评测集可再生，成本 ~¥1 / 22 分钟）。

**评测纪律沉淀**：三族模型隔离（deepseek 生成 / qwen 编译 / bailian embedding）、措辞去偏（avoided_terms）、chunk 级 ground truth、Wilson 95% CI、dev/eval 不相交 + eval 单次消费、每代方法配新 eval 快照——v1-v9 的"九轮复用同一测试集"反模式至此结构性根治。
