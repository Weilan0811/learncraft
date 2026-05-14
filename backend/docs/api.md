# Backend API 文档

本文档描述内容生成后端当前可用的 HTTP API。接口统一由 FastAPI 提供，启动服务后也可以通过 OpenAPI 页面查看：

```text
http://127.0.0.1:8000/docs
```

## 1. 基础信息

默认本地服务地址：

```text
http://127.0.0.1:8000
```

健康检查：

```http
GET /health
```

返回示例：

```json
{
  "status": "ok",
  "service": "content-generator-agent"
}
```

## 2. 内容生成任务

### 2.1 创建任务

```http
POST /api/content-generation/tasks
```

请求体为 `ContentGenerationRequest`。

```json
{
  "content_type": "slide_deck",
  "topic": "人工智能基础",
  "user_prompt": "为初学者生成一份课程导入 slides",
  "system_prompt": "内容需要清晰、适合教学展示",
  "knowledge_base_ids": ["default"],
  "generation_options": {
    "language": "zh-CN",
    "audience": "人工智能初学者",
    "difficulty": "introductory",
    "style": "educational",
    "slide_count": 6,
    "include_images": true,
    "include_mindmap": false,
    "citation_policy": "light",
    "allow_fallback": true
  }
}
```

返回体为 `TaskResult`。

```json
{
  "task_id": "task_xxxxxxxxxxxx",
  "status": "queued",
  "content_type": "slide_deck",
  "preview_url": null,
  "export_files": [],
  "errors": [],
  "current_node": null,
  "progress": {
    "stage": "queued",
    "display_stage": "queued",
    "current_stage": "queued",
    "current_node": null,
    "percent": 0
  },
  "created_at": "2026-05-14T00:00:00Z",
  "updated_at": "2026-05-14T00:00:00Z"
}
```

说明：

- API 创建任务后通过 FastAPI `BackgroundTasks` 执行生成流程。
- 任务状态由数据库持久化保存。
- 前端应通过轮询任务状态、事件和局部预览来展示进度。

### 2.2 查询任务状态

```http
GET /api/content-generation/tasks/{task_id}
```

返回 `TaskResult`，常用字段如下：

| 字段 | 说明 |
|---|---|
| `task_id` | 任务 ID。 |
| `status` | `queued` / `running` / `completed` / `failed`。 |
| `content_type` | 内容类型。 |
| `preview_url` | 完整预览 URL，任务生成完成后可用。 |
| `export_files` | 已导出的文件列表。 |
| `errors` | 任务错误信息。 |
| `current_node` | 当前或最近完成的 workflow node。 |
| `progress` | 节点级进度信息。 |
| `created_at` / `updated_at` | 创建与更新时间。 |

### 2.3 查询任务事件

```http
GET /api/content-generation/tasks/{task_id}/events
```

返回 `TaskEventsResponse`。

```json
{
  "task_id": "task_xxxxxxxxxxxx",
  "events": [
    {
      "event_id": "event_xxxxxxxxxxxx",
      "task_id": "task_xxxxxxxxxxxx",
      "type": "task_started",
      "unit_id": null,
      "payload": {
        "topic": "人工智能基础"
      },
      "created_at": "2026-05-14T00:00:00Z"
    }
  ]
}
```

当前事件类型：

| type | 说明 |
|---|---|
| `task_started` | 任务开始。 |
| `outline_ready` | 大纲生成完成。 |
| `unit_started` | 单元生成开始。 |
| `unit_spec_ready` | 单元 spec 生成完成。 |
| `element_ready` | 图片或 mindmap 元素生成完成。 |
| `unit_render_ready` | 单元渲染片段生成完成。 |
| `direct_spec_ready` | direct 内容 spec 生成完成，当前用于 `social_post` 和 `podcast_script`。 |
| `audio_segment_ready` | 播客分段音频生成完成，payload 包含 segment id、speaker、voice、audio URL、状态和 retry count。 |
| `direct_render_ready` | direct 内容渲染完成，当前用于 `social_post` 和 `podcast_script`。 |
| `task_completed` | 任务完成。 |
| `task_failed` | 任务失败。 |

### 2.4 获取完整预览

```http
GET /api/content-generation/tasks/{task_id}/preview
```

返回 `PreviewResponse`。

```json
{
  "content_type": "slide_deck",
  "render_model": {
    "render_type": "slide_deck",
    "title": "人工智能基础",
    "pages": []
  }
}
```

`render_model` 根据内容类型不同而不同：

| content_type | render_model |
|---|---|
| `lecture` | `LectureRenderModel` |
| `slide_deck` | `SlideRenderModel`，页面结构为 `scenekit.slide/v1` |
| `social_post` | `SocialPostRenderModel`，包含 HTML、article JSON、preview assets |
| `podcast_script` | `PodcastRenderModel`，包含脚本、分段音频、audio manifest 和完整音频 |

### 2.5 获取局部预览

```http
GET /api/content-generation/tasks/{task_id}/preview/partial
```

返回 `PartialPreviewResponse`。

局部预览用于生成过程中的前端增量展示。对于 unit-loop 类型，后端会保存逐单元渲染片段；对于 direct 类型，完成 direct render 后会写入 partial render model。

### 2.6 查询单元列表

```http
GET /api/content-generation/tasks/{task_id}/units
```

返回 `TaskUnitsResponse`。

```json
{
  "task_id": "task_xxxxxxxxxxxx",
  "units": [
    {
      "unit_id": "unit_01",
      "order": 1,
      "content_type": "slide_deck",
      "status": "rendered",
      "render_fragment": {},
      "updated_at": "2026-05-14T00:00:00Z",
      "errors": []
    }
  ]
}
```

### 2.7 获取单元预览

```http
GET /api/content-generation/tasks/{task_id}/units/{unit_id}/preview
```

返回 `UnitPreviewResponse`，用于前端按页或按章节展示生成结果。

### 2.8 导出任务结果

```http
POST /api/content-generation/tasks/{task_id}/export
```

请求体为 `ExportRequest`。

```json
{
  "export_type": "slide_json",
  "export_options": {}
}
```

返回体为 `ExportResult`。

```json
{
  "export_type": "slide_json",
  "file_url": "/api/assets/export_task_xxxxxxxxxxxx_slide_json/download",
  "status": "success",
  "metadata": {
    "task_id": "task_xxxxxxxxxxxx"
  }
}
```

当前建议使用的导出组合：

| content_type | 推荐 export_type | 说明 |
|---|---|---|
| `lecture` | `pdf` | 当前为占位 PDF，用于跑通导出链路。 |
| `lecture` | `image_assets` | 打包任务中生成的图片资源。 |
| `slide_deck` | `slide_json` | 导出前端 PPT/slide renderer 可消费的 JSON。 |
| `slide_deck` | `image_assets` | 打包任务中生成的图片资源。 |
| `social_post` | `html` | 导出微信公众号文章 HTML，同时生成 article JSON asset。 |
| `social_post` | `image_assets` | 打包推文图片资源。 |
| `podcast_script` | `markdown` | 导出播客脚本文本。 |
| `podcast_script` | `audio` | 导出完整音频；如果完整音频不存在则回退 audio manifest。 |

注意：`pptx` 等类型在 schema 或 profile 中已有预留，当前 exporter router 尚未形成完整生产契约。前端联调时优先使用上表中的组合。

## 3. 资源接口

### 3.1 查询资源元数据

```http
GET /api/assets/{asset_id}
```

返回 `AssetResponse`，包含资源 ID、文件名、content type、URL、metadata 等信息。

### 3.2 下载资源文件

```http
GET /api/assets/{asset_id}/download
```

返回文件流。资源文件由 `LocalStorageService` 保存到 `storage/files/`，资源元数据记录在 `storage/manifest.json`。

## 4. 请求字段说明

### 4.1 ContentGenerationRequest

| 字段 | 类型 | 说明 |
|---|---|---|
| `content_type` | string | 内容类型。当前运行支持 `lecture`、`slide_deck`、`social_post`、`podcast_script`。 |
| `topic` | string | 生成主题。 |
| `user_prompt` | string | 用户原始生成要求。 |
| `system_prompt` | string / null | 可选系统约束。 |
| `knowledge_base_ids` | string[] | 检索使用的知识库 ID。 |
| `generation_options` | object | 生成配置。 |

### 4.2 GenerationOptions

| 字段 | 默认值 | 说明 |
|---|---|---|
| `language` | `zh-CN` | 输出语言。 |
| `audience` | null | 目标读者或学习者。 |
| `difficulty` | `introductory` | `introductory` / `intermediate` / `advanced`。 |
| `style` | `educational` | 内容风格。 |
| `duration_minutes` | null | lecture 时长配置。 |
| `section_count` | null | lecture 章节数。 |
| `slide_count` | null | slide 页数。 |
| `max_section_count` | 8 | lecture 最大章节数。 |
| `max_slide_count` | 12 | slide 最大页数。 |
| `output_depth` | `standard` | `brief` / `standard` / `detailed`。 |
| `include_images` | true | 是否生成图片。 |
| `include_charts` | false | 是否生成图表，当前仍处于预留。 |
| `include_mindmap` | false | 是否生成 mindmap。 |
| `image_style` | null | 图片风格提示。 |
| `citation_policy` | `light` | `none` / `light` / `strict`。 |
| `allow_fallback` | false | real provider 失败时是否允许 fallback。 |
| `slide_theme` | null | slide 主题配置。 |
| `speaker_notes` | true | slide 是否生成讲稿备注。 |
| `pdf_options` | `{}` | PDF 导出配置预留。 |

## 5. 前端轮询建议

创建任务后，前端建议按以下顺序轮询：

```text
POST /api/content-generation/tasks
  ↓
GET /api/content-generation/tasks/{task_id}
  ↓
GET /api/content-generation/tasks/{task_id}/events
  ↓
GET /api/content-generation/tasks/{task_id}/preview/partial
  ↓
GET /api/content-generation/tasks/{task_id}/preview
```

推荐策略：

1. `status` 为 `queued` / `running` 时展示 `progress.percent` 和 `progress.display_stage`。
2. `events` 用于展示节点级或单元级生成动态。
3. `preview/partial` 用于边生成边预览。
4. `status=completed` 后请求完整 `preview`。
5. 用户点击导出后再调用 `POST /export`。

## 6. 常见错误

| HTTP 状态 | 场景 |
|---|---|
| 404 | 任务、预览、单元或资源不存在。 |
| 422 | 请求体字段不符合 Pydantic schema，例如 `generation_options` 写成旧字段 `options`。 |
| 500 | provider、数据库、文件写入或 workflow 未捕获异常。 |

PowerShell 中建议使用 `Invoke-RestMethod`：

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
