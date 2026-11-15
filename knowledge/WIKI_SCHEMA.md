# WIKI_SCHEMA — Agent Engineering Knowledge Wiki

> 本文是 Karpathy LLM Wiki 模式（gist: karpathy/llm-wiki, 2026-04-04）在本知识库的**领域实例化**，即该模式三要素中的第三层"schema 约定文档"。所有编译、维护、体检 wiki 的脚本与 LLM 流程都受本文约束；规则演进先改本文，再改代码。
>
> 出处与定位：Karpathy 原始发布物是 idea file（规范文本），明确"intentionally abstract, not a specific implementation"。本文按其三层架构 / 三操作 / 两文件的骨架，为"Agent 工程知识库"场景填充具体约定，并保留本项目的两个特有扩展（source_refs 锚定、scope 分层）。

## 1. 覆盖范围（Domain）

本 wiki 是 `knowledge/raw/`（本地自备的 Agent 工程语料，规模随 ingest 增长，主题域见各页 frontmatter 的 topic 标注）的**编译层**。它回答"Agent 工程领域内的问题"；领域外内容不建页。

## 2. 三层架构

| 层 | 位置 | 写权限 | 角色 |
|---|---|---|---|
| Raw sources | `knowledge/raw/*.md` | **不可变**（LLM 只读不写） | source of truth |
| Wiki | `knowledge/wiki/**` | **LLM 全权维护**（脚本代行） | 编译态知识：论断、跨源综合、交叉链接 |
| Schema | 本文 `knowledge/WIKI_SCHEMA.md` | 人与 LLM 共同演进 | 约束 wiki 的结构与工作流 |

## 3. 目录结构

```
knowledge/
├── WIKI_SCHEMA.md            # 本文（第三层）
├── raw/                      # 第一层：不可变源（21 篇）
└── wiki/                     # 第二层：LLM 全权维护
    ├── index.md              # 内容目录：每页恰一条登记（一行 wikilink + 一行摘要），按 type 分节；每次编译/ingest 重建
    ├── log.md                # append-only 操作日志（## [date time] op | note）
    ├── summaries/            # 单源编译页：一篇 raw → 一页（section 级锚定）
    ├── concepts/             # 跨源概念页：综合多篇 raw 的一个概念（doc 级锚定）
    └── comparisons/          # 对比页：多篇 raw 的结构化对比（doc 级锚定）
```

## 4. 页面格式

### 4.1 Frontmatter（平面 key: value，逗号分隔列表）

> 硬约束：不用 YAML 数组/嵌套。`kb_engine.parse_frontmatter` 按平面 `key: value` 行解析——本 wiki 页将来要进同一检索管线，格式必须兼容。

```yaml
---
title: 页面标题
type: summary          # summary | concept | comparison（三选一）
tags: retrieval,rag     # 逗号分隔；summary 页继承源 topic
sources: doc1,doc2      # 逗号分隔 raw doc_id（= raw 文件名 stem）
source_refs: doc1#Section Name,doc1#intro,doc2   # 锚点，见 4.4
summary: 一句话摘要     # index.md 登记用
created: 2026-11-12
updated: 2026-11-12
---
```

### 4.2 正文结构（按 type）

- **summary**：保留原文章节骨架（`## ` 分节），300–600 字，只保留可复核的事实/结论/参数/机制，删除铺垫、例子展开、推导过程。禁止编造原文没有的内容。出链不作硬性要求（溯源由 frontmatter 承担）。
- **concept**（跨源综合）：`## Definition` → `## Key Mechanisms` → `## Cross-source Consensus & Disagreements` → `## Open Questions` → `## Related`。**每页 ≥2 条出链**（指向 summaries/ 或其他 concepts/）。
- **comparison**（结构化对比）：对比维度用表格，`## Verdict` 给结论，`## Related` 给出链。**每页 ≥2 条出链**。对比对象必须都能溯源到 raw 语料。

### 4.3 Wikilinks

- 格式：`[[path/slug|可选别名]]`，路径相对 `knowledge/wiki/`，不含 `.md` 后缀，如 `[[concepts/hybrid-search|混合检索]]`、`[[summaries/<doc-slug>]]`。
- 文件名一律小写连字符（lowercase-hyphenated）。
- `index.md` 的登记行也用同一 wikilink 格式（这是 lint 对齐检查的依据）。

### 4.4 溯源（provenance）——本项目特有扩展

- **summary 页**：`source_refs` 到 **section 级**（`doc_id#Section Name`），由编译脚本从"wiki 保留的小节 ↔ raw 小节标题"自动匹配生成；匹配失败的节回退 `#intro`。
- **concept / comparison 页**：跨源综合不做 section 级自动锚定，`source_refs` 到 **doc 级**（无 `#`，展开时取该 doc 全部 chunks）。跨源要点段尾可加 `^[raw/<doc_id>]` 溯源标记（LLM 深度查负责校验，机械 lint 不查）。
- 精度分层规律：**编译态越抽象，锚定越粗**——这符合"wiki 论断 → raw 证据"的展开方向。

### 4.5 更新策略

- 任何页面被修改必须 bump `updated` 日期。
- 新页面必须登记进 `index.md`（每次编译/ingest 由脚本全量重建 index，保证不漏）。
- 每次操作（compile / ingest / retract / lint）必须向 `log.md` 追加一条。

## 5. 工作流（三操作）

- **Compile / Ingest**（构建期，脚本 `knowledge/scripts/compile_wiki.py`）：
  1. summaries：单源蒸馏（raw → wiki/summaries/，section 级 source_refs）
  2. 规划调用：基于全部 raw 的 title/topic 清单产出概念页与对比页清单（slug / 描述 / 涉及 doc_ids / tags）
  3. concepts & comparisons：逐页跨源综合（喂相关 raw 全文，截断防护）
  4. 重建 `index.md` + 追加 `log.md`
  增长期触发：人工审查通过新源后手动执行（human-in-the-loop 限频，不做定时任务）。
- **Query**（运行时，单元 2 实现）：wiki 页进 BM25/向量索引 → 命中后按 `source_refs` 确定性展开到 raw chunks → 返回"论断 + 证据"。**LLM 永远不直接碰索引层**——LLM 只碰 md，索引同步由代码负责。
- **Lint**（发布门槛，脚本 `knowledge/scripts/lint_wiki.py`）：机械三查见 §6；ingest 流程每次附带执行，不过即终止。

## 6. Lint 规则（机械三查，零 API 成本）

1. **死链**：所有 wiki 页（含 index.md）中的 `[[path]]` 必须存在对应文件。
2. **孤儿页**：`wiki/summaries|concepts|comparisons/` 下每个 .md 必须在 `index.md` 恰好登记一次。
3. **index 一致性**：`index.md` 中的每条 wikilink 目标文件存在，且无重复登记。

分级：以上为机械级（脚本即可查）；**LLM 深度查**（页间矛盾 / 过时声明 / 缺页）需要跨页推理，作为 ingest 的 `--deep-lint` 可选步骤引入（单元 3），默认关闭。

## 7. 安全网

- wiki 层全部 md 由 git 管理：LLM 写坏可 revert，人工可直接改后跑 lint 校验。
- "LLM 全权维护"指**人不写 wiki**，不是没人管得住它：schema 约束 + lint 门槛 + git 历史 + 人工审查入库，四重兜底。
