# Content Generator Agent Backend

本目录是内容生成 Agent 的后端模块，负责接收内容生成请求，调用知识库检索、LLM 结构化生成、图片生成、内容渲染与导出服务，最终返回前端可预览、可追踪、可导出的内容结果。

后端采用 FastAPI 暴露 HTTP API，使用 LangGraph 编排内容生成 workflow，使用 Pydantic schema 约束请求、状态、spec、render model、导出结果和资源元数据。任务状态通过 SQLModel 持久化到数据库，并支持节点级进度、事件流、局部预览和单元级预览。

## 当前能力概览

| 能力 | 当前状态 | 说明 |
|---|---|---|
| API 服务 | 已具备基础闭环 | 提供任务创建、任务查询、事件查询、完整预览、局部预览、单元预览、导出、资源查询和资源下载接口。 |
| 任务系统 | 已接入持久化 | `PersistentTaskService` 通过 `SQLModelTaskRepository` 保存任务状态、进度、render model、partial render model、unit snapshots、stream events、logs、assets 和 export files。 |
| Workflow 编排 | 已接入 LangGraph | 支持请求标准化、知识库检索、生成模式路由、outline 规划、unit loop、元素生成、校验、渲染和失败路径。 |
| 内容类型 | 支持 `lecture`、`slide_deck`、`social_post`、`podcast_script` | `lecture` 和 `slide_deck` 走 unit-loop workflow；`social_post` 和 `podcast_script` 走 direct workflow。 |
| 内容类型注册 | 已具备 registry 机制 | `app/content_types/` 统一声明生成模式、schema、renderer、generator、元素策略和导出格式。 |
| 检索服务 | 支持 stub 与外部 KB HTTP API | stub 用于本地测试；real 模式调用外部知识库检索服务。 |
| LLM 服务 | 支持 stub 与百炼兼容 OpenAI structured output | real 模式支持 JSON schema 约束、repair、重试、超时和 usage 记录。 |
| 图片服务 | 支持 stub、APIMart、百炼图片生成 | stub 模式生成本地 SVG 占位图；real 模式可生成远程图片并保存为本地 asset。 |
| TTS 服务 | 支持 stub 与百炼 Qwen-TTS | real 模式使用 `qwen3-tts-instruct-flash`，固定 `Person1 -> Ethan`、`Person2 -> Cherry`。 |
| Renderer | 已有 Lecture / Slide / SocialPost / Podcast renderer | lecture 输出阅读预览；slide 输出 `scenekit.slide/v1`；social_post 输出 WeChat article HTML 与 article JSON；podcast 输出脚本、分段音频、manifest 和完整音频。 |
| Exporter | 已有 PDF / Slide JSON / HTML / Image Assets / Markdown / Audio | PDF 当前为占位导出；Slide JSON、HTML、image assets、markdown、audio 已可落盘并返回下载 URL。 |
| Schema 导出 | 已具备 | `scripts/export_json_schema.py` 可将关键 Pydantic schema 导出到 `schema_exports/`，便于前端对齐类型。 |

## 技术栈

- Python 3.11+ / 3.13 兼容方向
- FastAPI：后端 HTTP API
- Pydantic / pydantic-settings：数据模型、配置管理、schema 导出
- SQLModel / SQLAlchemy：任务状态持久化
- Alembic：数据库迁移
- LangGraph：内容生成 workflow 编排
- httpx：LLM、Image provider、TTS provider、外部 KB HTTP 调用
- Local filesystem storage：MVP 本地资源存储

## 目录结构

```text
backend/
├── app/
│   ├── main.py                         # FastAPI 应用入口
│   ├── api/                            # HTTP API：content generation / assets
│   ├── content_types/                  # 内容类型 profile 注册表
│   ├── core/                           # 配置、数据库、日志、异常、调试产物
│   ├── models/                         # SQLModel 数据库模型
│   ├── schemas/                        # Pydantic 数据契约
│   ├── services/                       # 可替换服务层：task / rag / llm / image / storage
│   ├── workflows/                      # LangGraph workflow 与 nodes
│   ├── generators/                     # 内容 spec 生成逻辑
│   ├── renderers/                      # Spec -> RenderModel
│   ├── exporters/                      # RenderModel -> 可下载文件
│   ├── validators/                     # 本地校验器
│   └── prompts/                        # planner / generator / reviewer prompts
├── alembic/                            # 数据库迁移
├── schema_exports/                     # 已导出的 JSON Schema
├── scripts/                            # 工具脚本
└── tests/                              # 单元测试与 workflow 调试测试
```

## 快速启动

```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

本地开发默认建议先使用 stub 模式：

```env
CONTENT_GENERATOR_PROVIDER_MODE=stub
CONTENT_GENERATOR_DATABASE_URL=sqlite:///./content_generator.db
CONTENT_GENERATOR_STORAGE_ROOT=storage
```

接入真实服务时再配置：

```env
CONTENT_GENERATOR_PROVIDER_MODE=real
CONTENT_GENERATOR_BAILIAN_API_KEY=...
CONTENT_GENERATOR_BAILIAN_TTS_BASE_URL=https://dashscope.aliyuncs.com
CONTENT_GENERATOR_APIMART_API_KEY=...
CONTENT_GENERATOR_KB_API_BASE_URL=...
CONTENT_GENERATOR_KB_API_KEY=...
```

## 数据库

任务状态保存在 `content_generation_task` 表中。SQLite 本地开发会自动建表；MySQL 等生产数据库建议使用 Alembic 迁移。

```bash
cd backend
alembic upgrade head
```

## 常用命令

```bash
# 运行测试
pytest -q

# 调试 slide workflow
pytest backend/tests/test_workflow_debug.py::test_slides -q -s -p no:cacheprovider

# 导出前后端对齐用 JSON Schema
python scripts/export_json_schema.py
```

Windows PowerShell 调用 API 时建议使用 `Invoke-RestMethod`，避免把 Linux `curl -H -d` 写法直接复制到 PowerShell 中。

## 核心开发约定

1. 内容生成请求统一进入 `POST /api/content-generation/tasks`，由 `TaskService` 创建任务并触发 LangGraph workflow。
2. 新内容类型需要优先在 `app/content_types/` 注册 profile，再补齐 schema、prompt、generator、renderer、validator 和 exporter。
3. `lecture`、`slide_deck` 采用 `outline -> unit spec -> elements -> content spec -> render model` 的 unit-loop 生成路径。
4. `social_post` 和 `podcast_script` 采用 direct 生成路径，生成完整 spec 后直接校验、渲染与导出。
5. Generator 输出必须经过 Pydantic schema 校验，必要时走 repair 或 deterministic fallback。
6. Validator 负责保护结构闭合、引用覆盖、元素闭合和内容质量，不把明显不可渲染的 spec 继续传给 renderer。
7. Renderer 只负责把 spec 转成前端可消费的 render model；Exporter 只负责把 render model 落盘为文件。
8. workflow 每个关键节点需要更新 `current_node`、`progress`、`stream_events` 或 `logs`，便于前端轮询展示进度。
9. 本地资源统一通过 `LocalStorageService` 写入 `storage/files/`，资源元数据写入 `storage/manifest.json`。
10. 前后端字段契约以 Pydantic schema、OpenAPI 和 `schema_exports/` 为准。

## 文档索引

| 文档 | 内容 |
|---|---|
| `docs/api.md` | 后端 API、请求响应结构、导出接口、前后端联调示例。 |
| `docs/content_generation_workflow.md` | 内容生成 LangGraph workflow、节点职责、状态流转和扩展约定。 |
| `docs/social_post_generation.md` | 微信公众号推文生成链路、schema、prompt、图片规划、渲染导出约定。 |
| `docs/podcast_generation.md` | 播客生成链路、schema、TTS、音频拼接、重试和导出约定。 |
| `docs/development_notes.md` | 环境变量、调试方式、测试、数据库、常见问题和后续开发注意事项。 |

## 当前注意事项

- `pdf` exporter 当前仍是占位 PDF，后续需要接入真实 PDF 渲染。
- `slide_deck` 当前稳定输出 `slide_json`，`pptx` 字段已预留但 exporter router 尚未完成真实实现。
- `lecture` 当前以阅读预览模型为主，打印/PDF 模型仍需继续增强。
- `social_post` 当前只实现微信公众号文章，不覆盖微博、小红书、Twitter/X 等平台。
- `podcast_script` 当前支持双人中文播客脚本和音频生成，不包含背景音乐、混音、降噪和剪辑器能力。
