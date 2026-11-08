# 检索方案对比评测报告 v5

- 日期：2026-11-08 | 语料：21 页 / 2378 chunks | 评测集：38 条页面级标注
- 标注口径：top-k 返回 chunk 的 doc_id 命中任一相关页即算召回

## 总览

| 方案 | recall@5 | recall@10 | MRR | 延迟 p50 (ms) |
|---|---|---|---|---|
| A 纯关键词 (BM25, baseline) | 44.7% | 44.7% | 0.426 | 6 |
| B 纯向量 | 92.1% | 94.7% | 0.833 | 386 |
| C 混合 + RRF (等权) | 84.2% | 89.5% | 0.603 | 370 |
| D 混合 + query 类型路由 (加权 RRF) | 89.5% | 92.1% | 0.704 | 384 |

## 失败案例（top-10 未命中任一相关页）

### A 纯关键词 (BM25, baseline)（21 条）

- `q01` RAG 的基本原理是什么？检索和生成是怎么配合的？ （直白）→ 返回页: ['memory-helloagents-memretrieval', 'memory-helloagents-cybertown', 'engineering-helloagents-pitfalls']
- `q02` 上下文检索怎么解决传统 RAG 里 chunk 语义割裂的问题？ （直白）→ 返回页: ['memory-helloagents-memretrieval']
- `q03` BM25 和向量检索怎么融合？RRF 是怎么做的 （直白）→ 返回页: ['engineering-helloagents-pitfalls', 'memory-helloagents-memretrieval']
- `q04` 混合检索里稀疏和稠密两路结果如何合并排序 （语义漂移：不说 RRF）→ 返回页: ['memory-helloagents-memretrieval']
- `q05` 怎么给知识库检索结果做重排序提升质量 （直白 rerank）→ 返回页: ['memory-helloagents-memretrieval', 'memory-helloagents-context', 'engineering-helloagents-pitfalls']
- `q06` DPR 这类稠密检索模型的训练方法 （术语）→ 返回页: ['memory-helloagents-memretrieval', 'agents-helloagents-paradigms', 'agents-helloagents-intro']
- `q07` 怎么系统性地评测一个 AI 产品的输出质量 （直白）→ 返回页: ['agents-helloagents-paradigms', 'engineering-helloagents-pitfalls', 'agents-helloagents-intro']
- `q08` 让 LLM 当裁判评估对话质量可靠吗？MT-Bench 是怎么做的 （直白）→ 返回页: ['engineering-helloagents-pitfalls', 'memory-helloagents-cybertown', 'evals-helloagents-perf']
- `q10` 为什么快速迭代离不开评测集 （语义漂移：Iterating Quickly == Success）→ 返回页: ['evals-helloagents-perf', 'memory-helloagents-context', 'agents-helloagents-intro']
- `q11` 评估 LLM 应用时人工标注和自动评测怎么选 （对比类）→ 返回页: ['evals-helloagents-perf', 'engineering-helloagents-pitfalls']
- `q12` 什么时候该用 agent，什么时候普通工作流就够了 （直白 When to use agents）→ 返回页: ['engineering-helloagents-pitfalls']
- `q13` ReAct 模式如何把推理和行动结合起来 （直白）→ 返回页: ['agents-helloagents-paradigms', 'agents-helloagents-intro', 'memory-helloagents-cybertown']
- `q14` 构建有效智能体的最佳实践有哪些 （直白）→ 返回页: ['agents-helloagents-paradigms', 'engineering-helloagents-pitfalls', 'agents-helloagents-intro']
- `q15` LLM 自主智能体的系统架构包含哪些组件 （直白）→ 返回页: ['evals-helloagents-perf', 'agents-helloagents-intro', 'agents-helloagents-paradigms']
- `q17` 任务分解和自我反思机制怎么提升规划能力 （语义漂移：Task Decomposition / Self-Reflection）→ 返回页: ['agents-helloagents-paradigms', 'agents-helloagents-intro']
- `q19` 生成式代理的记忆流和反思机制是怎么设计的 （直白）→ 返回页: ['agents-helloagents-paradigms', 'memory-helloagents-context', 'memory-helloagents-memretrieval']
- `q20` MemGPT 怎么把操作系统的思想用在 LLM 内存管理上 （直白）→ 返回页: ['engineering-helloagents-pitfalls', 'memory-helloagents-context', 'memory-helloagents-cybertown']
- `q23` MCP 协议是什么？为什么重要 （直白）→ 返回页: ['engineering-helloagents-pitfalls', 'evals-helloagents-perf', 'memory-helloagents-context']
- `q24` LLM 应用系统有哪些常见设计模式 （直白）→ 返回页: ['agents-helloagents-intro', 'evals-helloagents-perf', 'engineering-helloagents-pitfalls']
- `q25` 怎么用 JSON Schema 约束模型输出格式 （语义漂移：不说 structured outputs）→ 返回页: ['engineering-helloagents-pitfalls', 'memory-helloagents-context', 'agents-helloagents-paradigms']
- `q29` 做 RAG 评测时应该看哪些指标 （跨主题）→ 返回页: ['evals-helloagents-perf', 'engineering-helloagents-pitfalls', 'agents-helloagents-intro']

### B 纯向量（2 条）

- `q01` RAG 的基本原理是什么？检索和生成是怎么配合的？ （直白）→ 返回页: ['memory-helloagents-memretrieval', 'retrieval-anthropic-contextual']
- `q14` 构建有效智能体的最佳实践有哪些 （直白）→ 返回页: ['agents-helloagents-paradigms', 'agents-helloagents-intro']

### C 混合 + RRF (等权)（4 条）

- `q01` RAG 的基本原理是什么？检索和生成是怎么配合的？ （直白）→ 返回页: ['memory-helloagents-memretrieval', 'retrieval-anthropic-contextual']
- `q14` 构建有效智能体的最佳实践有哪些 （直白）→ 返回页: ['agents-helloagents-paradigms', 'agents-helloagents-intro', 'engineering-helloagents-pitfalls']
- `q15` LLM 自主智能体的系统架构包含哪些组件 （直白）→ 返回页: ['agents-helloagents-intro', 'evals-helloagents-perf', 'agents-helloagents-paradigms']
- `q17` 任务分解和自我反思机制怎么提升规划能力 （语义漂移：Task Decomposition / Self-Reflection）→ 返回页: ['agents-helloagents-paradigms']

### D 混合 + query 类型路由 (加权 RRF)（3 条）

- `q01` RAG 的基本原理是什么？检索和生成是怎么配合的？ （直白）→ 返回页: ['memory-helloagents-memretrieval', 'retrieval-anthropic-contextual']
- `q14` 构建有效智能体的最佳实践有哪些 （直白）→ 返回页: ['agents-helloagents-paradigms', 'agents-helloagents-intro']
- `q15` LLM 自主智能体的系统架构包含哪些组件 （直白）→ 返回页: ['agents-helloagents-intro', 'evals-helloagents-perf', 'agents-helloagents-paradigms']

## 迭代轨迹（评测驱动的实现改进，全部数字可复现）

| 版本 | 评测集 | 改动 | C 等权混合 @5 | D 路由 @5 |
|---|---|---|---|---|
| v1 | 30 条 | 初版：纯正文 embedding、无 BM25 过滤、topic 硬路由 | 73.3% | 76.7% |
| v3 | 30 条 | +语境化 embedding（title/section 前缀）+ BM25 相对分数过滤（≥0.35×最高分） | 80.0% | 80.0% |
| v4 | 38 条 | +8 条术语型 query，暴露方案边界 | 84.2% | 78.9%（topic 硬路由误伤 q26/q27/q28） |
| v5 | 38 条 | topic 硬路由 → **query 类型路由 + 加权 RRF**（term: bm25×1.5 / semantic: vec×1.0） | 84.2% | **89.5%** |

v2 用了未重建完成的旧向量索引，数字作废（过程记录保留 raw-20261108.json）。

## per-category 分解（v5，recall@5）

| 类别 | n | A 关键词 | B 向量 | C 等权混合 | D 路由 |
|---|---|---|---|---|---|
| term（术语密集） | 8 | 100.0% | 100.0% | 100.0% | 100.0% |
| cross（跨主题） | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| retrieval | 6 | **0.0%** | 83.3% | 66.7% | **83.3%** |
| evals | 5 | 20.0% | 100.0% | 100.0% | 100.0% |
| agents | 6 | 16.7% | 66.7% | 33.3% | 50.0% |
| memory | 5 | 60.0% | 100.0% | 100.0% | 100.0% |
| engineering | 5 | 40.0% | 100.0% | 100.0% | 100.0% |

query 类型分类器（英文 token 占比 ≥0.35 判术语型）与人工标注一致率 94.7%（36/38）。

## 边界结论（本方案的核心产出）

1. **跨语言词面断裂是关键词检索的死穴**：中文 query 检索英文语料时 BM25 大面积漏召回（retrieval 类 recall@5 = 0%，21/30 条 miss），jieba 的中文 token 与英文文档的词几乎不相交——复现了实验室接口"语义漂移漏召回"的坑，且比预期更严重（是跨语言断裂）。
2. **小语料 + 术语密集 query 时 BM25 已经够用**（term 类四方案全部 100%）：词面精确命中在这种场景没有短板。
3. **语义主导的 query 上纯向量最优**；等权 RRF 会被 BM25 的跨语言噪声拖累（retrieval 类：等权混合 66.7% < 纯向量 83.3%——BM25 错误结果与向量正确结果在 RRF 里同分，中文噪声高位累加把正确页压下去）；**加权 RRF 修复了这一点**（路由 83.3% 追平向量），同时保住术语场景的词面强项（term 类 100%）。
4. **agents 类是剩余短板**（66.7%/50%）：中文 query 在中英混合语料上多页语义相近（hello-agents 多章互为邻居），且 chunk 与标题语义错位——预期由语料扩充与演化层（LLM Wiki 页级知识）解决，不在此轮修。
5. 生产配置采用 **D（query 类型路由）**；评测集与脚本随仓库交付，语料扩充后可一键复跑。

