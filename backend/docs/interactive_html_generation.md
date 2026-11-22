# Interactive HTML 课件生成说明

本文档描述 `interactive_html` 内容类型的当前实现。当前 `interactive_html` 用于生成“纵向教材式 + 对话导师”的在线互动 HTML 课件，并支持基于学习事件导出离线复习讲义。

```text
content_type = interactive_html
render_type = interactive_html_page
layout = vertical_lesson_with_tutor
```

## 1. 模块定位

`interactive_html` 生成链路用于将用户请求和知识库检索结果转成可在线学习的互动课件，并输出：

- `Outline`
- `InteractiveHtmlSectionSpec`
- `InteractiveHtmlSpec`
- `InteractiveHtmlRenderedUnit`
- `InteractiveHtmlRenderModel`
- 在线互动 runtime contract
- learning session / learning event 记录接口
- 离线复习讲义 HTML 导出

当前实现采用 unit-loop workflow，支持逐 section 生成、逐 section 渲染和局部预览。

## 2. 当前设计原则

1. 大纲只规划课程内容，不规划具体组件、互动位置和视觉模块。
2. Unit Spec 只描述教学设计，不输出 HTML / CSS。
3. 互动题由模板渲染，保证前端可交互性。
4. 讲解区由 LLM 生成受限 HTML + CSS，提升视觉表现力。
5. 渲染结果必须经过 sanitizer 和 validator。
6. 在线互动事件独立记录，离线讲义导出时读取 session events。

## 3. 生成流程

```text
用户请求
  ↓
知识库检索 retrieve_for_planning
  ↓
plan_outline
  └─ interactive_html_outline.md
  ↓
validate_outline
  ↓
initialize_interactive_html_units
  └─ 写入 DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE
  ↓
逐 section 循环：
  retrieve_for_unit
    ↓
  generate_unit_spec
    └─ interactive_html_unit_spec.md -> InteractiveHtmlSectionSpec
    ↓
  validate_unit_spec
    ├─ pass
    ├─ repair_unit_spec
    └─ fallback_unit_spec
    ↓
  collect_unit_required_elements
    └─ 当前 interactive_html 不生成 image / mindmap 元素
    ↓
  render_unit
    ├─ InteractionTemplateRenderer
    ├─ ExplanationHtmlComposer
    ├─ UnitHtmlAssembler
    ├─ sanitize_rendered_unit
    └─ validate_rendered_unit
    ↓
  publish_unit_render
    └─ unit_render_ready event
    ↓
  merge_unit_result
  ↓
assemble_content_spec
  └─ InteractiveHtmlSpec
  ↓
validate_content
  ↓
interactive_html_renderer
  └─ InteractiveHtmlRenderModel
  ↓
finalize_task
```

## 4. 相关文件

| 类型 | 路径 |
|---|---|
| 内容类型 profile | `app/content_types/interactive_html.py` |
| 内容类型注册 | `app/content_types/registry.py` |
| workflow 图 | `app/workflows/content_generation_graph.py` |
| unit loop 节点 | `app/workflows/nodes/unit_loop_node.py` |
| unit spec 生成节点 | `app/workflows/nodes/unit_spec_generator_node.py` |
| unit render 节点 | `app/workflows/nodes/unit_renderer_node.py` |
| render repair 节点 | `app/workflows/nodes/render_unit_repair_node.py` |
| content assemble 节点 | `app/workflows/nodes/assembler_node.py` |
| final renderer 节点 | `app/workflows/nodes/renderer_node.py` |
| spec schema | `app/schemas/specs/interactive_html.py` |
| style schema | `app/schemas/specs/interactive_html_style.py` |
| render schema | `app/schemas/render/interactive_html.py` |
| validator | `app/validators/interactive_html_validator.py` |
| interaction template renderer | `app/renderers/interactive_html_interaction_renderer.py` |
| explanation composer | `app/renderers/interactive_html_explanation_composer.py` |
| unit assembler | `app/renderers/interactive_html_unit_assembler.py` |
| unit composer | `app/renderers/interactive_html_composer.py` |
| final renderer | `app/renderers/interactive_html_renderer.py` |
| offline handout renderer | `app/renderers/interactive_html_handout.py` |
| HTML exporter | `app/exporters/html_exporter.py` |
| learning API | `app/api/learning.py` |
| learning schema | `app/schemas/learning.py` |
| learning service | `app/services/learning_service.py` |
| outline prompt | `app/prompts/planner/interactive_html_outline.md` |
| unit spec prompt | `app/prompts/generator/interactive_html_unit_spec.md` |
| unit render prompt | `app/prompts/generator/interactive_html_unit_render.md` |
| render repair prompt | `app/prompts/reviewer/interactive_html_render_repair.md` |

## 5. ContentTypeProfile

`interactive_html` profile 当前配置：

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
| `allowed_elements` | 空，当前不走 image / mindmap 元素分支 |
| `default_required_elements` | 空 |
| `optional_elements` | 空 |
| `exporter_types` | `html` |

## 6. Schema 结构

### 6.1 InteractiveHtmlSectionSpec

`InteractiveHtmlSectionSpec` 是单个互动课件 section 的教学设计规格。

| 字段 | 说明 |
|---|---|
| `section_id` | section ID，必须与当前 outline unit id 一致。 |
| `title` | section 标题。 |
| `learning_goal` | 学习目标。 |
| `narrative_goal` | 叙事目标或学习旅程。 |
| `teaching_flow` | 3-7 个教学块。 |
| `interaction_specs` | 当前 section 的互动规格。 |
| `concepts` | 概念引用。 |
| `citations` | 来源引用。 |

### 6.2 InteractiveHtmlTeachingBlock

`InteractiveHtmlTeachingBlock` 描述一个教学块的教学意图。

| 字段 | 说明 |
|---|---|
| `block_id` | 当前 section 内唯一。 |
| `block_type` | 教学块类型。 |
| `title` | 教学块标题。 |
| `teaching_role` | 教学角色，例如 `set_context`、`explain_core`、`diagnose_understanding`。 |
| `content_goal` | 该块需要达成的讲解目标。 |
| `must_cover` | 必须覆盖的信息点。 |
| `suggested_expression` | 可选表达建议。 |
| `interaction_id` | 若该 block 对应互动题，则指向 `interaction_specs`。 |
| `source_refs` | 引用的 chunk id。 |

当前允许的 `block_type`：

```text
intro
concept_explanation
case_compare
animated_flow
context_inspector
stepper
socratic_chat
scenario
scenario_discussion
single_choice
multiple_choice
short_answer
drag_match
sequence
reflection
summary
```

当前 P0 实际模板渲染的互动 block 类型为：

```text
single_choice
multiple_choice
short_answer
scenario_discussion
```

### 6.3 InteractiveHtmlInteractionSpec

`InteractiveHtmlInteractionSpec` 描述可交互题目的运行时契约。

| 字段 | 说明 |
|---|---|
| `interaction_id` | 当前 section 内唯一。 |
| `block_id` | 关联的 teaching block。 |
| `type` | `single_choice` / `multiple_choice` / `short_answer` / `scenario_discussion`。 |
| `event_type` | 前端提交事件类型。 |
| `target_concepts` | 诊断或练习的概念。 |
| `prompt` | 题干或互动提示。 |
| `options` | 选择题选项。 |
| `feedback_policy` | `local` / `submit_to_backend` / `local_and_submit`。 |
| `placeholder` | 文本输入占位符。 |
| `reference_points` | 简答 / 情景讨论参考要点。 |
| `min_length` | 简答 / 情景讨论最小字数建议。 |
| `scenario` | 情景讨论背景和任务。 |
| `visual_variant` | 视觉样式变体。 |
| `allow_adaptive_followup` | 是否允许后续自适应追问。 |

四类 P0 互动约束：

| 类型 | 硬约束 |
|---|---|
| `single_choice` | 至少 4 个 options；必须且只能有 1 个正确项；每个 option 必须有 feedback。 |
| `multiple_choice` | 至少 4 个 options；至少 1 个正确项；每个 option 必须有 feedback；采用选择 + 提交两步。 |
| `short_answer` | 必须有 prompt 和 placeholder；建议提供 reference_points 和 min_length。 |
| `scenario_discussion` | 必须有 prompt；`scenario.background` 和 `scenario.task` 必填；建议提供 reference_points 和 min_length。 |

### 6.4 InteractiveHtmlSpec

`InteractiveHtmlSpec` 是最终内容规格。

| 字段 | 说明 |
|---|---|
| `content_type` | 固定为 `interactive_html`。 |
| `lesson_id` | lesson ID。 |
| `title` | 课程标题。 |
| `subtitle` | 可选副标题。 |
| `meta` | 语言、受众、难度、预计时长。 |
| `pedagogy` | 导师语气、互动密度、术语难度。 |
| `sections` | 所有 `InteractiveHtmlSectionSpec`。 |
| `citations` | 全局引用。 |
| `assets` | 资源引用，当前预留。 |
| `export_options` | 导出选项。 |

### 6.5 InteractiveHtmlRenderedUnit

`InteractiveHtmlRenderedUnit` 是单个 section 的前端渲染片段。

| 字段 | 说明 |
|---|---|
| `section_id` | section ID。 |
| `title` | section 标题。 |
| `learning_goal` | 学习目标。 |
| `style_scope_id` | CSS 作用域 ID，例如 `ih-scope-unit_01`。 |
| `html_fragment` | 受限 HTML 片段，根节点为单个 section。 |
| `css_fragment` | 当前 section 的 CSS 片段。 |
| `block_manifest` | block 元信息清单。 |
| `interaction_manifest` | interaction 元信息清单。 |
| `render_notes` | 渲染备注、fallback 信息、缺失 block 信息。 |

### 6.6 InteractiveHtmlRenderModel

`InteractiveHtmlRenderModel` 是完整在线课件的前端契约。

| 字段 | 说明 |
|---|---|
| `render_type` | 固定为 `interactive_html_page`。 |
| `lesson_id` | lesson ID。 |
| `title` | 课程标题。 |
| `subtitle` | 可选副标题。 |
| `layout` | 固定为 `vertical_lesson_with_tutor`。 |
| `theme` | 从 style guide 派生的主题信息。 |
| `navigation` | section 导航。 |
| `interactions` | 全局互动清单。 |
| `runtime` | 运行时配置。 |
| `meta` | 元信息。 |
| `pedagogy` | 教学策略信息。 |
| `sections` | 所有 `InteractiveHtmlRenderedUnit`。 |
| `style_guide` | 完整样式指南。 |
| `citations` | 引用信息。 |

## 7. Prompt 分工

### 7.1 interactive_html_outline.md

目标：生成课程内容大纲。

输入：

- 用户主题
- 用户需求
- generation options
- planning 检索结果

输出：

- `Outline`

要求：

- `content_type` 固定为 `interactive_html`。
- units 中每个 unit 的 `unit_type` 固定为 `interactive_section`。
- units 至少 1 个，不能超过 `generation_options.max_section_count`；按主题复杂度、学习目标、深度与资料确定，默认上限为 8。
- 每个 unit 提供 `retrieval_queries` 和 `source_chunk_ids`。
- 不指定具体 Block 类型。
- 不规划互动检查点位置。
- 不指定图片、示例、流程动画、情景教学或练习题。

### 7.2 interactive_html_unit_spec.md

目标：根据 outline unit 和 section 检索结果生成教学设计规格。

输入：

- `unit_spec_id`
- `outline_unit`
- section 检索结果
- generation options

输出：

- `InteractiveHtmlSectionSpec`

要求：

- 只输出 JSON。
- 禁止输出 HTML、CSS、Markdown、解释性文字。
- `teaching_flow` 包含 3-7 个教学块。
- `interaction_specs` 通常包含 1-2 个互动点。
- 互动题必须服务于理解诊断、反思或迁移。
- 选择题必须包含正确答案和本地 feedback。
- 简答和情景讨论必须包含 reference_points。

### 7.3 interactive_html_unit_render.md

目标：根据 Unit Spec 生成非互动教学块的 HTML + CSS。

输入：

- Unit Spec
- Course Style Guide
- Runtime Contract
- 检索上下文

输出：

- `InteractiveHtmlExplanationRender`

要求：

- 只生成非互动 teaching blocks。
- 每个 block value 是单个 `<article>` 根节点。
- CSS 必须带 `style_scope_id` 作用域。
- 禁止输出互动 DOM。
- 禁止完整页面标签、script、外链资源、内联事件和全局 CSS。

### 7.4 interactive_html_render_repair.md

目标：修复未通过校验的 `InteractiveHtmlRenderedUnit`。

输入：

- 原始渲染产物
- 校验报告
- Unit Spec
- Course Style Guide

输出：

- 修复后的 `InteractiveHtmlRenderedUnit`

要求：

- 只修复校验报告指出的问题。
- 保持原有教学结构和内容。
- CSS 作用域、manifest 和 DOM 标记必须对齐。
- 不发明新的 `data-ih-action`。

## 8. 渲染实现

### 8.1 InteractionTemplateRenderer

`InteractionTemplateRenderer` 负责把 `interaction_specs` 变成稳定互动 DOM。

当前生成的关键 runtime attributes：

| 属性 | 用途 |
|---|---|
| `data-ih-action` | 前端 runtime 识别点击 / 提交动作。 |
| `data-interaction-id` | 绑定互动 ID。 |
| `data-option-id` | 绑定选项 ID。 |
| `data-correct` | 本地判断正确性。 |
| `data-feedback` | 本地反馈文本。 |
| `data-ih-input-for` | 文本输入框与互动 ID 绑定。 |
| `data-ih-feedback-for` | 反馈区域与互动 ID 绑定。 |
| `data-reference-points` | 简答 / 情景讨论参考要点。 |
| `data-min-length` | 文本输入最小长度建议。 |

当前 runtime action：

```text
single-choice
multiple-choice-toggle
multiple-choice-submit
short-answer-submit
scenario-discussion-submit
```

### 8.2 ExplanationHtmlComposer

`ExplanationHtmlComposer` 负责调用 LLM 生成非互动讲解区。

处理步骤：

1. 从 `section_spec.teaching_flow` 中剔除互动 blocks。
2. 构造 `interactive_html_unit_render.md` prompt。
3. 调用 `get_llm_service().generate_structured(...)`。
4. 校验 `block_html_map` 和 `css_fragment`。
5. 如果校验失败，回退到 fallback block 和 fallback CSS。

### 8.3 UnitHtmlAssembler

`UnitHtmlAssembler` 负责按 `teaching_flow` 顺序组装：

- 若 block 是互动 block，插入模板生成的互动 HTML。
- 若 block 是非互动 block，插入 LLM 生成的讲解 HTML。
- 若 block 缺失，插入 warning fallback block。
- 生成 `block_manifest` 和 `interaction_manifest`。
- 合并讲解 CSS 与互动基础 CSS。

### 8.4 InteractiveHtmlComposer

`InteractiveHtmlComposer` 是单元级 orchestrator：

```text
compose_unit(section_spec, style_guide, retrieval_context)
  ↓
InteractionTemplateRenderer.render
  ↓
ExplanationHtmlComposer.compose
  ↓
UnitHtmlAssembler.assemble
  ↓
sanitize_rendered_unit
  ↓
validate_rendered_unit
  ↓
InteractiveHtmlRenderedUnit
```

如果最终校验失败，会抛出 `InteractiveHtmlRenderError`，交给 workflow 的 `route_after_render_unit` 决定 retry、repair、fallback 或 fail。

### 8.5 InteractiveHtmlRenderer

`InteractiveHtmlRenderer.assemble(...)` 负责把多个 `InteractiveHtmlRenderedUnit` 汇总为完整 render model：

- 生成 `navigation`。
- 汇总 `interactions`。
- 写入 `runtime`。
- 写入 `theme` 和 `style_guide`。
- 写入 `sections`。

## 9. Validator 与安全约束

`interactive_html_validator.py` 当前覆盖以下约束：

### 9.1 Unit Spec 校验

- `section_id`、`title`、`learning_goal` 必填。
- `teaching_flow` 必须 3-7 个 block。
- `block_id` 唯一。
- block type 必须在允许集合内。
- 每个 block 必须有 `content_goal`。
- 至少包含一个讲解型 block。
- `interaction_id` 唯一。
- `interaction_specs.block_id` 必须存在于 `teaching_flow`。
- 四类 P0 互动必须满足题型硬约束。

### 9.2 Explanation Render 校验

- 非互动讲解 HTML 禁止 `script`、`style`、`button`、`input`、`textarea`、`form`。
- 禁止 `onclick` 等内联事件。
- 禁止 `data-ih-action` 和 `data-interaction-id`。
- CSS 不能为空。
- CSS 禁止 `body`、`html`、`:root` 全局选择器。
- CSS 禁止 `@import`、`url(...)`、`position: fixed`。
- CSS selector 必须包含 `style_scope_id`。

### 9.3 Rendered Unit 校验

- `html_fragment` 必须有单个 root section。
- 根 section 必须有 `id`、`class`、`data-section-id`。
- 禁止完整页面标签和危险标签。
- 互动 action 必须在允许集合内。
- block manifest 必须覆盖 DOM 中所有 `data-block-id`。
- interaction manifest 必须覆盖 DOM 中所有 `data-interaction-id`。
- CSS 必须经过作用域约束。

## 10. 学习事件与运行时

### 10.1 Runtime Config

`InteractiveRuntimeConfig` 当前默认值：

| 字段 | 默认值 | 说明 |
|---|---|---|
| `progress_tracking` | `true` | 开启学习进度追踪。 |
| `scoring_enabled` | `true` | 开启答题得分 / 正误记录。 |
| `session_required` | `true` | 在线互动需要 session。 |
| `event_endpoint_template` | `/api/interactive-lessons/{lesson_id}/sessions/{session_id}/events` | 前端提交互动事件的接口模板。 |

### 10.2 Learning API

创建 session：

```http
POST /api/interactive-lessons/{lesson_id}/sessions
```

提交事件：

```http
POST /api/interactive-lessons/{lesson_id}/sessions/{session_id}/events
```

查询 session state：

```http
GET /api/interactive-lessons/{lesson_id}/sessions/{session_id}/state
```

当前正式入口使用 `LearningService` 与 `SQLModelLearningRepository`，学习会话和事件保存在数据库中，复用任务仓储的数据库引擎。服务重启后可以继续读取。`InMemoryLearningService` 仅保留给独立检查使用。

除会话创建、事件提交和状态读取外，还提供学习摘要与规则复习要求接口，见[学习记录与复习](../../docs/design/learning-loop.md)。单选、多选提供本地答案判定；简答和讨论记录文本，未评分回答不计入正确率分母。

当前 event payload 支持：

| 字段 | 说明 |
|---|---|
| `selected_option_ids` | 选择题已选选项。 |
| `correct_option_ids` | 正确选项。 |
| `ordered_item_ids` | 排序结果，预留。 |
| `match_pairs` | 匹配结果，预留。 |
| `answer_text` | 简答 / 讨论文本。 |
| `is_correct` | 本地判断正确性。 |
| `reference_points` | 参考要点。 |
| `matched_points` | 命中的参考要点。 |
| `heuristic_score` | 简单启发式得分。 |
| `client_timestamp` | 前端提交时间。 |
| `confidence` | 学生自评信心。 |
| `time_spent_seconds` | 作答耗时。 |

## 11. 离线讲义导出

`interactive_html` 当前通过 `HTMLExporter` 导出离线复习讲义。

请求：

```http
POST /api/content-generation/tasks/{task_id}/export
```

请求体：

```json
{
  "export_type": "html",
  "export_options": {
    "session_id": "session_xxxxxxxxxxxx"
  }
}
```

导出流程：

```text
HTMLExporter.export
  ↓
判断 render_model 是否为 InteractiveHtmlRenderModel
  ↓
读取 export_options.session_id
  ↓
读取 content_spec，并校验为 InteractiveHtmlSpec
  ↓
learning_service.list_events(render_model.lesson_id, session_id)
  ↓
InteractiveHtmlStaticHandoutRenderer.render
  ↓
LocalStorageService.save_bytes
  ↓
ExportResult(file_url=...)
```

离线讲义处理逻辑：

- 使用在线课件 shell 样式。
- 保留 section 导航。
- 移除在线互动控件。
- 移除 `data-ih-action`、`data-ih-input-for`、`data-ih-feedback-for` 等运行时属性。
- 将学生答题事件转换为“答题记录”。
- 对服务端图片资源尝试 base64 内联。
- 保存为 `{task_id}-offline-handout.html`。

当前限制：

- 学习会话与事件保存到数据库，服务重启后仍可导出有效会话的作答记录。
- 当前导出需要已有 `content_spec` 和 `render_model`。
- 当前 API 可用导出为 `html`；`zip` 尚未接入 `ExportType` 和 exporter router。

## 12. 测试覆盖

当前相关测试：

| 测试文件 | 覆盖内容 |
|---|---|
| `tests/test_interactive_html_prompts.py` | prompt 职责边界、字段要求、render prompt 格式化。 |
| `tests/test_interactive_html_renderer.py` | render model assemble、四类互动模板、unit assembler、render_unit、repair / fallback。 |
| `tests/test_interactive_html_validator.py` | unit spec 校验、render fragment 校验、sanitizer、manifest 一致性。 |
| `tests/test_interactive_html_handout.py` | 离线讲义静态化、导航、答题记录、图片内联。 |
| `tests/test_workflow_structure.py` | workflow 节点和 repair / fallback 路径。 |
| `tests/test_unit_streaming.py` | 单元级流式快照和 partial preview。 |

常用命令：

```bash
pytest tests/test_interactive_html_prompts.py tests/test_interactive_html_renderer.py tests/test_interactive_html_validator.py tests/test_interactive_html_handout.py -q
```

## 13. 前端对接要点

前端渲染 `InteractiveHtmlRenderModel` 时需要关注：

1. `render_model.render_type` 为 `interactive_html_page`。
2. `render_model.layout` 为 `vertical_lesson_with_tutor`。
3. `render_model.sections[*].html_fragment` 是受限 HTML 片段。
4. `render_model.sections[*].css_fragment` 是当前 section 的 scoped CSS。
5. `render_model.navigation` 用于目录导航。
6. `render_model.interactions` 用于建立互动索引。
7. `render_model.runtime.event_endpoint_template` 用于提交学习事件。
8. 前端需要先创建 session，再允许提交互动。
9. 互动题点击、选择、提交由 `data-ih-action` 驱动。
10. 生成中可用 `preview/partial` 进行 section 级增量渲染。

## 14. 当前待完善事项

1. 学习会话与事件已经持久化，学习摘要和复习生成可以读取历史任务；长期学习画像仍待实现。
2. 当前 profile 仅声明 HTML 导出。ZIP 属于尚未实现的扩展格式。
3. 为 `repair_render_unit` 接入更明确的 LLM repair 输出链路，目前 `repair_context` 已传入 composer，但主要 repair 行为仍依赖重新 compose。
4. 扩展前端 runtime 对 `drag_match`、`sequence`、`socratic_chat`、`scenario` 的模板支持。
5. 将 `duration_minutes`、`section_count` 对 interactive_html 的影响进一步落到 planner 逻辑和 request validator 中。
6. 为离线讲义增加更完整的学习分析摘要。
7. 增加真实 LLM 下 interactive_html render 的慢任务回归样例。
