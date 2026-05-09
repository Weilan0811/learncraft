# 参考 OpenMAIC 的后端 Slide 生成改造方案

> 适用范围：当前上传的 `backend.zip` 后端工程。  
> 修改目标：严格参考 OpenMAIC 的 slide 约束思路，将当前 slide 生成从“标题 + 正文 + 可选图片”的松散规格，升级为“页面 DSL + 版式契约 + 资源白名单 + 校验修复 + 稳定渲染”的工程化链路。  
> 当前版本约束：不设计 cover 页；不生成 mindmap；只处理 slide_deck 的 image / text / layout / renderer 相关能力。

---

## 0. OpenMAIC 设计原则在本项目中的落地方式

OpenMAIC 的 slide 生成核心不是单纯提示词，而是以下组合：

1. **Slide 是视觉辅助，不是讲稿**  
   页面只放关键词、短句、要点、标签、图示说明；详细解释放入 `speaker_notes`。

2. **结构化页面 DSL**  
   LLM 输出结构化 JSON，元素带有类型、角色、布局信息、尺寸约束或可推导的版式约束。

3. **资源白名单**  
   Slide 只能引用后端声明并生成的资源，不能由 LLM 自行编造 URL 或图片 ID。

4. **生成后校验与修复**  
   LLM 输出后必须经过 normalize / validate / repair，再进入元素生成和 renderer。

5. **Renderer 只负责稳定渲染**  
   Renderer 不主动“创作内容”，只根据 spec 中的 layout、role、visual_ref 进行确定性排版。

本项目采用 OpenMAIC 思路，但保持当前 scenekit 渲染体系：

```text
Planner
  -> SlideSpecPage Generator
  -> Normalize Slide Spec
  -> Validate Slide Spec
  -> Repair Slide Spec
  -> Collect Required Elements
  -> Generate Image Elements
  -> Validate Unit
  -> Merge Unit Result
  -> Assemble SlideDeckSpec
  -> Render scenekit.slide/v1
```

---

## 1. 总体修改目标

### 1.1 删除 cover 设计

当前版本直接进入主题，不生成封面页。

落地要求：

- `SlideLayout` 删除 `cover`。
- planner prompt 不再要求第 1 页作为封面。
- `_choose_slide_layout()` 不再对 `unit.order == 1` 返回 `cover`。
- `slide_renderer.py` 删除 cover 分支，保留 `section-divider` 作为章节过渡页。

### 1.2 移除 mindmap 修改计划

当前版本不考虑思维导图元素。

落地要求：

- slide prompt 删除 mindmap 策略。
- slide fallback 不再读取 `include_mindmap`。
- `SlideSpecPage.required_elements` 不再允许 slide 使用 `mindmap`。
- element flow 的 slide 分支只收集 image。
- graph 层保留 `generate_mindmap_element` 不影响 lecture，但 slide 生成链路不再声明 mindmap。

### 1.3 强化 slide 结构约束

`SlideSpecPage` 从“内容块列表”升级为“页面设计规格”。

核心变化：

```text
title / body / bullet-list / visual / caption / takeaway
```

这些 role 形成 layout contract，renderer 根据 role 消费内容。

### 1.4 引入 normalize + repair

LLM 输出不直接进入后续流程，而是执行：

```text
generate_slide_unit_spec_with_llm
  -> normalize_slide_spec
  -> validate_unit_spec
  -> repair_unit_spec
  -> validate_unit_spec
```

P0 先把 `normalize_slide_spec()` 内嵌到 `unit_spec_generators.py`。  
P1 新增 `repair_unit_spec_node.py` 并接入 LangGraph。

---

# P0 修改方案

P0 目标：不用大改 graph，先通过 schema、prompt、fallback、validator、renderer 五处改动解决当前页面死板、文字截断、图片策略粗糙的问题。

---

## 2. 修改 `app/prompts/planner/slide_outline.md`

### 2.1 修改目标

让 Planner 直接输出后端支持的 layout 策略，不再生成 `comparison`、`timeline`、`process` 这类 schema 不支持的值。

### 2.2 明确替换内容

将当前：

```markdown
- visual_strategy 给出页面布局建议，例如 title-content、title-content-visual、comparison、timeline、process。
- 第 1 页适合作为导入页。
```

替换为：

```markdown
- visual_strategy 必须从以下枚举中选择：
  - title-content
  - title-content-visual
  - visual-left-content-right
  - summary-cards
  - section-divider
- 不生成 cover 页。第 1 页直接进入主题导入，优先使用 title-content-visual 或 visual-left-content-right。
- section-divider 只用于明确章节过渡页；如果没有明显章节结构，不使用 section-divider。
- 每个 unit 必须包含 source_chunk_ids 和 retrieval_queries。
```

### 2.3 增加页面类型规划规则

在“内容要求”下追加：

```markdown
页面类型与 visual_strategy 选择规则：
- 概念解释页：title-content 或 title-content-visual
- 案例页 / 场景页 / 应用页：visual-left-content-right
- 机制页 / 流程页 / 架构页：title-content-visual
- 并列三点 / 阶段总结 / 三个特征：summary-cards
- 章节过渡：section-divider

图片规划规则：
- 案例、场景、应用、机制、流程、架构页优先规划为带图片页面。
- 纯定义、简单总结、summary-cards 可不配图。
- 不规划 mindmap。
```

---

## 3. 修改 `app/prompts/generator/slide_deck_spec.md`

### 3.1 修改目标

让单页 spec generator 严格遵循 OpenMAIC 的“slide 是视觉辅助，不是讲稿”原则，同时输出满足当前 renderer 的 role contract。

### 3.2 删除内容

删除以下内容：

- 所有 `cover` 相关描述。
- 整个“思维导图使用策略”。
- 所有 `mindmap`、`secondary_visual`、`metadata.role = "mindmap"`、`metadata.downgrade = "text"` 相关内容。

### 3.3 重写“总体目标”

将“一、总体目标”改为：

```markdown
## 一、总体目标

生成的 slide spec 应接近真实课堂教学 PPT 或汇报 PPT。

每页 PPT 必须：
- 聚焦一个核心信息
- 页面文字短、清楚、可扫描
- 详细解释进入 speaker_notes
- 根据页面类型选择合适 layout
- 普通教学页优先配一张局部教学视觉资产
- 不生成 cover 页
- 不生成 mindmap
- 不生成长段讲义式正文
```

### 3.4 重写“图片策略”

```markdown
## 三、图片策略

如果 `generation_options.include_images` 为 true，应根据页面类型判断是否需要图片。

必须优先使用图片的页面：
- 案例页
- 场景页
- 应用页
- 技术机制页
- 流程说明页
- 架构说明页
- 观点论证页
- 技术演化页

可以不使用图片的页面：
- 纯概念定义页
- 简单总结页
- summary-cards 页
- section-divider 页

图片必须是嵌入 slide 的局部教学视觉资产，不是整页 PPT。

图片 instruction 必须包含：
- 画面主体
- 视觉形式：概念图、流程图、场景图、架构图、时间线、对比图、案例图等
- 需要强调的信息
- 是否允许少量标签
- 明确禁止完整 PPT 页面、标题栏、页脚、大段文字、复杂表格、summary panel
```

### 3.5 重写“版式选择规则”

```markdown
## 四、版式选择规则

layout 必须从以下枚举中选择：
- title-content
- title-content-visual
- visual-left-content-right
- summary-cards
- section-divider

### 1. title-content
适合：
- 纯概念解释
- 简短定义
- 不需要图片的说明页

必须包含：
- title
- body
- bullet-list 或 callout 至少一种
- takeaway

禁止：
- visual

### 2. title-content-visual
适合：
- 普通教学页
- 机制说明页
- 流程说明页
- 概念图解页

必须包含：
- title
- body
- bullet-list 或 callout 至少一种
- visual
- caption 或 takeaway 至少一种

### 3. visual-left-content-right
适合：
- 案例页
- 场景页
- 应用页
- 产品 / 系统 / 人物 / 实验页

必须包含：
- title
- visual
- body
- example / callout / bullet-list 至少一种
- caption 或 takeaway 至少一种

### 4. summary-cards
适合：
- 3 个并列概念
- 3 个特征
- 3 个阶段
- 3 个结论

必须包含：
- title
- body
- 3 个短卡片内容，使用 bullet-list、callout 或 comparison 表达
- takeaway

禁止：
- visual

### 5. section-divider
适合：
- 章节分隔
- 阶段过渡

必须包含：
- title
- body

禁止：
- visual
- bullet-list 超过 2 条
- 长正文
```

### 3.6 重写 `layout_hints` 要求

```markdown
## 七、layout_hints 要求

`layout_hints` 必须包含：

{
  "density": "light | balanced | rich",
  "supported_renderer": "scenekit.slide/v1",
  "page_kind": "concept | case | mechanism | comparison | summary | section",
  "visual_policy": "required | optional | forbidden",
  "text_budget": {
    "max_title_chars": 22,
    "max_core_message_chars": 45,
    "max_body_chars": 80,
    "max_bullet_count": 4,
    "max_bullet_chars": 35,
    "max_takeaway_chars": 55,
    "max_caption_chars": 35
  }
}

选择规则：
- title-content: visual_policy = forbidden
- summary-cards: visual_policy = forbidden
- section-divider: visual_policy = forbidden
- title-content-visual: visual_policy = required
- visual-left-content-right: visual_policy = required
```

### 3.7 增加完整输出示例

在 prompt 末尾加入一个示例，要求模型严格模仿字段结构：

```json
{
  "id": "slide_unit_001",
  "outline_unit_id": "unit_001",
  "order": 1,
  "title": "AI 如何完成任务",
  "core_message": "AI 通过感知、学习和决策完成复杂任务。",
  "layout": "title-content-visual",
  "design_intent": "用一页图文页解释 AI 完成任务的基本链路。",
  "theme_variant": "teaching-clean",
  "layout_hints": {
    "density": "balanced",
    "supported_renderer": "scenekit.slide/v1",
    "page_kind": "mechanism",
    "visual_policy": "required",
    "text_budget": {
      "max_title_chars": 22,
      "max_core_message_chars": 45,
      "max_body_chars": 80,
      "max_bullet_count": 4,
      "max_bullet_chars": 35,
      "max_takeaway_chars": 55,
      "max_caption_chars": 35
    }
  },
  "elements": [
    {
      "id": "slide_unit_001_title",
      "type": "text",
      "content": "AI 如何完成任务",
      "metadata": {"role": "title"}
    },
    {
      "id": "slide_unit_001_body",
      "type": "text",
      "content": "AI 系统通常先接收信息，再从数据中学习规律，最后输出判断或行动。",
      "metadata": {"role": "body"}
    },
    {
      "id": "slide_unit_001_points",
      "type": "text",
      "content": "感知环境\n学习规律\n辅助决策",
      "metadata": {"role": "bullet-list"}
    },
    {
      "id": "slide_unit_001_image_ref",
      "type": "element_ref",
      "element_id": "image_task_xxx_unit_001",
      "metadata": {"role": "visual", "placement": "primary"}
    },
    {
      "id": "slide_unit_001_caption",
      "type": "text",
      "content": "从输入到输出的任务链路",
      "metadata": {"role": "caption"}
    }
  ],
  "required_elements": [
    {
      "element_id": "image_task_xxx_unit_001",
      "type": "image",
      "title": "AI task flow visual",
      "purpose": "解释 AI 从输入到输出的任务链路。",
      "instruction": "Create a focused process diagram asset for a teaching slide. Show input, learning, decision, and output as a clean left-to-right flow. Use minimal Chinese labels. Do not create a full presentation slide, title bar, footer, bullet-list page, or summary panel.",
      "style": "clean educational diagram",
      "aspect_ratio": "16:9",
      "source_unit_id": "slide_unit_001",
      "source_outline_unit_id": "unit_001",
      "source_chunk_ids": [],
      "priority": "high"
    }
  ],
  "speaker_notes": "讲解时先说明 AI 不是单一动作，而是一条由输入、学习、判断和输出组成的任务链路。页面只展示关键链路，具体例子在口头讲解中补充。",
  "source_chunk_ids": []
}
```

---

## 4. 修改 `app/schemas/specs.py`

### 4.1 修改 `RequiredElementSpec`

当前：

```python
class RequiredElementSpec(SchemaModel):
    type: Literal["image", "mindmap"]
```

修改为：

```python
class RequiredElementSpec(SchemaModel):
    type: Literal["image"]
```

### 4.2 修改 `ElementRequest`

当前：

```python
class ElementRequest(SchemaModel):
    type: Literal["image", "mindmap"]
```

修改为：

```python
class ElementRequest(SchemaModel):
    type: Literal["image"]
```

说明：当前版本 slide 不再生成 mindmap。Lecture 若仍需 mindmap，应在后续单独拆分 `LectureRequiredElementSpec` 与 `SlideRequiredElementSpec`；本轮 slide 改造以 image 为唯一工作流元素。

### 4.3 修改 `SlideLayout`

当前：

```python
SlideLayout = Literal[
    "cover",
    "section-divider",
    "title-content",
    "title-content-visual",
    "visual-left-content-right",
    "summary-cards",
]
```

修改为：

```python
SlideLayout = Literal[
    "section-divider",
    "title-content",
    "title-content-visual",
    "visual-left-content-right",
    "summary-cards",
]
```

### 4.4 新增 role 与 layout contract 常量

在 `SlideSpecPage` 前新增：

```python
SLIDE_TEXT_ROLES = {
    "title",
    "body",
    "bullet-list",
    "example",
    "comparison",
    "callout",
    "caption",
    "takeaway",
    "note",
}

SLIDE_ELEMENT_REF_ROLES = {"visual"}

LAYOUT_REQUIRED_ROLES = {
    "section-divider": {"title", "body"},
    "title-content": {"title", "body"},
    "title-content-visual": {"title", "body", "visual"},
    "visual-left-content-right": {"title", "body", "visual"},
    "summary-cards": {"title", "body"},
}

LAYOUT_FORBIDDEN_ROLES = {
    "section-divider": {"visual"},
    "title-content": {"visual"},
    "summary-cards": {"visual"},
}

TEXT_LIMITS = {
    "title": 22,
    "body": 80,
    "bullet-list": 160,
    "example": 70,
    "comparison": 140,
    "callout": 50,
    "caption": 35,
    "takeaway": 55,
    "note": 60,
}
```

### 4.5 强化 `SlideSpecElement.validate_payload_for_type`

新增 role 检查：

```python
@model_validator(mode="after")
def validate_payload_for_type(self) -> "SlideSpecElement":
    role = self.metadata.get("role")

    if self.type == "text":
        if not self.content:
            raise ValueError("text slide elements require content")
        if role not in SLIDE_TEXT_ROLES:
            raise ValueError(f"unsupported text role: {role}")

    if self.type == "element_ref":
        if not self.element_id:
            raise ValueError("element_ref slide elements require element_id")
        if role not in SLIDE_ELEMENT_REF_ROLES:
            raise ValueError(f"unsupported element_ref role: {role}")

    return self
```

### 4.6 强化 `SlideSpecPage.validate_workflow_contract`

在现有校验基础上新增：

```python
roles = {element.metadata.get("role") for element in self.elements}

required_roles = LAYOUT_REQUIRED_ROLES.get(self.layout, set())
missing_roles = required_roles - roles
if missing_roles:
    raise ValueError(f"slide layout {self.layout} is missing roles: {sorted(missing_roles)}")

forbidden_roles = LAYOUT_FORBIDDEN_ROLES.get(self.layout, set())
used_forbidden = forbidden_roles & roles
if used_forbidden:
    raise ValueError(f"slide layout {self.layout} uses forbidden roles: {sorted(used_forbidden)}")

if self.layout_hints.get("supported_renderer") != "scenekit.slide/v1":
    raise ValueError("layout_hints.supported_renderer must be scenekit.slide/v1")

if self.layout_hints.get("visual_policy") not in {"required", "optional", "forbidden"}:
    raise ValueError("layout_hints.visual_policy must be required, optional, or forbidden")

if self.layout in {"title-content-visual", "visual-left-content-right"}:
    if self.layout_hints.get("visual_policy") != "required":
        raise ValueError(f"{self.layout} requires visual_policy=required")

if self.layout in {"title-content", "summary-cards", "section-divider"}:
    if self.layout_hints.get("visual_policy") != "forbidden":
        raise ValueError(f"{self.layout} requires visual_policy=forbidden")

for item in self.required_elements:
    if item.type != "image":
        raise ValueError("slide required_elements only support image")
```

### 4.7 文本长度处理方式

P0 不在 Pydantic validator 中直接 `raise` 文本长度错误。文本长度由 `normalize_slide_spec()` 自动截短，validator 只负责结构硬约束。

原因：文本长度是可修复质量问题；直接放进 schema 会提高 LLM 输出失败率。

---

## 5. 修改 `app/generators/unit_spec_generators.py`

### 5.1 修改入口函数

当前：

```python
def build_slide_unit_spec(...):
    ...
    try:
        return generate_slide_unit_spec_with_llm(state, unit, chunk_ids)
    except Exception:
        return build_slide_unit_spec_fallback(state, unit, chunk_ids)
```

修改为：

```python
def build_slide_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> SlideSpecPage:
    settings = get_settings()

    if settings.provider_mode == "stub":
        return normalize_slide_spec(build_slide_unit_spec_fallback(state, unit, chunk_ids), state, unit, chunk_ids)

    try:
        spec = generate_slide_unit_spec_with_llm(state, unit, chunk_ids)
    except Exception:
        spec = build_slide_unit_spec_fallback(state, unit, chunk_ids)

    return normalize_slide_spec(spec, state, unit, chunk_ids)
```

### 5.2 新增 `normalize_slide_spec()`

新增函数：

```python
def normalize_slide_spec(
    spec: SlideSpecPage,
    state: ContentGenerationState,
    unit: OutlineUnit,
    chunk_ids: list[str],
) -> SlideSpecPage:
    spec = _force_supported_layout(spec, unit)
    spec = _ensure_layout_hints(spec, unit)
    spec = _remove_forbidden_visuals(spec)
    spec = _ensure_required_text_roles(spec, unit)
    spec = _normalize_text_lengths(spec)
    spec = _ensure_visual_for_visual_layout(spec, state, unit, chunk_ids)
    spec = _dedupe_slide_elements(spec)
    spec = _sync_required_elements_with_refs(spec)
    spec = _ensure_speaker_notes(spec, unit)
    return spec
```

### 5.3 新增 `_force_supported_layout()`

```python
def _force_supported_layout(spec: SlideSpecPage, unit: OutlineUnit) -> SlideSpecPage:
    supported = {
        "section-divider",
        "title-content",
        "title-content-visual",
        "visual-left-content-right",
        "summary-cards",
    }
    if spec.layout not in supported:
        spec.layout = _choose_slide_layout(unit)
    return spec
```

### 5.4 新增 `_infer_page_kind()`

```python
def _infer_page_kind(unit: OutlineUnit) -> str:
    text = " ".join([unit.title, unit.core_message, *unit.key_points])
    if any(k in text for k in ["章节", "部分", "进入", "过渡"]):
        return "section"
    if any(k in text for k in ["案例", "事件", "人物", "产品", "场景", "应用"]):
        return "case"
    if any(k in text for k in ["机制", "流程", "过程", "原理", "架构", "链路"]):
        return "mechanism"
    if any(k in text for k in ["对比", "差异", "比较"]):
        return "comparison"
    if any(k in text for k in ["总结", "复盘", "结论", "要点"]):
        return "summary"
    return "concept"
```

### 5.5 新增图片决策函数 `_should_use_image()`

```python
def _should_use_image(unit: OutlineUnit, layout: str, options: dict[str, object]) -> bool:
    if not bool(options.get("include_images", True)):
        return False

    if layout in {"title-content", "summary-cards", "section-divider"}:
        return False

    page_kind = _infer_page_kind(unit)
    if page_kind in {"case", "mechanism"}:
        return True

    text = " ".join([unit.title, unit.core_message, *unit.key_points])
    image_keywords = [
        "案例", "场景", "应用", "机制", "流程", "架构", "系统", "人物", "实验",
        "技术", "演化", "过程", "影响", "风险", "趋势", "链路", "图解",
    ]
    return any(keyword in text for keyword in image_keywords)
```

### 5.6 修改 `_choose_slide_layout()`

当前会返回 `cover`。改为：

```python
def _choose_slide_layout(unit: OutlineUnit) -> str:
    supported = {
        "section-divider",
        "title-content",
        "title-content-visual",
        "visual-left-content-right",
        "summary-cards",
    }
    if unit.visual_strategy in supported:
        return unit.visual_strategy

    page_kind = _infer_page_kind(unit)
    if page_kind == "section":
        return "section-divider"
    if page_kind == "case":
        return "visual-left-content-right"
    if page_kind == "mechanism":
        return "title-content-visual"
    if page_kind in {"summary", "comparison"} or len(unit.key_points) >= 4:
        return "summary-cards"
    return "title-content-visual"
```

### 5.7 修改 `_design_intent_for_layout()`

删除 cover：

```python
def _design_intent_for_layout(layout: str) -> str:
    intents = {
        "section-divider": "Separate the deck into a new conceptual section with concise transition text.",
        "title-content": "Explain one idea with concise text blocks and no visual asset.",
        "title-content-visual": "Pair a compact explanation with one supporting teaching visual.",
        "visual-left-content-right": "Lead with a visual case or scenario and explain it in compact text blocks.",
        "summary-cards": "Summarize three parallel points as scan-friendly cards.",
    }
    return intents.get(layout, intents["title-content-visual"])
```

### 5.8 重写 `build_slide_unit_spec_fallback()`

核心要求：fallback 也必须遵守 OpenMAIC 式页面约束，不再每页塞图片，不再生成 mindmap。

替换逻辑：

```python
def build_slide_unit_spec_fallback(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> SlideSpecPage:
    slide_id = f"slide_{unit.id}"
    options = state.normalized_request or {}
    layout = _choose_slide_layout(unit)
    page_kind = _infer_page_kind(unit)
    use_image = _should_use_image(unit, layout, options)

    if not use_image and layout in {"title-content-visual", "visual-left-content-right"}:
        layout = "title-content"

    visual_policy = "required" if use_image else "forbidden"
    required_elements: list[RequiredElementSpec] = []

    elements = [
        SlideSpecElement(
            id=f"{slide_id}_title",
            type="text",
            content=_shorten_text(unit.title, 22),
            metadata={"role": "title"},
        ),
        SlideSpecElement(
            id=f"{slide_id}_body",
            type="text",
            content=_shorten_text(unit.core_message, 80),
            metadata={"role": "body", "emphasis": "primary"},
        ),
    ]

    points = _short_points(unit.key_points, max_count=3, max_chars=35)
    if points and layout != "section-divider":
        elements.append(
            SlideSpecElement(
                id=f"{slide_id}_points",
                type="text",
                content="\n".join(points),
                metadata={"role": "bullet-list"},
            )
        )

    if use_image:
        image_spec = _image_spec_for_unit(
            unit=unit,
            unit_spec_id=slide_id,
            request_id=state.request_id,
            chunk_ids=chunk_ids,
            aspect_ratio="16:9",
            style=str(options.get("image_style") or "clean educational diagram"),
            purpose="Support the slide's single core message with one focused teaching visual.",
            instruction=_image_instruction_for_slide(unit, layout, page_kind),
        )
        required_elements.append(image_spec)
        elements.append(
            SlideSpecElement(
                id=f"{slide_id}_image_ref",
                type="element_ref",
                element_id=image_spec.element_id,
                metadata={"role": "visual", "placement": "primary"},
            )
        )
        elements.append(
            SlideSpecElement(
                id=f"{slide_id}_caption",
                type="text",
                content=_shorten_text(f"图示：{unit.title}", 35),
                metadata={"role": "caption"},
            )
        )

    if layout != "section-divider":
        elements.append(
            SlideSpecElement(
                id=f"{slide_id}_takeaway",
                type="text",
                content=_shorten_text(unit.core_message, 55),
                metadata={"role": "takeaway"},
            )
        )

    return SlideSpecPage(
        id=slide_id,
        outline_unit_id=unit.id,
        order=unit.order,
        title=_shorten_text(unit.title, 22),
        core_message=_shorten_text(unit.core_message, 45),
        layout=layout,
        design_intent=_design_intent_for_layout(layout),
        theme_variant="teaching-clean",
        layout_hints={
            "density": _density_for_layout(layout),
            "supported_renderer": "scenekit.slide/v1",
            "page_kind": page_kind,
            "visual_policy": visual_policy,
            "text_budget": _default_text_budget(),
        },
        required_elements=required_elements,
        speaker_notes=_speaker_notes_for_unit(unit),
        source_chunk_ids=chunk_ids,
        elements=elements,
    )
```

### 5.9 新增文本工具函数

```python
def _shorten_text(value: str, max_chars: int) -> str:
    normalized = " ".join(str(value or "").split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1] + "…"


def _short_points(points: list[str], max_count: int, max_chars: int) -> list[str]:
    return [_shorten_text(point, max_chars) for point in points[:max_count] if point.strip()]


def _default_text_budget() -> dict[str, int]:
    return {
        "max_title_chars": 22,
        "max_core_message_chars": 45,
        "max_body_chars": 80,
        "max_bullet_count": 4,
        "max_bullet_chars": 35,
        "max_takeaway_chars": 55,
        "max_caption_chars": 35,
    }


def _density_for_layout(layout: str) -> str:
    if layout == "section-divider":
        return "light"
    if layout in {"visual-left-content-right", "summary-cards"}:
        return "rich"
    return "balanced"
```

### 5.10 新增图片 instruction 函数

```python
def _image_instruction_for_slide(unit: OutlineUnit, layout: str, page_kind: str) -> str:
    visual_form = {
        "case": "scenario illustration or case visual",
        "mechanism": "clean process diagram or mechanism diagram",
        "comparison": "simple comparison graphic",
        "concept": "concept illustration",
        "summary": "simple synthesis visual",
    }.get(page_kind, "clean educational visual")

    return (
        f"Create a focused {visual_form} asset for a teaching slide about '{unit.title}'. "
        f"The visual should support this core message: {unit.core_message}. "
        "Use a clean composition with one clear subject and minimal Chinese labels only when helpful. "
        "Do not create a full PowerPoint slide, title bar, footer, agenda page, bullet-list page, "
        "summary card layout, classroom poster, or text-heavy page. "
        "The image must be suitable as an embedded visual inside a slide layout."
    )
```

---

## 6. 修改 `app/workflows/nodes/validator_node.py`

### 6.1 修改目标

把 slide 质量问题分为硬错误与软警告。

- 硬错误：不能渲染、结构不合法、element_ref 无 required_element。
- 软警告：文字偏长、layout 与内容不够匹配、图片缺失后已降级。

### 6.2 修改 `validate_unit_spec()`

在 `if isinstance(unit_spec, SlideSpecPage):` 内追加：

```python
slide_errors, slide_warnings = _validate_slide_spec_quality(unit_spec)
errors.extend(slide_errors)
```

返回结构改为：

```python
return {
    "spec_validation_report": {
        "passed": not errors,
        "errors": errors,
        "warnings": slide_warnings if isinstance(unit_spec, SlideSpecPage) else [],
    },
    "errors": state.errors + errors,
    "current_node": "validate_unit_spec",
    "progress": unit_progress(state, "validating_unit_spec", current_node="validate_unit_spec"),
}
```

### 6.3 新增 `_validate_slide_spec_quality()`

```python
def _validate_slide_spec_quality(slide: SlideSpecPage) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    roles = [element.metadata.get("role") for element in slide.elements]
    role_set = set(roles)

    required = {
        "section-divider": {"title", "body"},
        "title-content": {"title", "body"},
        "title-content-visual": {"title", "body", "visual"},
        "visual-left-content-right": {"title", "body", "visual"},
        "summary-cards": {"title", "body"},
    }.get(slide.layout, set())

    missing = required - role_set
    if missing:
        errors.append(f"slide {slide.id} layout {slide.layout} missing roles: {sorted(missing)}")

    forbidden = {
        "section-divider": {"visual"},
        "title-content": {"visual"},
        "summary-cards": {"visual"},
    }.get(slide.layout, set())

    used_forbidden = forbidden & role_set
    if used_forbidden:
        errors.append(f"slide {slide.id} layout {slide.layout} uses forbidden roles: {sorted(used_forbidden)}")

    for element in slide.elements:
        if element.type == "text" and element.content:
            role = str(element.metadata.get("role") or "body")
            if _slide_text_too_long(role, element.content):
                warnings.append(f"slide {slide.id} {role} text may be too long")

    if slide.core_message and _visible_text_blob(slide).count(slide.core_message) >= 2:
        warnings.append(f"slide {slide.id} repeats core_message in multiple visible elements")

    if any(item.type != "image" for item in slide.required_elements):
        errors.append(f"slide {slide.id} required_elements only support image")

    return errors, warnings
```

### 6.4 新增辅助函数

```python
def _slide_text_too_long(role: str, content: str) -> bool:
    limits = {
        "title": 22,
        "body": 90,
        "bullet-list": 180,
        "example": 80,
        "comparison": 160,
        "callout": 60,
        "caption": 45,
        "takeaway": 65,
        "note": 70,
    }
    return len("".join(str(content).split())) > limits.get(role, 120)


def _visible_text_blob(slide: SlideSpecPage) -> str:
    return "\n".join(element.content or "" for element in slide.elements if element.type == "text")
```

---

## 7. 修改 `app/workflows/nodes/element_flow_node.py`

### 7.1 修改目标

将 image request 变成 OpenMAIC 式“资源白名单”：slide spec 先声明图片资源，后端只生成声明过的图片；后续 renderer 只引用已生成图片。

### 7.2 修改 `collect_unit_required_elements()`

当前 context 较少，修改为给图片生成更多页面上下文。

在构造 `ElementRequest` 时，将 `context` 改为：

```python
context={
    "unit_title": unit.title,
    "core_message": unit.core_message,
    "key_points": unit.key_points,
    "slide_layout": getattr(unit_spec, "layout", None),
    "design_intent": getattr(unit_spec, "design_intent", None),
    "page_kind": getattr(unit_spec, "layout_hints", {}).get("page_kind") if unit_spec else None,
    "visual_policy": getattr(unit_spec, "layout_hints", {}).get("visual_policy") if unit_spec else None,
}
```

将 `constraints` 改为：

```python
constraints={
    "language": (state.normalized_request or {}).get("language", "zh-CN"),
    "style": required.style,
    "aspect_ratio": required.aspect_ratio or "16:9",
    "usage": "embedded_slide_visual",
    "avoid_full_slide": True,
    "allow_text_labels": "minimal",
}
```

### 7.3 保留 dispatch 结构

`dispatch_element_generation()` 仍根据 `ElementRequest.type` 分发。由于 slide 只声明 image，slide 链路不会再触发 `generate_mindmap_element`。

---

## 8. 修改 `app/services/image_generation_service.py`

### 8.1 修改目标

图片服务的 prompt 进一步明确：生成“嵌入 PPT 的局部视觉资产”，不是完整页面。

### 8.2 修改 `_build_prompt()`

替换为：

```python
def _build_prompt(self, description: str, aspect_ratio: str) -> str:
    return (
        "Create a focused visual asset to be embedded inside a teaching slide. "
        "It must be an illustration, diagram, timeline, process graphic, comparison visual, "
        "architecture sketch, scenario image, or case visual. "
        "Do not create a full PowerPoint slide, title bar, footer, agenda page, bullet-list page, "
        "summary card layout, classroom poster, document page, or text-heavy UI. "
        "Use minimal labels only when they directly improve understanding. "
        "Keep the composition clean with one clear subject, strong visual hierarchy, and enough whitespace. "
        f"Aspect ratio: {aspect_ratio}. "
        f"Description: {description}"
    )
```

---

## 9. 修改 `app/renderers/slide_renderer.py`

### 9.1 修改目标

Renderer 不再主动创作内容；严格消费 spec 中的 role。

### 9.2 删除 cover 渲染分支

修改 `_background_for_layout()`：

```python
def _background_for_layout(layout: str, theme: KitTheme) -> KitSlideBackground:
    if layout == "section-divider":
        return KitSlideBackground(
            type="gradient",
            gradient={
                "type": "linear",
                "rotate": 135,
                "colors": [
                    {"pos": 0, "color": "#FFFFFF"},
                    {"pos": 1, "color": "#E0F2FE"},
                ],
            },
        )
    return KitSlideBackground(type="solid", color=theme.backgroundColor)
```

修改 `_render_slide_page()`：

```python
def _render_slide_page(...):
    text_items = _collect_text_items(slide)
    visual_refs = _collect_visual_refs(slide, element_lookup)

    if slide.layout == "section-divider":
        return _render_section_divider(slide, text_items, theme)
    if slide.layout == "visual-left-content-right":
        return _render_visual_left_content_right(slide, text_items, visual_refs, theme)
    if slide.layout == "title-content-visual":
        return _render_title_content_visual(slide, text_items, visual_refs, theme)
    if slide.layout == "summary-cards":
        return _render_summary_cards(slide, text_items, theme)
    return _render_title_content(slide, text_items, theme)
```

删除 `_render_cover_like()`，新增 `_render_section_divider()`。

### 9.3 新增 `_render_section_divider()`

```python
def _render_section_divider(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    theme: KitTheme,
) -> list[KitSlideElement]:
    return [
        _shape(f"{slide.id}_accent", 78, 132, 96, 8, theme.themeColors[0], radius=8),
        _text(
            f"{slide.id}_title",
            "Title",
            78,
            172,
            740,
            90,
            slide.title,
            theme,
            font_size=40,
            bold=True,
            color="#0F172A",
            line_height=1.12,
        ),
        _text(
            f"{slide.id}_body",
            "Core message",
            82,
            286,
            680,
            74,
            _fit_text(_primary_body(text_items, slide.core_message), 70),
            theme,
            font_size=22,
            color="#334155",
            line_height=1.35,
        ),
    ]
```

### 9.4 修改 `_collect_text_items()`

当前会自动补 takeaway，容易造成重复。修改为：

```python
def _collect_text_items(slide: SlideSpecPage) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for element in slide.elements:
        if element.type != "text" or not element.content:
            continue
        role = str(element.metadata.get("role") or "body")
        if role == "title":
            continue
        items.append(
            {
                "id": element.id,
                "role": role,
                "content": element.content.strip(),
                "name": str(element.metadata.get("name") or role),
            }
        )

    if not any(item["role"] == "body" for item in items):
        items.insert(
            0,
            {
                "id": f"{slide.id}_body_auto",
                "role": "body",
                "content": _fit_text(slide.core_message, 80),
                "name": "body",
            },
        )

    return _deduplicate_items(items)
```

### 9.5 修改 `_collect_visual_refs()`

当前 `return refs[:1]` 可以保留一张图，但要过滤 `role == visual` 且元素类型为 image。

```python
def _collect_visual_refs(
    slide: SlideSpecPage,
    element_lookup: dict[str, ContentElement],
) -> list[dict[str, object]]:
    refs: list[dict[str, object]] = []
    for spec_element in slide.elements:
        if spec_element.type != "element_ref" or not spec_element.element_id:
            continue
        referenced = element_lookup.get(spec_element.element_id)
        if referenced is None:
            continue
        role = str(spec_element.metadata.get("role") or referenced.type)
        if role != "visual":
            continue
        if getattr(referenced, "type", None) != "image":
            continue
        refs.append({"spec": spec_element, "element": referenced, "role": role})
    return refs[:1]
```

### 9.6 修改 `_render_title_content()`

函数签名改为不接收 visual_refs：

```python
def _render_title_content(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    theme: KitTheme,
) -> list[KitSlideElement]:
```

渲染逻辑：

- 优先渲染 comparison table。
- 有 2~3 个 body items 时渲染 feature cards。
- 不强制所有页面都是 3 卡片。
- takeaway 只在 spec 有 takeaway 时渲染。

修改 takeaway 调用：

```python
elements.extend(_takeaway_bar(slide, text_items, theme, top=408, fallback_to_core=False))
```

### 9.7 修改 `_render_summary_cards()`

函数签名改为：

```python
def _render_summary_cards(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    theme: KitTheme,
) -> list[KitSlideElement]:
```

删除 summary 页视觉元素渲染：

```python
# 删除 if visual_refs: ...
```

只消费卡片内容：

```python
card_items = _card_items(text_items, slide.core_message)[:3]
```

### 9.8 修改 `_takeaway_bar()`

当前 fallback 到 `slide.core_message` 会导致重复。改为：

```python
def _takeaway_bar(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    theme: KitTheme,
    top: int,
    fallback_to_core: bool = False,
) -> list[KitSlideElement]:
    takeaway = _content_by_role(text_items, "takeaway")
    if not takeaway and fallback_to_core:
        takeaway = slide.core_message
    if not takeaway:
        return []
    ...
```

各 layout 调用规则：

```python
# title-content / title-content-visual / visual-left-content-right / summary-cards
fallback_to_core=False

# section-divider
不调用 takeaway_bar
```

### 9.9 删除 mindmap 渲染分支

在 `_visual_element()` 中删除：

```python
if getattr(referenced, "type", None) == "mindmap" ...
```

保留 image 分支即可。

### 9.10 新增 render bounds 检查

在 `SlideRenderer.render()` 中：

```python
page_elements = _render_slide_page(slide, element_lookup, theme, spec)
page_elements = _clamp_render_bounds(page_elements)
```

新增：

```python
def _clamp_render_bounds(elements: list[KitSlideElement]) -> list[KitSlideElement]:
    for element in elements:
        if element.left < 0:
            element.left = 0
        if element.top < 0:
            element.top = 0
        if element.left + element.width > SLIDE_WIDTH:
            element.width = max(1, SLIDE_WIDTH - element.left)
        if element.top + element.height > SLIDE_HEIGHT:
            element.height = max(1, SLIDE_HEIGHT - element.top)
    return elements
```

---

## 10. 修改 `app/workflows/content_generation_graph.py`

P0 不调整 graph 结构。  
`generate_mindmap_element` 节点可以保留，避免影响 lecture 或已有测试；slide 生成不再声明 mindmap，因此不会触发 mindmap 分支。

---

# P1 修改方案

P1 目标：接近 OpenMAIC 的完整工程化约束方式，将 normalize / validate / repair 显式纳入 graph，并增强 LLM JSON 修复和渲染质量检查。

---

## 11. 新增 `app/workflows/nodes/repair_unit_spec_node.py`

### 11.1 新增节点文件

新增文件：

```text
app/workflows/nodes/repair_unit_spec_node.py
```

### 11.2 节点职责

`repair_unit_spec` 只做确定性修复，不调用 LLM。

修复内容：

1. slide 缺 title role：补 title。
2. slide 缺 body role：用 core_message 补 body。
3. visual layout 缺 visual：降级为 `title-content`。
4. forbidden visual 出现在 `title-content` / `summary-cards` / `section-divider`：移除 visual ref 与 required image。
5. text 过长：截短可见文本，把完整内容追加进 `speaker_notes`。
6. required_elements 与 element_ref 不一致：以实际 element_ref 为准同步。
7. `layout_hints.supported_renderer` 缺失：补 `scenekit.slide/v1`。
8. `layout_hints.visual_policy` 与 layout 不一致：按 layout 修正。

### 11.3 节点示例

```python
from app.generators.unit_spec_generators import normalize_slide_spec
from app.schemas.specs import SlideSpecPage
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.helpers import current_outline_unit, unit_progress


def repair_unit_spec(state: ContentGenerationState) -> dict[str, object]:
    unit = current_outline_unit(state)
    unit_spec = state.current_unit_spec

    if isinstance(unit_spec, SlideSpecPage):
        chunk_ids = [chunk.id for chunk in state.current_unit_context] or unit.source_chunk_ids
        repaired = normalize_slide_spec(unit_spec, state, unit, chunk_ids)
        return {
            "current_unit_spec": repaired,
            "current_node": "repair_unit_spec",
            "progress": unit_progress(state, "repairing_unit_spec", current_node="repair_unit_spec"),
        }

    return {
        "current_node": "repair_unit_spec",
        "progress": unit_progress(state, "repairing_unit_spec", current_node="repair_unit_spec"),
    }


__all__ = ["repair_unit_spec"]
```

---

## 12. 修改 `app/workflows/content_generation_graph.py`

### 12.1 新增 import

```python
from app.workflows.nodes.repair_unit_spec_node import repair_unit_spec
```

### 12.2 新增节点

```python
workflow.add_node("repair_unit_spec", repair_unit_spec)
```

### 12.3 修改 unit spec 校验路由

当前：

```python
workflow.add_conditional_edges(
    "validate_unit_spec",
    route_after_unit_spec_validation,
    {"pass": "collect_unit_required_elements", "fail": "fail_task"},
)
```

P1 修改为：

```python
workflow.add_conditional_edges(
    "validate_unit_spec",
    route_after_unit_spec_validation,
    {"pass": "collect_unit_required_elements", "fail": "repair_unit_spec"},
)
workflow.add_edge("repair_unit_spec", "validate_unit_spec")
```

### 12.4 防止无限 repair

在 `ContentGenerationState` 中增加：

```python
repair_counts: dict[str, int] = Field(default_factory=dict)
```

`repair_unit_spec()` 中按 unit id 计数。超过 1 次仍失败则让 route 进入 `fail_task`。

更稳的做法是在 `validator_node.py` 新增路由：

```python
def route_after_unit_spec_validation(state: ContentGenerationState) -> str:
    report = state.spec_validation_report or {}
    if report.get("passed"):
        return "pass"
    unit = current_outline_unit(state)
    repair_counts = state.repair_counts or {}
    if repair_counts.get(unit.id, 0) < 1:
        return "repair"
    return "fail"
```

对应 graph：

```python
{"pass": "collect_unit_required_elements", "repair": "repair_unit_spec", "fail": "fail_task"}
```

---

## 13. 修改 `app/services/llm_service.py`

### 13.1 修改目标

增强结构化 JSON 解析，降低模型输出 markdown fence 或前后解释导致的失败。

### 13.2 新增 `_extract_json_object()`

```python
def _extract_json_object(content: str) -> str:
    cleaned = content.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start : end + 1]

    return cleaned
```

### 13.3 修改 `generate_structured()` 中 JSON parse 逻辑

将：

```python
json.loads(cleaned)
```

改为：

```python
json.loads(_extract_json_object(cleaned))
```

### 13.4 强化 repair prompt

repair prompt 增加：

```text
只修复 JSON 格式、字段类型和 schema 不匹配问题。
不要新增无依据内容。
不要改变原始字段语义。
如果字段缺失，用最小可用值补齐。
只输出合法 JSON，不输出 Markdown 代码块。
```

---

## 14. 新增 render 质量检查

### 14.1 新增文件

```text
app/renderers/slide_render_validator.py
```

### 14.2 新增函数

```python
from app.renderers.slide_renderer import SLIDE_HEIGHT, SLIDE_WIDTH
from app.schemas.render import KitSlideElement


def validate_slide_render_elements(elements: list[KitSlideElement]) -> list[str]:
    errors: list[str] = []
    for element in elements:
        if element.left < 0 or element.top < 0:
            errors.append(f"{element.id} has negative position")
        if element.width <= 0 or element.height <= 0:
            errors.append(f"{element.id} has invalid size")
        if element.left + element.width > SLIDE_WIDTH:
            errors.append(f"{element.id} exceeds slide width")
        if element.top + element.height > SLIDE_HEIGHT:
            errors.append(f"{element.id} exceeds slide height")
    return errors
```

### 14.3 接入 `slide_renderer.py`

P1 中 renderer 不再只 clamp，还要记录 warning。由于当前 `SlideRenderModel` 没有 warnings 字段，先通过 `page.page.metadata` 不可用；建议在 `KitSlidePage` 增加：

```python
metadata: Metadata = Field(default_factory=dict)
```

然后：

```python
render_warnings = validate_slide_render_elements(page_elements)
...
page=KitSlidePage(
    ...,
    metadata={"render_warnings": render_warnings},
)
```

---

## 15. 测试修改建议

### 15.1 修改 `tests/test_schemas.py`

新增测试：

```python
def test_slide_layout_does_not_allow_cover():
    ...


def test_slide_required_elements_only_allow_image():
    ...


def test_title_content_visual_requires_visual_role():
    ...


def test_summary_cards_forbids_visual_role():
    ...
```

### 15.2 修改 `tests/test_workflow.py`

新增测试：

```python
def test_slide_stub_generation_never_outputs_mindmap():
    ...


def test_slide_stub_generation_never_outputs_cover():
    ...


def test_slide_visual_layout_has_image_required_element():
    ...
```

### 15.3 修改 `tests/test_workflow_structure.py`

P1 新增：

```python
def test_graph_contains_repair_unit_spec_node():
    ...
```

---

# 最终验收标准

## P0 验收标准

1. 生成 slide_deck 时，不出现 `layout = "cover"`。
2. 生成 slide_deck 时，不出现 `required_elements.type = "mindmap"`。
3. 普通图文页只声明一个 `image`，并通过 `element_ref` 的 `metadata.role = "visual"` 引用。
4. `title-content`、`summary-cards`、`section-divider` 不包含 visual。
5. `title-content-visual`、`visual-left-content-right` 必须包含 visual。
6. 可见文本明显变短，长解释进入 `speaker_notes`。
7. renderer 不再自动重复 `core_message` 作为 takeaway。
8. 图片 prompt 明确禁止生成完整 PPT 页面。
9. 前端渲染不再出现大面积文本截断。

## P1 验收标准

1. graph 中存在 `repair_unit_spec` 节点。
2. `validate_unit_spec` 失败后先进入一次 repair，再重新 validate。
3. repair 不调用 LLM，只执行确定性修复。
4. LLM 输出带 markdown fence 或解释文字时，`llm_service` 能提取 JSON。
5. render 后元素越界会被记录为 warning 或被 clamp。
6. 测试覆盖 cover 移除、mindmap 移除、layout-role contract、repair 节点。

---

# 推荐实施顺序

```text
1. 改 slide_outline.md
2. 改 slide_deck_spec.md
3. 改 specs.py
4. 改 unit_spec_generators.py
5. 改 validator_node.py
6. 改 element_flow_node.py
7. 改 image_generation_service.py
8. 改 slide_renderer.py
9. 跑现有 tests
10. 补 schema / workflow 测试
11. P1 新增 repair_unit_spec_node.py
12. P1 修改 graph 路由
13. P1 增强 llm_service JSON 提取
14. P1 增加 render validator
```

---

# 核心结论

本轮改造应采用 OpenMAIC 的强约束思想，但保持当前项目的模板化 renderer：

```text
LLM 负责生成结构化 slide spec
Schema 负责限定 layout / role / resource 类型
Normalizer 负责修正文本、图片策略和 layout
Validator 负责拦截不可渲染结构
Repair 节点负责一次确定性修复
Renderer 负责按 layout contract 稳定渲染
```

当前版本不引入 cover，不引入 mindmap，只把 image + text + layout contract 做稳。
