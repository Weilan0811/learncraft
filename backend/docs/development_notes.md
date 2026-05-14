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
- LLM 使用 deterministic fallback。
- 图片生成本地 SVG 占位图。
- 资源保存到本地 `storage/`。

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
| `CONTENT_GENERATOR_TEXT_MODEL` | 文本模型名称。 |
| `CONTENT_GENERATOR_IMAGE_PROVIDER` | 图片 provider，当前默认 `apimart`。 |
| `CONTENT_GENERATOR_IMAGE_MODEL` | 图片模型名称。 |
| `CONTENT_GENERATOR_IMAGE_RESOLUTION` | 图片分辨率，`1k` / `2k` / `4k`。 |
| `CONTENT_GENERATOR_TTS_PROVIDER` | TTS provider，当前默认 `bailian`。 |
| `CONTENT_GENERATOR_TTS_MODEL` | TTS 模型名称，当前默认 `qwen3-tts-instruct-flash`。 |
| `CONTENT_GENERATOR_TTS_PERSON1_VOICE` | 播客 `Person1` 音色，当前固定为 `Ethan`。 |
| `CONTENT_GENERATOR_TTS_PERSON2_VOICE` | 播客 `Person2` 音色，当前固定为 `Cherry`。 |
| `CONTENT_GENERATOR_TTS_OUTPUT_FORMAT` | TTS 输出格式，默认 `mp3`。 |
| `CONTENT_GENERATOR_BAILIAN_TTS_BASE_URL` | 百炼 TTS DashScope base URL。 |
| `CONTENT_GENERATOR_PODCAST_SEGMENT_MAX_RETRIES` | 播客单段 TTS 失败后的重试次数。 |
| `CONTENT_GENERATOR_PODCAST_SEGMENT_RETRY_DELAY_SECONDS` | 播客单段 TTS retry 前等待秒数。 |
| `CONTENT_GENERATOR_REQUEST_TIMEOUT_SECONDS` | provider 请求超时。 |
| `CONTENT_GENERATOR_MAX_RETRIES` | provider 重试次数。 |
| `CONTENT_GENERATOR_KB_RETRIEVAL_TOP_K` | 知识库检索 top_k。 |
| `CONTENT_GENERATOR_KB_MAX_CHARS_PER_ITEM` | 单条检索结果最大字符数。 |

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

SQLite 本地开发会自动建表，并补齐部分缺失列；生产数据库建议使用 Alembic。

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
4. 图片、HTML、JSON、ZIP 等文件都应通过 asset 接口访问。

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

# social_post schema / prompt / renderer / validator
pytest tests/test_social_post_schema.py tests/test_social_post_prompts.py tests/test_social_post_renderer.py tests/test_social_post_validator.py -q

# podcast schema / prompt / renderer / validator / TTS
pytest tests/test_tts_service.py tests/test_podcast_renderer.py tests/test_podcast_schema.py tests/test_podcast_validator.py tests/test_podcast_prompts.py tests/test_podcast_parser.py -q

# 调试 slide workflow，打印节点日志
pytest tests/test_workflow_debug.py::test_slides -q -s -p no:cacheprovider
```

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

Validator 的职责是保护后续 renderer，不把明显不可渲染或质量过低的内容继续向后传递。

## 9. Renderer 开发约定

Renderer 负责：

```text
ContentSpec -> RenderModel
```

约定：

1. renderer 不调用 LLM。
2. renderer 不改变内容语义。
3. renderer 可以做布局、安全区、截断和格式转换。
4. renderer 输出必须符合 `app/schemas/render/` 中的 typed schema。
5. slide renderer 输出必须符合前端 `scenekit.slide/v1` 契约。
6. social_post renderer 输出必须包含 HTML、article JSON 和 preview assets。
7. podcast renderer 输出必须包含分段音频、audio manifest 和完整音频 URL。

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
| `social_post` | `html`、`image_assets` |
| `podcast_script` | `markdown`、`audio` |

## 11. 前后端联调注意事项

1. 请求字段必须使用 `generation_options`，旧字段 `options` 会触发 422。
2. slide 页数使用 `generation_options.slide_count`。
3. lecture 章节数使用 `generation_options.section_count`。
4. 前端展示进度优先读取 `progress.percent` 和 `progress.display_stage`。
5. 生成中预览优先读取 `preview/partial` 或 `units/{unit_id}/preview`。
6. 生成完成后再读取完整 `preview`。
7. 导出文件通过 `export_files` 或 `ExportResult.file_url` 下载。
8. 资源 URL 使用 `/api/assets/{asset_id}/download`。

## 12. PowerShell API 调用

PowerShell 中不要直接复制 Linux curl 写法：

```bash
curl -X POST http://127.0.0.1:8000/api/content-generation/tasks -H "Content-Type: application/json" -d '{...}'
```

建议使用：

```powershell
$body = @{
  content_type = "slide_deck"
  topic = "人工智能基础"
  user_prompt = "为初学者生成一份课程导入 slides"
  knowledge_base_ids = @("default")
  generation_options = @{
    language = "zh-CN"
    difficulty = "introductory"
    include_images = $true
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/content-generation/tasks" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

## 13. 常见问题

### 13.1 422 Unprocessable Entity

常见原因：

- 请求体字段名错误，例如使用了旧字段 `options`。
- `slide_count`、`section_count` 超出范围。
- `content_type` 不在当前 schema 枚举内。
- JSON 嵌套层级或布尔值格式错误。

处理方式：

1. 查看 FastAPI `/docs` 中的 schema。
2. 对照 `ContentGenerationRequest.schema.json`。
3. 确认前端请求体字段与后端 Pydantic schema 一致。

### 13.2 Vite proxy ECONNREFUSED

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

### 13.3 任务一直 running

检查项：

1. provider 是否超时。
2. 图片生成任务是否轮询过久。
3. 数据库是否写入失败。
4. workflow 是否在某个节点抛出未捕获异常。
5. `storage/debug_workflow/{task_id}` 是否保存了最近 state。

### 13.4 导出失败

检查项：

1. 任务是否已有 `render_model`。
2. `export_type` 是否适配当前 `content_type`。
3. `get_exporter(...)` 是否支持该 export type。
4. `LocalStorageService` 是否有写入权限。

### 13.5 图片资源无法访问

检查项：

1. `storage/manifest.json` 是否存在对应 asset。
2. `storage/files/` 下是否存在真实文件。
3. `asset_public_base_url` 是否为 `/api/assets`。
4. 前端是否访问了 `/download` 路径。

## 14. 后续优先事项

1. 完成真实 PDF exporter。
2. 完成 slide PPTX exporter 或明确交由前端导出。
3. 强化 slide renderer 的稳定布局与文本安全区。
4. 将 social_post reviewer / repair 流程接入 direct workflow。
5. 增加真实 KB 检索的端到端测试。
6. 将 provider 错误、retry、token usage 进一步结构化。
7. 增加 podcast 真实 TTS 任务的慢任务回归测试。
8. 完善前端类型自动生成和 schema drift 检测。
