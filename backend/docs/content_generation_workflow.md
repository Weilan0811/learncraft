# 内容生成 Workflow 设计说明

本文档说明后端内容生成 workflow 的当前实现方式、节点职责、状态流转和扩展约定。

## 1. 设计目标

内容生成后端采用统一的任务入口和统一的状态模型，按内容类型选择生成路径：

| 内容类型 | 生成模式 | 当前用途 |
|---|---|---|
| `lecture` | `unit_loop` | 生成讲义 / 阅读材料。 |
| `slide_deck` | `unit_loop` | 生成课程 slides / PPT JSON。 |
| `interactive_html` | `unit_loop` | 生成分章阅读、模板练习与学习记录相结合的交互 HTML 讲义。 |
| `social_post` | `direct` | 生成微信公众号文章。 |
| `podcast_script` | `direct` | 生成中文双人播客脚本和音频。 |

核心目标：

1. 用户请求统一进入 `ContentGenerationRequest`。
2. 内容类型通过 `ContentTypeProfile` 注册，workflow 通过 profile 路由到对应生成模式。
3. `lecture`、`slide_deck`、`interactive_html` 支持按单元生成和逐单元预览。
4. `interactive_html` 将教学设计、互动模板、讲解 HTML/CSS 渲染拆开处理，保证互动控件稳定可用。
5. `social_post` 支持直接生成完整文章 spec、HTML 预览和 HTML 导出。
6. `podcast_script` 支持直接生成完整播客 spec、分段音频、完整音频和音频导出。
7. 每个关键节点写入进度、事件、日志和可持久化状态。
8. schema、validator、renderer、exporter 保持职责边界清晰。

## 2. 总体流程

```text
POST /api/content-generation/tasks
  ↓
PersistentTaskService.create_task
  ↓
FastAPI BackgroundTasks -> PersistentTaskService.run_task
  ↓
stream_content_generation(request, request_id=task_id)
  ↓
LangGraph StateGraph
  ↓
SQLModelTaskRepository.save_state
  ↓
GET /tasks/{task_id} / events / preview / partial preview / units
```

`stream_content_generation(...)` 会在 workflow 执行过程中持续 yield state update。`PersistentTaskService` 将每次 update 转成 `ContentGenerationState` 后保存到数据库。

## 3. ContentTypeProfile

内容类型注册表位于：

```text
app/content_types/
```

每个内容类型通过 `ContentTypeProfile` 声明：

| 字段 | 说明 |
|---|---|
| `content_type` | 内容类型名称。 |
| `generation_mode` | `unit_loop` 或 `direct`。 |
| `unit_type` | 单元类型，例如 `section`、`slide`、`interactive_section`、`article`。 |
| `requires_outline` | 是否需要 outline。 |
| `supports_unit_streaming` | 是否支持单元级流式快照。 |
| `planner_prompt_name` | planner prompt 文件名。 |
| `unit_spec_prompt_name` | unit spec 或 direct draft prompt 文件名。 |
| `spec_schema` | 内容 spec schema。 |
| `unit_spec_schema` | 单元 spec schema。 |
| `render_model_schema` | 渲染模型 schema。 |
| `renderer_factory` | renderer 工厂。 |
| `generator_name` | generator 标识。 |
| `element_policy` | 允许和默认生成的元素类型。 |
| `exporter_types` | 声明支持的导出类型。 |

当前注册内容类型：

```text
lecture         -> unit_loop
slide_deck      -> unit_loop
interactive_html -> unit_loop
social_post     -> direct
podcast_script  -> direct
```

`interactive_html` profile 当前关键配置：

| 字段 | 值 |
|---|---|
| `content_type` | `interactive_html` |
| `generation_mode` | `unit_loop` |
| `unit_type` | `interactive_section` |
| `requires_outline` | `True` |
| `supports_unit_streaming` | `True` |
| `planner_prompt_name` | `interactive_html_outline.md` |
| `unit_spec_prompt_name` | `interactive_html_unit_spec.md` |
| `spec_schema` | `InteractiveHtmlSpec` |
| `unit_spec_schema` | `InteractiveHtmlSectionSpec` |
| `render_model_schema` | `InteractiveHtmlRenderModel` |
| `renderer_factory` | `InteractiveHtmlRenderer` |
| `generator_name` | `interactive_html` |
| `element_policy` | 当前不生成 image / mindmap 元素 |
| `exporter_types` | 仅 `html`，导出带指定会话作答记录的静态讲义 |

## 4. unit_loop 生成路径

适用内容类型：

- `lecture`
- `slide_deck`
- `interactive_html`

当前主线流程：

```text
normalize_request
  ↓
retrieve_for_planning
  ↓
route_generation_mode -> unit_loop
  ↓
plan_outline
  ↓
validate_outline
  ↓
route_content_type
  ↓
initialize_section_units / initialize_slide_units / initialize_interactive_html_units
  ↓
generate_units_parallel
  ↓
assemble_content_spec
  ↓
validate_content
  ↓
route_renderer
  ↓
lecture_renderer / slide_renderer / interactive_html_renderer
  ↓
finalize_task
```

`generate_units_parallel` 是 unit-loop 的并发执行节点。它按 `CONTENT_GENERATOR_GENERATION_UNIT_CONCURRENCY` 将 `pending_unit_ids` 分批，每个 worker 使用隔离的 `ContentGenerationState` 副本执行单元内 pipeline：

```text
retrieve_for_unit
  ↓
generate_unit_spec
  ↓
validate_unit_spec
  ├─ pass
  ├─ repair -> repair_unit_spec -> validate_unit_spec
  ├─ fallback -> fallback_unit_spec -> validate_unit_spec
  └─ fail
  ↓
collect_unit_required_elements
  ↓
generate_image_element / generate_mindmap_element
  ↓
merge_unit_elements
  ↓
validate_unit
  ↓
render_unit
  ├─ pass
  ├─ retry
  ├─ repair -> repair_render_unit
  ├─ fallback -> fallback_render_unit
  └─ fail
  ↓
publish_unit_render
  ↓
merge_unit_result
```

并发节点不会让多个 worker 直接写主 state 的 `current_unit_id`、`current_unit_spec` 或 `current_unit_context`。每个单元完成后返回 `UnitPipelineResult`，主节点按 outline 顺序合并 `unit_results`、`render_units`、`unit_context_map`、`elements`、`stream_events` 和 `partial_render_model`。

### 4.1 主要节点职责

| 节点 | 职责 |
|---|---|
| `normalize_request` | 标准化用户请求和 generation options。 |
| `retrieve_for_planning` | 启用本地检索时，先调用文本模型规划 1—4 条知识查询，再逐条检索并合并资料；未启用时返回明确的关闭状态。 |
| `plan_outline` | 生成 `Outline`。`interactive_html` 使用 `interactive_html_outline.md`，只规划课程内容，不规划具体 block 或互动位置。 |
| `validate_outline` | 校验 outline 结构、unit_type、顺序、引用和 content_type。 |
| `initialize_section_units` | 初始化 lecture section 队列。 |
| `initialize_slide_units` | 初始化 slide page 队列。 |
| `initialize_interactive_html_units` | 初始化 interactive_html section 队列，并写入默认 `style_guide`。 |
| `generate_units_parallel` | 以有限并发执行单元内检索、spec、元素、渲染和发布事件，并按 outline 顺序合并结果。 |
| `retrieve_for_unit` | 直接执行大纲单元的 `retrieval_queries`；没有章节结果时沿用大纲阶段资料，并保存实际使用情况。 |
| `generate_unit_spec` | 根据 profile 调用对应 generator，生成 `LectureSection`、`SlideSpecPage` 或 `InteractiveHtmlSectionSpec`。 |
| `validate_unit_spec` | 校验单元 spec 的结构、引用和 renderer 契约。 |
| `repair_unit_spec` | 单元 spec 校验失败后，最多执行一次 LLM repair。 |
| `fallback_unit_spec` | `allow_fallback=true` 时生成 deterministic fallback spec。 |
| `collect_unit_required_elements` | 收集当前单元声明的图片或 mindmap 需求；`interactive_html` 当前为空。 |
| `dispatch_element_generation` | 旧串行路径中的 LangGraph Send 分发节点，当前主线已由 `generate_units_parallel` 在 worker 内直接生成元素。 |
| `generate_image_element` | 调用图片服务生成 `ImageElement`。 |
| `generate_mindmap_element` | 生成 `MindmapElement`。 |
| `merge_unit_elements` | 合并元素生成结果。 |
| `validate_unit` | 校验当前单元的 spec + elements 闭合性。 |
| `render_unit` | 生成单元级 render fragment。`interactive_html` 在此阶段生成 `InteractiveHtmlRenderedUnit`。 |
| `repair_render_unit` | 当前只支持 `interactive_html` 的单元渲染修复。 |
| `fallback_render_unit` | 当前只支持 `interactive_html` 的 fallback 单元渲染。 |
| `publish_unit_render` | 写入 `unit_render_ready` stream event；并发主线会按 outline 顺序合并事件，接口返回仍可按 unit order 展示。 |
| `merge_unit_result` | 将当前单元结果写入 `unit_results`，推进到下一个单元。 |
| `assemble_content_spec` | 汇总所有单元，组装 `LectureSpec`、`SlideDeckSpec` 或 `InteractiveHtmlSpec`。 |
| `validate_content` | 校验最终内容 spec。 |
| `lecture_renderer` | 将 `LectureSpec` 转为 `LectureRenderModel`。 |
| `slide_renderer` | 将 `SlideDeckSpec` 转为 `SlideRenderModel`。 |
| `interactive_html_renderer` | 将已渲染 section 汇总成 `InteractiveHtmlRenderModel`。 |
| `finalize_task` | 标记任务完成，写入最终进度。 |
| `fail_task` | 标记任务失败，写入错误信息。 |

## 5. interactive_html 生成路径

`interactive_html` 采用 unit-loop，但单元内部的设计与 lecture / slide 不同。它的核心拆分是：

```text
OutlineUnit
  ↓
InteractiveHtmlSectionSpec
  ├─ teaching_flow：教学块序列，只描述教学目标和互动占位
  ├─ interaction_specs：四类 P0 互动规格
  ├─ concepts / citations
  ↓
render_unit
  ├─ InteractionTemplateRenderer：按模板生成互动 DOM
  ├─ ExplanationHtmlComposer：LLM 生成非互动讲解 HTML + CSS
  ├─ UnitHtmlAssembler：按 teaching_flow 顺序组装讲解块与互动块
  ├─ sanitize_rendered_unit
  └─ validate_rendered_unit
  ↓
InteractiveHtmlRenderedUnit
  ├─ html_fragment
  ├─ css_fragment
  ├─ block_manifest
  └─ interaction_manifest
  ↓
InteractiveHtmlRenderer.assemble
  ↓
InteractiveHtmlRenderModel
```

### 5.1 Planner 职责

`interactive_html_outline.md` 只负责课程内容规划：

- 输出 `Outline`。
- `content_type` 固定为 `interactive_html`。
- `unit_type` 固定为 `interactive_section`。
- 每个 unit 必须有 `retrieval_queries` 和 `source_chunk_ids`。
- 不指定具体 block 类型。
- 不规划互动检查点位置。
- 不指定图片、示例、流程动画、情景教学或练习题。

### 5.2 Unit Spec 职责

`interactive_html_unit_spec.md` 输出 `InteractiveHtmlSectionSpec`，只描述教学设计，不输出 HTML / CSS。

核心字段：

| 字段 | 说明 |
|---|---|
| `section_id` | 必须等于当前 outline unit id。 |
| `title` | 当前 section 标题。 |
| `learning_goal` | 当前 section 学习目标。 |
| `narrative_goal` | 当前 unit 的叙事主线。 |
| `teaching_flow` | 3-7 个教学块，组织讲解、案例、流程、互动、总结。 |
| `interaction_specs` | P0 四类互动规格，通常 1-2 个互动点。 |
| `concepts` | 当前 section 涉及的核心概念。 |
| `citations` | 当前 section 引用来源。 |

当前 P0 互动类型：

| type | event_type | 渲染方式 |
|---|---|---|
| `single_choice` | `single_choice_answered` | 模板生成选项按钮和本地反馈区域。 |
| `multiple_choice` | `multiple_choice_answered` | 模板生成多选按钮、提交按钮和反馈区域。 |
| `short_answer` | `short_answer_submitted` | 模板生成 textarea、提交按钮和参考要点。 |
| `scenario_discussion` | `scenario_discussion_submitted` | 模板生成情景卡、textarea、提交按钮和参考要点。 |

### 5.3 单元渲染职责

`render_unit` 对 `InteractiveHtmlSectionSpec` 执行：

1. `InteractionTemplateRenderer.render(...)` 读取 `interaction_specs`，生成稳定互动 HTML。
2. `ExplanationHtmlComposer.compose(...)` 读取非互动 teaching blocks，调用 LLM 输出 `InteractiveHtmlExplanationRender`。
3. `UnitHtmlAssembler.assemble(...)` 按 `teaching_flow` 原始顺序合并讲解块和互动块。
4. `sanitize_rendered_unit(...)` 清洗 HTML / CSS。
5. `validate_rendered_unit(...)` 校验 DOM、manifest、CSS 作用域和安全约束。
6. 通过后写入 `render_units` 和 `partial_render_model`。

`ExplanationHtmlComposer` 的 LLM 输出只允许生成非互动教学块：

- 输出 `block_html_map` 和 `css_fragment`。
- 每个 block value 必须是单个 `<article>` 根节点。
- 禁止生成 `button`、`input`、`textarea`、`form`。
- 禁止生成 `data-ih-action` 和 `data-interaction-id`。
- 禁止完整页面标签、脚本、外链、全局 CSS 选择器。
- CSS 必须使用 `style_scope_id` 作用域。

### 5.4 修复与 fallback

`interactive_html` 当前有两层修复：

| 阶段 | 节点 | 行为 |
|---|---|---|
| unit spec 校验失败 | `repair_unit_spec` | 最多一次 LLM repair，然后回到 `validate_unit_spec`。 |
| unit spec 校验失败且允许 fallback | `fallback_unit_spec` | 构造 deterministic `InteractiveHtmlSectionSpec`。 |
| render_unit 传输类错误 | `render_unit` retry | 最多一次 transport retry。 |
| render_unit 非传输类错误 | `repair_render_unit` | 当前仅支持 interactive_html，重新 compose unit。 |
| render_unit 失败且允许 fallback | `fallback_render_unit` | 构造 fallback explanation HTML + 互动模板。 |

`allow_fallback` 来自 `generation_options.allow_fallback`。本地演示和课堂 demo 建议开启，真实质量评估时可以关闭以暴露问题。

## 6. direct 生成路径

当前适用内容类型：

- `social_post`
- `podcast_script`

流程：

```text
normalize_request
  ↓
retrieve_for_planning
  ↓
route_generation_mode -> direct
  ↓
generate_direct_content
  ↓
validate_direct_content
  ↓
render_direct_content
  ↓
finalize_task
```

节点职责：

| 节点 | 职责 |
|---|---|
| `generate_direct_content` | 根据内容类型调用 direct generator。`social_post` 生成 `SocialPostSpec`，`podcast_script` 生成 `PodcastSpec`。 |
| `validate_direct_content` | 根据内容类型调用 validator。`social_post` 校验文章结构、引用和图片绑定；`podcast_script` 校验说话人、开场、轮次、TTS 标签和 voice mapping。 |
| `render_direct_content` | 根据内容类型调用 renderer。`social_post` 输出 HTML、article JSON 和 preview assets；`podcast_script` 输出分段音频、audio manifest 和完整音频。 |

`podcast_script` 渲染时还会写入 `audio_segment_ready` 事件，payload 包含 segment id、speaker、voice、audio URL、状态和 retry count。

`social_post` 图片 slot 使用 `CONTENT_GENERATOR_IMAGE_GENERATION_CONCURRENCY` 做有限并发生成，输出的 `image_assets` 按 slot 顺序保持稳定。`podcast_script` TTS segment 使用 `CONTENT_GENERATOR_TTS_GENERATION_CONCURRENCY` 做有限并发合成，最终 `segments` 和 `audio_assets` 按 segment order 排序。

## 7. 状态模型

workflow 全局状态为 `ContentGenerationState`，关键字段如下：

| 字段 | 说明 |
|---|---|
| `request_id` | 当前任务 ID。 |
| `content_type` | 内容类型。 |
| `raw_request` | 原始请求。 |
| `normalized_request` | 标准化后的生成配置。 |
| `planning_chunks` | planning 阶段检索结果。 |
| `current_unit_context` | 当前单元检索结果。 |
| `unit_context_map` | 单元 ID 到检索上下文的映射。 |
| `outline` | 生成的大纲。 |
| `pending_unit_ids` | 待生成单元 ID。 |
| `completed_unit_ids` | 已完成单元 ID。 |
| `current_unit_id` | 当前单元 ID。 |
| `current_unit_spec` | 当前单元 spec。 |
| `current_unit_element_requests` | 当前单元声明的元素请求。 |
| `unit_results` | 所有单元生成结果。 |
| `content_spec` | 最终内容 spec。 |
| `render_units` | 单元级 render snapshot。 |
| `style_guide` | interactive_html 课程样式指南。 |
| `partial_render_model` | 局部预览模型。 |
| `render_model` | 最终完整渲染模型。 |
| `stream_events` | 前端可消费的流式事件。 |
| `logs` | workflow 结构化日志。 |
| `metrics` | 节点耗时、provider token、retry 和 fallback 观测数据。 |
| `retry_counts` | unit spec / render unit 等节点的 retry 计数。 |
| `progress` | 当前进度。 |
| `status` | `queued` / `running` / `completed` / `failed`。 |

## 8. 进度约定

当前进度由 `build_progress(...)` 统一生成。

| stage | percent | 说明 |
|---|---:|---|
| `queued` | 0 | 任务已创建。 |
| `running` / `normalizing` | 5 | 任务开始和请求标准化。 |
| `retrieving` | 15 | planning 阶段检索。 |
| `planning` / `validating_outline` | 25 | 大纲生成和校验。 |
| `initializing_units` | 30 | 初始化单元队列。 |
| unit loop stages | 30-80 | 单元检索、生成、元素生成、校验、渲染、单元发布。 |
| `generating_direct_content` | 65 | direct 内容生成。 |
| `validating_direct_content` | 82 | direct 内容校验。 |
| `assembling_content` / `validating_content` | 88 | 汇总与整体验证。 |
| `rendering` | 95 | 最终渲染。 |
| `completed` / `failed` | 100 | 任务结束。 |

说明：`repairing_render_unit`、`fallback_render_unit` 等细分 stage 当前未在 `_percent_for_stage` 中单独分配百分比，实际进度会通过 `ensure_monotonic_progress(...)` 保持不回退。

## 9. 持久化、引用与观测

`SQLModelTaskRepository.save_state(...)` 仍会保留旧字段兼容读取，但产品态主要数据源已经拆到多张表：

| 数据 | 产品态存储 |
|---|---|
| 任务摘要、平台关联、状态、进度 | `content_generation_task` |
| 大纲、content spec、unit spec、unit render、partial/final render | `content_generation_artifact` |
| planning 和 unit spec 阶段检索引用 | `content_generation_reference` |
| stream events | `TaskEventStore` 保存到 `storage/logs/content-generation/{task_id}.events.json`；路径随日志配置变化 |
| 查询及生成调用用量 | `retrieval_record`、大纲等产物中的实际调用记录；工作流日志与调试快照补充排查，`/metrics` 兼容接口当前返回空列表 |
| 资源状态 | `content_generation_asset` 与渲染产物保存失败原因及重试状态 |
| 学习会话和事件 | `interactive_learning_session`、`interactive_learning_event` |
| 图片、音频、导出文件 | 本地文件存储与 `manifest.json` |

写入时机：

| 阶段 | artifact/reference/metric |
|---|---|
| `plan_outline` 后 | 写入 `outline` artifact；planning chunks 写入 `reference(stage=planning)`。 |
| `generate_units_parallel` 合并后 | 每个 unit 写入 `unit_spec`、`unit_render` artifact；unit 检索 chunks 写入 `reference(stage=unit_spec, unit_id=...)`。 |
| unit render 完成后 | 写入 `unit_render_ready` event；更新 `partial_render` artifact。 |
| `assemble_content_spec` 后 | 写入 `content_spec` artifact。 |
| 最终 renderer 后 | 写入 `final_render` artifact，并更新任务 `preview_url`。 |
| 每个 graph update | 保存任务进度、产物和累计事件文件；节点及供应商观测同时进入工作流日志或调试快照。 |

本地 `storage/debug_workflow/{task_id}` 仍会保存 JSON 调试快照，只用于开发排障；产物和引用查询以数据库为准，事件从持久事件文件读取；不要依赖已移除的旧指标表。

前端可以通过以下接口读取这些状态：

```text
GET /api/content-generation/tasks/{task_id}
GET /api/content-generation/tasks/{task_id}/events
GET /api/content-generation/tasks/{task_id}/preview/partial
GET /api/content-generation/tasks/{task_id}/units
GET /api/content-generation/tasks/{task_id}/units/{unit_id}/preview
GET /api/content-generation/tasks/{task_id}/preview
GET /api/content-generation/tasks/{task_id}/artifacts
GET /api/content-generation/tasks/{task_id}/outline
GET /api/content-generation/tasks/{task_id}/references
GET /api/content-generation/tasks/{task_id}/units/{unit_id}/references
GET /api/content-generation/tasks/{task_id}/metrics
```

外部应用可通过 `platform_log_id`、`platform_user_id`、`platform_session_id` 关联任务。LearnCraft 保存这些标识，不建立跨库外键，也不限定外部会话只能关联一个产物。接入方式见[集成契约](../../docs/reference/platform-contract.md)。

## 10. 扩展新内容类型的步骤

新增内容类型建议按以下顺序实现：

1. 在 `app/schemas/base.py` 中确认 `ContentType` 枚举。
2. 新增 spec schema 和 render model schema。
3. 在 `app/content_types/` 新建 profile 并注册到 `registry.py`。
4. 明确使用 `unit_loop` 或 `direct`。
5. 编写 planner / generator / reviewer prompt。
6. 实现 generator。
7. 实现 validator。
8. 实现 renderer 或 unit-level composer。
9. 如需导出，实现 exporter 并接入 `workflows/routers.py`。
10. 增加 API、schema、workflow、prompt、validator、renderer 和 exporter 测试。
11. 导出 JSON Schema，并与前端对齐字段契约。

## 11. 开发约定

- workflow 节点只处理当前节点职责，避免跨层写 exporter 逻辑。
- generator 输出必须是 schema 实例或可被 schema 校验的 dict。
- validator 发现不可渲染结构时应阻断后续 renderer。
- `interactive_html` 的 Unit Spec 不包含 HTML / CSS，HTML/CSS 只在 unit render 阶段产生。
- `interactive_html` 的互动控件由模板生成，LLM 只生成非互动讲解区 HTML/CSS。
- 常规 renderer 不调用 LLM；`interactive_html` 的 `ExplanationHtmlComposer` 是当前例外，调用 LLM 生成受限的讲解片段。
- exporter 不重新生成内容，只负责将 render model 落盘。
- 任务进度、事件和日志应在关键节点持续更新。
- 并发节点必须使用单元隔离 state，再按 `unit_order` 合并主 state；不要在 worker 间共享 `current_unit_*` 游标。
- 新增字段后同步更新 Pydantic schema、JSON Schema、API 文档和前端类型。
