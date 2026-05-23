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

#### slide_deck 请求示例

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

#### interactive_html 请求示例

```json
{
  "content_type": "interactive_html",
  "topic": "生成式 AI 如何理解你的问题？",
  "user_prompt": "生成一份纵向教材式 + 对话导师的互动 HTML 课件，包含单选、多选、简答和情景讨论。",
  "knowledge_base_ids": ["default"],
  "generation_options": {
    "language": "zh-CN",
    "audience": "AI 初学者",
    "difficulty": "introductory",
    "style": "educational",
    "section_count": 5,
    "output_depth": "standard",
    "allow_fallback": true
  }
}
```

返回体为 `TaskResult`。

```json
{
  "task_id": "task_xxxxxxxxxxxx",
  "status": "queued",
  "content_type": "interactive_html",
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
  "created_at": "2026-05-23T00:00:00Z",
  "updated_at": "2026-05-23T00:00:00Z"
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
        "topic": "生成式 AI 如何理解你的问题？"
      },
      "created_at": "2026-05-23T00:00:00Z"
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
| `unit_render_ready` | 单元渲染片段生成完成。`lecture`、`slide_deck`、`interactive_html` 都可使用。 |
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
  "content_type": "interactive_html",
  "render_model": {
    "render_type": "interactive_html_page",
    "lesson_id": "lesson_task_xxxxxxxxxxxx",
    "title": "生成式 AI 如何理解你的问题？",
    "layout": "vertical_lesson_with_tutor",
    "navigation": [],
    "interactions": [],
    "sections": []
  }
}
```

`render_model` 根据内容类型不同而不同：

| content_type | render_model |
|---|---|
| `lecture` | `LectureRenderModel`。 |
| `slide_deck` | `SlideRenderModel`，页面结构为 `scenekit.slide/v1`。 |
| `interactive_html` | `InteractiveHtmlRenderModel`，包含 `navigation`、`interactions`、`runtime`、`sections`、`style_guide`。 |
| `social_post` | `SocialPostRenderModel`，包含 HTML、article JSON、preview assets。 |
| `podcast_script` | `PodcastRenderModel`，包含脚本、分段音频、audio manifest 和完整音频。 |

### 2.5 获取局部预览

```http
GET /api/content-generation/tasks/{task_id}/preview/partial
```

返回 `PartialPreviewResponse`。

局部预览用于生成过程中的前端增量展示。对于 unit-loop 类型，后端会保存逐单元渲染片段；对于 direct 类型，完成 direct render 后会写入 partial render model。

`interactive_html` 的局部预览会随着每个 section 的 `InteractiveHtmlRenderedUnit` 完成而更新，前端可以按 `sections` 数量增量渲染。

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
      "content_type": "interactive_html",
      "status": "rendered",
      "render_fragment": {
        "section_id": "unit_01",
        "title": "问题如何进入模型",
        "learning_goal": "理解提示词进入模型后的基本处理过程",
        "style_scope_id": "ih-scope-unit_01",
        "html_fragment": "<section ...></section>",
        "css_fragment": ".ih-scope-unit_01 { ... }",
        "block_manifest": [],
        "interaction_manifest": []
      },
      "updated_at": "2026-05-23T00:00:00Z",
      "errors": []
    }
  ]
}
```

### 2.7 获取单元预览

```http
GET /api/content-generation/tasks/{task_id}/units/{unit_id}/preview
```

返回 `UnitPreviewResponse`，用于前端按页、按章节或按互动 HTML section 展示生成结果。

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
| `interactive_html` | `html` | 导出离线复习讲义 HTML，需要传入 `export_options.session_id`。 |
| `social_post` | `html` | 导出微信公众号文章 HTML，同时生成 article JSON asset。 |
| `social_post` | `image_assets` | 打包推文图片资源。 |
| `podcast_script` | `markdown` | 导出播客脚本文本。 |
| `podcast_script` | `audio` | 导出完整音频；如果完整音频不存在则回退 audio manifest。 |

`interactive_html` 离线讲义导出示例：

```json
{
  "export_type": "html",
  "export_options": {
    "session_id": "session_xxxxxxxxxxxx"
  }
}
```

说明：

- `session_id` 必须来自 `POST /api/interactive-lessons/{lesson_id}/sessions`。
- 导出时后端会读取该 session 的学习事件，把在线互动控件静态化，并附加答题记录。
- 当前 learning session 与事件存储为 in-memory，服务重启后 session 不保留。
- `interactive_html` profile 中声明了 `zip`，但当前 `ExportType` 和 exporter router 尚未接入 `zip`，API 层可用导出以 `html` 为准。
- `pptx` 等类型在 schema 或 profile 中已有预留，当前 exporter router 尚未形成完整生产契约。

## 3. 互动学习接口

互动学习接口用于 `interactive_html` 在线课件运行时记录学生交互事件，并为离线复习讲义导出提供答题记录。

### 3.1 创建学习 Session

```http
POST /api/interactive-lessons/{lesson_id}/sessions
```

请求体当前为空对象即可：

```json
{}
```

返回 `SessionResponse`：

```json
{
  "session_id": "session_xxxxxxxxxxxx",
  "lesson_id": "lesson_task_xxxxxxxxxxxx",
  "state": {}
}
```

### 3.2 提交学习事件

```http
POST /api/interactive-lessons/{lesson_id}/sessions/{session_id}/events
```

请求体为 `SubmitEventRequest`。

单选题示例：

```json
{
  "section_id": "unit_01",
  "block_id": "unit_01_q1",
  "interaction_id": "interaction_unit_01_sc",
  "event_type": "single_choice_answered",
  "payload": {
    "selected_option_ids": ["a"],
    "correct_option_ids": ["a"],
    "is_correct": true,
    "client_timestamp": "2026-05-23T00:00:00+08:00",
    "time_spent_seconds": 18
  }
}
```

简答题或情景讨论示例：

```json
{
  "section_id": "unit_03",
  "block_id": "unit_03_discussion",
  "interaction_id": "interaction_unit_03_discussion",
  "event_type": "scenario_discussion_submitted",
  "payload": {
    "answer_text": "我会先判断学生是否已经理解核心概念，再决定是否给出追问。",
    "reference_points": ["理解诊断", "迁移应用", "反馈闭环"],
    "matched_points": ["理解诊断", "反馈闭环"],
    "heuristic_score": 2,
    "confidence": "medium",
    "time_spent_seconds": 72
  }
}
```

返回 `EventResponse`：

```json
{
  "event_id": "event_xxxxxxxxxxxx",
  "feedback": {
    "message": "你的回答已记录，请继续学习下一部分。",
    "tone": "encouraging"
  },
  "event_saved": true
}
```

当前支持的 `event_type`：

| event_type | 用途 |
|---|---|
| `single_choice_answered` | 单选题提交。 |
| `multiple_choice_answered` | 多选题提交。 |
| `short_answer_submitted` | 简答题提交。 |
| `scenario_discussion_submitted` | 情景讨论提交。 |
| `drag_match_submitted` | 拖拽匹配提交，schema 预留。 |
| `sequence_submitted` | 排序题提交，schema 预留。 |
| `socratic_round_answered` | 多轮启发式问答提交，schema 预留。 |
| `scenario_choice_selected` | 情景选择提交，schema 预留。 |
| `hint_requested` | 请求提示。 |
| `confused_clicked` | 学生标记困惑。 |

### 3.3 查询学习 Session 状态

```http
GET /api/interactive-lessons/{lesson_id}/sessions/{session_id}/state
```

返回 `SessionStateResponse`：

```json
{
  "session_id": "session_xxxxxxxxxxxx",
  "lesson_id": "lesson_task_xxxxxxxxxxxx",
  "total_events": 3,
  "interaction_summary": {
    "total_answered": 2,
    "help_requested_count": 1,
    "total_events": 3
  }
}
```

## 4. 资源接口

### 4.1 查询资源元数据

```http
GET /api/assets/{asset_id}
```

返回 `AssetResponse`，包含资源 ID、文件名、content type、URL、metadata 等信息。

### 4.2 下载资源文件

```http
GET /api/assets/{asset_id}/download
```

返回文件流。资源文件由 `LocalStorageService` 保存到 `storage/files/`，资源元数据记录在 `storage/manifest.json`。

## 5. 请求字段说明

### 5.1 ContentGenerationRequest

| 字段 | 类型 | 说明 |
|---|---|---|
| `content_type` | string | 当前运行支持 `lecture`、`slide_deck`、`interactive_html`、`social_post`、`podcast_script`。 |
| `topic` | string | 生成主题。 |
| `user_prompt` | string | 用户原始生成要求。 |
| `system_prompt` | string / null | 可选系统约束。 |
| `knowledge_base_ids` | string[] | 检索使用的知识库 ID。 |
| `generation_options` | object | 生成配置。 |

`ContentType` schema 中还保留了 `video_script`、`project_task`、`quiz_pack`、`learning_path` 等未来类型，但当前 runtime registry 尚未注册这些类型，提交后会在 workflow 路由阶段失败。

### 5.2 GenerationOptions

| 字段 | 默认值 | 说明 |
|---|---|---|
| `language` | `zh-CN` | 输出语言。 |
| `audience` | null | 目标读者或学习者。 |
| `difficulty` | `introductory` | `introductory` / `intermediate` / `advanced`。 |
| `style` | `educational` | 内容风格。 |
| `duration_minutes` | null | lecture / interactive_html 可参考的时长配置。 |
| `section_count` | null | lecture / interactive_html 章节数建议。当前强校验只针对 `lecture`。 |
| `slide_count` | null | slide 页数。 |
| `max_section_count` | 8 | lecture 最大章节数；interactive_html outline prompt 当前建议 4-8 个 units。 |
| `max_slide_count` | 12 | slide 最大页数。 |
| `output_depth` | `standard` | `brief` / `standard` / `detailed`。 |
| `include_images` | true | 是否生成图片。`interactive_html` 当前不走图片元素分支。 |
| `include_charts` | false | 是否生成图表，当前仍处于预留。 |
| `include_mindmap` | false | 是否生成 mindmap。`interactive_html` 当前不走 mindmap 元素分支。 |
| `image_style` | null | 图片风格提示。 |
| `citation_policy` | `light` | `none` / `light` / `strict`。 |
| `allow_fallback` | false | provider 或渲染失败时是否允许 fallback。对 interactive_html 的 unit spec / render unit fallback 很重要。 |
| `slide_theme` | null | slide 主题配置。 |
| `speaker_notes` | true | slide 是否生成讲稿备注。 |
| `pdf_options` | `{}` | PDF 导出配置预留。 |

## 6. 前端轮询建议

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
4. `interactive_html` 可以优先使用 `preview/partial.render_model.sections` 做 section 级增量展示。
5. `status=completed` 后请求完整 `preview`。
6. 用户点击导出后再调用 `POST /export`。

## 7. 常见错误

| HTTP 状态 | 场景 |
|---|---|
| 404 | 任务、预览、单元、学习 session 或资源不存在。 |
| 422 | 请求体字段不符合 Pydantic schema，例如 `generation_options` 写成旧字段 `options`，或 `export_type` 使用了当前 `ExportType` 不支持的值。 |
| 500 | provider、数据库、文件写入或 workflow 未捕获异常。 |

PowerShell 中建议使用 `Invoke-RestMethod`：

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
