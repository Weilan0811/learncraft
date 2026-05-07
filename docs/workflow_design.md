# 内容生成 Agent Workflow 最终设计方案

## 1. 文档定位

本文档用于指导内容生成 Agent 的 LangGraph workflow 最终实现。当前 MVP 支持两类内容生成：

- `lecture`
- `slide_deck`

当前 MVP 支持两类多模态元素生成：

- `image`
- `mindmap`

后续扩展位包括：

- 内容类型扩展：`social_post`、`podcast_script`、`video_script`、`quiz_pack`、`learning_path`
- 元素类型扩展：`table`、`quiz`、`chart`、`citation`、`audio`、`video`

本方案采用统一主链路：

```text
request
  -> retrieval
  -> outline
  -> unit_loop
  -> unit_spec
  -> image / mindmap elements
  -> assembled content_spec
  -> renderer
  -> preview
```

导出流程由前端导出动作触发，基于已生成的 `render_model` 和资源快照执行。

---

## 2. 总体设计原则

### 2.1 主链路原则

内容生成 Agent 统一采用以下生成主线：

```text
content_request
  -> outline
  -> unit_specs
  -> elements
  -> content_spec
  -> render_model
```

其中：

| 层级 | 产物 | 职责 |
|---|---|---|
| 请求层 | `ContentGenerationRequest` | 接收用户主题、内容类型、知识库、生成配置 |
| 规划层 | `Outline` | 生成全局内容结构 |
| 单元层 | `UnitSpec` | 按章 / 按页生成结构化内容单元 |
| 元素层 | `ImageElement` / `MindmapElement` | 生成真实多模态元素 |
| 组装层 | `LectureSpec` / `SlideDeckSpec` | 合并所有单元结果 |
| 渲染层 | `LectureRenderModel` / `SlideRenderModel` | 生成前端可预览模型 |

### 2.2 分支原则

workflow 中保留三类分支点：

```text
content_type 分支
element_type 分支
renderer 分支
```

当前实现分支：

```text
content_type:
  - lecture
  - slide_deck

element_type:
  - image
  - mindmap

renderer:
  - lecture_renderer
  - slide_renderer
```

后续新增内容类型或元素类型时，扩展对应分支节点与 schema。

### 2.3 循环原则

workflow 中采用 `outline.units` 作为循环粒度。

```text
lecture:
  unit = section

slide_deck:
  unit = slide / page
```

每个 unit 独立完成：

```text
retrieve_for_unit
generate_unit_spec
collect_unit_required_elements
generate_unit_elements_parallel
validate_unit
merge_unit_result
```

所有 unit 完成后统一执行：

```text
assemble_content_spec
validate_content
render_content
```

### 2.4 并行原则

单个 unit 内部的元素生成采用 Fan-out / Fan-in 结构：

```text
collect_unit_required_elements
  -> dispatch_element_generation
      -> generate_image_element
      -> generate_mindmap_element
  -> merge_unit_elements
```

一个 `ElementRequest` 对应一个并行 worker。并行 worker 只生成一个 element。所有分支结果由 `merge_unit_elements` 汇总。

---

## 3. 最终 Workflow 总览

```text
START
  ↓
normalize_request
  ↓
retrieve_for_planning
  ↓
plan_outline
  ↓
validate_outline
  ↓
route_content_type
      ├─ lecture      -> initialize_section_units
      └─ slide_deck   -> initialize_slide_units

  ↓
unit_loop
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
      ├─ generate_image_element
      └─ generate_mindmap_element
  ↓
merge_unit_elements
  ↓
validate_unit
  ↓
merge_unit_result
  ↓
has_more_units?
      ├─ yes -> retrieve_for_unit
      └─ no  -> assemble_content_spec

  ↓
validate_content
  ↓
route_renderer
      ├─ lecture      -> lecture_renderer
      └─ slide_deck   -> slide_renderer
  ↓
finalize_task
  ↓
END
```

异常恢复路径：

```text
validate_outline failed
  -> repair_outline
  -> validate_outline

validate_unit_spec failed
  -> repair_unit_spec
  -> collect_unit_required_elements

element generation failed
  -> retry_failed_elements
  -> merge_unit_elements

validate_unit failed
  -> repair_unit_result
  -> validate_unit

validate_content failed
  -> repair_content_spec
  -> validate_content

unrecoverable failure
  -> fail_task
  -> END
```

---

## 4. 节点职责定义

### 4.1 `normalize_request`

#### 职责

标准化用户请求，补齐默认配置。

#### 示例输入

```json
{
  "content_type": "slide_deck",
  "topic": "人工智能基础导论",
  "user_prompt": "生成一份适合本科一年级学生学习的课件",
  "knowledge_base_ids": ["kb_ai_basic"],
  "generation_options": {
    "language": "zh-CN"
  }
}
```

#### 示例输出

```json
{
  "normalized_request": {
    "content_type": "slide_deck",
    "topic": "人工智能基础导论",
    "language": "zh-CN",
    "difficulty": "introductory",
    "audience": "本科一年级学生"
  }
}
```

---

### 4.2 `retrieve_for_planning`

#### 职责

面向整体主题执行第一次检索，为 outline 生成提供上下文。

#### 输出

```json
{
  "planning_chunks": [
    {
      "id": "chunk_001",
      "source_id": "doc_001",
      "source_title": "人工智能基础教材",
      "content": "人工智能是研究如何使机器表现出智能行为的技术领域……",
      "score": 0.89,
      "metadata": {
        "page": 3,
        "section": "第一章"
      }
    }
  ]
}
```

---

### 4.3 `plan_outline`

#### 职责

生成全局内容大纲。`Outline` 定义整份内容的标题、目标、结构、单元列表、每个单元的核心信息和推荐元素。

#### 输出

```json
{
  "id": "outline_001",
  "type": "outline",
  "version": "1.0",
  "content_type": "slide_deck",
  "title": "人工智能基础导论",
  "language": "zh-CN",
  "audience": {
    "label": "本科一年级学生",
    "prior_knowledge": "无系统 AI 基础"
  },
  "difficulty": "introductory",
  "global_objectives": [
    "理解人工智能的基本概念",
    "区分人工智能、机器学习与深度学习"
  ],
  "units": [
    {
      "id": "unit_001",
      "order": 1,
      "unit_type": "slide",
      "title": "什么是人工智能",
      "goal": "解释人工智能的定义与边界",
      "core_message": "人工智能的核心是让机器表现出一定程度的智能行为。",
      "key_points": [
        "人工智能的基本定义",
        "人工智能与传统程序的区别"
      ],
      "visual_strategy": "title-left-text-right-visual",
      "recommended_elements": [
        {
          "type": "image",
          "purpose": "展示人工智能应用场景",
          "priority": "high"
        }
      ],
      "retrieval_queries": [
        "人工智能 定义 基本概念"
      ],
      "source_chunk_ids": ["chunk_001"]
    }
  ],
  "metadata": {
    "created_by": "planner_node"
  }
}
```

---

### 4.4 `validate_outline`

#### 职责

校验 outline 是否满足后续单元生成要求。

#### 校验项

```text
1. outline.id 存在
2. outline.content_type 合法
3. outline.units 非空
4. units 中 id 唯一
5. 每个 unit 包含 title、goal、core_message
6. 每个 unit 包含 retrieval_queries
7. recommended_elements 只包含当前支持或预留的元素类型
```

---

### 4.5 `route_content_type`

#### 职责

根据 `content_type` 初始化不同类型的 unit 循环。

#### 路由规则

```text
lecture:
  -> initialize_section_units

slide_deck:
  -> initialize_slide_units
```

当前两条分支均进入统一的 `unit_loop`。差异由 `unit_type`、`content_type` 和 `generate_unit_spec` 内部路由处理。

---

### 4.6 `initialize_section_units`

#### 职责

为讲义生成初始化章节循环。

#### 输出

```json
{
  "pending_unit_ids": ["unit_001", "unit_002", "unit_003"],
  "current_unit_index": 0,
  "completed_unit_ids": [],
  "failed_unit_ids": []
}
```

---

### 4.7 `initialize_slide_units`

#### 职责

为 slide deck 生成初始化页面循环。

#### 输出

```json
{
  "pending_unit_ids": ["unit_001", "unit_002", "unit_003"],
  "current_unit_index": 0,
  "completed_unit_ids": [],
  "failed_unit_ids": []
}
```

---

### 4.8 `retrieve_for_unit`

#### 职责

根据当前 unit 的标题、核心信息、检索 query 执行二次检索。

#### 输出

```json
{
  "current_unit_context": [
    {
      "id": "chunk_011",
      "source_id": "doc_001",
      "source_title": "人工智能基础教材",
      "content": "人工智能的核心目标包括感知、推理、学习和决策……",
      "score": 0.91
    }
  ]
}
```

---

### 4.9 `generate_unit_spec`

#### 职责

根据当前 unit、当前 unit context 和 content_type 生成单元 spec。

#### 路由规则

```text
content_type = lecture:
  -> generate_lecture_section_spec

content_type = slide_deck:
  -> generate_slide_page_spec
```

---

### 4.10 `validate_unit_spec`

#### 职责

校验单元 spec 的结构完整性。

#### 校验项

```text
1. unit_spec.id 存在
2. unit_spec.outline_unit_id 与当前 unit.id 一致
3. unit_spec.title 存在
4. unit_spec 中的 element_ref 均有 element_id
5. element_ref 对应的 element_id 均能在 required_elements 中找到
6. required_elements 中只包含 image 或 mindmap
7. required_elements 中 element_id 唯一
```

---

### 4.11 `collect_unit_required_elements`

#### 职责

从当前 unit spec 中收集 `required_elements`，转换为统一 `ElementRequest`。

#### 输出

```json
{
  "current_unit_element_requests": [
    {
      "element_id": "image_001",
      "type": "image",
      "title": "人工智能应用场景示意图",
      "purpose": "展示 AI 在多个行业中的应用",
      "instruction": "生成一张简洁学术风格插图，展示 AI 在教育、医疗、交通、金融中的应用。",
      "source_content_type": "slide_deck",
      "source_unit_id": "slide_001",
      "source_outline_unit_id": "unit_001",
      "source_chunk_ids": ["chunk_011"],
      "constraints": {
        "style": "clean academic illustration",
        "aspect_ratio": "4:3"
      },
      "priority": "high",
      "retry_policy": {
        "max_retries": 2,
        "fallback_strategy": "placeholder_asset"
      }
    }
  ]
}
```

---

### 4.12 `dispatch_element_generation`

#### 职责

将当前 unit 的 `ElementRequest` 拆分为多个并行任务。

#### 分发规则

```text
ElementRequest.type = image
  -> Send("generate_image_element")

ElementRequest.type = mindmap
  -> Send("generate_mindmap_element")
```

#### Fan-out 结构

```text
dispatch_element_generation
  ├─ generate_image_element(element_request=image_001)
  ├─ generate_mindmap_element(element_request=mindmap_001)
  └─ generate_image_element(element_request=image_002)
```

---

### 4.13 `generate_image_element`

#### 职责

根据单个 `ImageElementRequest` 调用图片生成服务，保存资源，返回 `ImageElement`。

#### 输出

```json
{
  "current_unit_elements": [
    {
      "id": "image_001",
      "type": "image",
      "title": "人工智能应用场景示意图",
      "status": "completed",
      "prompt": "A clean academic illustration showing AI applications in education, healthcare, transportation and finance.",
      "asset_id": "asset_img_001",
      "asset_url": "/api/assets/asset_img_001/download",
      "alt_text": "人工智能在教育、医疗、交通和金融中的应用场景示意图。",
      "source_unit_id": "slide_001",
      "source_outline_unit_id": "unit_001",
      "source_chunk_ids": ["chunk_011"],
      "metadata": {
        "width": 1280,
        "height": 960,
        "format": "png",
        "aspect_ratio": "4:3"
      }
    }
  ]
}
```

---

### 4.14 `generate_mindmap_element`

#### 职责

根据单个 `MindmapElementRequest` 生成 Markdown 思维导图。

#### 输出

```json
{
  "current_unit_elements": [
    {
      "id": "mindmap_001",
      "type": "mindmap",
      "title": "人工智能基础知识结构",
      "status": "completed",
      "markdown": "# 人工智能基础\n## 基本概念\n### 人工智能\n### 机器学习\n### 深度学习\n## 应用场景\n### 教育\n### 医疗\n### 金融",
      "source_unit_id": "lecture_sec_001",
      "source_outline_unit_id": "unit_001",
      "source_chunk_ids": ["chunk_011"],
      "metadata": {
        "max_depth": 3,
        "format": "markmap_markdown"
      }
    }
  ]
}
```

---

### 4.15 `merge_unit_elements`

#### 职责

汇总并行 element 生成结果，写入当前 unit 和全局 elements registry。

#### 合并规则

```text
1. 读取 current_unit_elements
2. 按 element.id 写入 state.elements
3. 成功元素写入 unit_results[current_unit_id].elements
4. 失败元素写入 failed_element_requests
5. 重复 element_id 按最新成功结果覆盖
```

---

### 4.16 `validate_unit`

#### 职责

校验当前 unit spec 与当前 unit elements 是否闭合。

#### 校验项

```text
1. unit_spec 中所有 element_ref 均存在对应 element
2. required_elements 中所有 high priority 元素均生成成功
3. ImageElement 包含 prompt、asset_url、alt_text
4. MindmapElement 包含 markdown
5. element.source_unit_id 与当前 unit spec id 一致
6. renderer 支持当前 unit 中出现的元素类型
```

---

### 4.17 `merge_unit_result`

#### 职责

将当前 unit 的 spec、elements、validation report 写入 `unit_results`。

#### 输出

```json
{
  "unit_results": {
    "unit_001": {
      "unit_id": "unit_001",
      "status": "completed",
      "unit_spec": {},
      "elements": {},
      "validation_report": {}
    }
  },
  "completed_unit_ids": ["unit_001"],
  "current_unit_index": 1
}
```

---

### 4.18 `has_more_units`

#### 职责

判断是否继续 unit 循环。

#### 路由规则

```text
current_unit_index < len(pending_unit_ids)
  -> retrieve_for_unit

current_unit_index >= len(pending_unit_ids)
  -> assemble_content_spec

failed_unit_count > max_allowed_failed_units
  -> fail_task
```

---

### 4.19 `assemble_content_spec`

#### 职责

将所有 unit spec 合并为完整 `LectureSpec` 或 `SlideDeckSpec`。

#### 讲义合并

```text
unit_results[].unit_spec
  -> LectureSpec.sections[]
```

#### Slide 合并

```text
unit_results[].unit_spec
  -> SlideDeckSpec.slides[]
```

---

### 4.20 `validate_content`

#### 职责

校验完整 content_spec 与全局 elements 是否闭合。

#### 校验项

```text
1. content_spec.outline_id 与 outline.id 一致
2. content_spec 中所有 unit 均来自 outline.units
3. content_spec 中所有 element_ref 均存在对应 element
4. 全局 elements 中所有 element_id 唯一
5. 所有高优先级 image / mindmap 元素生成成功
6. renderer 支持所有需要渲染的元素
```

---

### 4.21 `route_renderer`

#### 职责

根据 content_type 路由到对应 renderer。

#### 路由规则

```text
lecture:
  -> lecture_renderer

slide_deck:
  -> slide_renderer
```

---

### 4.22 `lecture_renderer`

#### 职责

将 `LectureSpec` 与 `elements` 转换为讲义预览模型。

#### 输出

```json
{
  "render_type": "lecture_page",
  "title": "人工智能基础导论",
  "sections": [
    {
      "id": "lecture_sec_001",
      "title": "什么是人工智能",
      "render_blocks": [
        {
          "type": "heading",
          "content": "什么是人工智能"
        },
        {
          "type": "paragraph",
          "content": "人工智能通常指……"
        },
        {
          "type": "image",
          "element_id": "image_001",
          "asset_url": "/api/assets/asset_img_001/download"
        },
        {
          "type": "mindmap",
          "element_id": "mindmap_001",
          "markdown": "# 人工智能基础\n## 基本概念"
        }
      ]
    }
  ],
  "printable_model": {}
}
```

---

### 4.23 `slide_renderer`

#### 职责

将 `SlideDeckSpec` 与 `elements` 转换为 `scenekit.slide/v1` 预览模型。

#### 输出

```json
{
  "render_type": "slide_deck",
  "version": "scenekit.slide/v1",
  "pages": [
    {
      "id": "slide_001",
      "title": "什么是人工智能",
      "width": 960,
      "height": 540,
      "elements": []
    }
  ]
}
```

---

### 4.24 `finalize_task`

#### 职责

保存任务最终结果，更新任务状态为 `completed`。

#### 保存内容

```text
outline
content_spec
elements
render_model
task logs
token usage
asset refs
```

---

### 4.25 `fail_task`

#### 职责

保存失败状态和可解释错误信息。

#### 输出

```json
{
  "status": "failed",
  "errors": [
    {
      "stage": "validate_content",
      "code": "missing_required_element",
      "message": "image_001 生成失败且 fallback 失败",
      "recoverable": false
    }
  ]
}
```

---

## 5. State 最终结构

```python
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


ContentType = Literal["lecture", "slide_deck"]
ElementType = Literal["image", "mindmap"]

TaskStatus = Literal[
    "pending",
    "retrieving",
    "planning",
    "generating_unit",
    "generating_elements",
    "validating",
    "rendering",
    "completed",
    "failed",
]


class WorkflowError(BaseModel):
    stage: str
    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)
    recoverable: bool = True


class ElementStatus(BaseModel):
    element_id: str
    type: ElementType
    status: Literal["pending", "generating", "completed", "failed", "skipped"]
    retry_count: int = 0
    error: Optional[str] = None


class UnitGenerationResult(BaseModel):
    unit_id: str
    status: Literal["pending", "completed", "failed"]
    unit_spec: Optional[dict[str, Any]] = None
    element_requests: dict[str, dict[str, Any]] = Field(default_factory=dict)
    elements: dict[str, dict[str, Any]] = Field(default_factory=dict)
    validation_report: Optional[dict[str, Any]] = None
    errors: list[WorkflowError] = Field(default_factory=list)


class ContentGenerationState(BaseModel):
    # task
    task_id: str
    request_id: str
    status: TaskStatus = "pending"
    current_stage: Optional[str] = None

    # request
    raw_request: dict[str, Any]
    normalized_request: Optional[dict[str, Any]] = None
    content_type: ContentType

    # retrieval
    planning_chunks: list[dict[str, Any]] = Field(default_factory=list)
    current_unit_context: list[dict[str, Any]] = Field(default_factory=list)
    unit_context_map: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)

    # outline
    outline: Optional[dict[str, Any]] = None
    outline_validation_report: Optional[dict[str, Any]] = None

    # unit loop
    pending_unit_ids: list[str] = Field(default_factory=list)
    completed_unit_ids: list[str] = Field(default_factory=list)
    failed_unit_ids: list[str] = Field(default_factory=list)
    current_unit_index: int = 0
    current_unit_id: Optional[str] = None
    current_unit_spec: Optional[dict[str, Any]] = None
    current_unit_element_requests: list[dict[str, Any]] = Field(default_factory=list)
    current_unit_elements: list[dict[str, Any]] = Field(default_factory=list)

    # unit results
    unit_results: dict[str, UnitGenerationResult] = Field(default_factory=dict)

    # assembled result
    content_spec: Optional[dict[str, Any]] = None
    elements: dict[str, dict[str, Any]] = Field(default_factory=dict)
    element_status: dict[str, ElementStatus] = Field(default_factory=dict)
    render_model: Optional[dict[str, Any]] = None

    # validation
    spec_validation_report: Optional[dict[str, Any]] = None
    validation_report: Optional[dict[str, Any]] = None

    # retry
    retry_counts: dict[str, int] = Field(default_factory=dict)
    failed_element_requests: list[dict[str, Any]] = Field(default_factory=list)
    max_allowed_failed_units: int = 0

    # logs
    errors: list[WorkflowError] = Field(default_factory=list)
    token_usage: dict[str, Any] = Field(default_factory=dict)
    logs: list[dict[str, Any]] = Field(default_factory=list)
```

---

## 6. 核心 Schema 设计

### 6.1 OutlineUnit

```json
{
  "id": "unit_001",
  "order": 1,
  "unit_type": "slide",
  "title": "什么是人工智能",
  "goal": "解释人工智能的定义与边界",
  "core_message": "人工智能的核心是让机器表现出一定程度的智能行为。",
  "key_points": [
    "人工智能的基本定义",
    "人工智能与传统程序的区别"
  ],
  "visual_strategy": "title-left-text-right-visual",
  "recommended_elements": [
    {
      "type": "image",
      "purpose": "展示人工智能应用场景",
      "priority": "high"
    }
  ],
  "retrieval_queries": [
    "人工智能 定义 基本概念"
  ],
  "source_chunk_ids": ["chunk_001"]
}
```

---

### 6.2 SlideUnitSpec

```json
{
  "id": "slide_001",
  "outline_unit_id": "unit_001",
  "order": 1,
  "title": "什么是人工智能",
  "core_message": "人工智能的核心是让机器表现出一定程度的智能行为。",
  "slide_role": "concept_explanation",
  "layout": "title-left-text-right-visual",
  "speaker_notes": "这一页用于建立基本概念。",
  "slots": [
    {
      "id": "slot_001",
      "type": "text",
      "slot_role": "title",
      "content": "什么是人工智能",
      "position_hint": {
        "region": "top",
        "priority": 1
      }
    },
    {
      "id": "slot_002",
      "type": "text",
      "slot_role": "body",
      "content": "人工智能是让机器表现出感知、学习、推理、生成或决策能力的技术体系。",
      "position_hint": {
        "region": "left",
        "priority": 2
      },
      "source_chunk_ids": ["chunk_011"]
    },
    {
      "id": "slot_003",
      "type": "element_ref",
      "slot_role": "main_visual",
      "element_id": "image_001",
      "purpose": "展示人工智能应用场景",
      "position_hint": {
        "region": "right",
        "priority": 3
      }
    }
  ],
  "required_elements": [
    {
      "element_id": "image_001",
      "type": "image",
      "title": "人工智能应用场景示意图",
      "purpose": "作为右侧主视觉",
      "instruction": "生成一张简洁学术风格插图，展示 AI 在教育、医疗、交通、金融中的应用。",
      "style": "clean academic illustration",
      "aspect_ratio": "4:3",
      "source_unit_id": "slide_001",
      "source_outline_unit_id": "unit_001",
      "source_chunk_ids": ["chunk_011"],
      "priority": "high"
    }
  ],
  "source_chunk_ids": ["chunk_011"]
}
```

---

### 6.3 LectureSectionSpec

```json
{
  "id": "lecture_sec_001",
  "outline_unit_id": "unit_001",
  "order": 1,
  "title": "什么是人工智能",
  "summary": "本节介绍人工智能的定义、边界和典型应用。",
  "learning_goal": "学生能够用自己的话解释人工智能的基本含义。",
  "blocks": [
    {
      "id": "block_001",
      "type": "heading",
      "level": 2,
      "content": "什么是人工智能"
    },
    {
      "id": "block_002",
      "type": "paragraph",
      "content": "人工智能通常指使机器表现出感知、学习、推理、生成或决策等智能行为的技术体系。",
      "source_chunk_ids": ["chunk_011"]
    },
    {
      "id": "block_003",
      "type": "element_ref",
      "element_id": "mindmap_001",
      "purpose": "展示本节知识结构",
      "display_hint": {
        "placement": "after_paragraph",
        "width": "full"
      }
    }
  ],
  "required_elements": [
    {
      "element_id": "mindmap_001",
      "type": "mindmap",
      "title": "人工智能基础知识结构",
      "purpose": "用思维导图概括本节知识结构",
      "instruction": "根据本节内容生成一个三层以内的 Markdown 思维导图。",
      "source_unit_id": "lecture_sec_001",
      "source_outline_unit_id": "unit_001",
      "source_chunk_ids": ["chunk_011"],
      "priority": "high"
    }
  ],
  "source_chunk_ids": ["chunk_011"]
}
```

---

### 6.4 ElementRequest

```json
{
  "element_id": "image_001",
  "type": "image",
  "title": "人工智能应用场景示意图",
  "purpose": "展示 AI 在多个行业中的应用",
  "instruction": "生成一张简洁学术风格插图，展示 AI 在教育、医疗、交通、金融中的应用。",
  "source_content_type": "slide_deck",
  "source_unit_id": "slide_001",
  "source_outline_unit_id": "unit_001",
  "source_chunk_ids": ["chunk_011"],
  "context": {
    "unit_title": "什么是人工智能",
    "core_message": "人工智能的核心是让机器表现出一定程度的智能行为。",
    "key_points": [
      "人工智能的基本定义",
      "人工智能的典型应用"
    ]
  },
  "constraints": {
    "language": "zh-CN",
    "style": "clean academic illustration",
    "aspect_ratio": "4:3"
  },
  "render_hints": {
    "usage": "slide_main_visual",
    "preferred_width": 380,
    "preferred_height": 300
  },
  "priority": "high",
  "retry_policy": {
    "max_retries": 2,
    "fallback_strategy": "placeholder_asset"
  }
}
```

---

### 6.5 ImageElement

```json
{
  "id": "image_001",
  "type": "image",
  "title": "人工智能应用场景示意图",
  "status": "completed",
  "prompt": "A clean academic illustration showing AI applications in education, healthcare, transportation and finance.",
  "asset_id": "asset_img_001",
  "asset_url": "/api/assets/asset_img_001/download",
  "alt_text": "人工智能在教育、医疗、交通和金融中的应用场景示意图。",
  "source_unit_id": "slide_001",
  "source_outline_unit_id": "unit_001",
  "source_chunk_ids": ["chunk_011"],
  "metadata": {
    "width": 1280,
    "height": 960,
    "format": "png",
    "aspect_ratio": "4:3"
  },
  "generation_info": {
    "generator": "image_generation_service",
    "provider": "apimart",
    "model": "gpt-image-2"
  }
}
```

---

### 6.6 MindmapElement

```json
{
  "id": "mindmap_001",
  "type": "mindmap",
  "title": "人工智能基础知识结构",
  "status": "completed",
  "markdown": "# 人工智能基础\n## 基本概念\n### 人工智能\n### 机器学习\n### 深度学习\n## 应用场景\n### 教育\n### 医疗\n### 金融",
  "source_unit_id": "lecture_sec_001",
  "source_outline_unit_id": "unit_001",
  "source_chunk_ids": ["chunk_011"],
  "metadata": {
    "max_depth": 3,
    "node_count": 9,
    "format": "markmap_markdown"
  },
  "render_hints": {
    "renderer": "markmap",
    "export_as": ["svg", "png"]
  }
}
```

---

## 7. LangGraph 代码级结构建议

### 7.1 节点注册

```python
workflow.add_node("normalize_request", normalize_request)
workflow.add_node("retrieve_for_planning", retrieve_for_planning)
workflow.add_node("plan_outline", plan_outline)
workflow.add_node("validate_outline", validate_outline)
workflow.add_node("repair_outline", repair_outline)

workflow.add_node("initialize_section_units", initialize_section_units)
workflow.add_node("initialize_slide_units", initialize_slide_units)

workflow.add_node("retrieve_for_unit", retrieve_for_unit)
workflow.add_node("generate_unit_spec", generate_unit_spec)
workflow.add_node("validate_unit_spec", validate_unit_spec)
workflow.add_node("repair_unit_spec", repair_unit_spec)

workflow.add_node("collect_unit_required_elements", collect_unit_required_elements)
workflow.add_node("generate_image_element", generate_image_element)
workflow.add_node("generate_mindmap_element", generate_mindmap_element)
workflow.add_node("merge_unit_elements", merge_unit_elements)

workflow.add_node("validate_unit", validate_unit)
workflow.add_node("repair_unit_result", repair_unit_result)
workflow.add_node("merge_unit_result", merge_unit_result)
workflow.add_node("assemble_content_spec", assemble_content_spec)
workflow.add_node("validate_content", validate_content)
workflow.add_node("repair_content_spec", repair_content_spec)

workflow.add_node("lecture_renderer", lecture_renderer)
workflow.add_node("slide_renderer", slide_renderer)
workflow.add_node("finalize_task", finalize_task)
workflow.add_node("fail_task", fail_task)
```

---

### 7.2 主边定义

```python
workflow.add_edge(START, "normalize_request")
workflow.add_edge("normalize_request", "retrieve_for_planning")
workflow.add_edge("retrieve_for_planning", "plan_outline")
workflow.add_edge("plan_outline", "validate_outline")
```

---

### 7.3 Outline 校验分支

```python
workflow.add_conditional_edges(
    "validate_outline",
    route_after_outline_validation,
    {
        "pass": "route_content_type",
        "repair": "repair_outline",
        "fail": "fail_task",
    },
)

workflow.add_edge("repair_outline", "validate_outline")
```

---

### 7.4 Content Type 分支

```python
workflow.add_conditional_edges(
    "route_content_type",
    route_content_type,
    {
        "lecture": "initialize_section_units",
        "slide_deck": "initialize_slide_units",
    },
)

workflow.add_edge("initialize_section_units", "retrieve_for_unit")
workflow.add_edge("initialize_slide_units", "retrieve_for_unit")
```

---

### 7.5 Unit 循环主链路

```python
workflow.add_edge("retrieve_for_unit", "generate_unit_spec")
workflow.add_edge("generate_unit_spec", "validate_unit_spec")

workflow.add_conditional_edges(
    "validate_unit_spec",
    route_after_unit_spec_validation,
    {
        "pass": "collect_unit_required_elements",
        "repair": "repair_unit_spec",
        "fail": "fail_task",
    },
)

workflow.add_edge("repair_unit_spec", "validate_unit_spec")
workflow.add_edge("collect_unit_required_elements", "dispatch_element_generation")
```

---

### 7.6 Element 并行分发

`dispatch_element_generation` 使用动态 `Send` 派发任务。

```python
from langgraph.constants import Send


def dispatch_element_generation(state: ContentGenerationState):
    sends = []

    for req in state.current_unit_element_requests:
        if req["type"] == "image":
            sends.append(
                Send(
                    "generate_image_element",
                    {
                        "task_id": state.task_id,
                        "current_unit_id": state.current_unit_id,
                        "element_request": req,
                    },
                )
            )

        if req["type"] == "mindmap":
            sends.append(
                Send(
                    "generate_mindmap_element",
                    {
                        "task_id": state.task_id,
                        "current_unit_id": state.current_unit_id,
                        "element_request": req,
                    },
                )
            )

    return sends
```

并行节点统一返回：

```python
{
    "current_unit_elements": [element]
}
```

失败时返回：

```python
{
    "failed_element_requests": [
        {
            "element_id": req["element_id"],
            "type": req["type"],
            "reason": "generation timeout",
        }
    ]
}
```

---

### 7.7 Element 汇总

```python
workflow.add_edge("generate_image_element", "merge_unit_elements")
workflow.add_edge("generate_mindmap_element", "merge_unit_elements")
workflow.add_edge("merge_unit_elements", "validate_unit")
```

State 中 `current_unit_elements` 采用 list 聚合，`merge_unit_elements` 统一写入 dict。

```python
def merge_unit_elements(state: ContentGenerationState):
    merged_elements = dict(state.elements)

    for element in state.current_unit_elements:
        merged_elements[element["id"]] = element

    return {
        "elements": merged_elements
    }
```

---

### 7.8 Unit 校验与循环

```python
workflow.add_conditional_edges(
    "validate_unit",
    route_after_unit_validation,
    {
        "pass": "merge_unit_result",
        "repair": "repair_unit_result",
        "retry_elements": "retry_failed_elements",
        "fail": "fail_task",
    },
)

workflow.add_edge("repair_unit_result", "validate_unit")
workflow.add_edge("retry_failed_elements", "merge_unit_elements")
```

循环判断：

```python
workflow.add_conditional_edges(
    "merge_unit_result",
    should_continue_units,
    {
        "continue": "retrieve_for_unit",
        "done": "assemble_content_spec",
        "failed": "fail_task",
    },
)
```

判断函数：

```python
def should_continue_units(state: ContentGenerationState) -> str:
    if len(state.failed_unit_ids) > state.max_allowed_failed_units:
        return "failed"

    if state.current_unit_index < len(state.pending_unit_ids):
        return "continue"

    return "done"
```

---

### 7.9 组装、校验与渲染分支

```python
workflow.add_edge("assemble_content_spec", "validate_content")

workflow.add_conditional_edges(
    "validate_content",
    route_after_content_validation,
    {
        "pass": "route_renderer",
        "repair": "repair_content_spec",
        "fail": "fail_task",
    },
)

workflow.add_edge("repair_content_spec", "validate_content")

workflow.add_conditional_edges(
    "route_renderer",
    route_renderer,
    {
        "lecture": "lecture_renderer",
        "slide_deck": "slide_renderer",
    },
)

workflow.add_edge("lecture_renderer", "finalize_task")
workflow.add_edge("slide_renderer", "finalize_task")
workflow.add_edge("finalize_task", END)
workflow.add_edge("fail_task", END)
```

---

## 8. 并行处理设计

### 8.1 Fan-out / Fan-in 模式

Element 生成节点采用标准 Fan-out / Fan-in：

```text
collect_unit_required_elements
  ↓
dispatch_element_generation
  ├─ generate_image_element(req_1)
  ├─ generate_image_element(req_2)
  └─ generate_mindmap_element(req_3)
  ↓
merge_unit_elements
```

### 8.2 并行粒度

当前 MVP 使用以下并行粒度：

```text
unit 之间串行
unit 内 element 并行
```

第二阶段可扩展为：

```text
unit 之间有限并行
unit 内 element 并行
```

### 8.3 并行返回约定

每个 worker 节点返回 list：

```python
{
    "current_unit_elements": [element]
}
```

所有 worker 结果由 reducer 聚合到 `current_unit_elements`。

### 8.4 合并约定

`merge_unit_elements` 将 list 转换为全局 dict：

```python
state.elements[element["id"]] = element
```

### 8.5 并发限制

service 层控制最大并发数。

建议配置：

```env
CONTENT_GENERATOR_MAX_CONCURRENT_IMAGES=2
CONTENT_GENERATOR_MAX_CONCURRENT_MINDMAPS=3
CONTENT_GENERATOR_MAX_CONCURRENT_ELEMENTS=3
```

示例：

```python
image_semaphore = asyncio.Semaphore(2)

async def generate_image_with_limit(request):
    async with image_semaphore:
        return await image_generation_service.generate(request)
```

---

## 9. 重试与降级策略

### 9.1 节点级重试

| 节点 | 最大重试次数 | 失败处理 |
|---|---:|---|
| `retrieve_for_planning` | 1 | 使用空上下文继续 |
| `plan_outline` | 2 | 进入 `fail_task` |
| `generate_unit_spec` | 2 | 进入 `repair_unit_spec` |
| `generate_image_element` | 2 | 生成 placeholder image |
| `generate_mindmap_element` | 1 | 生成简化 Markdown 大纲 |
| `render_content` | 1 | 返回 validate_content 检查 |

### 9.2 Image 降级

图片生成失败后返回 placeholder image：

```json
{
  "id": "image_001",
  "type": "image",
  "title": "人工智能应用场景示意图",
  "status": "completed",
  "asset_url": "/api/assets/placeholder_image/download",
  "alt_text": "图片生成失败后的占位图",
  "metadata": {
    "fallback": true
  }
}
```

### 9.3 Mindmap 降级

思维导图生成失败后返回简化 Markdown：

```json
{
  "id": "mindmap_001",
  "type": "mindmap",
  "title": "人工智能基础知识结构",
  "status": "completed",
  "markdown": "# 人工智能基础\n## 核心概念\n## 典型应用\n## 学习重点",
  "metadata": {
    "fallback": true
  }
}
```

---

## 10. Validator 规则

### 10.1 Outline 校验

```text
1. outline 存在
2. outline.units 非空
3. unit.id 唯一
4. unit.order 连续或可排序
5. unit.title 存在
6. unit.core_message 存在
7. unit.retrieval_queries 存在
```

### 10.2 UnitSpec 校验

```text
1. unit_spec.id 存在
2. unit_spec.outline_unit_id 存在
3. unit_spec.outline_unit_id 等于当前 unit.id
4. slots / blocks 非空
5. element_ref 均有 element_id
6. required_elements 中包含所有被引用的 element_id
7. required_elements 类型限定为 image / mindmap
```

### 10.3 Element 校验

```text
ImageElement:
  1. id 存在
  2. type = image
  3. prompt 存在
  4. asset_url 存在
  5. alt_text 存在

MindmapElement:
  1. id 存在
  2. type = mindmap
  3. markdown 存在
  4. markdown 以 # 开头
```

### 10.4 Unit 校验

```text
1. unit_spec 中所有 element_ref 均能在 current_unit_elements 或 state.elements 中找到
2. 所有 high priority required_elements 均生成成功
3. 元素 source_unit_id 与当前 unit spec id 一致
4. 当前 renderer 支持所有元素类型
```

### 10.5 Content 校验

```text
1. content_spec.outline_id 与 outline.id 一致
2. content_spec 中所有 section / slide 均有 outline_unit_id
3. content_spec 中所有 element_ref 均有真实 element
4. elements 全局 id 唯一
5. render_model 所需资源均可访问
```

---

## 11. Render 设计

### 11.1 LectureRenderer

输入：

```text
LectureSpec + elements
```

处理规则：

```text
heading block -> heading render block
paragraph block -> paragraph render block
element_ref(image) -> image render block
element_ref(mindmap) -> mindmap render block
```

输出：

```json
{
  "render_type": "lecture_page",
  "title": "人工智能基础导论",
  "sections": [],
  "printable_model": {}
}
```

---

### 11.2 SlideRenderer

输入：

```text
SlideDeckSpec + elements
```

处理规则：

```text
text slot -> scenekit text element
element_ref(image) -> scenekit image element
element_ref(mindmap) -> mindmap preview block 或转 SVG/PNG 后作为 image element
```

输出：

```json
{
  "render_type": "slide_deck",
  "version": "scenekit.slide/v1",
  "pages": []
}
```

---

## 12. API 与任务状态

### 12.1 创建任务

```http
POST /api/content-generation/tasks
```

请求：

```json
{
  "content_type": "slide_deck",
  "topic": "人工智能基础导论",
  "user_prompt": "生成一份适合本科一年级学生学习的课件",
  "knowledge_base_ids": ["kb_ai_basic"],
  "generation_options": {
    "language": "zh-CN",
    "difficulty": "introductory",
    "include_images": true,
    "include_mindmaps": true,
    "include_tables": false,
    "include_quizzes": false,
    "include_charts": false,
    "include_citations": false
  }
}
```

响应：

```json
{
  "task_id": "task_001",
  "status": "queued"
}
```

---

### 12.2 查询任务

```http
GET /api/content-generation/tasks/{task_id}
```

响应：

```json
{
  "task_id": "task_001",
  "status": "generating_elements",
  "content_type": "slide_deck",
  "progress": {
    "current_stage": "generate_unit_elements_parallel",
    "current_unit_id": "unit_003",
    "completed_units": 2,
    "total_units": 8,
    "completed_elements": 4,
    "total_elements": 7
  },
  "preview_url": null,
  "errors": []
}
```

---

### 12.3 获取预览

```http
GET /api/content-generation/tasks/{task_id}/preview
```

响应：

```json
{
  "task_id": "task_001",
  "content_type": "slide_deck",
  "render_model": {}
}
```

---

### 12.4 导出内容

```http
POST /api/content-generation/tasks/{task_id}/export
```

请求：

```json
{
  "export_type": "slide_json"
}
```

响应：

```json
{
  "export_type": "slide_json",
  "file_url": "/api/assets/asset_export_001/download",
  "status": "success"
}
```

---

## 13. 后端模块落地结构

```text
backend/app/
  workflows/
    content_generation_graph.py
    states.py
    routers.py
    nodes/
      normalize_request_node.py
      retriever_node.py
      planner_node.py
      unit_initializer_node.py
      unit_spec_generator_node.py
      element_collector_node.py
      element_dispatcher_node.py
      image_element_node.py
      mindmap_element_node.py
      validator_node.py
      assembler_node.py
      renderer_node.py

  schemas/
    request.py
    outline.py
    specs.py
    elements.py
    render.py
    validation.py
    state.py

  services/
    llm_service.py
    rag_service.py
    image_generation_service.py
    asset_service.py
    storage_service.py

  generators/
    lecture_section_spec_generator.py
    slide_page_spec_generator.py
    image_prompt_generator.py
    mindmap_generator.py

  renderers/
    lecture_renderer.py
    slide_renderer.py
```

---

## 14. 开发优先级

### P0：主闭环

```text
1. ContentGenerationState
2. Outline schema
3. LectureSectionSpec schema
4. SlidePageSpec schema
5. LectureSpec / SlideDeckSpec assemble
6. ElementRequest schema
7. ImageElement schema
8. MindmapElement schema
9. normalize_request
10. retrieve_for_planning
11. plan_outline
12. initialize units
13. unit_loop
14. generate_unit_spec
15. collect_required_elements
16. dispatch_element_generation
17. generate_image_element
18. generate_mindmap_element
19. merge_unit_elements
20. validate_unit
21. assemble_content_spec
22. route_renderer
23. lecture_renderer
24. slide_renderer
```

### P1：稳定性

```text
1. outline repair
2. unit_spec repair
3. failed element retry
4. image placeholder fallback
5. mindmap fallback
6. task progress
7. task logs
8. asset availability check
9. node-level timeout
10. service-level concurrency limit
```

### P2：扩展能力

```text
1. unit 级并行
2. table element
3. quiz element
4. chart element
5. citation element
6. social_post content_type
7. podcast_script content_type
8. PPTX export
9. user edit and partial regeneration
```

---

## 15. 最终实现口径

本 workflow 采用以下最终结构：

```text
1. content_type 使用条件分支。
2. outline.units 使用循环。
3. unit 内 required_elements 使用并行 Fan-out / Fan-in。
4. image 和 mindmap 使用独立 worker 节点。
5. unit 结果统一写入 unit_results。
6. 所有 unit 完成后统一 assemble_content_spec。
7. renderer 根据 content_type 分支执行。
8. export 由前端导出动作触发。
```

当前 MVP 的主链路为：

```text
request
  -> retrieve_for_planning
  -> outline
  -> unit_loop
  -> unit_spec
  -> image / mindmap elements
  -> assemble_content_spec
  -> validate_content
  -> lecture_renderer / slide_renderer
  -> preview
```

当前 MVP 的元素类型为：

```text
image
mindmap
```

当前 MVP 的内容类型为：

```text
lecture
slide_deck
```

Table、Quiz、Chart、Citation 作为扩展能力保留 schema 与路由扩展位置，当前 workflow 不生成这些元素。