<div align="center">

# Content Generator Agent

**多模态教学内容生成工具：给一个主题，产出可学、可听、可发、可导出的教学资源。**

![FastAPI](https://img.shields.io/badge/FastAPI-009485?style=flat-square&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square)
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)

</div>

## 它是什么

一个可以独立运行的内容生成工具，也可以作为内容生成组件嵌入更大的教育系统。

输入主题和学习要求，它会完成大纲规划、分章写作、配图、排版和音频合成，输出五种教学资源。互动讲义还带答题与学习记录：学生的作答会持久化，学习摘要和薄弱点分析可以继续被其它系统消费。

一句话：**把“做一个教学资源”从几天的重复劳动，变成一次可配置的生成任务。**

<img src="docs/assets/interactive-lesson.png" width="820" alt="互动讲义章节、讲解与答题"/>

*互动讲义：章节导航、分章讲解与互动题*

## 能生成什么

| 类型 | 产物 | 典型用途 |
|---|---|---|
| 互动讲义 | 单文件 HTML，分章节讲解 + 单选/多选/短答/情境讨论 | 学生自学、课后练习 |
| 播客 | 多人对谈脚本 + 按角色合成的 MP3 | 通勤听、课程音频 |
| 图文推文 | 封面、章节配图、公众号风格长文 | 知识分享、内容推送 |
| 讲义 | 分章节图文，支持 PDF / Markdown / HTML | 备课、系统学习材料 |
| 幻灯片 | 逐页内容与配图，支持 Slide JSON / PDF | 课堂演示、分享 |

互动讲义不是静态页面。学生答题、写短答、点提示都会产生学习事件，事件落库后可以查询、汇总，也可以导出成带答题记录的离线讲义。

## 怎么用

### 作为独立工具

打开工作台，选择内容类型，填写主题和生成要求，生成完成后在右侧预览，按需导出。历史记录里可以找回之前的任务，失败的图片或音频可以单独重试。

### 作为 HTTP API

```bash
curl -X POST http://localhost:8000/api/content-generation/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "interactive_html",
    "topic": "提示工程中的少样本示例",
    "user_prompt": "面向零基础学员，用 4 个章节讲解，并加入选择题和反思题。",
    "generation_options": { "difficulty": "introductory", "max_section_count": 4 }
  }'
```

返回 `task_id` 后可以轮询任务、读取预览、导出文件；互动讲义还可以创建学习会话、提交事件、获取摘要。

### 嵌入更大的教育系统

生成请求支持 `X-Platform-User-Id`、`X-Platform-Session-Id` 等上下文，以及 `knowledge_base_ids` 知识库参数；学习事件与摘要通过独立接口暴露，外部系统可以按自己的节奏消费。内容类型由注册表管理，新增一种内容不需要改工作流主干。

## 它是怎么工作的

```mermaid
flowchart LR
    A[主题与要求] --> B[检索 / 资料准备]
    B --> C[规划大纲]
    C --> D[分章并行生成]
    D --> E[校验与修复]
    E --> F[渲染与组装]
    F --> G[预览 / 导出]
```

- 单文档类型（推文、播客）一次成文；多章节类型（讲义、幻灯片、互动讲义）按章节并行生成。
- 每完成一章立即落库并推送到前端，不必等整篇结束。
- 单个章节或资源失败会先修复、再降级或记为失败资源，其它部分继续生成。
- 任务中断后重启会被标记，已生成的内容和预览保留。

## 学习记录

互动讲义的学习数据是这条工具链里最特别的一部分：

1. 学生答题或求助，前端提交学习事件；
2. 事件写入数据库，按章节、互动、事件类型保存；
3. 学习摘要计算完成度、正确率、求助次数、薄弱概念和复习章节；
4. adaptive brief 把薄弱点整理成新的生成要求，一键生成复习讲义。

<img src="docs/assets/adaptive-review.png" width="820" alt="学习摘要与针对薄弱点再生成"/>

*学习摘要：完成度、正确率、薄弱概念与复习入口*

这些数据也可以通过接口被外部系统读取，用于学习分析、推荐或画像更新。当前的 brief 由规则和模板生成，结果可解释、可测试，接口按 LLM 版本设计。

## 模块化

项目按职责拆分，各模块可以单独使用，也可以组合成完整链路：

- **内容类型注册表**：每种内容有独立的大纲约束、生成器、校验器和导出格式。
- **Provider 工厂**：文本、图片、语音可分别切换服务商，不绑死单一模型。
- **本地知识库**：BM25 + 向量混合检索、动态 ingest/retract、多目标 qrels 评测体系（见下方「知识库引擎」）。
- **任务与资源仓储**：任务、产物、资源、引用分表存储，失败资源可单独重试。
- **学习服务**：会话、事件、摘要、brief 独立于生成流程，可按需启用。
- **导出器**：PDF、Markdown、HTML、Slide JSON、图片资源、音频各自独立。

## 🗄️ 知识库引擎（Knowledge Base）

生成链路的检索层完全自建：**自备语料、本地索引、四路检索、自带评测**，不依赖外部知识库服务。

### 快速开始

**1. 准备语料**：把你的 markdown 文档放入 `knowledge/raw/`，每篇带 frontmatter：

```markdown
---
title: 文档标题
topic: 主题标签（如 agents / retrieval，用于路由与分层统计）
source_url: 原始出处（可选）
---

正文……
```

**2. 建库**（切分 800/120、结构垃圾过滤、向量化、BM25 索引一次完成）：

先执行 `uv sync --group dev` 安装项目及检索依赖。使用默认本地 BGE-M3 时执行 `uv sync --extra kb-local --group dev`，并按下方模型说明下载模型。使用百炼向量服务时设置系统环境变量 `KB_EMBEDDER=bailian` 和 `CONTENT_GENERATOR_BAILIAN_API_KEY`，无需安装本地模型依赖。

```bash
python -m knowledge.scripts.build_kb --rebuild
```

**3. 检索**（四策略统一入口，CPU/GPU 均可运行）：

```python
import sys; sys.path.insert(0, ".")
from knowledge.engine import kb_engine as kb

chunks = kb.load_all_chunks()          # 全量 chunk（含元数据）
bm25 = kb.load_bm25_index(chunks)      # jieba 分词 BM25
embedder = kb.get_embedder()           # 默认本地 BGE-M3，可用 KB_EMBEDDER=bailian 切云端

results = kb.search("hybrid", "如何设计多智能体的任务编排", chunks, bm25, embedder, top_k=10)
# method: keyword | vector | hybrid | router（查询感知加权融合）
for chunk, score in results:
    print(f"{score:.3f}  {chunk.doc_id}::{chunk.section}")
```

**4. 动态增删**（human-in-the-loop：人工审查后手动执行，lint 三查不过即中止）：

```bash
python -m knowledge.scripts.ingest --file knowledge/raw/new-doc.md   # 增量入库（秒级）
python -m knowledge.scripts.ingest --retract <doc_id>                # 撤除（raw 移入 retracted/ 可逆）
```

### 本地模型备忘

| 模型 | 用途 | 获取与配置 |
|---|---|---|
| `BAAI/bge-m3`（~2.3GB） | 默认稠密向量（1024 维，8K 上下文） | `modelscope download --model BAAI/bge-m3 --local_dir .models/bge-m3`；路径自动探测 `.models/bge-m3`，或用 `BGE_M3_PATH` 指定 |
| `BAAI/bge-reranker-v2-m3`（可选） | 交叉编码精排（实验结论：对任务级长 query 不建议启用，见评测报告） | 下载到 `.models/bge-reranker-v2-m3`，或 `BGE_RERANKER_PATH` 指定 |

环境变量：`KB_EMBEDDER=bge_m3|bailian`（向量后端，bailian 回滚到云端 embedding）、`KB_FILTER_JUNK=1`（结构垃圾过滤开关，默认开）。

### 评测体系（Evaluation）

仓库自带完整的检索评测管线（脚本在 `knowledge/scripts/`），**评测数据不对你的语料预置——对自建语料跑一遍管线即可产出**：

1. **query 快照**：从任务画像采样生成多措辞层级的评测 query（`gen_v8_queries.py`）
2. **多目标 qrels**：BM25 候选池 + LLM 盲判扩容（TREC pooling 惯例），源 GT 与判 2 扩容构成 strict/lenient 双口径（`build_qrels.py`）
3. **双口径打分**：doc/chunk recall@k、MRR，全部带 Wilson 95% CI，按 slice 分层（`bench_v8.py`）

本库语料上的实测结论（方法与口径详见 [评测报告](knowledge/eval/results/report-v8-final.md)）：

| 臂 | docR@10 | strict cR@10 |
|---|---|---|
| router（加权融合） | **71.5%** [63–79] | 42.2% [32–52] |
| vector | 67.7% [59–75] | **42.2%** [32–52] |
| hybrid | 68.5% [60–76] | 41.1% [32–51] |
| keyword（BM25） | 31.5% [24–40] | 27.8% [20–38] |

同一引擎换 query 分布（合成问句 vs 任务级拼接）实测相差 **12pp**——query 形态是比索引调优更大的杠杆；交叉编码器精排与 wiki 检索通道均经实验裁决未进主链路（负结果与机制诊断在报告中留档）。

### 知识演化层（LLM Wiki）

`knowledge/WIKI_SCHEMA.md` 定义了 Karpathy LLM Wiki 模式的领域实例化（raw 不可变 / 编译层 LLM 维护 / schema 约束三方）。`compile_wiki.py` 生成概念蒸馏页与双链引用图，定位是 **citation 导航与知识地图**，不承担检索召回（大实验裁决详见评测报告）。

### 语料与数据合规

- **知识内容零进仓库**：语料、评测 query、qrels 等衍生的评测数据均只存本地（`.gitignore` 已固化），仓库只交付"组织你自己的语料"的能力。
- **抓取工具保持中性**：不内置任何目标站点清单，目标 URL 由使用者自行提供。

## 快速开始

环境要求：Python 3.11+，Node.js 20+。

```bash
git clone https://github.com/Weilan0811/content-generator-agent.git
cd content-generator-agent

python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

uv sync --group dev

# 配置环境变量
cp .env.example .env            # Windows: copy .env.example .env

# 启动后端
python -m uvicorn app.main:app --app-dir backend --port 8000

# 启动前端
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`。

### 配置 `.env`

默认 `stub` 模式不调用外部服务，也不需要 Key，适合先跑通页面和流程。要看真实生成效果，把模式改为 `real`，并填好对应服务商的 Key：

```dotenv
CONTENT_GENERATOR_PROVIDER_MODE=real

# 文本模型（所有内容类型都需要）
CONTENT_GENERATOR_TEXT_PROVIDER=bailian
CONTENT_GENERATOR_TEXT_MODEL=qwen3.5-flash
CONTENT_GENERATOR_BAILIAN_API_KEY=sk-...

# 图片生成（讲义、幻灯片、图文推文需要）
CONTENT_GENERATOR_IMAGE_PROVIDER=apimart
CONTENT_GENERATOR_APIMART_API_KEY=sk-...

# 语音合成（播客需要）
CONTENT_GENERATOR_TTS_PROVIDER=bailian
CONTENT_GENERATOR_TTS_MODEL=qwen3-tts-flash

# 本地知识库检索（可选，默认关闭；开启见下方「知识库引擎」章节）
# CONTENT_GENERATOR_KB_PROVIDER=local
```

- 文本 provider 可选 `bailian` / `deepseek`，图片 provider 可选 `apimart` / `bailian`。
- 播客复用 `CONTENT_GENERATOR_BAILIAN_API_KEY`；互动讲义只需要文本能力。
- 知识库检索默认关闭；要接入自托管检索，设置 `CONTENT_GENERATOR_KB_PROVIDER=local`。
- 数据库默认是仓库根目录下的 SQLite，首次启动自动建表；换 MySQL 时配置 `CONTENT_GENERATOR_DATABASE_URL` 或 `DB_*` 分组。
- 改完 `.env` 后重启后端生效。完整配置见 [.env.example](.env.example)。

## 项目结构

```
backend/app/
  api/            生成任务、资源重试、导出、学习会话
  content_types/  内容类型注册与各自的生成/校验规则
  workflows/      规划、并行生成、校验、渲染、组装
  services/       LLM/图片/TTS、任务与学习数据仓储、导出
  renderers/      幻灯片、互动讲义、离线讲义
  models/         任务、产物、资源、学习事件
frontend/         生成工作台、预览、历史记录、学习摘要
docs/             架构、互动讲义、学习闭环、集成契约、ADR
```

## 限制

知识库检索当前关闭（请求字段和检索接口已保留）；幻灯片版式与自动配图仍在打磨。

## 文档

| 文档 | 内容 |
|---|---|
| [docs/architecture.md](docs/architecture.md) | 分层、工作流、内容类型注册、存储与迁移 |
| [docs/interactive-lesson.md](docs/interactive-lesson.md) | 互动讲义从大纲到运行时、导出与离线讲义的契约 |
| [docs/learning-loop.md](docs/learning-loop.md) | 学习会话、事件、摘要、adaptive brief 的字段与算法 |
| [docs/platform-contract.md](docs/platform-contract.md) | 对外集成：请求头、知识库、学习数据与扩展字段 |
| [docs/adr.md](docs/adr.md) | 关键取舍：Composer、离线讲义、规则 brief 先行 |
| [docs/demo.md](docs/demo.md) | 演示录屏脚本与复现步骤 |
| [backend/README.md](backend/README.md) | 后端工程细节、接口与持久化 |
