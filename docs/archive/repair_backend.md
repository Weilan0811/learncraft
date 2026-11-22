# Interactive HTML P0 受控自由渲染修改指南

## 1. 修改目标

本次修改只完善 P0 在线互动 HTML 生成闭环，不实现 P1 离线 handout。

P0 的目标是把当前 `interactive_html` 从“LLM 直接在 Unit Spec 中写 `html_fragment`，Renderer 做简单清洗”调整为“受控自由 HTML 渲染”。

调整后的生成链路为：

```text
用户请求
  ↓
知识库检索
  ↓
Outline 生成
  ↓
课程级 Style Guide 生成
  ↓
逐 unit 生成 Unit Spec
  ↓
逐 unit 调用 LLM Render / HTML Composer
  ↓
HTML + CSS + Interaction 协议校验
  ↓
前端组装在线课件
  ↓
创建 Learning Session
  ↓
记录 LearningEvent
```

核心原则：

1. Outline 保持现有职责，继续负责课程内容结构和 unit 划分。
2. Unit Spec 聚焦教学组织，负责说明当前 unit 如何把知识讲清楚。
3. Render 阶段调用大模型，根据 Unit Spec 生成美观、连贯、可直接展示的 HTML + CSS。
4. 前端负责课程壳、侧边导航、unit 路由、交互 runtime 和事件提交。
5. 后端负责生成协议、交互标记、CSS 作用域、安全校验、render repair。
6. P0 暂不生成 `OfflineHandoutSpec`，暂不生成总结知识卡片，暂不做个性化补丁。

---

## 2. 当前后端状态判断

当前后端已有 `interactive_html` 的基本闭环：

| 模块 | 当前文件 | 当前状态 |
|---|---|---|
| 内容类型注册 | `app/content_types/interactive_html.py` | 已有 `interactive_html` profile |
| Outline Prompt | `app/prompts/planner/interactive_html_outline.md` | 效果可保留 |
| Unit Spec Prompt | `app/prompts/generator/interactive_html_unit_spec.md` | 同时承担教学设计和 HTML 生成，需要拆分 |
| Unit Spec Schema | `app/schemas/specs/interactive_html.py` | `InteractiveHtmlSectionSpec` 中包含 `html_fragment`，需要调整 |
| Renderer | `app/renderers/interactive_html_renderer.py` | 目前主要做 `sanitize_html_fragment` 和 assemble，需要升级为 LLM Composer |
| Validator | `app/validators/interactive_html_validator.py` | 目前校验 HTML fragment，需要拆成 spec 校验和 render package 校验 |
| Unit Render Node | `app/workflows/nodes/unit_renderer_node.py` | 已有逐 unit render 节点，可复用并改造 |
| Final Renderer Node | `app/workflows/nodes/renderer_node.py` | 当前会重新 render 整体 spec，需要避免重复生成 |
| Learning API | `app/api/learning.py` | 已有 session 与 event API，P0 可继续使用 |
| Learning Service | `app/services/learning_service.py` | 目前为内存实现，P0 demo 可用，稳定联调建议落库 |

本次修改的重点不是重做整个 workflow，而是把 `interactive_html` 的 spec/render 边界理清，并让 render 阶段具备独立的大模型 HTML 生成能力。

---

## 3. 新的 P0 产物边界

### 3.1 Outline 产物

保持现有 `InteractiveHtmlOutline`，不做大改。

Outline 继续输出：

```text
课程标题
课程目标
目标受众
难度等级
unit / section 列表
每个 unit 的学习目标
每个 unit 的核心概念
每个 unit 的关键问题或知识范围
```

Outline 不负责：

```text
不指定具体 HTML
不指定 CSS
不指定互动控件具体结构
不指定页面版式
不指定动画细节
```

### 3.2 Unit Spec 产物

Unit Spec 输出教学设计，不输出 HTML。

建议将 `InteractiveHtmlSectionSpec` 调整为：

```python
class InteractiveHtmlSectionSpec(SchemaModel):
    section_id: str
    title: str
    learning_goal: str
    narrative_goal: str
    teaching_flow: list[InteractiveHtmlTeachingBlock] = Field(default_factory=list)
    interaction_specs: list[InteractiveHtmlInteractionSpec] = Field(default_factory=list)
    concepts: list[ConceptRef] = Field(default_factory=list)
    citations: list[CitationRef] = Field(default_factory=list)
```

新增教学 block schema：

```python
class InteractiveHtmlTeachingBlock(SchemaModel):
    block_id: str
    block_type: Literal[
        "intro",
        "concept_explanation",
        "case_compare",
        "animated_flow",
        "context_inspector",
        "stepper",
        "socratic_chat",
        "scenario",
        "single_choice",
        "multiple_choice",
        "short_answer",
        "drag_match",
        "sequence",
        "reflection",
        "summary",
    ]
    title: str
    teaching_role: str
    content_goal: str
    must_cover: list[str] = Field(default_factory=list)
    suggested_expression: str | None = None
    interaction_id: str | None = None
    source_refs: list[str] = Field(default_factory=list)
```

新增互动 spec：

```python
class InteractiveHtmlInteractionSpec(SchemaModel):
    interaction_id: str
    block_id: str
    type: Literal[
        "single_choice",
        "multiple_choice",
        "short_answer",
        "drag_match",
        "sequence",
        "socratic_chat",
        "scenario",
        "complete_section",
        "tab_select",
        "flow_control",
    ]
    event_type: Literal[
        "single_choice_answered",
        "multiple_choice_answered",
        "short_answer_submitted",
        "drag_match_submitted",
        "sequence_submitted",
        "socratic_round_answered",
        "scenario_choice_selected",
        "hint_requested",
        "confused_clicked",
    ]
    target_concepts: list[str] = Field(default_factory=list)
    prompt: str | None = None
    options: list[dict] = Field(default_factory=list)
    feedback_policy: Literal["frontend_static", "submit_to_backend"] = "submit_to_backend"
    allow_adaptive_followup: bool = True
```

### 3.3 Render 产物

Render 阶段输出 `InteractiveHtmlRenderedUnit`，包含 HTML、CSS 和前端 runtime 所需 manifest。

建议新增或替换当前 `InteractiveHtmlRenderSection`：

```python
class InteractiveHtmlRenderedUnit(SchemaModel):
    section_id: str
    title: str
    learning_goal: str
    style_scope_id: str
    html_fragment: str
    css_fragment: str
    block_manifest: list[InteractiveHtmlRenderBlockRef] = Field(default_factory=list)
    interaction_manifest: list[InteractionRenderRef] = Field(default_factory=list)
    render_notes: dict = Field(default_factory=dict)
```

`html_fragment` 只包含当前 unit 的 `<section>`，不包含完整页面标签：

```html
<section
  id="unit_01"
  class="ih-unit ih-scope-unit-01"
  data-section-id="unit_01"
>
  ...
</section>
```

`css_fragment` 必须被 `style_scope_id` 作用域包住：

```css
.ih-scope-unit-01 {
  --ih-accent: #5b6cff;
  --ih-surface: #ffffff;
}

.ih-scope-unit-01 .ih-card {
  border-radius: 24px;
  padding: 20px;
}
```

---

## 4. 课程级 Style Guide

为了解决各 unit 风格不一致的问题，在 Outline 之后新增一个课程级 Style Guide。

### 4.1 新增 schema

建议新增文件：

```text
app/schemas/specs/interactive_html_style.py
```

内容示例：

```python
class InteractiveHtmlCourseStyleGuide(SchemaModel):
    style_id: str
    layout_mode: Literal["vertical_lesson_with_tutor"] = "vertical_lesson_with_tutor"
    visual_keywords: list[str] = Field(default_factory=list)
    color_tokens: dict[str, str] = Field(default_factory=dict)
    typography: dict[str, str] = Field(default_factory=dict)
    component_motifs: list[str] = Field(default_factory=list)
    interaction_style: dict[str, str] = Field(default_factory=dict)
    animation_style: dict[str, str] = Field(default_factory=dict)
    spacing_density: Literal["compact", "medium", "relaxed"] = "medium"
    avoid: list[str] = Field(default_factory=list)
```

### 4.2 推荐默认值

P0 可以先使用默认 Style Guide，后续再调用大模型生成。

```json
{
  "style_id": "warm_tutor_card_v1",
  "layout_mode": "vertical_lesson_with_tutor",
  "visual_keywords": ["温和", "卡片式", "流程清晰", "轻量动画"],
  "color_tokens": {
    "background": "#f7f4ef",
    "surface": "#ffffff",
    "primary": "#5b6cff",
    "accent": "#ffb86b",
    "text": "#1f2937"
  },
  "component_motifs": [
    "rounded cards",
    "soft shadow",
    "dotted connector",
    "teacher speech bubble",
    "step badges"
  ],
  "avoid": [
    "dense tables",
    "tiny text",
    "large empty space",
    "unbalanced two-column layout",
    "unscoped css"
  ]
}
```

### 4.3 工作流落点

新增节点二选一：

方案 A：显式新增节点，推荐。

```text
plan_outline
  ↓
generate_interactive_html_style_guide
  ↓
initialize_interactive_html_units
```

方案 B：不改 graph，在 `initialize_interactive_html_units` 或 `render_unit` 中注入默认 Style Guide。

P0 demo 更建议先用方案 B 快速落地；如果要提升风格一致性和可配置性，再改成方案 A。

---

## 5. Prompt 修改

### 5.1 拆分现有 Unit Spec Prompt

当前文件：

```text
app/prompts/generator/interactive_html_unit_spec.md
```

当前问题：该 prompt 同时要求模型输出 `html_fragment`、block refs 和 interaction refs，导致 spec 和 render 混在一起。

修改后，该文件只输出教学设计 JSON。

新的 prompt 目标：

```text
你是互动式 HTML 课件单元教学设计器。
你需要根据 outline_unit 和检索结果，规划当前 unit 的教学展开方式。
你只输出 InteractiveHtmlSectionSpec JSON。
禁止输出 HTML、CSS、Markdown、解释性文字。
```

建议 prompt 结构：

```text
## 输出字段
- section_id
- title
- learning_goal
- narrative_goal
- teaching_flow
- interaction_specs
- concepts
- citations

## 教学组织要求
- 目标是把当前 unit 的知识讲清楚。
- 使用若干个 teaching block 组织讲解、案例、流程、互动、总结。
- 每个 block 写清楚教学作用、内容目标、必须覆盖的信息。
- 互动题服务于理解诊断、反思或迁移。
- 通常 1-2 个互动点。
- 不生成 HTML。
- 不生成 CSS。
- 不指定具体 class。
```

### 5.2 新增 Unit Render Prompt

新增文件：

```text
app/prompts/generator/interactive_html_unit_render.md
```

该 prompt 负责把 Unit Spec 渲染成 HTML + CSS package。

核心要求：

```text
你是互动式 HTML 课件视觉渲染器。
你需要根据 Unit Spec、Course Style Guide、Runtime Contract，生成当前 unit 的 HTML + CSS。
页面应该完整、连贯、美观，避免机械套模板。
你可以参考 block 类型的教学意图自由设计布局。
你必须遵守交互协议、CSS 作用域和安全约束。
```

输出 JSON：

```json
{
  "section_id": "...",
  "title": "...",
  "learning_goal": "...",
  "style_scope_id": "ih-scope-unit-01",
  "html_fragment": "<section ...>...</section>",
  "css_fragment": ".ih-scope-unit-01 { ... }",
  "block_manifest": [],
  "interaction_manifest": [],
  "render_notes": {}
}
```

Render prompt 需要明确：

```text
允许自由设计：
- 布局节奏
- 卡片组合
- 流程展示方式
- 对话导师呈现方式
- 小动画 class 命名
- 视觉层次和留白

必须固定：
- 根节点必须是单个 section
- 根 section 必须有 id、class、data-section-id
- 每个教学区块必须有 data-block-id、data-block-type
- 每个互动元素必须有 data-ih-action 和 data-interaction-id
- interaction_manifest 必须覆盖所有 data-interaction-id
- CSS 必须用 style_scope_id 作用域包住
- 禁止 script、iframe、外链资源、内联事件
```

### 5.3 新增可选 Style Guide Prompt

如果采用显式风格生成，新增：

```text
app/prompts/generator/interactive_html_style_guide.md
```

输入：课程标题、课程目标、受众、难度、outline。  
输出：`InteractiveHtmlCourseStyleGuide` JSON。

P0 可先使用默认 Style Guide，暂不新增该 prompt。

---

## 6. Renderer / Composer 修改

### 6.1 当前 renderer 的问题

当前 `app/renderers/interactive_html_renderer.py` 的核心逻辑是：

```python
html_fragment=sanitize_html_fragment(section.html_fragment)
```

这意味着 HTML 已经在 Unit Spec 阶段生成，Renderer 只做清洗和组装。

### 6.2 修改目标

将 renderer 升级为 `InteractiveHtmlComposer`。

推荐新增文件：

```text
app/renderers/interactive_html_composer.py
```

职责：

```text
输入：InteractiveHtmlSectionSpec + CourseStyleGuide + RuntimeContract
调用：LLM generate_structured
输出：InteractiveHtmlRenderedUnit
校验：validate_rendered_unit
失败：repair / fallback
```

接口示例：

```python
class InteractiveHtmlComposer:
    def compose_unit(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
        runtime_contract: InteractiveHtmlRuntimeContract,
        retrieval_context: list | None = None,
    ) -> InteractiveHtmlRenderedUnit:
        ...
```

### 6.3 `InteractiveHtmlRenderer` 的新职责

保留 `InteractiveHtmlRenderer`，但只负责 assemble。

```python
class InteractiveHtmlRenderer:
    def assemble(
        self,
        lesson_id: str,
        title: str,
        rendered_units: list[InteractiveHtmlRenderedUnit],
        style_guide: InteractiveHtmlCourseStyleGuide,
    ) -> InteractiveHtmlRenderModel:
        ...
```

Final render 不再重新生成每个 unit 的 HTML。

---

## 7. Workflow 修改

### 7.1 修改 `render_unit`

当前文件：

```text
app/workflows/nodes/unit_renderer_node.py
```

当前逻辑：

```python
elif isinstance(state.current_unit_spec, InteractiveHtmlSectionSpec):
    fragment = InteractiveHtmlRenderer().render_unit(state.current_unit_spec, unit_elements).model_dump(mode="json")
```

修改为：

```python
elif isinstance(state.current_unit_spec, InteractiveHtmlSectionSpec):
    style_guide = get_or_build_interactive_html_style_guide(state)
    runtime_contract = build_interactive_html_runtime_contract()
    rendered_unit = InteractiveHtmlComposer().compose_unit(
        section_spec=state.current_unit_spec,
        style_guide=style_guide,
        runtime_contract=runtime_contract,
        retrieval_context=state.current_unit_context,
    )
    fragment = rendered_unit.model_dump(mode="json")
```

### 7.2 修改 partial render model

当前 `_build_partial_render_model()` 中：

```python
sections = [InteractiveHtmlRenderSection.model_validate(snapshot.render_fragment) ...]
return InteractiveHtmlRenderer()._assemble(spec, sections)
```

修改为：

```python
rendered_units = [
    InteractiveHtmlRenderedUnit.model_validate(snapshot.render_fragment)
    for snapshot in ordered
    if snapshot.status == "rendered"
]
return InteractiveHtmlRenderer().assemble(
    lesson_id=f"partial_lesson_{state.request_id}",
    title=state.outline.title if state.outline else state.topic,
    rendered_units=rendered_units,
    style_guide=get_or_build_interactive_html_style_guide(state),
)
```

### 7.3 修改 final renderer

当前 `interactive_html_renderer` 会基于 `content_spec` 再 render 一次。

建议改为从 `state.render_units` 组装最终 `InteractiveHtmlRenderModel`：

```python
def interactive_html_renderer(state: ContentGenerationState) -> dict[str, object]:
    rendered_units = sorted(
        [snapshot for snapshot in state.render_units.values() if snapshot.status == "rendered"],
        key=lambda snapshot: snapshot.order,
    )
    render_model = InteractiveHtmlRenderer().assemble(
        lesson_id=f"lesson_{state.request_id}",
        title=state.outline.title if state.outline else state.topic,
        rendered_units=[InteractiveHtmlRenderedUnit.model_validate(s.render_fragment) for s in rendered_units],
        style_guide=get_or_build_interactive_html_style_guide(state),
    )
    return {"render_model": render_model, ...}
```

这样可以避免 final renderer 重新调用 LLM，保护流式预览结果和最终结果一致。

---

## 8. Validator 修改

### 8.1 拆分校验职责

当前文件：

```text
app/validators/interactive_html_validator.py
```

建议拆成三类校验：

```python
def validate_unit_spec(section: InteractiveHtmlSectionSpec) -> InteractiveHtmlValidationReport:
    ...

def validate_rendered_unit(unit: InteractiveHtmlRenderedUnit) -> InteractiveHtmlValidationReport:
    ...

def sanitize_rendered_unit(unit: InteractiveHtmlRenderedUnit) -> InteractiveHtmlRenderedUnit:
    ...
```

### 8.2 Unit Spec 校验

检查内容：

```text
section_id/title/learning_goal 不为空
teaching_flow 至少 3 个 block
teaching_flow 中 block_id 唯一
interaction_specs 中 interaction_id 唯一
interaction_specs.block_id 必须存在于 teaching_flow
互动 block 必须有对应 interaction_spec
每个 block 有明确 content_goal
每个 unit 至少有 1 个讲解类 block
复杂 unit 通常至少有 1 个互动类 block
citations/source_refs 使用当前检索 chunk id
```

### 8.3 Rendered Unit 校验

检查 HTML：

```text
html_fragment 必须是单个 section 根节点
section id 必须等于 section_id
根节点必须包含 style_scope_id class
禁止 html/head/body/script/style/iframe/object/embed/link/meta
禁止 onClick/onChange/onInput 等内联事件
禁止 javascript: URL
每个 data-block-id 必须出现在 block_manifest
每个 data-interaction-id 必须出现在 interaction_manifest
每个 data-ih-action 必须属于允许列表
文本长度不能过短
至少有标题、正文和可视化教学结构
```

检查 CSS：

```text
css_fragment 不能为空
所有主要选择器必须以 .{style_scope_id} 开头
禁止 body/html/:root 全局选择器
禁止 @import
禁止 url(http...), url(https...), 外链字体和外链图片
禁止 position: fixed
限制 z-index 最大值，例如 <= 20
禁止全局 button/div/section 选择器
必须包含基础响应式规则或 max-width 约束
必须包含 overflow-wrap 或 word-break 保护长文本
```

### 8.4 Repair 策略

新增 render repair prompt：

```text
app/prompts/reviewer/interactive_html_render_repair.md
```

触发条件：

```text
HTML 安全校验失败
CSS 作用域校验失败
manifest 与 DOM 不一致
交互协议缺失
内容过短或结构过空
```

最多 repair 2 次。超过次数后使用 fallback renderer。

---

## 9. 交互通信协议

### 9.1 HTML 中只保留标记

大模型生成的 HTML 不允许包含 JS。交互行为由前端 runtime 统一接管。

允许的标记：

```html
<button
  data-ih-action="single-choice"
  data-section-id="unit_01"
  data-block-id="unit_01_check"
  data-interaction-id="unit_01_i1"
  data-option-id="a"
>
  选项 A
</button>
```

### 9.2 建议统一 data 属性

```text
data-section-id       当前 unit id
data-block-id         当前教学 block id
data-block-type       当前 block 类型
data-interaction-id   当前互动 id
data-ih-action        前端 runtime 动作类型
data-option-id        选择题选项 id
data-item-id          拖拽/排序 item id
data-target-id        匹配目标 id
data-feedback-for     前端写入反馈的位置
data-state            前端写入交互状态
```

需要在 `ALLOWED_ATTRS` 中增加：

```python
"data-feedback-for",
"data-state",
"data-role",
"aria-describedby",
```

### 9.3 前端提交事件格式

前端 runtime 统一提交：

```json
{
  "section_id": "unit_01",
  "block_id": "unit_01_check",
  "interaction_id": "unit_01_i1",
  "event_type": "single_choice_answered",
  "payload": {
    "selected_option_ids": ["a"],
    "time_spent_seconds": 32,
    "confidence": "medium"
  }
}
```

提交接口沿用：

```text
POST /api/interactive-lessons/{lesson_id}/sessions/{session_id}/events
```

P0 阶段可以继续使用当前 in-memory service。若需要支持刷新后继续学习，建议提前落库。

---

## 10. API / RenderModel 返回结构

当前 `InteractiveHtmlRenderModel.sections` 里只有：

```text
section_id
title
learning_goal
html_fragment
block_refs
```

建议改成：

```python
class InteractiveHtmlRenderSection(SchemaModel):
    section_id: str
    title: str
    learning_goal: str
    style_scope_id: str
    html_fragment: str
    css_fragment: str
    block_manifest: list[InteractiveHtmlRenderBlockRef] = Field(default_factory=list)
    interaction_manifest: list[InteractionRenderRef] = Field(default_factory=list)
```

最终 `InteractiveHtmlRenderModel`：

```python
class InteractiveHtmlRenderModel(SchemaModel):
    render_type: str = "interactive_html_page"
    lesson_id: str
    title: str
    subtitle: str | None = None
    layout: Literal["vertical_lesson_with_tutor"] = "vertical_lesson_with_tutor"
    style_guide: dict = Field(default_factory=dict)
    course_css: str | None = None
    navigation: list[NavigationItem] = Field(default_factory=list)
    interactions: list[InteractionRenderRef] = Field(default_factory=list)
    runtime: InteractiveRuntimeConfig = Field(default_factory=InteractiveRuntimeConfig)
    sections: list[InteractiveHtmlRenderSection] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)
    citations: list[dict] = Field(default_factory=list)
```

前端展示逻辑：

```text
读取 render_model.sections
为每个 unit 注入 css_fragment
将 html_fragment 放入 unit 容器
侧边菜单根据 navigation 路由到 section_id
事件监听绑定到 [data-ih-action]
根据 interaction_manifest 找 event_type
提交 LearningEvent
```

---

## 11. Fallback 策略

P0 不要完全依赖 LLM render 成功。

保留 fallback，但 fallback 应从新的 `InteractiveHtmlSectionSpec.teaching_flow` 生成基础 HTML + CSS。

建议新增：

```text
app/renderers/interactive_html_fallback_renderer.py
```

职责：

```text
当 LLM render 失败、校验失败或 repair 失败时，生成基础可用 unit。
```

Fallback 输出也必须符合：

```text
InteractiveHtmlRenderedUnit
html_fragment
css_fragment
block_manifest
interaction_manifest
```

当前 `unit_spec_generators.py` 中存在两个 `build_interactive_html_unit_spec_fallback` 定义，需要清理成一个版本，避免维护者误判。

---

## 12. 文件级修改清单

### 12.1 必改文件

| 文件 | 修改内容 |
|---|---|
| `app/schemas/specs/interactive_html.py` | 移除 `InteractiveHtmlSectionSpec.html_fragment` 的核心地位，新增 `teaching_flow`、`interaction_specs` |
| `app/schemas/render/interactive_html.py` | 新增 `style_scope_id`、`css_fragment`、`block_manifest`、`interaction_manifest` |
| `app/prompts/generator/interactive_html_unit_spec.md` | 改为只生成教学设计 spec |
| `app/prompts/generator/interactive_html_unit_render.md` | 新增，负责 HTML + CSS package 生成 |
| `app/renderers/interactive_html_renderer.py` | 改为 assemble，不再负责简单 sanitize 单元 HTML |
| `app/renderers/interactive_html_composer.py` | 新增，调用 LLM 生成 rendered unit |
| `app/validators/interactive_html_validator.py` | 拆分 spec 校验、rendered unit 校验、CSS 校验 |
| `app/workflows/nodes/unit_renderer_node.py` | interactive_html 分支改为调用 composer |
| `app/workflows/nodes/renderer_node.py` | final render 改为从 `state.render_units` 组装 |
| `app/generators/unit_spec_generators.py` | interactive_html spec 生成适配新 schema，清理重复 fallback |

### 12.2 建议新增文件

| 文件 | 用途 |
|---|---|
| `app/schemas/specs/interactive_html_style.py` | Course Style Guide schema |
| `app/schemas/render/interactive_html_runtime.py` | Runtime contract schema，可并入 render/interactive_html.py |
| `app/renderers/interactive_html_composer.py` | LLM render composer |
| `app/renderers/interactive_html_fallback_renderer.py` | fallback renderer |
| `app/prompts/reviewer/interactive_html_render_repair.md` | render repair prompt |
| `backend/tests/test_interactive_html_composer.py` | composer 与 validator 测试 |
| `backend/tests/test_interactive_html_runtime_contract.py` | 交互协议测试 |

---

## 13. 推荐实施顺序

### Step 1：调整 schema

先修改：

```text
app/schemas/specs/interactive_html.py
app/schemas/render/interactive_html.py
```

完成后确保项目能启动，旧字段如果需要兼容，可以临时保留：

```python
html_fragment: str | None = None  # deprecated
```

### Step 2：改 Unit Spec Prompt

将 `interactive_html_unit_spec.md` 改为教学设计输出。

验证目标：LLM 输出不再包含 HTML。

### Step 3：新增 Render Prompt 与 Composer

新增：

```text
interactive_html_unit_render.md
interactive_html_composer.py
```

验证目标：单个 unit 能生成 `html_fragment + css_fragment + manifest`。

### Step 4：拆分 Validator

先实现基础校验：

```text
HTML 安全
CSS 作用域
DOM 与 manifest 一致
交互协议一致
```

高级视觉检查可以后续加。

### Step 5：改 `render_unit` 节点

将 interactive_html 的 unit render 改为调用 composer。

验证目标：任务执行中可以逐 unit 产出 HTML preview。

### Step 6：改 final renderer

final renderer 只组装 `state.render_units`，不重复调用 LLM。

验证目标：最终 preview 与流式 preview 一致。

### Step 7：前后端联调事件协议

验证：

```text
点击选择题按钮
↓
前端 runtime 捕获 data-ih-action
↓
构造 SubmitEventRequest
↓
POST learning event
↓
页面显示反馈
```

---

## 14. P0 验收标准

### 14.1 生成质量

```text
课程能被拆分为多个 unit
每个 unit 有完整讲解、可视化组织和自然收束
每个 unit 的视觉表现不机械重复
整体风格保持一致
没有明显文字溢出、超宽布局和大片空白
```

### 14.2 工程稳定性

```text
Unit Spec 不包含 HTML/CSS
Render 输出包含 html_fragment 和 css_fragment
CSS 全部作用域隔离
DOM 中所有 interaction id 都能在 manifest 中找到
manifest 中所有 interaction id 都能在 DOM 中找到
final render 不重复调用 unit render
fallback 能在 LLM 失败时产出可展示页面
```

### 14.3 交互闭环

```text
前端可以创建 session
前端可以监听 data-ih-action
选择题、简答、流程控制、情景选择至少各跑通一种
LearningEvent 能提交成功
Session state 能返回事件统计
```

### 14.4 安全边界

```text
禁止 script
禁止 iframe
禁止外链资源
禁止 inline event handler
禁止 javascript: URL
禁止未作用域 CSS
禁止覆盖全局 body/html/root
```

---

## 15. 暂缓内容

P0 阶段暂缓：

```text
OfflineHandoutSpec
完整离线 HTML 导出
summary_knowledge_card
PersonalizedHandoutPatch
LearnerState 深度分析
PDF handout
Adaptive Agent 个性化补充
```

但 P0 的 RenderModel 应保留后续可扩展空间：

```text
section_id
block_id
interaction_id
target_concepts
citations
render_notes
```

这些字段会成为后续 P1/P2 的输入基础。

---

## 16. 最终建议

P0 的关键改造不是把前端 renderer 完全后移到后端，也不是把所有页面都写成固定模板。

建议采用：

```text
结构化 Unit Spec
+ 课程级 Style Guide
+ LLM Unit HTML Composer
+ 固定交互通信协议
+ CSS 作用域约束
+ Render Package Validator
```

这样可以同时获得三点收益：

1. 页面质量由大模型在 render 阶段自由发挥，减少模板僵硬感。
2. 前端交互协议稳定，能够持续记录学习事件。
3. 后续 P1 handout 可以基于 unit spec、render package 和 learning events 平滑扩展。
