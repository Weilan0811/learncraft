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

平台接入时可选传入以下 header，生成模块只保存关联 ID，不做跨库外键：

```http
X-Platform-Log-Id: platform_log_001
X-Platform-User-Id: platform_user_001
X-Platform-Session-Id: platform_session_001
```

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
- 请求中的 `generation_options.allow_fallback` 会覆盖 `.env` 中的 `CONTENT_GENERATOR_ALLOW_FALLBACK` 默认值。生产质量评估建议关闭 fallback，demo 或本地调试可开启。

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

### 2.8 获取单元纯文本

```http
GET /api/content-generation/tasks/{task_id}/units/{unit_id}/text
```

返回 `UnitTextResponse`，用于获取某个已渲染单元清洗 HTML 标签后的纯文本内容。

```json
{
  "task_id": "task_xxxxxxxxxxxx",
  "unit_id": "unit-01-intro",
  "content_type": "interactive_html",
  "title": "当 AI “听懂”你的话——什么是理解？",
  "full_text": "清洗后的单元全文...",
  "chunks": [
    {
      "chunk_id": "chunk-01",
      "text": "第一个 block 清洗后的纯文本..."
    },
    {
      "chunk_id": "chunk-02",
      "text": "第二个 block 清洗后的纯文本..."
    }
  ]
}
```

说明：

- `full_text` 来自整个 `html_fragment` 的纯文本。
- `chunks` 按 `block_manifest` 对应的 block 顺序切分。
- `chunks` 中每项只包含 `chunk_id` 和 `text`，`chunk_id` 使用 `chunk-01`、`chunk-02` 这样的顺序编号。

### 2.9 查询阶段产物

```http
GET /api/content-generation/tasks/{task_id}/artifacts
GET /api/content-generation/tasks/{task_id}/artifacts/{artifact_id}
GET /api/content-generation/tasks/{task_id}/outline
```

`artifacts` 返回大纲、unit spec、content spec、unit render、partial render 和 final render 等阶段产物摘要。`outline` 是读取最新 `artifact_type=outline` 的便捷接口。

常见 `artifact_type`：

| artifact_type | 说明 |
|---|---|
| `outline` | 大纲。 |
| `unit_spec` | 单元 spec，带 `unit_id`。 |
| `content_spec` | 完整内容 spec。 |
| `unit_render` | 单元渲染片段，带 `unit_id` 和 `unit_order`。 |
| `partial_render` | 局部预览 render model。 |
| `final_render` | 完整预览 render model。 |

### 2.10 查询检索引用

```http
GET /api/content-generation/tasks/{task_id}/references
GET /api/content-generation/tasks/{task_id}/units/{unit_id}/references
```

第一个接口返回 task 大纲 planning 阶段使用的 reference chunks；第二个接口返回某个 unit spec 阶段使用的 reference chunks。返回格式与 unit text 接口相近：

```json
{
  "task_id": "task_xxxxxxxxxxxx",
  "unit_id": "unit-01-intro",
  "content_type": "interactive_html",
  "title": "当 AI “听懂”你的话——什么是理解？",
  "chunks": [
    {
      "chunk_id": "source_id",
      "title": "source_title",
      "text": "content"
    }
  ]
}
```

task 级 references 的 `unit_id` 为 `null`。`chunk_id` 优先使用 `source_id`，`text` 当前使用 DB 中保存的 `content_excerpt`。

### 2.11 查询观测指标

```http
GET /api/content-generation/tasks/{task_id}/metrics
```

返回 `GenerationMetricListResponse`。当前该兼容接口对已有任务返回空 `metrics` 列表，没有独立指标表。查询规划、大纲和章节的实际调用用量保存在对应任务产物中，详见[知识查询流程](../../docs/design/retrieval-workflow.md)。工作流日志与调试快照另用于排查。

### 2.12 导出任务结果

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
| `lecture` | `pdf` | 使用 ReportLab 排版讲义正文与图片，输出实际 PDF。 |
| `lecture` | `html` / `markdown` | 导出完整 HTML 或 Markdown 讲义。 |
| `lecture` | `image_assets` | 打包任务中生成的图片资源。 |
| `slide_deck` | `slide_json` | 导出前端 PPT/slide renderer 可消费的 JSON。 |
| `slide_deck` | `image_assets` | 打包任务中生成的图片资源。 |
| `interactive_html` | `html` | 导出离线复习讲义 HTML，需要传入 `export_options.session_id`。 |
| `social_post` | `html` | 导出微信公众号文章 HTML，同时生成 article JSON asset。 |
| `social_post` | `image_assets` | 打包推文图片资源。 |
| `podcast_script` | `markdown` | 导出播客脚本文本。 |
| `podcast_script` | `audio` | 导出完整音频；完整音频缺失且分段齐全时自动重新合成，并保存更新后的预览、音频清单和导出记录。仍有失败分段时返回失败，需先重试对应分段。 |

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
- 当前学习会话与事件保存到数据库，重启后可继续读取；导出必须使用属于该讲义的有效会话。
- `interactive_html` profile 当前仅声明 `html`，导出需要 `export_options.session_id`；当前没有交互讲义 ZIP 导出接口。
- `pptx` 等类型在 schema 或 profile 中已有预留，当前 exporter router 尚未形成完整生产契约。

## 3. 互动学习接口

以下接口使用数据库保存会话与事件。学习摘要与复习要求另有正式入口，完整字段见[学习记录与复习](../../docs/design/learning-loop.md)：

- `GET /api/interactive-lessons/{lesson_id}/sessions/{session_id}/summary`
- `POST /api/interactive-lessons/{lesson_id}/sessions/{session_id}/adaptive-brief`

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
| `knowledge_base_ids` | string[] | 保留并持久化的关联字段，当前不承担分库选择或授权。 |
| `kb_mode` | string | `platform`、`materials_only` 或 `fused`，分别选择平台材料、任务附件或融合结果；需启用本地检索适配器。 |
| `attachments` | object[] | 本次材料正文，结构为 `{filename, content}`；最多 10 份，每份最多 200,000 个字符。 |
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
| `max_section_count` | 8 | 讲义与交互讲义的大纲章节上限；交互讲义至少 1 章，实际数量由主题、要求和资料决定。 |
| `max_slide_count` | 12 | slide 最大页数。 |
| `output_depth` | `standard` | `brief` / `standard` / `detailed`。 |
| `image_style` | null | 图片风格提示。 |
| `citation_policy` | `light` | `none` / `light` / `strict`。 |
| `allow_fallback` | false | provider 或渲染失败时是否允许 fallback。对 interactive_html 的 unit spec / render unit fallback 很重要。 |
| `slide_theme` | null | slide 主题配置。 |
| `speaker_notes` | true | slide 是否生成讲稿备注。 |
| `pdf_options` | `{}` | PDF 导出配置预留。 |

说明：如果请求体没有显式传 `allow_fallback`，后端使用环境变量 `CONTENT_GENERATOR_ALLOW_FALLBACK` 作为默认值；请求体显式传入时，以请求体为准。

多模态输出由内容类型固定，不再接受 `include_images` / `include_charts` / `include_mindmap` 字段：讲义、幻灯片、图文推文固定生成图片；播客固定生成音频；交互式讲义仅文本；图表和思维导图不再生成。

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
7. 需要展示引用来源时读取 `/references` 或 `/units/{unit_id}/references`。
8. 需要性能面板或排障信息时读取 `/metrics`。

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
