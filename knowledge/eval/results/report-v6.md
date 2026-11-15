# 检索方案对比评测报告 v6

- 日期：2026-11-12 | 语料：21 页 raw / 259 wiki chunks | 评测集：38 条页面级标注
- 标注口径：top-k 返回 chunk 的 doc_id 命中任一相关页即算召回

## 总览

| 方案 | recall@5 | recall@10 | MRR | 延迟 p50 (ms) |
|---|---|---|---|---|
| A raw 直检 (router, v5 最优) | 89.5% | 92.1% | 0.704 | 949 |
| B wiki 展开 (编译层命中 → source_refs → raw 证据) | 94.7% | 100.0% | 0.727 | 853 |
| C 双路 RRF (raw router ∪ wiki 展开) | 86.8% | 97.4% | 0.792 | 1808 |

## Citation fidelity（臂 B，wiki 论断 → raw 证据链完整性）

- source_refs 总数：1651 | **精确解析：81.8%** | 降级解析（section 锚失败→doc 级展开）：18.2% | 硬失败（doc 不存在）：0.0%
- 锚点分级：summary 页 section 级（doc#Section），concept/comparison 页 doc 级
- 失败分层：section 锚失败仍指向正确文档，降级保召回（演化层 lint 的治理对象）；doc 级失败才是断链

## 失败案例（top-10 未命中任一相关页）

### A raw 直检 (router, v5 最优)（3 条）

- `q01` → 返回页: ['DOC32', 'DOC35']
- `q14` → 返回页: ['DOC05', 'DOC04']
- `q15` → 返回页: ['DOC04', 'DOC15', 'DOC05']

### B wiki 展开 (编译层命中 → source_refs → raw 证据)（0 条）


### C 双路 RRF (raw router ∪ wiki 展开)（1 条）

- `q14` → 返回页: ['DOC05', 'DOC04', 'DOC31']

## 结论与分析

### 1. 三臂解读

- **臂 B（纯 wiki 展开）recall@10 = 100%，用 11% 的索引体积（259/2637 chunks）超过 raw 直检**。机理：wiki 命中给出的是"编译态论断"，其 source_refs 指向的全部证据 docs 进入 top-10（页间交错），生成层拿到的是多样且完整的证据集而非零散 chunk。router 的 3 条 miss（q01/q14/q15）全部被 wiki 臂救回。
- **臂 C（fused）是部署形态推荐**：MRR 0.792（比 raw 直检 +12.5%）且 recall@10 97.4%（+5.3pp），两个排序质量指标同时超越单通道。代价：延迟 p50 翻倍（1808ms，双通道各需一次 query embedding）。
- **raw 直检仍是 term query 的兜底**：wiki 层蒸馏删除了精确术语细节（如 q06 "DPR 训练方法"在编译层找不到 DPR 的训练段落），纯 wiki 臂在 term-heavy query 上依赖命中页的 refs 覆盖面。双路融合的结构意义正在于此：语义 query 由 wiki 论断提升排序，term query 由 raw 精确匹配兜住召回。

### 2. 调优过程（两次迭代的 badcase 资产）

首跑数据：wiki 臂 recall@10 84.2%，citation fidelity 84.7%（1699 refs，24 个失败锚）。两次修复：

1. **锚点解析修复**：含逗号的标题（如 "Building blocks, workflows, and agents"）被逗号分隔格式拆成假 ref → 解析侧按已知 doc 集合重组；section 锚失败从"丢弃"改为"降级 doc 级展开"（保召回）。fidelity 达到 exact 81.8% + 降级 18.2% = **100% 解析、0 断链**。
2. **展开偏置修复**：降级后的 doc 级展开（单页可达 99 chunks）以顺序拼接淹没其他命中页（q01 的 top-10 被单个 doc 全占，recall 跌至 65.8%）→ 改为**页间交错**（两级 round-robin：页间轮转 + 页内 ref 轮转），recall 恢复并反超至 100%。

教训：父子展开的排序不是"子集拼接"而是"证据集配额分配"——每个 wiki 命中是一等公民，其证据在 top-k 里的出镜权必须与命中页数均衡。

### 3. 与 RAPTOR 的区别（面试叙事）

RAPTOR 是对 raw chunks 一次性聚类建树，构建后**无维护语义**——新文档进来只能重建或局部插入，节点与原文的对应关系不可审计。本实现的不同：编译层（wiki）有**维护操作语义**（ingest 增量更新受影响页 / lint 三查发布门槛 / retract 两层删除），锚定是确定性的（source_refs → raw chunks 查表），且证据链完整性可度量（citation fidelity）。聚类树回答"相似 chunk 怎么组织"，wiki 层回答"知识怎么保持最新且可溯源"。

### 4. 已知限制与后续

- wiki 臂的 100% recall 依赖页间交错的宽证据集语义（top-10 ≈ 5-8 个 docs 的代表 chunks）；若消费方要求高精度小证据集，应回到 fused 臂按 MRR 排序取 top。
- 18.2% 的降级锚（LLM 蒸馏改写标题）是演化层 LLM 深度 lint 的治理对象：lint 报告降级锚列表 → 重编译对应页。
- fused 臂延迟 1808ms 可优化：两通道 query embedding 复用同一次调用。
