# Slide 生成方案重新收束版修改建议

## 1. 修改目标

本轮修改聚焦生成稳定性与成品可展示性，优先解决以下问题：

1. 页面内容与模板结构不匹配。
2. 页面正文、要点或总结内容显示不完整。
3. 部分页面出现大量空白，信息密度不足。
4. 图片信息量过大，不适合小尺寸嵌入展示。
5. validator 主要检查结构合法性，对最终成品质量保护不足。
6. spec、element、render 任一阶段失败后缺少有效回退机制。

本轮方案采用收束策略：固定少量稳定布局，统一文本预算，按布局控制图片风格，并在 spec 与 render 两个阶段引入质量校对和回退重试。

---

## 2. 总体设计原则

### 2.1 布局数量收束

当前版本只保留 2 种稳定布局：

1. `image_text`：图文并存页。
2. `visual_summary`：示意图 + 总结页。

所有 slide spec 只能选择这 2 种布局。后续页面多样性通过图片风格、文本内容、示意图类型和局部排版细节体现。

### 2.2 文本预算前置

每种布局都必须定义严格的文本预算。LLM 生成 spec 时必须遵守预算，后端 normalize 阶段继续执行裁剪、补齐和纠偏。

文本预算优先级高于内容丰富度。页面内容应保持短句、关键词、短要点和总结句形式，详细讲解进入 `speaker_notes`。

### 2.3 图片风格按布局分流

图片生成服务根据 layout 选择不同 prompt。

- `image_text` 使用低信息密度图片，适合小图嵌入。
- `visual_summary` 使用中高信息密度图片，适合承担结构总结功能。

### 2.4 成品质量闭环

validator 分为两层：

1. 规则校验：由代码确定性检查 schema、role、文本长度、元素引用。
2. 质量校对：由 LLM 检查内容质量、布局匹配度、页面可展示性。

工作流支持失败回退：

- spec 质量不合格：重新生成 spec。
- 图片风格不合格：重新生成 element。
- 渲染排版不合格：重新 render。
- 页面内容与布局整体不匹配：回退到 spec 生成。

---

## 3. 固定布局设计

## 3.1 布局 A：`image_text`

### 适用场景

- 概念解释
- 案例说明
- 应用场景
- 机制介绍
- 技术原理说明

### 页面结构

- 顶部：标题
- 左侧：1 张辅助说明图
- 右侧：核心解释 + 2 到 4 条要点
- 底部：1 条核心总结句

### 元素角色

必须包含：

- `title`
- `explanation`
- `bullet_list`
- `takeaway`
- `visual`

### 文本预算

- `title`：不超过 20 个中文字符。
- `explanation`：不超过 2 句。
- `bullet_list`：2 到 4 条。
- 每条 bullet：不超过 28 个中文字符。
- `takeaway`：不超过 32 个中文字符。

### 图片要求

图片应为低信息密度视觉辅助，建议风格包括：

- 写实示意图
- 手绘示意图
- 教育插画
- 简洁技术示意图
- 单对象场景图

图片限制：

- 不生成复杂信息图。
- 不生成大量文字标签。
- 不生成整页 PPT 截图式画面。
- 不生成密集脑图式画面。

---

## 3.2 布局 B：`visual_summary`

### 适用场景

- 流程总结
- 结构总览
- 方法归纳
- 阶段复盘
- 系统框架说明

### 页面结构

- 顶部：标题
- 中部：1 张大尺寸示意图
- 下方或右侧：简短总结性文本

### 元素角色

必须包含：

- `title`
- `summary_text`
- `visual`

可选包含：

- `takeaway`

### 文本预算

- `title`：不超过 20 个中文字符。
- `summary_text`：不超过 3 句。
- `takeaway`：不超过 32 个中文字符。

### 图片要求

图片承担主要信息表达功能，建议风格包括：

- 流程图
- 结构图
- 信息图
- 方法框架图
- 阶段总结图

图片要求：

- 信息结构清晰。
- 层级关系明确。
- 文字字号可读。
- 画面整体适合 slide 中大尺寸展示。

---

## 4. 工作流调整

## 4.1 单页生成闭环

每一页 slide 按以下流程生成：

```text
retrieve_for_unit
  -> generate_unit_spec
  -> normalize_slide_spec
  -> validate_spec_rules
  -> review_unit_spec_by_llm
  -> generate_elements
  -> render_slide
  -> validate_render_rules
  -> review_rendered_slide_by_llm
  -> accept_slide
```

## 4.2 回退规则

### Spec 阶段失败

触发条件：

- 内容空洞。
- 文本超过预算。
- layout 与页面内容不匹配。
- required role 缺失。
- 图片需求描述不清晰。

处理方式：

```text
review_unit_spec_by_llm -> regenerate_unit_spec
```

重试上限：2 次。

### Element 阶段失败

触发条件：

- 图片风格与 layout 不匹配。
- `image_text` 页生成了信息密集型图片。
- `visual_summary` 页生成了普通插图，无法承担总结功能。
- 图片明显像整页 PPT。

处理方式：

```text
review_rendered_slide_by_llm -> regenerate_elements
```

重试上限：2 次。

### Render 阶段失败

触发条件：

- 文本显示不完整。
- 页面元素重叠。
- 大面积无效空白。
- 图片或文本区域比例失衡。
- 页面整体未达到可展示标准。

处理方式：

```text
review_rendered_slide_by_llm -> rerender
```

若 rerender 后仍失败，回退到 spec 阶段。

---

## 5. 文件级修改建议

## 5.1 `app/prompts/planner/slide_outline.md`

### 修改目标

让 planner 只规划稳定页面类型，避免输出当前 renderer 无法稳定承接的复杂结构。

### 修改内容

将 `visual_strategy` 收缩为以下枚举：

```text
image_text
visual_summary
```

增加页面规划规则：

```text
1. 普通概念解释、案例说明、机制介绍、应用场景页使用 image_text。
2. 流程总结、结构总览、方法归纳、阶段复盘页使用 visual_summary。
3. 每页必须有明确核心信息。
4. 每页最多规划 4 条要点。
5. 避免只包含标题和一句泛化描述的页面。
6. 避免规划需要大量正文才能讲清楚的页面。
```

---

## 5.2 `app/prompts/generator/slide_deck_spec.md`

### 修改目标

让 spec 生成严格围绕两种固定布局，确保内容可以被 renderer 稳定承接。

### 修改内容

限定 layout：

```text
layout 只能为 image_text 或 visual_summary。
```

定义 `image_text` 输出契约：

```text
必须包含：
- title
- explanation
- bullet_list
- takeaway
- visual

文本预算：
- title <= 20 中文字符
- explanation <= 2 句
- bullet_list 2~4 条
- 单条 bullet <= 28 中文字符
- takeaway <= 32 中文字符
```

定义 `visual_summary` 输出契约：

```text
必须包含：
- title
- summary_text
- visual

可选：
- takeaway

文本预算：
- title <= 20 中文字符
- summary_text <= 3 句
- takeaway <= 32 中文字符
```

增加输出前自检清单：

```text
1. layout 是否只使用 image_text 或 visual_summary。
2. required roles 是否齐全。
3. 文本是否符合预算。
4. 页面内容是否具体、可讲解、可展示。
5. visual instruction 是否与 layout 匹配。
6. image_text 页是否避免信息密集图。
7. visual_summary 页是否让图片承担总结结构功能。
8. 输出是否为合法 JSON。
```

---

## 5.3 `app/schemas/specs.py`

### 修改目标

让 schema 直接约束稳定布局、元素角色和文本预算。

### 修改内容

修改 `SlideLayout`：

```python
SlideLayout = Literal["image_text", "visual_summary"]
```

统一 `SlideSpecElement.metadata.role`：

```text
title
explanation
bullet_list
summary_text
takeaway
visual
```

增加 layout-role 校验：

```text
image_text 必须包含：title、explanation、bullet_list、takeaway、visual
visual_summary 必须包含：title、summary_text、visual
```

增加文本预算校验：

```text
title <= 20 中文字符
explanation <= 2 句
bullet_list 2~4 条
单条 bullet <= 28 中文字符
summary_text <= 3 句
takeaway <= 32 中文字符
```

增加引用校验：

```text
visual role 必须对应 required_elements 中的 image element。
required_elements 中未被引用的 image 应记录 warning。
```

---

## 5.4 `app/generators/unit_spec_generators.py`

### 修改目标

在 LLM 输出后执行统一标准化，保证进入 element 和 render 阶段的 spec 可控。

### 修改内容

新增函数：

```python
def normalize_slide_spec(spec, unit, state):
    ...
```

该函数执行：

1. role 命名归一。
2. layout 非法时纠正为 `image_text`。
3. 缺失 required role 时补齐最小内容。
4. 超长文本裁剪，完整内容进入 `speaker_notes`。
5. `image_text` 中 bullet 超过 4 条时压缩为 4 条。
6. `visual_summary` 中出现冗余 bullet_list 时合并为 summary_text。
7. 根据 layout 生成对应 image required_element。
8. 为 required_element 写入明确的图片风格约束。

fallback 只允许生成：

```text
image_text
visual_summary
```

fallback 内容也必须遵守文本预算。

---

## 5.5 `app/workflows/nodes/validator_node.py`

### 修改目标

将 validator 分为规则校验与质量校验入口。

### 修改内容

规则校验检查：

1. layout 合法性。
2. required roles 完整性。
3. 文本预算。
4. visual 引用合法性。
5. required_elements 与 element_ref 对齐。

校验输出结构建议：

```json
{
  "passed": true,
  "errors": [],
  "warnings": [],
  "retryable": false,
  "retry_from_step": "accept"
}
```

当出现可修复问题时，设置：

```json
{
  "passed": false,
  "retryable": true,
  "retry_from_step": "regenerate_spec"
}
```

---

## 5.6 新增 `app/workflows/nodes/review_unit_spec_node.py`

### 修改目标

在 spec 规则校验后增加 LLM 质量校对。

### 输入

- 当前 slide spec
- 当前 outline unit
- 检索 chunk 摘要
- 文本预算
- layout 说明

### 校对内容

1. 内容是否具体。
2. 内容是否适合当前 layout。
3. 文本是否像 slide 内容。
4. 图片需求是否清晰。
5. 页面是否存在显示不全风险。
6. 页面是否存在信息过少风险。

### 输出格式

```json
{
  "passed": true,
  "issues": [],
  "repair_advice": "",
  "retry_from_step": "accept"
}
```

失败时：

```json
{
  "passed": false,
  "issues": ["内容过于空洞", "图片需求不明确"],
  "repair_advice": "重写 explanation 和 bullet_list，补充具体场景信息。",
  "retry_from_step": "regenerate_spec"
}
```

---

## 5.7 `app/workflows/nodes/element_flow_node.py`

### 修改目标

让图片生成任务获得 layout 上下文，按页面需求生成合适图片。

### 修改内容

构造 element request 时增加：

```json
{
  "layout": "image_text",
  "visual_type": "illustration",
  "information_density": "low",
  "text_in_image": "minimal",
  "expected_usage": "small_slide_visual"
}
```

`visual_summary` 页使用：

```json
{
  "layout": "visual_summary",
  "visual_type": "summary_diagram",
  "information_density": "medium_or_high",
  "text_in_image": "allowed",
  "expected_usage": "large_slide_visual"
}
```

---

## 5.8 `app/services/image_generation_service.py`

### 修改目标

按 layout 分流图片 prompt。

### `image_text` prompt 要求

```text
Create a focused visual asset for a teaching slide.
Use a realistic illustration, hand-drawn sketch, or clean educational illustration style.
The image should explain one concept or scenario.
Keep information density low.
Use little or no text inside the image.
Do not create a mind-map, dense infographic, poster, full slide, title page, agenda page, or bullet-list layout.
```

### `visual_summary` prompt 要求

```text
Create a structured summary diagram for a teaching slide.
Use a clear infographic, flowchart, framework diagram, or process diagram style.
The image should carry the main structural information of the slide.
Moderate text labels are allowed if they are readable.
Keep the hierarchy clear and visually organized.
Do not create a full PowerPoint slide screenshot or a decorative illustration without structure.
```

---

## 5.9 `app/renderers/slide_renderer.py`

### 修改目标

renderer 围绕两种固定版式稳定输出。

### 修改内容

只保留两个主渲染函数：

```python
_render_image_text_slide()
_render_visual_summary_slide()
```

### `image_text` 渲染规则

```text
顶部：title
左侧：visual
右侧：explanation + bullet_list
底部：takeaway
```

固定约束：

1. 左侧图片区固定宽高。
2. 右侧文本区固定宽高。
3. bullet 最多 4 条。
4. takeaway 最多 2 行。
5. render 阶段不自动补充额外文本。
6. 超长文本在 render 前必须已经处理完成。

### `visual_summary` 渲染规则

```text
顶部：title
中部：visual 大图
底部：summary_text + takeaway
```

固定约束：

1. visual 区域优先保证完整展示。
2. summary_text 最多 3 句。
3. 文本区域高度固定。
4. 不拼接冗余 body、core_message 或自动 takeaway。

### 删除自动补内容逻辑

删除或禁用：

1. 自动补 takeaway。
2. 自动重复 core_message。
3. 自动从 body 拆出额外卡片。
4. 自动追加未在 spec 中定义的说明内容。

---

## 5.10 新增 `app/workflows/nodes/review_rendered_slide_node.py`

### 修改目标

在 render 完成后进行成品级 LLM 校对。

### 输入

- 当前 slide spec
- rendered slide JSON
- 元素位置与尺寸摘要
- 图片描述或 URL
- 文本内容摘要

### 校对内容

1. 文本是否完整显示。
2. 页面是否有明显大面积空白。
3. 图片与文本是否匹配。
4. 图片风格是否适合 layout。
5. 页面是否达到可展示标准。
6. 是否需要回退到 spec、element 或 render 阶段。

### 输出格式

```json
{
  "passed": true,
  "issues": [],
  "repair_advice": "",
  "retry_from_step": "accept"
}
```

失败时：

```json
{
  "passed": false,
  "issues": ["右侧文本过长，存在显示不完整风险"],
  "repair_advice": "压缩 bullet_list，每条控制在 20 字以内。",
  "retry_from_step": "regenerate_spec"
}
```

`retry_from_step` 允许值：

```text
regenerate_spec
regenerate_elements
rerender
accept
```

---

## 6. P0 修改任务

P0 目标：先让生成结果稳定、完整、可展示。

1. 将 layout 收缩为：
   - `image_text`
   - `visual_summary`

2. 重写 `slide_outline.md`：
   - 只规划两种 visual strategy。
   - 增加页面内容规划规则。

3. 重写 `slide_deck_spec.md`：
   - 加入两种 layout 的元素契约。
   - 加入严格文本预算。
   - 加入图片风格约束。
   - 加入输出前 checklist。

4. 修改 `specs.py`：
   - 收缩 layout 枚举。
   - 收缩 role 枚举。
   - 增加 role 完整性校验。
   - 增加文本预算校验。

5. 修改 `unit_spec_generators.py`：
   - 新增 `normalize_slide_spec()`。
   - fallback 只生成两种布局。
   - required image element 根据 layout 写入不同 visual constraints。

6. 修改 `image_generation_service.py`：
   - 根据 layout 分流图片 prompt。

7. 修改 `slide_renderer.py`：
   - 只保留两个稳定渲染函数。
   - 删除自动补内容逻辑。
   - 固定文本区与图片区。

8. 修改 `validator_node.py`：
   - 增加 deterministic 规则校验。
   - 输出统一 validation report。

---

## 7. P1 修改任务

P1 目标：形成质量闭环与自动回退机制。

1. 新增 `review_unit_spec_node.py`：
   - LLM 校对 spec 内容质量。
   - 失败后回退 `generate_unit_spec`。

2. 新增 `review_rendered_slide_node.py`：
   - LLM 校对最终页面质量。
   - 失败后按原因回退。

3. 修改 LangGraph workflow：
   - spec review 不通过时重新生成 spec。
   - render review 不通过时按失败原因回退。
   - 每页最大重试次数限制为 3 次。

4. 增加失败原因分类日志：
   - `empty_content`
   - `layout_mismatch`
   - `text_overflow`
   - `image_style_mismatch`
   - `large_blank_area`
   - `render_overlap`
   - `not_presentation_ready`

5. 增加任务状态记录：
   - 当前 slide order
   - 当前 retry count
   - 最近一次失败原因
   - 当前回退阶段

---

## 8. 推荐实施顺序

### 第一步：稳定 schema 与 prompt

修改：

1. `slide_outline.md`
2. `slide_deck_spec.md`
3. `specs.py`

目标：让 LLM 输出内容从源头收束。

### 第二步：稳定生成与图片风格

修改：

1. `unit_spec_generators.py`
2. `element_flow_node.py`
3. `image_generation_service.py`

目标：让 spec 与 image element 按 layout 匹配。

### 第三步：稳定渲染

修改：

1. `slide_renderer.py`
2. `validator_node.py`

目标：确保页面结构固定、内容完整显示。

### 第四步：加入质量闭环

新增：

1. `review_unit_spec_node.py`
2. `review_rendered_slide_node.py`

修改：

1. LangGraph workflow
2. task progress / retry state

目标：让系统具备自动判断与重试能力。

---

## 9. 验收标准

完成 P0 后，生成结果应满足：

1. 所有 slide 只使用 `image_text` 或 `visual_summary`。
2. 页面文本完整显示。
3. 每页都有明确主题、视觉元素和总结信息。
4. `image_text` 页图片适合小尺寸展示。
5. `visual_summary` 页图片能够承担结构表达功能。
6. 页面不出现明显大面积空白。
7. renderer 不再自动拼接重复内容。

完成 P1 后，生成结果应满足：

1. spec 质量不合格时可自动重试。
2. render 成品不合格时可自动回退。
3. 每页有明确质量校对报告。
4. 失败原因可追踪。
5. 最终 slide 达到可展示标准。
