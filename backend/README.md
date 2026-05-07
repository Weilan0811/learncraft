# Content Generator Agent Backend

本目录是内容生成 Agent 的后端模块，负责接收内容生成请求，基于知识库检索生成大纲，按内容单元生成 lecture 或 slide spec，生成所需多模态元素，渲染预览模型，并导出 PDF、Slide JSON 或资源包。

当前后端采用 FastAPI 暴露 HTTP API，使用 LangGraph 编排内容生成 workflow，并通过 Pydantic schema 统一约束请求、状态、内容 spec、渲染模型、导出结果和资源元数据。

## 当前能力概览

| 能力 | 当前状态 | 说明 |
|---|---|---|
| API 服务 | 已具备基础接口 | 提供任务创建、任务查询、预览、导出、资源查询和资源下载接口。 |
| Workflow 编排 | 已接入 LangGraph StateGraph | 内容生成流程已拆分为 focused node modules，并支持内容类型分支、单元循环、元素并行生成。 |
| 内容类型 | MVP 支持 `lecture`、`slide_deck` | 非 MVP 类型已在基础类型中预留，启用时需要同步补齐 spec、renderer、exporter 和 workflow route。 |
| 检索服务 | 已有 Stub 与 Qdrant 真实服务骨架 | 支持 planning / generation 两阶段检索，真实模式依赖百炼 embedding 与 `langchain_qdrant`。 |
| LLM 服务 | 已有百炼兼容 OpenAI structured output 调用 | 支持 schema 校验、repair prompt、重试、超时和 token usage 记录，workflow 中的真实接入仍需补齐。 |
| 图片服务 | 已有 Stub、APIMart、百炼图片生成服务 | 支持图片任务轮询、远程图片下载、本地落盘和 asset metadata 记录。 |
| 本地资源存储 | 已实现 | 通过 `storage/manifest.json` 管理资源记录，文件保存到 `storage/files/`。 |
| Renderer | 已有 Lecture / Slide renderer 初版 | Lecture renderer 输出阅读/打印预览模型骨架；Slide renderer 输出基础 scene-like JSON。 |
| Exporter | 已有 PDF / Slide JSON / image assets 初版 | PDF 当前为占位 PDF；Slide JSON 可序列化 render model；图片资源包可打包 zip。 |
| 任务系统 | 当前为同步内存执行 | 后续需要迁移为异步任务与持久化任务状态。 |

## 技术栈

- Python 3.11+ / 3.13 兼容方向
- FastAPI：后端 HTTP API
- Pydantic / pydantic-settings：数据模型、配置管理、schema 导出
- LangGraph：内容生成 workflow 编排
- httpx：LLM、Embedding、Image provider HTTP 调用
- Qdrant / langchain_qdrant：向量检索接入
- Local filesystem storage：MVP 本地资源存储


## 目录结构

```text
backend/
├── app/
│   ├── main.py                         # FastAPI 应用入口，注册 CORS、health check 与 API router
│   ├── api/                            # HTTP API 层
│   │   ├── content_generation.py        # 内容生成任务 API：创建、查询、预览、导出
│   │   └── assets.py                    # 资源 API：资源元数据查询、文件下载
│   ├── core/                           # 核心配置、异常、日志、任务状态
│   │   ├── config.py                    # Settings，统一读取 CONTENT_GENERATOR_* 环境变量
│   │   ├── task.py                      # TaskStatus 等任务状态定义
│   │   ├── exceptions.py                # 项目异常定义
│   │   └── logging.py                   # 日志配置入口
│   ├── schemas/                        # Pydantic 数据契约
│   │   ├── base.py                      # 内容类型、元素类型、导出类型、基础 schema
│   │   ├── request.py                   # 内容生成请求与 generation options
│   │   ├── outline.py                   # 大纲 Outline / OutlineUnit
│   │   ├── specs.py                     # LectureSpec / SlideDeckSpec / RequiredElementSpec
│   │   ├── elements.py                  # Text/Image/Mindmap/Chart/Table/Quiz/Citation 等元素 schema
│   │   ├── render.py                    # LectureRenderModel / SlideRenderModel
│   │   ├── export.py                    # ExportRequest / ExportResult
│   │   ├── assets.py                    # AssetRecord / AssetResponse
│   │   ├── task.py                      # TaskResult / PreviewResponse / StoredTask
│   │   └── state.py                     # ContentGenerationState，LangGraph 全局状态
│   ├── services/                       # 可替换服务层
│   │   ├── task_service.py              # 任务创建、预览、导出；当前为 InMemoryTaskService
│   │   ├── rag_service.py               # StubRAGService / QdrantRAGService / BailianEmbeddingService
│   │   ├── llm_service.py               # StubLLMService / BailianLLMService
│   │   ├── image_generation_service.py  # Stub/APIMart/百炼图片生成服务
│   │   ├── storage_service.py           # LocalStorageService，本地文件与 manifest 管理
│   │   ├── asset_service.py             # Local asset 查询服务
│   │   └── citation_service.py          # 引用服务预留
│   ├── workflows/                      # LangGraph workflow 编排
│   │   ├── content_generation_graph.py  # StateGraph 构建与 run_content_generation 入口
│   │   ├── routers.py                   # content_type / export_type 路由
│   │   ├── states.py                    # workflow state 兼容导出
│   │   └── nodes/                       # workflow 节点
│   │       ├── normalize_request_node.py
│   │       ├── retriever_node.py
│   │       ├── planner_node.py
│   │       ├── unit_loop_node.py
│   │       ├── unit_spec_generator_node.py
│   │       ├── element_flow_node.py
│   │       ├── image_element_node.py
│   │       ├── mindmap_element_node.py
│   │       ├── validator_node.py
│   │       ├── assembler_node.py
│   │       ├── renderer_node.py
│   │       ├── finalizer_node.py
│   │       └── helpers.py
│   ├── generators/                     # 单元 spec 生成逻辑
│   │   └── unit_spec_generators.py      # LectureSection / SlideSpecPage deterministic fallback
│   ├── renderers/                      # Spec -> RenderModel
│   │   ├── lecture_renderer.py
│   │   └── slide_renderer.py
│   ├── exporters/                      # RenderModel -> 可下载文件
│   │   ├── pdf_exporter.py
│   │   ├── slide_exporter.py
│   │   ├── asset_exporter.py
│   │   └── markdown_exporter.py
│   └── prompts/                        # 后续真实 LLM 接入使用的 prompt 模板
│       ├── planner/
│       ├── generator/
│       └── reviewer/
├── schema_exports/                     # 已导出的 JSON Schema 文件
└── scripts/
    └── export_json_schema.py           # 导出后端 schema 到 JSON Schema
```

## 核心生成流程

当前主流程入口是：

```python
app.workflows.content_generation_graph.run_content_generation(request, request_id=None)
```

整体流程如下：

```text
POST /api/content-generation/tasks
  ↓
InMemoryTaskService.create_task
  ↓
run_content_generation
  ↓
normalize_request
  ↓
retrieve_for_planning
  ↓
plan_outline
  ↓
validate_outline
  ↓
route_content_type
  ├─ lecture     -> initialize_section_units
  └─ slide_deck  -> initialize_slide_units
  ↓
[unit loop]
  retrieve_for_unit
  generate_unit_spec
  validate_unit_spec
  collect_unit_required_elements
  dispatch_element_generation
    ├─ generate_image_element    并行
    └─ generate_mindmap_element  并行
  merge_unit_elements
  validate_unit
  merge_unit_result
  should_continue_units
  ↓
assemble_content_spec
  ↓
validate_content
  ↓
route_renderer
  ├─ lecture     -> lecture_renderer
  └─ slide_deck  -> slide_renderer
  ↓
finalize_task
```

这个流程包含三个关键结构：

1. **内容类型分支**：`lecture` 和 `slide_deck` 在单元初始化、spec 组装、renderer 阶段走不同路径。
2. **单元循环**：每个 section / slide 作为一个 unit 逐个生成 spec、元素和校验结果。
3. **元素并行生成**：每个 unit 的 image / mindmap 通过 LangGraph `Send` 分发到对应 worker，再合并回全局资产列表。

## API 说明

### 系统健康检查

```http
GET /health
```

返回：

```json
{
  "status": "ok",
  "service": "content-generator-agent"
}
```

### 创建内容生成任务

```http
POST /api/content-generation/tasks
```

请求示例：

```json
{
  "content_type": "slide_deck",
  "topic": "人工智能基础",
  "user_prompt": "为初学者生成一份课程导入 slides",
  "system_prompt": "内容需要清晰、适合教学展示",
  "knowledge_base_ids": ["default"],
  "options": {
    "language": "zh-CN",
    "difficulty": "introductory",
    "style": "educational",
    "include_images": true,
    "include_mindmap": true
  }
}
```

返回 `TaskResult`，包含 `task_id`、`status`、`preview_url`、`export_files` 和 `errors`。

### 查询任务状态

```http
GET /api/content-generation/tasks/{task_id}
```

当前返回内存中的任务结果。后续异步化后，应返回节点级进度、时间戳、结构化错误和可重试状态。

### 获取预览

```http
GET /api/content-generation/tasks/{task_id}/preview
```

返回 `PreviewResponse`，其中包含 `content_type` 与 `render_model`。

### 导出结果

```http
POST /api/content-generation/tasks/{task_id}/export
```

请求示例：

```json
{
  "export_type": "slide_json",
  "export_options": {}
}
```

当前支持的实际 exporter：

| export_type | Exporter | 输出 |
|---|---|---|
| `pdf` | `PDFExporter` | PDF 文件，目前为占位 PDF |
| `slide_json` | `SlideExporter` | Slide render model JSON |
| `image_assets` | `AssetExporter` | 图片资源 zip 包，包含 `manifest.json` |

`pptx`、`markdown`、`html` 已在基础类型中预留，生产使用前需要补齐真实 exporter。

### 资源查询与下载

```http
GET /api/assets/{asset_id}
GET /api/assets/{asset_id}/download
```

资源由 `LocalStorageService` 保存到本地，并在 `storage/manifest.json` 中记录元数据。

## 配置说明

配置集中在 `app/core/config.py`，通过环境变量前缀 `CONTENT_GENERATOR_` 注入。

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `CONTENT_GENERATOR_APP_NAME` | `Content Generator Agent` | FastAPI 应用名称 |
| `CONTENT_GENERATOR_APP_VERSION` | `0.1.0` | 应用版本 |
| `CONTENT_GENERATOR_CORS_ORIGINS` | `http://localhost:5173`, `http://127.0.0.1:5173` | 前端跨域来源 |
| `CONTENT_GENERATOR_STORAGE_BACKEND` | `local` | 存储后端，当前实现 local |
| `CONTENT_GENERATOR_STORAGE_ROOT` | `storage` | 本地存储根目录 |
| `CONTENT_GENERATOR_ASSET_PUBLIC_BASE_URL` | `/api/assets` | 资源公开访问基础路径 |
| `CONTENT_GENERATOR_PROVIDER_MODE` | `stub` | `stub` 使用占位服务；`real` 使用真实 provider |
| `CONTENT_GENERATOR_TEXT_PROVIDER` | `bailian` | 文本模型 provider |
| `CONTENT_GENERATOR_TEXT_MODEL` | `qwen3.5-flash` | 文本模型名称 |
| `CONTENT_GENERATOR_IMAGE_PROVIDER` | `apimart` | 图片模型 provider |
| `CONTENT_GENERATOR_IMAGE_MODEL` | `gpt-image-2` | 图片模型名称 |
| `CONTENT_GENERATOR_EMBEDDING_PROVIDER` | `bailian` | embedding provider |
| `CONTENT_GENERATOR_EMBEDDING_MODEL` | `text-embedding-v3` | embedding 模型 |
| `CONTENT_GENERATOR_APIMART_API_KEY` | `None` | APIMart API Key |
| `CONTENT_GENERATOR_BAILIAN_API_KEY` | `None` | 百炼 API Key |
| `CONTENT_GENERATOR_QDRANT_PATH` | `storage/qdrant_data` | Qdrant 本地数据路径 |
| `CONTENT_GENERATOR_QDRANT_COLLECTION` | `default` | 默认知识库 collection |
| `CONTENT_GENERATOR_RETRIEVAL_TOP_K` | `5` | 检索 top-k |
| `CONTENT_GENERATOR_MAX_RETRIEVAL_CHARS` | `6000` | 单次检索上下文字符上限 |

本地开发可先使用 `CONTENT_GENERATOR_PROVIDER_MODE=stub`，以便绕过真实 LLM、Embedding、图片 provider。

## Schema 导出

`schema_exports/` 中保存了已导出的 JSON Schema，可用于前端类型同步、接口契约校验和文档生成。

重新导出：

```bash
cd backend
python scripts/export_json_schema.py
```

建议后续将 schema 导出接入 CI，在后端 schema 修改后自动更新前端类型，减少手写类型漂移。

## 模块功能说明

### 1. API 层：`app/api/`

`content_generation.py` 负责内容生成任务相关接口：

- 创建任务：`POST /tasks`
- 查询任务：`GET /tasks/{task_id}`
- 获取预览：`GET /tasks/{task_id}/preview`
- 导出文件：`POST /tasks/{task_id}/export`

`assets.py` 负责资源访问：

- 查询资源元数据：`GET /api/assets/{asset_id}`
- 下载资源文件：`GET /api/assets/{asset_id}/download`

### 2. Schema 层：`app/schemas/`

Schema 是当前项目的核心契约层，主要分为：

- 请求契约：`ContentGenerationRequest`、`GenerationOptions`
- 大纲契约：`Outline`、`OutlineUnit`
- 内容规格契约：`LectureSpec`、`SlideDeckSpec`、`LectureSection`、`SlideSpecPage`
- 元素契约：`ImageElement`、`MindmapElement`、`TextElement` 等
- 渲染契约：`LectureRenderModel`、`SlideRenderModel`
- workflow 状态契约：`ContentGenerationState`
- 导出与资源契约：`ExportRequest`、`ExportResult`、`AssetRecord`

后续扩展内容类型时，优先从 schema 层补齐契约，再接入 generator、renderer、exporter 与 workflow route。

### 3. Services 层：`app/services/`

Services 封装外部依赖和可替换基础设施：

- `task_service.py`：当前使用 `InMemoryTaskService` 同步执行 workflow，并将任务结果保存在进程内存。
- `rag_service.py`：提供 stub 检索和 Qdrant 检索。真实检索依赖百炼 embedding 与本地 Qdrant collection。
- `llm_service.py`：提供百炼兼容 OpenAI 的结构化输出调用，支持 JSON schema 校验与 repair。
- `image_generation_service.py`：提供 stub、APIMart、百炼三类图片生成实现。
- `storage_service.py`：提供本地文件存储、manifest 记录、checksum 和下载 URL。
- `asset_service.py`：面向 API 层提供资源查询与文件路径读取。
- `citation_service.py`：引用去重、引用格式化的预留服务。

### 4. Workflow 层：`app/workflows/`

`content_generation_graph.py` 定义完整 LangGraph StateGraph。节点实现拆分到 `nodes/`：

| 节点 | 功能 |
|---|---|
| `normalize_request_node.py` | 标准化用户请求和 options |
| `retriever_node.py` | planning 阶段和 unit 阶段检索 |
| `planner_node.py` | 生成内容大纲；当前仍以 deterministic fallback 为主 |
| `unit_loop_node.py` | 初始化 lecture sections / slide pages，并控制 unit 循环 |
| `unit_spec_generator_node.py` | 针对当前 unit 生成 LectureSection 或 SlideSpecPage |
| `element_flow_node.py` | 收集 required elements，分发并行元素生成，合并元素结果 |
| `image_element_node.py` | 生成图片元素 |
| `mindmap_element_node.py` | 生成思维导图元素 |
| `validator_node.py` | 校验 outline、unit spec、unit result、content spec |
| `assembler_node.py` | 汇总 unit results，组装 ContentSpec |
| `renderer_node.py` | 根据 content_type 路由到 LectureRenderer 或 SlideRenderer |
| `finalizer_node.py` | 标记完成或失败，并整理最终状态 |

### 5. Generators 层：`app/generators/`

`unit_spec_generators.py` 提供当前 deterministic fallback：

- `build_lecture_unit_spec(...)`：基于 `OutlineUnit` 生成 `LectureSection`
- `build_slide_unit_spec(...)`：基于 `OutlineUnit` 生成 `SlideSpecPage`
- `required_elements_for_unit(...)`：为每个 unit 生成 image 与 mindmap 需求声明

后续真实 LLM 接入时，可以保留 fallback，新增 lecture / slide 专用 prompt 与 generator。

### 6. Renderers 层：`app/renderers/`

Renderer 负责将内容 spec 转换为前端可预览、可导出的 render model：

- `LectureRenderer`：将 `LectureSpec` 转换为 `LectureRenderModel`
- `SlideRenderer`：将 `SlideDeckSpec` 转换为 `SlideRenderModel`

当前实现仍偏 MVP 骨架，后续需要补齐目录、引用、阅读模式、打印模式、scene-content-kit page schema、主题、布局和图片渲染。

### 7. Exporters 层：`app/exporters/`

Exporter 负责将 render model 输出为可下载文件：

- `PDFExporter`：生成 PDF 文件，当前为最小占位 PDF。
- `SlideExporter`：序列化 `SlideRenderModel` 为 JSON 文件。
- `AssetExporter`：收集 render model 中引用的图片资源，打包为 zip。
- `MarkdownExporter`：已预留，后续用于 lecture、script 和未来内容类型的 Markdown 导出。

## 进一步开发指南

### P0：完成真实生成闭环

1. **接入真实 Planner**
   - 修改 `backend/app/workflows/nodes/planner_node.py`。
   - 使用 `get_llm_service().generate_structured(...)` 生成 `Outline`。
   - Prompt 使用 `app/prompts/planner/lecture_outline.md` 和 `app/prompts/planner/slide_outline.md`。
   - Planner 输入应包含用户请求、`content_type`、检索结果和 `GenerationOptions`。
   - 输出必须经过 `Outline` schema 校验。
   - 失败时记录 `workflow_errors`，进入 repair 或 fail 路径。
   - 保留 deterministic fallback，用于 provider 不可用、schema repair 失败或本地测试。

2. **接入真实 Unit Spec Generator**
   - 修改 `backend/app/generators/unit_spec_generators.py`。
   - 拆分 lecture 与 slide generator。
   - lecture 输出 `LectureSection`。
   - slide 输出 `SlideSpecPage`。
   - Unit Spec Generator 输入应包含 outline unit、相关检索 chunk、`GenerationOptions` 和 content_type 上下文。
   - 每个 unit spec 应包含 `outline_unit_id`、标题、主体内容、学习目标 / 页面意图、`source_chunk_ids`、`required_elements` 和引用来源信息。
   - slide spec 应补齐 speaker notes、页面结构和所需 image / mindmap 声明。
   - lecture spec 应补齐章节正文、summary、学习目标和所需 image / mindmap 声明。
   - 保留 deterministic fallback，用于 provider 不可用、schema repair 失败或本地测试。

3. **接入真实 Element 生成**
   - 修改 `backend/app/workflows/nodes/element_flow_node.py` 及相关 element worker。
   - 基于 unit spec 中的 `required_elements` 生成真实 image / mindmap。
   - ImageElement 接入 `backend/app/services/image_generation_service.py`，生成真实图片并保存 asset metadata。
   - MindmapElement 先支持 Markdown mindmap spec 生成，后续补充 SVG / PNG asset URL。
   - 复用 LangGraph Send 机制并行分发 element 生成任务。
   - Element 生成结果按 `element_id` 合并回全局 assets、unit results 和 content spec。
   - 记录每个 element 的生成状态、失败原因、retry count、来源 unit 和 source references。
   - 保证 spec 中声明的 required elements 可以被真实生成、追踪和复用。

4. **完善 Validator**
   - 修改 `backend/app/workflows/nodes/validator_node.py`。
   - 增加 outline、unit spec、content spec 的结构闭合校验。
   - 增加引用覆盖校验：每个 section / slide 至少能追溯到相关 chunk。
   - 增加 required element 闭合校验：spec 声明的元素必须生成或有明确失败状态。
   - 增加内容质量校验：标题、正文、summary、speaker notes 不为空，结构符合 content_type。
   - 增加 GenerationOptions 约束校验：生成结果应符合 audience、duration、slide_count、image_style、citation_policy、slide_theme 等配置要求。
   - 增加 repair 路径：schema 合法但质量不足时，回到对应 planner、unit spec generator 或 element generator 修复。
   - 将 validation result 写入 `workflow_errors`、`element_status` 和 `unit_results`。

5. **扩展 GenerationOptions**
   - 修改 `backend/app/schemas/request.py`。
   - 增加 audience、difficulty、duration、slide_count、image_style、citation_policy、pdf_options、slide_theme、language、output_depth 等字段。
   - 按 content_type 做校验：lecture 使用 duration / section / audience / difficulty / output_depth 策略，slide_deck 使用 slide_count / theme / image_style / speaker_notes 策略。
   - 将 `GenerationOptions` 写入 workflow state。
   - Planner、Unit Spec Generator、Element Generator、Validator 和 Renderer 都应从 state 中读取同一份 `GenerationOptions`。
   - 后续前端表单字段应与后端 schema 保持同步，可通过 OpenAPI / JSON Schema 自动生成类型，减少字段漂移。

6. **完成 Renderer MVP**
   - 该阶段 Renderer 的目标是服务前端 preview，优先保证可展示、可对齐、可迭代。
   - 修改 `backend/app/renderers/lecture_renderer.py`，将 `LectureSpec` 转换为前端可消费的 `LectureRenderModel`。
   - `LectureRenderer`：补齐标题、学习目标、目录、章节正文、summary、引用、图片、mindmap、阅读模式和基础打印模式。
   - 修改 `backend/app/renderers/slide_renderer.py`，将 `SlideDeckSpec` 转换为前端可消费的 slide render model。
   - `SlideRenderer`：将 `SlideDeckSpec` 转换为 scene-content-kit page schema 或过渡型 typed slide preview schema，支持标题、正文、图片、mindmap、speaker notes、主题和基础布局。
   - 修改 `backend/app/schemas/render.py`，将当前 dict 型 render model 逐步替换为 typed render model。
   - 与前端 `LectureRenderer`、`SlideRenderer` 对齐字段契约，重点明确 image、mindmap、citation、asset URL、speaker notes 的数据结构。
   - 暂时保留 JSON preview fallback，方便前后端联调和调试。


### P0：任务异步化与持久化

当前 `InMemoryTaskService.create_task(...)` 会同步执行 workflow，请求耗时会随 LLM、检索、图片生成明显增加。后续建议：

1. 新增任务表或轻量持久化层，保存：
   - `task_id`
   - `content_type`
   - `status`
   - `current_node`
   - `progress`
   - `request_payload`
   - `render_snapshot_path`
   - `errors`
   - `created_at` / `updated_at`

2. 使用以下任一方式派发 workflow：
   - FastAPI `BackgroundTasks`：适合单机 MVP。
   - Celery：适合需要成熟队列、重试、监控的部署。
   - Arq：适合 async Python 与 Redis 场景。

3. 查询任务时返回节点级进度：
   - retrieving
   - planning
   - generating unit specs
   - generating elements
   - validating
   - rendering
   - exporting

4. 将 `render_model` 持久化为 snapshot，支持服务重启后继续预览和导出。

### P1：资源、引用与预览能力

1. **资源存储升级**
   - 保留 `LocalStorageService` 作为开发环境默认实现。
   - 新增 OSS / S3-compatible storage service。
   - 增加签名 URL、过期时间、文件元数据与访问权限策略。

2. **CitationService 实现**
   - 对 chunk 引用去重。
   - 保留 source title、page、section、URL、chunk id。
   - 输出 lecture / PDF / slide 可复用的 citation view model。

3. **Mindmap 资源化**
   - 当前 `MindmapElement` 保存 Markdown。
   - 后续增加 SVG / PNG asset URL。
   - PDF 和 Slide 嵌入时直接使用静态资源。

4. **预览可编辑与局部再生成**
   - `PreviewResponse` 增加可编辑版本元数据。
   - 支持 section / slide 级别重新生成。
   - 保存用户编辑 diff 或新版本 render snapshot。

### P1：Slide 与 PDF 导出增强

1. **Slide JSON**
   - 将 `SlidePageModel.page` 从自由 dict 收敛为 scene-content-kit 官方 page schema。
   - 支持 text、image、mindmap、table 的稳定布局。
   - 增加主题、字体、尺寸、缩略图等渲染字段。

2. **PDF**
   - 将 `LectureRenderModel.printable_model` 从 dict 替换为 typed print/PDF model。
   - 覆盖目录、页眉页脚、页边距、分页策略、图片、mindmap 和引用区。

3. **PPTX**
   - 保留 `slide_json` 作为中间格式。
   - 后续新增 `PPTXExporter`，从 scene-content-kit page schema 或统一 slide render model 转换为 PPTX。

### P2：内容类型扩展

基础类型中已预留：

- `social_post`
- `podcast_script`
- `video_script`
- `project_task`
- `quiz_pack`
- `learning_path`

启用新内容类型时，按以下顺序开发：

1. 在 `app/schemas/specs.py` 增加对应 Spec。
2. 在 `ContentSpec` union 中加入新 Spec。
3. 在 `app/workflows/routers.py` 增加 content_type route。
4. 增加对应 unit 初始化和 unit generator。
5. 增加 renderer。
6. 增加 exporter 或映射到已有 exporter。
7. 导出 JSON Schema 并同步前端类型。
8. 增加最小 API 集成测试。

### 暂缓内容

以下能力已预留，但建议在 MVP 数据流稳定后实现：

- ChartElement 与 ECharts option 映射
- TableElement 的 typed schema 与导出契约
- QuizElement 的题型 schema、交互渲染和作答反馈
- Markdown / HTML 导出
- audio / video element union

## 推荐开发顺序

1. 完成真实 Planner LLM 接入。
2. 完成 lecture / slide unit spec LLM generator。
3. 完成 validator 的引用覆盖、内容质量和 repair 路径。
4. 扩展 `GenerationOptions` 并接入前端表单字段。
5. 完成 renderer MVP，保证 preview 可被前端稳定消费。
6. 将任务系统迁移到异步执行和持久化状态。
7. 将 render snapshot 持久化，支持重启后预览与导出。
8. 完善 PDF、Slide JSON、image assets 的导出质量。
9. 增加 schema 自动导出与前端类型生成。
10. 接入 OSS / S3-compatible storage 与签名 URL。
11. 扩展 citation、mindmap 静态资源、局部再生成等 P1 能力。

## 开发约定建议

- 所有跨模块数据结构优先定义在 `app/schemas/`。
- workflow 节点只处理状态转移，不直接写复杂业务逻辑。
- 外部模型、检索、图片、存储能力统一通过 `services/` 封装。
- 新增内容类型时同步更新 schema、generator、renderer、exporter、router、schema_exports 和前端类型。
- 真实 LLM 输出必须经过 Pydantic schema 校验。
- 对耗时任务统一写入 `current_node`、`progress`、`workflow_errors` 和 token / cost metadata。
- 本地开发默认使用 stub provider，集成测试再切换到 real provider。

## 最小测试建议

建议至少补充以下测试：

1. `POST /api/content-generation/tasks` 创建 lecture 任务。
2. `POST /api/content-generation/tasks` 创建 slide_deck 任务。
3. `GET /tasks/{task_id}/preview` 获取 render model。
4. `POST /tasks/{task_id}/export` 导出 PDF。
5. `POST /tasks/{task_id}/export` 导出 Slide JSON。
6. `POST /tasks/{task_id}/export` 导出 image assets。
7. `GET /api/assets/{asset_id}` 查询资源。
8. `GET /api/assets/{asset_id}/download` 下载资源。
9. `provider_mode=stub` 下完整 workflow 不依赖外部服务。
10. `provider_mode=real` 下 LLM 输出 schema repair 生效。

## 当前开发重点总结

当前后端已经具备内容生成 Agent 的分层骨架：API 接收任务，TaskService 调用 LangGraph workflow，workflow 依次完成检索、大纲、单元 spec、元素生成、校验、渲染，最后通过 exporter 输出文件。

下一阶段重点是将 deterministic fallback 替换为真实 LLM 生成链路，并在任务异步化、render snapshot 持久化、renderer 完整化和导出质量上补齐 MVP 闭环。
