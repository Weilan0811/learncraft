# Content Generation Refactor Progress

本文档基于 `docs/improve.md` 和当前工作区改动，记录已经完成的重构内容与后续待办事项。

## 已完成内容

### 第一阶段：生成底座解耦

已完成“通用生成内核 + Content Type Profile”底座改造。

- 将后端 schema 边界从 `MvpContentType` 扩展为更开放的 `ContentType`。
- 新增 `backend/app/content_types/`：
  - `base.py`
  - `registry.py`
  - `lecture.py`
  - `slide_deck.py`
  - `__init__.py`
- 当前注册并支持的 profile：
  - `lecture`
  - `slide_deck`
- 将 lecture / slide_deck 的 unit 类型、prompt 名称、spec schema、render schema、renderer factory、generator 名称等信息放入 profile。
- 将 planner、unit generator、assembler、renderer router 中的部分内容类型判断收敛到 profile registry。
- 保持现有 lecture / slide_deck 业务能力不变。

### 第一阶段补充：目录结构重组

已进行受控目录重组，便于后续人工审查和维护。

- 将原 `backend/app/schemas/specs.py` 拆分为：
  - `backend/app/schemas/specs/common.py`
  - `backend/app/schemas/specs/lecture.py`
  - `backend/app/schemas/specs/slide.py`
  - `backend/app/schemas/specs/__init__.py`
- 将原 `backend/app/schemas/render.py` 拆分为：
  - `backend/app/schemas/render/lecture.py`
  - `backend/app/schemas/render/slide.py`
  - `backend/app/schemas/render/__init__.py`
- 将原 `backend/app/schemas/elements.py` 拆分为：
  - `backend/app/schemas/elements/common.py`
  - `backend/app/schemas/elements/visual.py`
  - `backend/app/schemas/elements/learning.py`
  - `backend/app/schemas/elements/__init__.py`
- 通过 package `__init__.py` 保持原有导入方式兼容，例如 `from app.schemas.specs import LectureSpec`。

### 第一阶段补充：生成日志增强

已完善生成过程日志，方便后续维护排查。

- 新增结构化 workflow log entry。
- `ContentGenerationState.logs` 改为结构化日志列表。
- 生成过程会记录任务开始、节点完成、任务完成、任务失败等事件。
- 日志会持久化到数据库任务记录。
- 同时写入任务级 JSONL 文件：
  - `storage/logs/content-generation/{task_id}.log`
- 新增数据库迁移：
  - `backend/alembic/versions/20260511_0002_add_task_logs.py`

### 第二阶段：unit 级 render

已完成 unit 级渲染主链路。

- 新增 workflow 节点：
  - `backend/app/workflows/nodes/unit_renderer_node.py`
  - `backend/app/workflows/nodes/publish_event_node.py`
- workflow unit loop 已从：

```text
validate_unit -> merge_unit_result
```

调整为：

```text
validate_unit -> render_unit -> publish_unit_render -> merge_unit_result
```

- `LectureRenderer` 已支持：
  - `render_unit(...)`
  - `assemble(...)`
  - 原 `render(...)` 兼容保留
- `SlideRenderer` 已支持：
  - `render_unit(...)`
  - `assemble(...)`
  - 原 `render(...)` 兼容保留
- 每个 lecture section / slide page 完成后可生成独立 render fragment。

### 第三阶段：partial preview 与任务持久化

已完成部分结果持久化和轮询式流式接口。

- `ContentGenerationState` 新增：
  - `render_units`
  - `partial_render_model`
  - `stream_events`
- 新增 schema：
  - `RenderUnitSnapshot`
  - `TaskStreamEvent`
- `ContentGenerationTask` 新增持久化字段：
  - `outline`
  - `unit_results`
  - `render_units`
  - `partial_render_model`
  - `stream_events`
- 新增数据库迁移：
  - `backend/alembic/versions/20260511_0003_add_streaming_snapshots.py`
- `SQLModelTaskRepository.save_state()` 会保存 outline、unit results、render units、partial preview 和 stream events。
- 新增 API：
  - `GET /api/content-generation/tasks/{task_id}/events`
  - `GET /api/content-generation/tasks/{task_id}/preview/partial`
  - `GET /api/content-generation/tasks/{task_id}/units`
  - `GET /api/content-generation/tasks/{task_id}/units/{unit_id}/preview`
- `backend/scripts/export_json_schema.py` 已加入新增 response schema 导出。

### 前端流式展示

已完成前端对 partial preview 的基础展示支持。

- `frontend/src/api/contentGenerationApi.ts` 新增：
  - `getContentGenerationEvents`
  - `getContentGenerationPartialPreview`
  - `getContentGenerationUnits`
- `frontend/src/types/export.ts` 新增：
  - `PartialPreviewResponse`
  - `TaskStreamEvent`
  - `RenderUnitSnapshot`
  - `TaskEventsResponse`
  - `TaskUnitsResponse`
- `frontend/src/stores/contentGenerationStore.ts` 在任务轮询过程中同步拉取：
  - stream events
  - render units
  - partial preview
- `frontend/src/pages/ContentPreviewPage.tsx` 优先展示 partial preview，任务完成后展示 final preview。
- `frontend/src/components/generation/GenerationProgress.tsx` 增加已渲染 unit 数和最新事件展示。
- `frontend/src/components/generation/ExportActions.tsx` 调整为任务完成后才允许导出。

## 已验证内容

已运行以下验证：

```bash
uv run pytest backend/tests -q
```

结果：

```text
82 passed, 2 skipped, 1 warning
```

```bash
npm run build
```

结果：构建通过。Vite 仍提示 chunk size 超过 500 kB，这是打包体积警告，不是构建失败。

```bash
uv run python backend/scripts/export_json_schema.py
```

结果：执行通过，并刷新 schema exports。

## 待办事项

### 第四阶段：接入 social_post

建议下一步优先接入 `social_post`，用于验证 direct workflow。

- 新增 `SocialPostSpec`
- 新增 `SocialPostRenderModel`
- 新增 `SocialPostProfile`
- 新增 `SocialPostGenerator`
- 新增 `SocialPostValidator`
- 新增 `SocialPostRenderer`
- 新增 direct path workflow：

```text
retrieve_for_planning
  -> generate_social_post_spec
  -> validate_social_post
  -> generate_required_elements
  -> render_social_post
  -> finalize
```

- 前端新增 social post 预览 renderer。

### 第五阶段：接入 podcast

播客仍未接入。

- 建议确认内容类型命名：`podcast` 还是沿用 `podcast_script`。
- 新增 `PodcastSpec`
- 新增 `PodcastSegmentSpec`
- 新增 `PodcastRenderModel`
- 新增 `AudioScriptElement`
- 新增 `AudioFileElement`
- 新增 `TTSService`
- 新增 `PodcastProfile`
- 新增 `PodcastGenerator`
- 新增 `PodcastValidator`
- 新增 `PodcastRenderer`
- 新增 workflow 节点：
  - `tts_node.py`
  - `audio_assembler_node.py`
- 支持文本脚本片段流式输出，再支持音频片段输出。

### 第六阶段：强化教材和 PPT

教材增强待办：

- 增加 `InteractiveElement`
- 增加 quiz / reflection / drag_sort / fill_blank / case_analysis / code_exercise 等交互类型。
- 扩展 lecture block 类型，支持可交互 block。
- 更新 lecture profile 的 element policy。
- 前端增加交互式 block 渲染组件。

PPT 增强待办：

- 新增 `SlideSpecValidator`
- 新增 `SlideLayoutValidator`
- 新增 `SlideRenderValidator`
- 支持 slide spec repair。
- 支持布局 downgrade / fallback。
- 在每页生成后立即做页面级质量校验。
- 前端补充页级错误状态展示。

### Workflow kernel 继续解耦

当前主图仍然主要服务 outline + unit loop。后续应继续推进：

- 新增 `route_generation_mode`。
- 将 unit path 和 direct path 明确拆分。
- 将 generator / validator / renderer strategy 进一步放入 profile。
- 将 lecture / slide_deck 的剩余分支继续向 profile 或 strategy 下沉。
- 为未来 `social_post`、`podcast`、`video_script` 避免继续污染主图。

### 事件流能力增强

当前前端采用轮询 JSON 接口，尚未实现 SSE / WebSocket。

- 可新增 `GET /tasks/{task_id}/events/stream`。
- 支持按 `last_event_id` 增量拉取 events。
- 增加事件去重和事件序号。
- 前端 store 可从全量轮询改为增量拉取或 SSE。
- 支持任务失败时实时显示失败节点、错误详情和恢复建议。

### 日志与可观测性增强

当前已有基础结构化日志，但还可继续增强：

- 记录每个节点耗时。
- 记录 LLM prompt 摘要、模型名、token usage。
- 记录元素生成重试次数和 fallback 原因。
- 增加日志下载接口。
- 增加 task detail 页面中的日志查看面板。

### 数据库与迁移

已新增 logs 和 streaming snapshots 迁移，但还需要生产级确认。

- 在 MySQL 环境验证 `20260511_0002_add_task_logs.py`。
- 在 MySQL 环境验证 `20260511_0003_add_streaming_snapshots.py`。
- 评估 JSON 字段大小和索引策略。
- 对历史任务数据补默认值。

### 前端体验待办

- 当前 partial preview 是轮询式更新，后续可以优化为增量事件驱动。
- 增加“正在生成第 N 页 / 第 N 节”的更清晰状态。
- 对 slide / lecture 增加 unit 列表导航。
- 对失败 unit 增加错误提示和重试入口。
- 对 partial preview 和 final preview 增加明显状态标识。
- 解决当前部分中文文案存在乱码的问题。

### 测试待办

- 为前端 store 增加测试框架和单元测试。
- 为 partial preview UI 增加组件测试。
- 为 API 增加 events 增量查询测试。
- 为数据库迁移增加 MySQL 集成验证。
- 增加真实 provider 模式下的慢任务流式输出测试。

## 当前注意事项

- 当前工作区中 `docs/openmaic_slide_backend_modification_plan.md` 处于删除状态，该变化并非本轮阶段改造的核心内容，需要单独确认是否保留删除。
- `docs/improve.md` 当前处于未跟踪状态，需要确认是否纳入版本管理。
- 浏览器插件验证曾出现连接超时；已通过后端测试、前端 build 和接口测试覆盖主要功能。
