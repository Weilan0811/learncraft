# Backend 开发注意事项

本文档记录后端开发、调试、测试、配置和常见问题。

## 1. 本地开发模式

建议本地优先使用 stub 模式跑通闭环：

```env
CONTENT_GENERATOR_PROVIDER_MODE=stub
CONTENT_GENERATOR_DATABASE_URL=sqlite:///./content_generator.db
CONTENT_GENERATOR_STORAGE_ROOT=storage
```

stub 模式下：

- RAG 使用 stub 检索结果。
- LLM 使用 deterministic fallback 或本地 fallback 逻辑。
- 图片生成本地 SVG 占位图。
- TTS 生成本地 stub 音频。
- 资源保存到本地 `storage/`。
- `CONTENT_GENERATOR_ALLOW_FALLBACK` 可设为 `true` 方便 demo；真实质量评估建议保持 `false`，让 provider 和 schema 错误暴露出来。

## 2. 真实服务模式

接入真实 provider 时配置：

```env
CONTENT_GENERATOR_PROVIDER_MODE=real
CONTENT_GENERATOR_BAILIAN_API_KEY=...
CONTENT_GENERATOR_BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CONTENT_GENERATOR_BAILIAN_TTS_BASE_URL=https://dashscope.aliyuncs.com
CONTENT_GENERATOR_APIMART_API_KEY=...
CONTENT_GENERATOR_APIMART_BASE_URL=https://api.apimart.ai/v1
CONTENT_GENERATOR_KB_API_BASE_URL=...
CONTENT_GENERATOR_KB_API_KEY=...
```

常用配置：

| 环境变量 | 说明 |
|---|---|
| `CONTENT_GENERATOR_PROVIDER_MODE` | `stub` 或 `real`。 |
| `CONTENT_GENERATOR_TEXT_PROVIDER` | 文本模型 provider，当前默认 `bailian`。 |
| `CONTENT_GENERATOR_TEXT_MODEL` | 文本模型名称，当前默认 `qwen3.5-flash`。 |
| `CONTENT_GENERATOR_IMAGE_PROVIDER` | 图片 provider，当前默认 `apimart`。 |
| `CONTENT_GENERATOR_IMAGE_MODEL` | 图片模型名称，当前默认 `gpt-image-2`。 |
| `CONTENT_GENERATOR_IMAGE_RESOLUTION` | 图片分辨率，`1k` / `2k` / `4k`。 |
| `CONTENT_GENERATOR_TTS_PROVIDER` | TTS provider，当前默认 `bailian`。 |
| `CONTENT_GENERATOR_TTS_MODEL` | TTS 模型名称，当前默认 `qwen3-tts-instruct-flash`。 |
| `CONTENT_GENERATOR_TTS_PERSON1_VOICE` | 播客 `Person1` 音色，当前固定为 `Ethan`。 |
| `CONTENT_GENERATOR_TTS_PERSON2_VOICE` | 播客 `Person2` 音色，当前固定为 `Cherry`。 |
| `CONTENT_GENERATOR_TTS_OUTPUT_FORMAT` | TTS 输出格式，默认 `mp3`。 |
| `CONTENT_GENERATOR_BAILIAN_TTS_BASE_URL` | 百炼 TTS DashScope base URL。 |
| `CONTENT_GENERATOR_PODCAST_SEGMENT_MAX_RETRIES` | 播客单段 TTS 失败后的重试次数。 |
| `CONTENT_GENERATOR_PODCAST_SEGMENT_RETRY_DELAY_SECONDS` | 播客单段 TTS retry 前等待秒数。 |
| `CONTENT_GENERATOR_ALLOW_FALLBACK` | 请求未显式设置 `generation_options.allow_fallback` 时的默认 fallback 策略。 |
| `CONTENT_GENERATOR_GENERATION_UNIT_CONCURRENCY` | unit-loop 中单元批处理并发数，默认 `3`。 |
| `CONTENT_GENERATOR_IMAGE_GENERATION_CONCURRENCY` | social post 图片 slot 并发数，默认 `3`。 |
| `CONTENT_GENERATOR_TTS_GENERATION_CONCURRENCY` | podcast TTS segment 并发数，默认 `4`。 |
| `CONTENT_GENERATOR_PROVIDER_RATE_LIMIT_BACKOFF_SECONDS` | provider rate limit 场景预留 backoff 秒数。 |
| `CONTENT_GENERATOR_REQUEST_TIMEOUT_SECONDS` | provider 请求超时。 |
| `CONTENT_GENERATOR_MAX_RETRIES` | provider 重试次数。 |
| `CONTENT_GENERATOR_KB_RETRIEVAL_TOP_K` | 知识库检索 top_k。 |
| `CONTENT_GENERATOR_KB_MAX_CHARS_PER_ITEM` | 单条检索结果最大字符数。 |
| `CONTENT_GENERATOR_KB_REQUEST_TIMEOUT_SECONDS` | 知识库检索请求超时。 |

## 3. 数据库配置

本地 SQLite：

```env
CONTENT_GENERATOR_DATABASE_URL=sqlite:///./content_generator.db
```

MySQL：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=root
DB_PASSWORD=...
DB_DATABASE=future_learning
```

也可以直接使用：

```env
CONTENT_GENERATOR_DATABASE_URL=mysql+pymysql://root:password@localhost:3306/future_learning
```

迁移命令：

```bash
cd backend
alembic upgrade head
```

当前迁移文件：

| revision | 说明 |
|---|---|
| `20260508_0001` | 创建 `content_generation_task` 表。 |
| `20260511_0002` | 增加 task logs。 |
| `20260511_0003` | 增加 outline、partial render model、unit results、render units、stream events。 |
| `20260624_0004` | 增加 artifact/reference/asset 表和平台关联字段，并迁移历史大 JSON 产物。 |
| `20260624_0005` | 增加 event/metric 观测表。 |

SQLite 本地开发会自动建表，并补齐部分缺失列；生产数据库建议使用 Alembic。

当前产品态可信数据源：

| 表 | 用途 |
|---|---|
| `content_generation_task` | 轻量任务状态、平台关联、进度、preview URL 和错误摘要。 |
| `content_generation_artifact` | outline、unit spec、content spec、unit render、partial/final render。 |
| `content_generation_reference` | planning 和 unit spec 阶段引用的知识库 chunks。 |
| `content_generation_event` | 前端事件流，append-only。 |
| `content_generation_metric` | 节点耗时、provider token、retry、fallback 原因。 |

旧字段仍保留兼容读取，但新增产品接口优先读取 artifact/reference/event/metric 表。

## 4. 资源存储

默认使用本地文件存储：

```text
storage/
├── files/              # 真实文件
├── manifest.json       # asset metadata
├── debug_workflow/     # workflow 调试状态
└── logs/               # 日志目录预留
```

资源访问方式：

```text
GET /api/assets/{asset_id}
GET /api/assets/{asset_id}/download
```

开发约定：

1. 生成文件统一通过 `LocalStorageService` 保存。
2. 不在业务节点中手写文件路径和下载 URL。
3. asset metadata 需要包含 `task_id`、`kind`、`content_type` 等必要信息。
4. 图片、HTML、JSON、ZIP、音频等文件都应通过 asset 接口访问。
5. `interactive_html` 离线讲义中的服务端图片资源会在 `InteractiveHtmlStaticHandoutRenderer` 中尝试转成 data URL 内联，便于离线查看。
6. 并发生成时多个 service 实例可能同时写入 `manifest.json`，`LocalStorageService` 已按 manifest 路径加进程内锁；跨进程部署时建议迁移到对象存储或数据库 asset 表。

## 5. 测试

运行全部测试：

```bash
pytest -q
```

常用测试：

```bash
# API 基础测试
pytest tests/test_api.py -q

# 任务持久化测试
pytest tests/test_task_persistence.py -q

# workflow 结构测试
pytest tests/test_workflow_structure.py -q

# workflow 日志测试
pytest tests/test_workflow_logs.py -q

# 单元级流式预览测试
pytest tests/test_unit_streaming.py -q

# Task 7 并发策略与 graph 并发接入测试
pytest tests/test_parallel_units.py tests/test_social_post_renderer.py tests/test_podcast_renderer.py -q

# interactive_html prompt / renderer / validator / handout
pytest tests/test_interactive_html_prompts.py tests/test_interactive_html_renderer.py tests/test_interactive_html_validator.py tests/test_interactive_html_handout.py -q

# social_post schema / prompt / renderer / validator
pytest tests/test_social_post_schema.py tests/test_social_post_prompts.py tests/test_social_post_renderer.py tests/test_social_post_validator.py -q

# podcast schema / prompt / renderer / validator / TTS
pytest tests/test_tts_service.py tests/test_podcast_renderer.py tests/test_podcast_schema.py tests/test_podcast_validator.py tests/test_podcast_prompts.py tests/test_podcast_parser.py -q

# 调试 slide workflow，打印节点日志
pytest tests/test_workflow_debug.py::test_slides -q -s -p no:cacheprovider
```

并发脚本验证：

```bash
python scripts/test_parallel_image_generation.py
python scripts/test_parallel_tts_generation.py
python scripts/test_unit_batching.py
python scripts/test_parallel_unit_pipeline.py
```

脚本输出 JSON 到 `backend/scripts/concurrency_test_outputs/`，用于确认图片 slot、TTS segment、unit batching 和 graph 级 unit pipeline 是否有限并发且顺序稳定。

## 6. Schema 导出

前后端字段对齐使用 JSON Schema：

```bash
python scripts/export_json_schema.py
```

导出目录：

```text
schema_exports/
```

新增或修改 Pydantic schema 后，需要重新导出，并同步前端类型。

当前已在代码中引入但需要确认导出的 interactive_html 相关 schema：

- `InteractiveHtmlSectionSpec`
- `InteractiveHtmlSpec`
- `InteractiveHtmlRenderModel`
- `InteractiveHtmlRenderedUnit`
- `InteractiveHtmlRenderBlockRef`
- `InteractionRenderRef`
- `InteractiveHtmlCourseStyleGuide`

如果 `schema_exports/` 中缺少上述文件，需要更新 `scripts/export_json_schema.py` 的导出列表。

## 7. Prompt 开发约定

Prompt 路径：

```text
app/prompts/
├── planner/
├── generator/
└── reviewer/
```

开发约定：

1. prompt 输出必须绑定明确的 Pydantic schema。
2. prompt 中需要说明字段约束、引用要求、长度要求和 renderer 契约。
3. real 模式下 LLM 输出必须经过 `generate_structured(...)`。
4. schema 校验失败时优先走 repair 或 fallback。
5. fallback 结果也必须满足同一套 schema。
6. prompt 修改后补充对应测试，避免字段漂移。

`interactive_html` prompt 的职责边界：

| Prompt | 职责 | 禁止事项 |
|---|---|---|
| `planner/interactive_html_outline.md` | 生成课程内容大纲，只规划 section 学习目标、核心信息、检索 query。 | 不指定 block 类型、互动位置、图片、流程动画、练习题。 |
| `generator/interactive_html_unit_spec.md` | 生成 `InteractiveHtmlSectionSpec`，规划 teaching_flow 和 interaction_specs。 | 禁止输出 HTML、CSS、Markdown 代码块和解释文字。 |
| `generator/interactive_html_unit_render.md` | 生成非互动教学块的 `block_html_map` 和 `css_fragment`。 | 禁止 button、input、textarea、form、data-ih-action、data-interaction-id、script、外链资源和全局 CSS。 |
| `reviewer/interactive_html_render_repair.md` | 修复未通过校验的 `InteractiveHtmlRenderedUnit`。 | 不大幅重写未报错部分，不发明新的 data-ih-action。 |

## 8. Validator 开发约定

Validator 需要覆盖：

| 校验项 | 说明 |
|---|---|
| schema 合法性 | Pydantic 层保证基础字段合法。 |
| 结构闭合 | outline、unit spec、content spec、render model 能对应。 |
| 引用覆盖 | section / slide / article block 能追溯到 chunk。 |
| 元素闭合 | required elements 均已生成或有明确失败状态。 |
| renderer 契约 | spec 字段满足 renderer 的布局和字段要求。 |
| 内容质量 | 标题、正文、摘要、speaker notes、图片说明等不为空。 |
| HTML 安全 | interactive_html 的 HTML fragment 禁止脚本、外链、内联事件和完整页面标签。 |
| CSS 作用域 | interactive_html 的 CSS 必须限制在 `style_scope_id` 下。 |
| Manifest 一致性 | interactive_html 的 DOM 中 `data-block-id`、`data-interaction-id` 必须和 manifest 对齐。 |

Validator 的职责是保护后续 renderer，不把明显不可渲染或质量过低的内容继续向后传递。

`interactive_html_validator.py` 当前拆为三类核心校验：

| 函数 | 输入 | 用途 |
|---|---|---|
| `validate_unit_spec` | `InteractiveHtmlSectionSpec` | 校验教学块、互动规格、题型硬约束。 |
| `validate_explanation_render` | `block_html_map`、`css_fragment` | 校验 LLM 生成的非互动讲解 HTML/CSS。 |
| `validate_rendered_unit` | `InteractiveHtmlRenderedUnit` | 校验最终单元 fragment、CSS、block manifest、interaction manifest。 |
| `sanitize_rendered_unit` | `InteractiveHtmlRenderedUnit` | 清洗 HTML/CSS 后再进入最终校验。 |
| `validate_content` | `InteractiveHtmlSpec` | 校验完整互动课程 spec。 |

## 9. Renderer 开发约定

Renderer 负责：

```text
ContentSpec -> RenderModel
```

约定：

1. 常规 renderer 不调用 LLM，不改变内容语义。
2. `interactive_html` 当前有单元级 composer 例外：`ExplanationHtmlComposer` 会调用 LLM 生成非互动讲解 HTML/CSS。
3. `interactive_html` 的互动控件由 `InteractionTemplateRenderer` 模板生成，不交给 LLM 自由发挥。
4. renderer 可以做布局、安全区、截断和格式转换。
5. renderer 输出必须符合 `app/schemas/render/` 中的 typed schema。
6. slide renderer 输出必须符合前端 `scenekit.slide/v1` 契约。
7. interactive_html renderer 输出必须符合前端 `interactive_html_page` 契约。
8. social_post renderer 输出必须包含 HTML、article JSON 和 preview assets。
9. podcast renderer 输出必须包含分段音频、audio manifest 和完整音频 URL。

`interactive_html` 渲染链路：

```text
InteractiveHtmlSectionSpec
  ↓
InteractionTemplateRenderer.render
  ↓
ExplanationHtmlComposer.compose
  ↓
UnitHtmlAssembler.assemble
  ↓
sanitize_rendered_unit / validate_rendered_unit
  ↓
InteractiveHtmlRenderedUnit
  ↓
InteractiveHtmlRenderer.assemble
  ↓
InteractiveHtmlRenderModel
```

## 10. Exporter 开发约定

Exporter 负责：

```text
RenderModel -> downloadable asset
```

约定：

1. exporter 不重新生成内容。
2. exporter 不修改 render model。
3. exporter 通过 `LocalStorageService` 保存文件。
4. exporter 返回 `ExportResult`。
5. 新增 export_type 时需要更新 `app/schemas/base.py`、`app/workflows/routers.py`、内容类型 profile、API 文档和测试。

当前建议使用的导出组合：

| 内容类型 | 导出类型 |
|---|---|
| `lecture` | `pdf`、`image_assets` |
| `slide_deck` | `slide_json`、`image_assets` |
| `interactive_html` | `html` |
| `social_post` | `html`、`image_assets` |
| `podcast_script` | `markdown`、`audio` |

`interactive_html` 的 `html` 导出行为：

1. 请求必须包含 `export_options.session_id`。
2. `HTMLExporter` 读取任务的 `InteractiveHtmlRenderModel` 和 `InteractiveHtmlSpec`。
3. `get_learning_service().list_events(render_model.lesson_id, session_id)` 获取学习记录。
4. `InteractiveHtmlStaticHandoutRenderer` 把在线课件静态化为离线复习讲义。
5. 输出文件名形如 `{task_id}-offline-handout.html`。

当前注意：`interactive_html` profile 中声明了 `zip`，但 `ExportType` 未包含 `zip`，`get_exporter(...)` 也未接入 ZIP exporter。API 层不能直接提交 `export_type = "zip"`。

## 11. Learning Session 开发约定

互动学习接口位于：

```text
app/api/learning.py
app/schemas/learning.py
app/services/learning_service.py
```

当前接口：

| 接口 | 用途 |
|---|---|
| `POST /api/interactive-lessons/{lesson_id}/sessions` | 创建学习 session。 |
| `POST /api/interactive-lessons/{lesson_id}/sessions/{session_id}/events` | 提交互动学习事件。 |
| `GET /api/interactive-lessons/{lesson_id}/sessions/{session_id}/state` | 查询 session 状态和简单统计。 |

当前实现为 `InMemoryLearningService`：

- session 和 events 保存在进程内字典。
- 服务重启后数据丢失。
- 暂不支持跨实例共享。
- 离线讲义导出依赖 session 仍存在于内存中。

后续生产化需要将 session 和 event 持久化到数据库，并与用户身份、课程任务、班级上下文建立关联。

## 12. 前后端联调注意事项

1. 请求字段必须使用 `generation_options`，旧字段 `options` 会触发 422。
2. slide 页数使用 `generation_options.slide_count`。
3. lecture 章节数使用 `generation_options.section_count`。
4. interactive_html 可以使用 `generation_options.section_count` 表达期望章节数，但当前 request validator 只对 lecture 做强校验；最终 section 数主要由 outline prompt 控制在 4-8 个。
5. 前端展示进度优先读取 `progress.percent` 和 `progress.display_stage`。
6. 生成中预览优先读取 `preview/partial` 或 `units/{unit_id}/preview`。
7. interactive_html 前端渲染需要消费 `html_fragment`、`css_fragment`、`navigation`、`interactions`、`runtime.event_endpoint_template`。
8. interactive_html 在线互动提交到 `/api/interactive-lessons/{lesson_id}/sessions/{session_id}/events`。
9. interactive_html 离线讲义导出前必须先创建 session，并至少确保后端内存中存在该 session。
10. 生成完成后再读取完整 `preview`。
11. 导出文件通过 `export_files` 或 `ExportResult.file_url` 下载。
12. 资源 URL 使用 `/api/assets/{asset_id}/download`。
13. 大纲引用读取 `/api/content-generation/tasks/{task_id}/references`。
14. unit 引用读取 `/api/content-generation/tasks/{task_id}/units/{unit_id}/references`。
15. 阶段产物读取 `/api/content-generation/tasks/{task_id}/artifacts` 或 `/outline`。
16. 观测指标读取 `/api/content-generation/tasks/{task_id}/metrics`。
17. 平台侧继续保持一会话一主产物，生成模块通过 `X-Platform-Log-Id`、`X-Platform-User-Id`、`X-Platform-Session-Id` 保存关联 ID。

## 13. PowerShell API 调用

PowerShell 中不要直接复制 Linux curl 写法：

```bash
curl -X POST http://127.0.0.1:8000/api/content-generation/tasks -H "Content-Type: application/json" -d '{...}'
```

建议使用：

```powershell
$body = @{
  content_type = "interactive_html"
  topic = "生成式 AI 如何理解你的问题？"
  user_prompt = "生成一份互动 HTML 课件"
  knowledge_base_ids = @("default")
  generation_options = @{
    language = "zh-CN"
    audience = "AI 初学者"
    difficulty = "introductory"
    section_count = 5
    allow_fallback = $true
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/content-generation/tasks" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

## 14. 常见问题

### 14.1 422 Unprocessable Entity

常见原因：

- 请求体字段名错误，例如使用了旧字段 `options`。
- `slide_count`、`section_count` 超出范围。
- `content_type` 不在当前 schema 枚举内。
- `export_type` 不在 `ExportType` 枚举内，例如当前提交 `zip` 会失败。
- JSON 嵌套层级或布尔值格式错误。

处理方式：

1. 查看 FastAPI `/docs` 中的 schema。
2. 对照 `ContentGenerationRequest.schema.json`。
3. 确认前端请求体字段与后端 Pydantic schema 一致。

### 14.2 Vite proxy ECONNREFUSED

现象：

```text
http proxy error: /api/content-generation/tasks
connect ECONNREFUSED 127.0.0.1:8000
```

原因：

- 后端没有启动。
- 后端端口不是 8000。
- 前端 proxy 配置和后端地址不一致。

处理方式：

```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 14.3 任务一直 running

检查项：

1. provider 是否超时。
2. 图片生成任务是否轮询过久。
3. interactive_html 的 `ExplanationHtmlComposer` 是否在单元渲染阶段调用 LLM 超时。
4. 数据库是否写入失败。
5. workflow 是否在某个节点抛出未捕获异常。
6. `storage/debug_workflow/{task_id}` 是否保存了最近 state。

### 14.4 interactive_html 单元渲染失败

检查项：

1. `InteractiveHtmlSectionSpec` 是否包含 3-7 个 teaching blocks。
2. 互动 block 的 `interaction_id` 是否能在 `interaction_specs` 中找到。
3. 选择题是否满足正确答案数量和 feedback 约束。
4. LLM 生成的讲解 HTML 是否包含了禁止标签、按钮、输入框或 `data-ih-action`。
5. CSS 是否全部带有 `style_scope_id` 作用域。
6. DOM 中的 `data-block-id`、`data-interaction-id` 是否和 manifest 对齐。
7. `generation_options.allow_fallback` 是否开启。

### 14.5 interactive_html 离线讲义导出失败

检查项：

1. 任务是否已有 `render_model` 和 `content_spec`。
2. `export_type` 是否为 `html`。
3. `export_options.session_id` 是否存在且属于 `render_model.lesson_id`。
4. 后端服务是否重启过；当前 learning session 为 in-memory。
5. `LocalStorageService` 是否有写入权限。

### 14.6 导出失败

检查项：

1. 任务是否已有 `render_model`。
2. `export_type` 是否适配当前 `content_type`。
3. `get_exporter(...)` 是否支持该 export type。
4. `LocalStorageService` 是否有写入权限。

### 14.7 图片资源无法访问

检查项：

1. `storage/manifest.json` 是否存在对应 asset。
2. `storage/files/` 下是否存在真实文件。
3. `asset_public_base_url` 是否为 `/api/assets`。
4. 前端是否访问了 `/download` 路径。

### 14.8 fallback 行为和预期不一致

检查项：

1. 请求体是否显式传了 `generation_options.allow_fallback`。
2. `.env` 中 `CONTENT_GENERATOR_ALLOW_FALLBACK` 的值。
3. stub 模式下 fallback 总是允许，用于本地闭环。
4. real 模式下默认不 fallback，除非 `.env` 默认开启或请求显式开启。

### 14.9 并发生成速度没有变化

检查项：

1. `.env` 中 `CONTENT_GENERATOR_GENERATION_UNIT_CONCURRENCY`、`CONTENT_GENERATOR_IMAGE_GENERATION_CONCURRENCY`、`CONTENT_GENERATOR_TTS_GENERATION_CONCURRENCY` 是否大于 1。
2. provider 是否有更严格的限流，导致并发请求被排队或重试。
3. 任务是否只有一个 unit、一个图片 slot 或一个 TTS segment。
4. `GET /metrics` 中节点耗时和 provider retry 是否异常升高。

## 15. 后续优先事项

1. 完成真实 PDF exporter。
2. 完成 slide PPTX exporter 或明确交由前端导出。
3. 强化 slide renderer 的稳定布局与文本安全区。
4. 将 social_post reviewer / repair 流程接入 direct workflow。
5. 增加真实 KB 检索的端到端测试。
6. 根据线上 provider 限流情况调整默认并发和 backoff 策略。
7. 增加 podcast 真实 TTS 任务的慢任务回归测试。
8. 完善前端类型自动生成和 schema drift 检测。
9. 将 interactive_html learning session / event 从 in-memory 迁移到数据库。
10. 补齐 interactive_html ZIP exporter 或移除 profile 中尚未可用的 `zip` 声明。
11. 为 interactive_html 的 render repair prompt 接入真实 LLM 修复链路，并补充失败样例回归测试。
