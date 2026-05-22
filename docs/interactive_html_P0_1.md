# interactive_html P0 交互模板化渲染修改方案

## 1. 文档目标

本文档用于指导 `interactive_html` P0 阶段的下一步后端与前端改造。

当前目标聚焦在线互动 HTML 课件生成闭环：

```text
outline
  ↓
unit spec
  ↓
讲解内容 LLM HTML 渲染
  +
互动内容模板化渲染
  ↓
unit html/css 组装
  ↓
前端展示与交互事件提交
```

本阶段暂不实现 P1 离线 handout。所有设计需要为后续 handout 派生预留结构，但不展开离线讲义生成流程。

---

## 2. 当前问题判断

当前 `interactive_html` 已经将生成流程拆为：

```text
outline -> spec -> render
```

其中：

1. `outline` 负责课程结构和 unit 划分，当前效果可保留。
2. `spec` 负责逐 unit 生成教学组织，包括 `teaching_flow` 与 `interaction_specs`。
3. `render` 负责生成可展示的 HTML/CSS。

当前主要问题是：

```text
LLM 在 render 阶段同时生成讲解 HTML 与互动 HTML。
```

这会导致互动内容不稳定：

1. `data-ih-action` 可能缺失或写错。
2. `data-interaction-id` 可能无法和 `interaction_specs` 对齐。
3. 单选、多选、简答、情景讨论的 DOM 结构不稳定。
4. 前端 runtime 难以通过统一事件委托接管。
5. 后端 validator 很难稳定确认交互是否真的可用。
6. 交互事件无法可靠提交到 learning event API。

因此，下一步需要将 render 阶段拆成两部分：

```text
讲解 / 总结部分：由 LLM 生成 HTML + CSS
互动部分：由后端模板生成 HTML
```

---

## 3. 核心设计结论

本方案采用：

```text
LLM 自由讲解渲染 + 互动模板稳定渲染 + Unit 级组装
```

对应原则如下：

| 内容类型 | 生成方式 | 目标 |
|---|---|---|
| 讲解内容 | LLM 生成 HTML/CSS | 保证表达自然、视觉丰富、页面不死板 |
| 总结内容 | LLM 生成 HTML/CSS | 保证收束清晰、版面自然 |
| 单选题 | 后端模板生成 | 保证按钮可点击、事件可记录 |
| 多选题 | 后端模板生成 | 保证选择状态、提交状态和 payload 稳定 |
| 简答题 | 后端模板生成 | 保证 textarea、submit、答案记录稳定 |
| 情景讨论 | 后端模板生成 | 保证场景、输入、提交、事件记录稳定 |
| Unit 组装 | 后端按 `teaching_flow` 顺序组装 | 保证教学顺序与 spec 一致 |

一句话总结：

```text
让 LLM 负责“讲清楚、讲好看”，让模板负责“点得动、传得出、记得住”。
```

---

## 4. 修改后的 P0 生成流程

### 4.1 总流程

```text
用户请求
  ↓
知识库检索
  ↓
Outline Generator
  ↓
Unit Spec Generator
  - teaching_flow
  - interaction_specs
  ↓
Unit Spec Validator
  ↓
InteractiveHtmlComposer
  ├─ InteractionTemplateRenderer
  │   ├─ single_choice
  │   ├─ multiple_choice
  │   ├─ short_answer
  │   └─ scenario_discussion
  │
  ├─ ExplanationHtmlComposer
  │   └─ LLM 只生成非互动教学块 HTML/CSS
  │
  └─ UnitHtmlAssembler
      ├─ 按 teaching_flow 顺序组装讲解块与互动块
      ├─ 合并 css_fragment
      ├─ 生成 block_manifest
      └─ 生成 interaction_manifest
  ↓
Rendered Unit Validator
  ↓
前端展示
  ↓
前端 runtime 监听 data-ih-action
  ↓
POST LearningEvent
```

### 4.2 render 阶段内部流程

```text
InteractiveHtmlSectionSpec
  ↓
split teaching_flow
  ├─ explanation blocks
  └─ interaction blocks
  ↓
InteractionTemplateRenderer.render()
  ↓
ExplanationHtmlComposer.compose()
  ↓
UnitHtmlAssembler.assemble()
  ↓
validate rendered unit
  ↓
repair explanation html/css if needed
  ↓
return InteractiveHtmlRenderedUnit
```

---

## 5. Spec 层修改建议

### 5.1 保留 `teaching_flow`

`teaching_flow` 继续作为 unit 内部的教学顺序描述。

示例：

```json
{
  "block_id": "unit_01_intro",
  "block_type": "concept_explanation",
  "teaching_role": "建立核心概念",
  "content_goal": "解释为什么交互控件需要稳定协议",
  "must_cover": ["data-ih-action", "interaction_id", "frontend runtime"]
}
```

### 5.2 保留并增强 `interaction_specs`

`interaction_specs` 作为互动模板生成的唯一事实来源。

互动模板不再依赖 LLM 生成的 DOM，而是依赖 `interaction_specs` 生成稳定 HTML。

### 5.3 增强互动选项结构

建议新增或调整：

```python
class InteractiveHtmlInteractionOption(SchemaModel):
    id: str
    text: str
    is_correct: bool | None = None
    feedback: str | None = None
```

将原来的：

```python
options: list[dict]
```

改为：

```python
options: list[InteractiveHtmlInteractionOption]
```

### 5.4 增强 `InteractiveHtmlInteractionSpec`

建议字段：

```python
class InteractiveHtmlInteractionSpec(SchemaModel):
    interaction_id: str
    block_id: str
    type: Literal[
        "single_choice",
        "multiple_choice",
        "short_answer",
        "scenario_discussion",
    ]
    event_type: Literal[
        "single_choice_answered",
        "multiple_choice_answered",
        "short_answer_submitted",
        "scenario_discussion_submitted",
    ]
    prompt: str
    options: list[InteractiveHtmlInteractionOption] = Field(default_factory=list)
    target_concepts: list[str] = Field(default_factory=list)
    feedback_policy: Literal["local", "submit_to_backend", "local_and_submit"] = "local_and_submit"

    # short_answer / scenario_discussion
    placeholder: str | None = None
    reference_points: list[str] = Field(default_factory=list)
    min_length: int | None = None

    # scenario_discussion
    scenario: dict[str, Any] = Field(default_factory=dict)
```

### 5.5 四类互动 spec 要求

#### single_choice

要求：

1. 至少 4 个 option。
2. 必须且只能有 1 个 `is_correct=true`。
3. 每个 option 需要 feedback。
4. event_type 固定为 `single_choice_answered`。

#### multiple_choice

要求：

1. 至少 4 个 option。
2. 至少 1 个 `is_correct=true`。
3. 每个 option 需要 feedback。
4. event_type 固定为 `multiple_choice_answered`。
5. 前端采用“选择 + 提交”两步。

#### short_answer

要求：

1. 必须有 prompt。
2. 必须有 placeholder。
3. 建议有 `reference_points`。
4. 建议设置 `min_length`。
5. event_type 固定为 `short_answer_submitted`。

#### scenario_discussion

要求：

1. 必须有 `scenario.background`。
2. 必须有 `scenario.task`。
3. 必须有 prompt。
4. 建议有 `reference_points`。
5. event_type 固定为 `scenario_discussion_submitted`。

---

## 6. Render 层拆分方案

建议新增或拆分以下模块：

```text
app/renderers/interactive_html_composer.py
app/renderers/interactive_html_explanation_composer.py
app/renderers/interactive_html_interaction_renderer.py
app/renderers/interactive_html_unit_assembler.py
```

如果短期不希望增加太多文件，可以先在 `interactive_html_composer.py` 内实现多个类，稳定后再拆文件。

---

## 7. InteractionTemplateRenderer 设计

### 7.1 职责

`InteractionTemplateRenderer` 负责将 `interaction_specs` 转换为稳定 DOM。

输入：

```text
InteractiveHtmlSectionSpec
style_scope_id
```

输出：

```text
dict[block_id, RenderedInteractionBlock]
```

示例结构：

```python
class RenderedInteractionBlock(SchemaModel):
    block_id: str
    interaction_id: str
    interaction_type: str
    html_fragment: str
    block_manifest_item: dict
    interaction_manifest_item: dict
```

### 7.2 支持类型

P0 阶段只实现四类：

```text
single_choice
multiple_choice
short_answer
scenario_discussion
```

暂缓：

```text
drag_match
sequence
socratic_chat
flashcard
```

---

## 8. 四类互动模板协议

### 8.1 通用 DOM 属性

所有互动模板必须包含：

```html
data-block-id
data-block-type
data-interaction-id
data-ih-action
```

推荐补充：

```html
data-option-id
data-option-label
data-correct
data-feedback
data-ih-input-for
data-ih-feedback-for
data-reference-points
data-min-length
```

### 8.2 single_choice 模板

关键结构：

```html
<article
  class="ih-block ih-interaction ih-quiz ih-quiz--single"
  data-block-id="unit_01_sc"
  data-block-type="single_choice"
>
  <p class="ih-question">...</p>

  <button
    type="button"
    class="ih-option"
    data-ih-action="single-choice"
    data-interaction-id="unit_01_i_sc"
    data-option-id="a"
    data-correct="true"
    data-feedback="..."
  >
    ...
  </button>

  <div
    class="ih-feedback"
    data-ih-feedback-for="unit_01_i_sc"
    aria-live="polite"
  ></div>
</article>
```

前端 action：

```text
single-choice
```

提交 payload：

```json
{
  "selected_option_ids": ["a"],
  "is_correct": true
}
```

---

### 8.3 multiple_choice 模板

关键结构：

```html
<button
  type="button"
  class="ih-option"
  data-ih-action="multiple-choice-toggle"
  data-interaction-id="unit_01_i_mc"
  data-option-id="a"
  data-correct="true"
>
  ...
</button>

<button
  type="button"
  class="ih-submit"
  data-ih-action="multiple-choice-submit"
  data-interaction-id="unit_01_i_mc"
>
  提交答案
</button>
```

前端 action：

```text
multiple-choice-toggle
multiple-choice-submit
```

提交 payload：

```json
{
  "selected_option_ids": ["a", "b"],
  "correct_option_ids": ["a", "d"],
  "is_correct": false
}
```

---

### 8.4 short_answer 模板

关键结构：

```html
<textarea
  class="ih-textarea"
  data-ih-input-for="unit_01_i_sa"
  placeholder="..."
></textarea>

<button
  type="button"
  class="ih-submit"
  data-ih-action="short-answer-submit"
  data-interaction-id="unit_01_i_sa"
  data-min-length="20"
  data-reference-points="要点1|要点2|要点3"
>
  提交简答
</button>

<div
  class="ih-feedback"
  data-ih-feedback-for="unit_01_i_sa"
  aria-live="polite"
></div>
```

前端 action：

```text
short-answer-submit
```

提交 payload：

```json
{
  "answer_text": "...",
  "reference_points": ["要点1", "要点2"],
  "matched_points": ["要点1"],
  "heuristic_score": 50
}
```

---

### 8.5 scenario_discussion 模板

关键结构：

```html
<article
  class="ih-block ih-interaction ih-scenario"
  data-block-id="unit_01_sd"
  data-block-type="scenario_discussion"
>
  <div class="scenario-card">
    <p>场景背景...</p>
    <p>任务...</p>
  </div>

  <textarea
    class="ih-textarea"
    data-ih-input-for="unit_01_i_sd"
    placeholder="..."
  ></textarea>

  <button
    type="button"
    class="ih-submit"
    data-ih-action="scenario-discussion-submit"
    data-interaction-id="unit_01_i_sd"
    data-min-length="30"
    data-reference-points="要点1|要点2|要点3"
  >
    提交讨论
  </button>

  <div
    class="ih-feedback"
    data-ih-feedback-for="unit_01_i_sd"
    aria-live="polite"
  ></div>
</article>
```

前端 action：

```text
scenario-discussion-submit
```

提交 payload：

```json
{
  "answer_text": "...",
  "reference_points": ["要点1", "要点2"],
  "matched_points": ["要点1"],
  "heuristic_score": 50
}
```

---

## 9. ExplanationHtmlComposer 设计

### 9.1 职责

`ExplanationHtmlComposer` 只调用 LLM 生成非互动教学块 HTML/CSS。

允许生成：

```text
intro
concept_explanation
case_compare
animated_flow
context_inspector
stepper
reflection
summary
```

禁止生成：

```text
single_choice
multiple_choice
short_answer
scenario_discussion
button/input/textarea 互动控件
data-ih-action
data-interaction-id
script
onclick
```

### 9.2 建议输出格式

LLM 不再输出完整 unit HTML，而是输出 block html map：

```json
{
  "section_id": "unit_01",
  "style_scope_id": "ih-scope-unit-01",
  "block_html_map": {
    "unit_01_intro": "<article ...>...</article>",
    "unit_01_concept": "<article ...>...</article>",
    "unit_01_summary": "<article ...>...</article>"
  },
  "css_fragment": ".ih-scope-unit-01 .xxx { ... }",
  "render_notes": {
    "layout_pattern": "story_flow_with_checkpoint"
  }
}
```

### 9.3 Prompt 修改重点

原 `interactive_html_unit_render.md` 应修改为：

```text
你只负责生成非互动教学块的 HTML/CSS。
互动题、输入框、按钮、提交反馈区域由系统模板生成。
你不得生成 data-ih-action、data-interaction-id、script、onclick。
你需要根据 teaching_flow 中的非互动 block 生成自然、连贯、美观的讲解内容。
```

---

## 10. UnitHtmlAssembler 设计

### 10.1 职责

`UnitHtmlAssembler` 负责按 `teaching_flow` 顺序组装最终 unit。

输入：

```text
section_spec
explanation_block_html_map
interaction_block_html_map
css_fragment
style_scope_id
```

输出：

```text
InteractiveHtmlRenderedUnit
```

### 10.2 组装逻辑

伪代码：

```python
def assemble(section_spec, explanation_blocks, interaction_blocks, css_fragment):
    html_parts = []

    for block in section_spec.teaching_flow:
        if block.block_id in interaction_blocks:
            html_parts.append(interaction_blocks[block.block_id].html_fragment)
        elif block.block_id in explanation_blocks:
            html_parts.append(explanation_blocks[block.block_id])
        else:
            html_parts.append(render_missing_block_placeholder(block))

    html_fragment = wrap_unit_section(
        section_id=section_spec.section_id,
        style_scope_id=style_scope_id,
        html_parts=html_parts,
    )

    return InteractiveHtmlRenderedUnit(
        section_id=section_spec.section_id,
        html_fragment=html_fragment,
        css_fragment=css_fragment + interaction_base_css,
        block_manifest=build_block_manifest(...),
        interaction_manifest=build_interaction_manifest(...),
    )
```

### 10.3 缺失块处理

如果某个 block 没有被 LLM 或模板成功生成：

1. 不直接失败整个 unit。
2. 插入一个轻量 fallback block。
3. 记录 warning。
4. 触发 repair 或返回可见占位说明。

示例：

```html
<article class="ih-block ih-warning" data-block-id="...">
  <h3>本段内容需要补充</h3>
  <p>系统未能成功生成该教学块，已记录用于修复。</p>
</article>
```

---

## 11. Validator 修改方案

Validator 分为两层：

```text
Spec Validator
Rendered Unit Validator
```

---

### 11.1 Spec Validator

校验 `InteractiveHtmlSectionSpec`。

新增校验：

1. `teaching_flow.block_id` 不重复。
2. `interaction_specs.interaction_id` 不重复。
3. 每个 `interaction_spec.block_id` 必须出现在 `teaching_flow`。
4. 每个互动类型字段完整。
5. `single_choice` 必须且只能有一个正确选项。
6. `multiple_choice` 至少一个正确选项。
7. `short_answer` 必须有 prompt 和 placeholder。
8. `scenario_discussion` 必须有 scenario background/task。
9. `event_type` 和 `type` 必须匹配。

映射关系：

```text
single_choice -> single_choice_answered
multiple_choice -> multiple_choice_answered
short_answer -> short_answer_submitted
scenario_discussion -> scenario_discussion_submitted
```

---

### 11.2 Explanation HTML Validator

单独校验 LLM 生成的讲解 HTML。

禁止出现：

```text
<script>
<style>
onclick
onchange
oninput
data-ih-action
data-interaction-id
<input>
<textarea>
<button>
<form>
```

允许出现普通展示类 HTML：

```text
article
section
div
p
h2
h3
ul
ol
li
span
strong
em
table
blockquote
```

CSS 禁止：

```text
body
html
:root
position: fixed
z-index: 9999
@import
url(
```

CSS 必须 scoped：

```text
.ih-scope-{section_id} ...
```

---

### 11.3 Rendered Unit Validator

校验最终 unit。

必查项：

1. 每个 `interaction_specs.interaction_id` 都出现在 DOM。
2. 每个 interaction 都有合法 `data-ih-action`。
3. `interaction_manifest` 与 DOM 中的 `data-interaction-id` 一致。
4. 每个 `data-interaction-id` 都能在 manifest 中找到。
5. 每个 `data-block-id` 都能在 block_manifest 中找到。
6. 最终 HTML 不包含 `<html> / <head> / <body>`。
7. 最终 HTML 不包含 `<script>`。
8. 最终 HTML 不包含未授权事件属性。
9. CSS 不污染全局。
10. unit root 必须包含：

```html
<section class="ih-unit ih-scope-xxx" data-section-id="xxx">
```

---

## 12. 前端 Runtime 修改方案

前端 runtime 通过事件委托监听：

```js
document.addEventListener("click", handleInteractiveHtmlAction)
```

识别：

```text
[data-ih-action]
```

P0 阶段支持 action：

```text
single-choice
multiple-choice-toggle
multiple-choice-submit
short-answer-submit
scenario-discussion-submit
```

### 12.1 单选

行为：

1. 点击 option。
2. 当前题其他选项取消选中。
3. 当前选项标记 selected。
4. 根据 `data-correct` 显示本地反馈。
5. 组装 payload。
6. POST learning event。

### 12.2 多选

行为：

1. 点击 option 时 toggle selected。
2. 点击 submit 时计算选择结果。
3. 根据正确选项显示反馈。
4. 组装 payload。
5. POST learning event。

### 12.3 简答

行为：

1. 读取 `[data-ih-input-for="{interaction_id}"]`。
2. 检查 min_length。
3. 根据 reference_points 做轻量本地匹配。
4. 显示反馈。
5. POST learning event。

### 12.4 情景讨论

行为：

1. 读取 textarea。
2. 检查 min_length。
3. 根据 reference_points 做轻量本地匹配。
4. 显示鼓励式反馈。
5. POST learning event。

### 12.5 统一 payload

```json
{
  "section_id": "unit_01",
  "block_id": "unit_01_sc",
  "interaction_id": "unit_01_i_sc",
  "event_type": "single_choice_answered",
  "payload": {
    "selected_option_ids": ["a"],
    "answer_text": null,
    "is_correct": true,
    "target_concepts": ["..."],
    "client_timestamp": "..."
  }
}
```

---

## 13. API 与学习事件服务

现有 learning event API 可以继续使用，但需要确认支持新增事件：

```text
scenario_discussion_submitted
```

需要检查并更新：

```text
SubmitEventRequest.event_type
LearningEvent.event_type
learning_service._build_interaction_summary
```

P0 阶段可以继续使用内存服务，但建议尽快规划数据库持久化。当前修改重点是：

1. 事件能从前端成功发到后端。
2. 后端能记录 event。
3. session summary 能统计四类互动。
4. 前端能看到本地即时反馈。

---

## 14. CSS 与视觉策略

互动模板不应写死为单一视觉。

建议结构固定，皮肤可变：

```text
DOM 协议固定
CSS token 可变
视觉变体可变
```

推荐交互视觉变体：

```text
diagnostic_card
checkpoint
tutor_question
challenge_box
scenario_decision
```

可以在 `interaction_specs` 中加：

```python
visual_variant: Literal[
    "diagnostic_card",
    "checkpoint",
    "tutor_question",
    "challenge_box",
    "scenario_decision",
] | None = None
```

模板 renderer 根据 `visual_variant` 加 class：

```html
<article class="ih-block ih-interaction ih-variant-checkpoint">
```

这样互动稳定，同时减少“每页都长一样”的问题。

---

## 15. Prompt 修改方案

### 15.1 Unit Spec Prompt

Unit Spec Prompt 需要明确：

1. `spec` 负责教学组织。
2. 互动问题只生成 `interaction_specs`。
3. 不生成 HTML。
4. 每个 unit 推荐包含 1 个互动块。
5. 长 unit 可以包含 2 个互动块。
6. 互动类型从四类中选择：

```text
single_choice
multiple_choice
short_answer
scenario_discussion
```

Prompt 增加约束：

```text
互动题必须服务于当前 unit 的学习目标。
互动题必须诊断具体 target_concepts。
选择题必须包含正确答案与反馈。
简答题和情景讨论必须包含 reference_points。
```

---

### 15.2 Render Prompt

Render Prompt 需要明确：

```text
你只生成非互动教学块。
系统会在之后插入互动模板。
你需要让讲解块之间自然衔接，并为后续互动题留出语义过渡。
```

禁止：

```text
不要生成任何互动题。
不要生成按钮、输入框、textarea、form。
不要生成 data-ih-action。
不要生成 data-interaction-id。
不要生成 JavaScript。
```

建议输出：

```json
{
  "block_html_map": {
    "block_id": "<article ...>...</article>"
  },
  "css_fragment": "...",
  "render_notes": {}
}
```

---

## 16. 建议实施顺序

### Step 1：Schema 调整

修改：

```text
app/schemas/specs/interactive_html.py
```

完成：

1. 增强 `InteractiveHtmlInteractionSpec`。
2. 新增 `InteractiveHtmlInteractionOption`。
3. 支持 `scenario_discussion`。
4. 增加 event_type 映射。
5. 必要时增加 `visual_variant`。

---

### Step 2：Unit Spec Prompt 调整

修改：

```text
app/prompts/generator/interactive_html_unit_spec.md
```

完成：

1. interaction_specs 字段要求。
2. 四类互动生成规则。
3. 禁止生成 HTML。
4. 要求正确答案、反馈、reference_points。

---

### Step 3：新增 InteractionTemplateRenderer

新增：

```text
app/renderers/interactive_html_interaction_renderer.py
```

完成：

1. `render_single_choice`
2. `render_multiple_choice`
3. `render_short_answer`
4. `render_scenario_discussion`
5. 生成 interaction_manifest item。
6. 生成 block_manifest item。

---

### Step 4：拆分 ExplanationHtmlComposer

新增或改造：

```text
app/renderers/interactive_html_explanation_composer.py
```

完成：

1. 过滤 teaching_flow 中的互动 block。
2. 构造 LLM render prompt。
3. 输出 `block_html_map + css_fragment`。
4. 禁止 LLM 输出互动控件。

---

### Step 5：新增 UnitHtmlAssembler

新增：

```text
app/renderers/interactive_html_unit_assembler.py
```

完成：

1. 按 teaching_flow 顺序合并讲解块与互动块。
2. 合并 CSS。
3. 生成最终 `InteractiveHtmlRenderedUnit`。
4. 统一生成 `block_manifest` 和 `interaction_manifest`。

---

### Step 6：改造 InteractiveHtmlComposer

修改：

```text
app/renderers/interactive_html_composer.py
```

改为 orchestration：

```python
interaction_blocks = interaction_renderer.render(section_spec, style_scope_id)
explanation_blocks = explanation_composer.compose(section_spec, style_guide, style_scope_id)
rendered_unit = unit_assembler.assemble(section_spec, explanation_blocks, interaction_blocks)
validated = validator.validate_rendered_unit(rendered_unit)
```

---

### Step 7：Validator 更新

修改：

```text
app/validators/interactive_html_validator.py
```

新增：

1. `validate_unit_spec`
2. `validate_explanation_render`
3. `validate_rendered_unit`
4. 四类互动模板校验。
5. action 枚举更新。

新增合法 action：

```text
single-choice
multiple-choice-toggle
multiple-choice-submit
short-answer-submit
scenario-discussion-submit
```

---

### Step 8：前端 runtime 更新

前端需要实现或确认：

1. 事件委托监听 `[data-ih-action]`。
2. 单选点击反馈与提交。
3. 多选 toggle 与 submit。
4. 简答提交。
5. 情景讨论提交。
6. payload 组装。
7. POST learning event。
8. 本地反馈区域更新。

---

### Step 9：端到端测试

至少准备 4 个测试任务：

1. 只包含单选题的 unit。
2. 包含多选题的 unit。
3. 包含简答题的 unit。
4. 包含情景讨论的 unit。

每个测试需要验证：

1. HTML 正常显示。
2. 交互控件可以点击/输入。
3. 即时反馈正常显示。
4. payload 字段完整。
5. 后端收到 learning event。
6. session summary 能看到事件记录。

---

## 17. 验收标准

P0 完善后的验收标准如下。

### 17.1 生成质量

1. 讲解内容不空洞。
2. unit 内部讲解、互动、总结衔接自然。
3. 页面视觉不再明显模板化。
4. 互动模块样式与整体页面协调。
5. 移动端无严重横向溢出。

### 17.2 交互稳定性

1. 单选题可点击并显示反馈。
2. 多选题可多选、取消选择并提交。
3. 简答题可输入并提交。
4. 情景讨论可输入并提交。
5. 每个互动都能生成完整 payload。
6. 每个 payload 都能提交到后端 event API。
7. DOM 中的 interaction_id 与 manifest 一致。

### 17.3 后端稳定性

1. LLM 讲解 HTML 不包含互动协议。
2. 互动 DOM 全部来自模板 renderer。
3. validator 能发现缺失 interaction_id、非法 action、未 scoped CSS。
4. repair 只修复讲解 HTML/CSS，不重写互动模板。
5. fallback 能保证 unit 至少可展示。

### 17.4 前端稳定性

1. 前端只依赖 `data-ih-action` 接管事件。
2. 前端不依赖 LLM 生成的自由 class。
3. 新增互动类型时，只需扩展 runtime action handler。
4. 前端能够将多个 unit 组装成完整课程页面。

---

## 18. 本阶段不做的内容

P0 阶段暂不实现：

```text
离线 handout 生成
summary_knowledge_card
个性化补丁 PersonalizedHandoutPatch
LearnerState 深度分析
拖拽匹配 drag_match
排序题 sequence
真正多轮 socratic_chat
复杂动画状态机
PDF 导出
```

这些能力放到 P1/P2/P3。

---

## 19. 最终目标状态

本次修改完成后，系统应形成如下能力：

```text
spec 决定讲什么、哪里互动
LLM render 决定讲解内容怎么表现
template renderer 决定互动控件怎么运行
assembler 决定 unit 怎么合成
frontend runtime 决定事件怎么触发和提交
validator 保证协议一致和可展示
```

最终交付给前端的 unit package 仍保持：

```json
{
  "section_id": "unit_01",
  "style_scope_id": "ih-scope-unit-01",
  "html_fragment": "...",
  "css_fragment": "...",
  "block_manifest": [],
  "interaction_manifest": []
}
```

该结构能够继续支持：

1. 在线预览。
2. unit 级路由。
3. 前端侧边栏导航。
4. 学习事件记录。
5. 后续 P1 离线 handout 派生。
