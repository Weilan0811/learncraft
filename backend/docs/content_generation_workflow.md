# 内容生成 Workflow 设计说明

本文档说明后端内容生成 workflow 的当前实现方式、节点职责、状态流转和扩展约定。

## 1. 设计目标

内容生成后端采用统一的任务入口和统一的状态模型，按内容类型选择生成路径：

| 内容类型 | 生成模式 | 当前用途 |
|---|---|---|
| `lecture` | `unit_loop` | 生成讲义 / 阅读材料。 |
| `slide_deck` | `unit_loop` | 生成课程 slides / PPT JSON。 |
| `social_post` | `direct` | 生成微信公众号文章。 |

核心目标：

1. 用户请求统一进入 `ContentGenerationRequest`。
2. 内容类型通过 `ContentTypeProfile` 注册，不在 workflow 中硬编码扩展逻辑。
3. `lecture`、`slide_deck` 支持按单元生成和逐单元预览。
4. `social_post` 支持直接生成完整文章 spec、HTML 预览和 HTML 导出。
5. 每个关键节点写入进度、事件、日志和可持久化状态。
6. schema、validator、renderer、exporter 保持职责边界清晰。

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
GET /tasks/{task_id} / events / preview / units
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
| `unit_type` | 单元类型，例如 `section`、`slide`、`article`。 |
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
lecture      -> unit_loop
slide_deck   -> unit_loop
social_post  -> direct
```

## 4. unit_loop 生成路径

适用内容类型：

- `lecture`
- `slide_deck`

流程：

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
initialize_section_units / initialize_slide_units
  ↓
retrieve_for_unit
  ↓
generate_unit_spec
  ↓
validate_unit_spec
  ↓
collect_unit_required_elements
  ↓
dispatch_element_generation
  ↓
generate_image_element / generate_mindmap_element
  ↓
merge_unit_elements
  ↓
validate_unit
  ↓
render_unit
  ↓
publish_unit_render
  ↓
merge_unit_result
  ↓
should_continue_units
  ↓
assemble_content_spec
  ↓
validate_content
  ↓
route_renderer
  ↓
lecture_renderer / slide_renderer
  ↓
finalize_task
```

### 4.1 主要节点职责

| 节点 | 职责 |
|---|---|
| `normalize_request` | 标准化用户请求和 generation options。 |
| `retrieve_for_planning` | 为大纲规划检索知识库 chunk。 |
| `plan_outline` | 生成 `Outline`。 |
| `validate_outline` | 校验 outline 结构和生成约束。 |
| `initialize_section_units` | 初始化 lecture section 队列。 |
| `initialize_slide_units` | 初始化 slide page 队列。 |
| `retrieve_for_unit` | 为当前单元检索更聚焦的上下文。 |
| `generate_unit_spec` | 生成 `LectureSection` 或 `SlideSpecPage`。 |
| `validate_unit_spec` | 校验单元 spec 的结构、引用和 renderer 契约。 |
| `collect_unit_required_elements` | 收集当前单元声明的图片或 mindmap 需求。 |
| `dispatch_element_generation` | 使用 LangGraph Send 机制分发元素生成。 |
| `generate_image_element` | 调用图片服务生成 `ImageElement`。 |
| `generate_mindmap_element` | 生成 `MindmapElement`。 |
| `merge_unit_elements` | 合并元素生成结果。 |
| `validate_unit` | 校验当前单元的 spec + elements 闭合性。 |
| `render_unit` | 生成单元级 render fragment。 |
| `publish_unit_render` | 写入单元级 snapshot 和 stream event。 |
| `merge_unit_result` | 将当前单元结果写入 `unit_results`。 |
| `assemble_content_spec` | 汇总所有单元，组装 `LectureSpec` 或 `SlideDeckSpec`。 |
| `validate_content` | 校验最终内容 spec。 |
| `lecture_renderer` | 将 `LectureSpec` 转为 `LectureRenderModel`。 |
| `slide_renderer` | 将 `SlideDeckSpec` 转为 `SlideRenderModel`。 |
| `finalize_task` | 标记任务完成，写入最终进度。 |
| `fail_task` | 标记任务失败，写入错误信息。 |

## 5. direct 生成路径

当前适用内容类型：

- `social_post`

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
| `generate_direct_content` | 调用 `SocialPostGenerator` 生成 `SocialPostSpec`，包括 outline、draft、image slots 和 image assets。 |
| `validate_direct_content` | 调用 `SocialPostValidator` 校验文章结构、引用和图片绑定，生成 wechat-claw article JSON。 |
| `render_direct_content` | 调用 `SocialPostRenderer` 输出 HTML、article JSON 和 preview assets。 |

## 6. 状态模型

workflow 全局状态为 `ContentGenerationState`，关键字段如下：

| 字段 | 说明 |
|---|---|
| `request_id` | 当前任务 ID。 |
| `content_type` | 内容类型。 |
| `raw_request` | 原始请求。 |
| `normalized_request` | 标准化后的生成配置。 |
| `planning_chunks` | planning 阶段检索结果。 |
| `current_unit_context` | 当前单元检索结果。 |
| `outline` | 生成的大纲。 |
| `pending_unit_ids` | 待生成单元 ID。 |
| `completed_unit_ids` | 已完成单元 ID。 |
| `current_unit_id` | 当前单元 ID。 |
| `current_unit_spec` | 当前单元 spec。 |
| `current_unit_elements` | 当前单元生成的元素。 |
| `unit_results` | 所有单元生成结果。 |
| `content_spec` | 最终内容 spec。 |
| `render_units` | 单元级 render snapshot。 |
| `partial_render_model` | 局部预览模型。 |
| `render_model` | 最终完整渲染模型。 |
| `stream_events` | 前端可消费的流式事件。 |
| `logs` | workflow 结构化日志。 |
| `progress` | 当前进度。 |
| `status` | `queued` / `running` / `completed` / `failed`。 |

## 7. 进度约定

当前进度由 `build_progress(...)` 统一生成。

| stage | percent | 说明 |
|---|---:|---|
| `queued` | 0 | 任务已创建。 |
| `running` / `normalizing` | 5 | 任务开始和请求标准化。 |
| `retrieving` | 15 | planning 阶段检索。 |
| `planning` / `validating_outline` | 25 | 大纲生成和校验。 |
| `initializing_units` | 30 | 初始化单元队列。 |
| unit loop stages | 30-80 | 单元检索、生成、元素生成、校验、渲染。 |
| `generating_direct_content` | 65 | direct 内容生成。 |
| `validating_direct_content` | 82 | direct 内容校验。 |
| `assembling_content` / `validating_content` | 88 | 汇总与整体验证。 |
| `rendering` | 95 | 最终渲染。 |
| `completed` / `failed` | 100 | 任务结束。 |

## 8. 持久化与预览

`SQLModelTaskRepository.save_state(...)` 会将 state 中的重要字段保存到 `content_generation_task` 表：

| 数据 | 存储字段 |
|---|---|
| 任务状态 | `status` |
| 当前节点 | `current_node` |
| 进度 | `progress` |
| 大纲 | `outline` |
| 完整 render model | `render_model` |
| 局部 render model | `partial_render_model` |
| 内容 spec | `content_spec` |
| 单元结果 | `unit_results` |
| 单元预览 | `render_units` |
| 事件流 | `stream_events` |
| 元素 | `elements` |
| 日志 | `logs` |
| 资源 ID | `asset_ids` |
| 错误 | `errors` |

前端可以通过以下接口读取这些状态：

```text
GET /api/content-generation/tasks/{task_id}
GET /api/content-generation/tasks/{task_id}/events
GET /api/content-generation/tasks/{task_id}/preview/partial
GET /api/content-generation/tasks/{task_id}/units
GET /api/content-generation/tasks/{task_id}/units/{unit_id}/preview
GET /api/content-generation/tasks/{task_id}/preview
```

## 9. 扩展新内容类型的步骤

新增内容类型建议按以下顺序实现：

1. 在 `app/schemas/base.py` 中确认 `ContentType` 枚举。
2. 新增 spec schema 和 render model schema。
3. 在 `app/content_types/` 新建 profile 并注册到 `registry.py`。
4. 编写 planner / generator / reviewer prompt。
5. 实现 generator。
6. 实现 validator。
7. 实现 renderer。
8. 如需导出，实现 exporter 并接入 `workflows/routers.py`。
9. 增加 API、schema、workflow 和 renderer 测试。
10. 导出 JSON Schema，并与前端对齐字段契约。

## 10. 开发约定

- workflow 节点只处理当前节点职责，避免跨层写 renderer 或 exporter 逻辑。
- generator 输出必须是 schema 实例或可被 schema 校验的 dict。
- validator 发现不可渲染结构时应阻断后续 renderer。
- renderer 不调用 LLM，不直接修改原始 spec 语义。
- exporter 不重新生成内容，只负责将 render model 落盘。
- 任务进度、事件和日志应在关键节点持续更新。
- 新增字段后同步更新 Pydantic schema、JSON Schema、API 文档和前端类型。
