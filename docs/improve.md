我建议**不要继续在当前 `content_generation_graph.py` 里硬加更多分支**。当前代码已经具备一个很好的 MVP 骨架：`retrieve → outline → unit loop → element generation → assemble → render`，但它现在被 `lecture / slide_deck` 两种内容类型写死了。接下来应该把它改成**“通用生成内核 + 内容类型 Profile/Strategy 插件”**的结构。

核心目标是：

> 保留当前 LangGraph 的可读性，但把“不同内容类型的差异”从主工作流里移出去，放到各自的 Profile、Generator、Validator、Renderer 中管理。

---

## 1. 当前结构的主要问题

### 问题一：内容类型虽然预留了，但实际被 MVP 类型锁死

`base.py` 里已经有：

```python
ContentType = Literal[
    "lecture",
    "slide_deck",
    "social_post",
    "podcast_script",
    ...
]
```

但 `request.py / state.py / outline.py / specs.py / task.py` 实际使用的是：

```python
MvpContentType = Literal["lecture", "slide_deck"]
```

这会导致推文、播客无法自然接入，只能继续加临时判断。

---

### 问题二：当前工作流默认所有内容都适合“大纲 → 单元循环”

这对教材和 PPT 合理，但对推文不一定合理。

推文可能是：

```text
retrieve → generate social post spec → validate → render
```

不一定需要 outline，也不一定需要 unit loop。

播客则是：

```text
retrieve → outline → segment script → validate script → TTS → audio assemble
```

它和 PPT/教材的渲染逻辑完全不同。

---

### 问题三：当前渲染发生在最后，不支持页级流式输出

现在是：

```text
所有 unit 生成完成
  ↓
assemble_content_spec
  ↓
validate_content
  ↓
lecture_renderer / slide_renderer
  ↓
finalize_task
```

所以前端只能等全部完成后拿到 `render_model`。

但产品要求是：

```text
生成第 1 页 / 第 1 节 → 立即渲染
生成第 2 页 / 第 2 节 → 立即追加渲染
...
最终完成后再做整体校验和导出
```

这意味着 renderer 必须从“最终整包渲染”改成“**unit 级渲染 + 最终 assemble**”。

---

## 2. 推荐的总体架构

建议改成四层：

```text
API 层
  ↓
Task / Streaming 状态层
  ↓
通用 Workflow Kernel
  ↓
Content Type Profiles
      ├─ lecture profile
      ├─ slide_deck profile
      ├─ social_post profile
      └─ podcast profile
```

也就是：

```text
主工作流只管通用流程
具体内容类型自己声明：
- 是否需要 outline
- unit 是什么
- 用哪个 spec schema
- 用哪个 generator
- 用哪个 validator
- 用哪个 renderer
- 是否需要元素生成
- 是否需要 TTS
- 是否支持流式输出
```

---

## 3. 新增 ContentTypeProfile，替代到处 if/else

建议新增：

```text
app/content_types/
├── __init__.py
├── registry.py
├── base.py
├── lecture.py
├── slide_deck.py
├── social_post.py
└── podcast.py
```

核心抽象可以是：

```python
@dataclass(frozen=True)
class ContentTypeProfile:
    content_type: str
    unit_type: str

    requires_outline: bool
    supports_unit_streaming: bool

    outline_prompt_path: str | None
    unit_spec_prompt_path: str | None

    spec_schema: type[SchemaModel]
    unit_spec_schema: type[SchemaModel] | None
    render_model_schema: type[SchemaModel]

    planner: PlannerStrategy
    unit_generator: UnitGeneratorStrategy | None
    direct_generator: DirectGeneratorStrategy | None
    element_policy: ElementPolicy
    validator_suite: ValidatorSuite
    renderer: RendererStrategy
    exporter_types: list[str]
```

注册中心：

```python
CONTENT_TYPE_PROFILES = {
    "lecture": LectureProfile(),
    "slide_deck": SlideDeckProfile(),
    "social_post": SocialPostProfile(),
    "podcast_script": PodcastProfile(),
}
```

主工作流中只拿 profile：

```python
profile = get_content_type_profile(state.content_type)
```

而不是：

```python
if state.content_type == "slide_deck":
    ...
else:
    ...
```

这样后续增加短视频脚本、测验、项目任务，也不会继续污染主图。

---

## 4. 工作流要改成“通用主流程 + 可选节点”

建议把现在的固定流程：

```text
normalize
retrieve_for_planning
plan_outline
validate_outline
route_content_type
initialize_units
unit loop
assemble_content_spec
validate_content
render
finalize
```

改成：

```text
normalize_request
  ↓
retrieve_for_planning
  ↓
route_generation_mode
  ├─ direct_generation_path
  └─ outline_unit_generation_path
```

---

### A. Direct Path：适合推文

```text
normalize_request
  ↓
retrieve_for_planning
  ↓
generate_direct_spec
  ↓
validate_direct_spec
  ↓
collect_required_elements
  ↓
generate_elements
  ↓
render_direct_content
  ↓
publish_render_snapshot
  ↓
finalize_task
```

适用：

```text
social_post
短文案
摘要
单页宣传语
```

推文不需要强行拆成多个 unit，否则会让代码和生成逻辑都变复杂。

---

### B. Unit Path：适合教材、PPT、播客

```text
normalize_request
  ↓
retrieve_for_planning
  ↓
plan_outline
  ↓
validate_outline
  ↓
initialize_units
  ↓
unit loop:
      retrieve_for_unit
      generate_unit_spec
      validate_unit_spec
      collect_required_elements
      generate_elements / generate_audio
      validate_unit
      render_unit
      validate_render_unit
      publish_unit_render
      merge_unit_result
  ↓
assemble_content_spec
  ↓
validate_content
  ↓
final_render_merge
  ↓
finalize_task
```

关键变化是：**`render_unit` 必须前移到 unit loop 内部。**

---

## 5. 为流式输出新增 Unit Render Snapshot

当前 `ContentGenerationState` 里只有：

```python
render_model: RenderModel | None
```

建议新增：

```python
render_units: dict[str, RenderUnitSnapshot]
partial_render_model: RenderModel | None
stream_events: list[TaskStreamEvent]
```

示例 schema：

```python
class RenderUnitSnapshot(SchemaModel):
    unit_id: str
    order: int
    content_type: str
    status: Literal["pending", "rendered", "failed"]
    render_fragment: dict[str, object]
    updated_at: str | None = None
    errors: list[str] = Field(default_factory=list)
```

再新增事件：

```python
class TaskStreamEvent(SchemaModel):
    event_id: str
    task_id: str
    type: Literal[
        "task_started",
        "outline_ready",
        "unit_started",
        "unit_spec_ready",
        "element_ready",
        "unit_render_ready",
        "task_completed",
        "task_failed",
    ]
    unit_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    created_at: str
```

这样前端可以收到：

```json
{
  "type": "unit_render_ready",
  "unit_id": "unit_003",
  "payload": {
    "render_fragment": {
      "page": { "...": "..." }
    }
  }
}
```

---

## 6. Renderer 要拆成 UnitRenderer 和 FinalRenderer

当前 renderer 是：

```python
SlideRenderer.render(deck_spec, elements) -> SlideRenderModel
LectureRenderer.render(lecture_spec, elements) -> LectureRenderModel
```

建议改成：

```python
class UnitRenderer(Protocol):
    def render_unit(self, unit_spec, elements) -> RenderUnitSnapshot:
        ...

class FinalRenderer(Protocol):
    def assemble(self, content_spec, render_units) -> RenderModel:
        ...
```

对 PPT：

```python
SlideRenderer.render_unit(SlideSpecPage, elements) -> SlidePageModel
SlideRenderer.assemble(SlideDeckSpec, render_units) -> SlideRenderModel
```

对教材：

```python
LectureRenderer.render_unit(LectureSection, elements) -> LectureRenderSection
LectureRenderer.assemble(LectureSpec, render_units) -> LectureRenderModel
```

对播客：

```python
PodcastRenderer.render_unit(PodcastSegmentSpec, elements) -> PodcastSegmentRenderModel
PodcastRenderer.assemble(PodcastSpec, render_units) -> PodcastRenderModel
```

对推文：

```python
SocialPostRenderer.render_direct(SocialPostSpec) -> SocialPostRenderModel
```

---

## 7. 数据库存储也要支持部分结果

当前 `ContentGenerationTask` 里有：

```python
render_model: dict | None
content_spec: dict | None
elements: list[dict]
```

建议增加：

```python
outline: dict | None
unit_results: dict
render_units: dict
partial_render_model: dict | None
stream_events: list[dict]
```

更理想的结构：

```python
class ContentGenerationTask(SQLModel, table=True):
    ...
    outline: dict[str, Any] | None
    content_spec: dict[str, Any] | None
    render_model: dict[str, Any] | None
    partial_render_model: dict[str, Any] | None

    unit_results: dict[str, Any]
    render_units: dict[str, Any]
    stream_events: list[dict[str, Any]]
```

这样即使任务没完成，前端也能查询当前已经生成好的页面。

---

## 8. API 层建议增加流式接口

当前只有：

```text
POST /tasks
GET /tasks/{task_id}
GET /tasks/{task_id}/preview
```

建议新增：

```text
GET /tasks/{task_id}/events
GET /tasks/{task_id}/preview/partial
GET /tasks/{task_id}/units
GET /tasks/{task_id}/units/{unit_id}/preview
```

其中：

### `GET /events`

用于 SSE 或轮询式事件流：

```text
GET /api/content-generation/tasks/{task_id}/events
```

返回任务执行事件。

### `GET /preview/partial`

返回当前已完成部分：

```text
GET /api/content-generation/tasks/{task_id}/preview/partial
```

PPT 可以返回：

```json
{
  "content_type": "slide_deck",
  "render_model": {
    "render_type": "slide_deck",
    "title": "...",
    "pages": [
      { "page": "第1页" },
      { "page": "第2页" }
    ]
  }
}
```

教材可以返回：

```json
{
  "content_type": "lecture",
  "render_model": {
    "render_type": "lecture_page",
    "sections": [
      { "id": "lecture_unit_001", "render_blocks": [] }
    ]
  }
}
```

这样可以兼容你们现有前端的 preview 思路。

---

## 9. 不同内容类型的推荐流程

### 9.1 推文生成：Direct Workflow

推文短小精悍，不建议强行走完整 outline/unit 流程。

推荐：

```text
retrieve_for_planning
  ↓
generate_social_post_spec
  ↓
validate_social_post
  ↓
generate_required_elements
  ↓
render_social_post
  ↓
finalize
```

新增 schema：

```python
class SocialPostSpec(SchemaModel):
    id: str
    type: Literal["social_post"] = "social_post"
    title: str
    platform: Literal["wechat", "xiaohongshu", "weibo", "twitter", "generic"] = "generic"
    hook: str
    body: str
    hashtags: list[str] = Field(default_factory=list)
    call_to_action: str | None = None
    citations: list[str] = Field(default_factory=list)
```

Renderer 输出：

```python
class SocialPostRenderModel(SchemaModel):
    render_type: Literal["social_post"] = "social_post"
    platform: str
    title: str
    content: str
    metadata: dict[str, object] = Field(default_factory=dict)
```

---

### 9.2 播客生成：Script + TTS Workflow

播客不应该只是 `podcast_script`，后续一定会涉及音频文件，所以建议内容类型用：

```python
"podcast"
```

而不是只叫：

```python
"podcast_script"
```

推荐流程：

```text
retrieve_for_planning
  ↓
plan_podcast_outline
  ↓
segment loop:
      retrieve_for_segment
      generate_segment_script
      validate_script
      render_script_segment
      publish_script_segment
      tts_segment
      publish_audio_segment
  ↓
assemble_podcast_script
  ↓
merge_audio
  ↓
finalize
```

新增元素：

```python
class AudioScriptElement(BaseElement):
    type: Literal["audio_script"] = "audio_script"
    speaker: str | None = None
    content: str
    estimated_seconds: int | None = None


class AudioFileElement(BaseElement):
    type: Literal["audio_file"] = "audio_file"
    asset_url: str
    duration_seconds: float | None = None
    format: str = "mp3"
```

新增服务：

```text
app/services/tts_service.py
```

新增节点：

```text
app/workflows/nodes/tts_node.py
app/workflows/nodes/audio_assembler_node.py
```

播客可以先流式输出文字脚本，再输出对应音频片段。

---

### 9.3 教材生成：Section Streaming + Interactive Elements

教材未来要增加可交互性，建议把 `LectureSection` 扩展成更通用的 `LearningSectionSpec`，但短期可以先在 `LectureSection.blocks` 中允许更多 block：

```python
LectureBlock = (
    TextBlock
    | ElementReferenceBlock
    | InteractionBlock
)
```

新增元素：

```python
class InteractiveElement(BaseElement):
    type: Literal["interactive_task"] = "interactive_task"
    interaction_type: Literal[
        "quiz",
        "reflection",
        "drag_sort",
        "fill_blank",
        "case_analysis",
        "code_exercise",
    ]
    instruction: str
    payload: dict[str, object] = Field(default_factory=dict)
    answer_key: dict[str, object] | None = None
```

教材 profile 的 element policy 可以是：

```python
ElementPolicy(
    allowed_elements=["image", "mindmap", "quiz", "interactive_task"],
    default_required_elements=["image"],
    optional_elements=["mindmap", "quiz", "interactive_task"],
)
```

教材流式输出应按 section：

```text
生成 section_001 → render section_001 → 前端追加
生成 section_002 → render section_002 → 前端追加
```

---

### 9.4 PPT 生成：Page Streaming + Strict Validator

PPT 的问题不是只需要更多 layout，而是需要更强的页面级质量控制。

建议把 PPT validator 拆成三层：

```text
SlideSpecValidator
  检查 schema、字段、元素引用、layout_hints

SlideLayoutValidator
  检查文字长度、元素数量、版式密度、图片比例、是否超出安全区域

SlideRenderValidator
  检查 render_model 是否可能截断、是否缺主标题、是否视觉区域为空
```

PPT 的 unit loop 应该变成：

```text
generate_slide_spec
  ↓
validate_slide_spec
  ↓
repair_slide_spec if failed
  ↓
generate_elements
  ↓
render_slide_page
  ↓
validate_render_page
  ↓
repair_or_downgrade_layout
  ↓
publish_slide_page
```

也就是说 PPT 的 validator 不应该只在最终整包时做，而应该**每页生成后立刻校验**。

---

## 10. 建议的目录结构调整

可以改成：

```text
app/
├── content_types/
│   ├── base.py
│   ├── registry.py
│   ├── lecture.py
│   ├── slide_deck.py
│   ├── social_post.py
│   └── podcast.py
│
├── schemas/
│   ├── base.py
│   ├── request.py
│   ├── state.py
│   ├── outline.py
│   ├── specs/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── lecture.py
│   │   ├── slide.py
│   │   ├── social_post.py
│   │   └── podcast.py
│   ├── elements/
│   │   ├── __init__.py
│   │   ├── visual.py
│   │   ├── interactive.py
│   │   └── audio.py
│   └── render/
│       ├── __init__.py
│       ├── lecture.py
│       ├── slide.py
│       ├── social_post.py
│       └── podcast.py
│
├── workflows/
│   ├── content_generation_graph.py
│   ├── graph_factory.py
│   ├── nodes/
│   │   ├── normalize_request_node.py
│   │   ├── retrieve_node.py
│   │   ├── planner_node.py
│   │   ├── direct_generator_node.py
│   │   ├── unit_generator_node.py
│   │   ├── element_flow_node.py
│   │   ├── tts_node.py
│   │   ├── unit_renderer_node.py
│   │   ├── publish_event_node.py
│   │   ├── assembler_node.py
│   │   ├── validator_node.py
│   │   └── finalizer_node.py
│
├── generators/
│   ├── base.py
│   ├── lecture_generator.py
│   ├── slide_generator.py
│   ├── social_post_generator.py
│   └── podcast_generator.py
│
├── validators/
│   ├── base.py
│   ├── common_validators.py
│   ├── lecture_validator.py
│   ├── slide_spec_validator.py
│   ├── slide_layout_validator.py
│   ├── slide_render_validator.py
│   ├── social_post_validator.py
│   └── podcast_validator.py
│
├── renderers/
│   ├── base.py
│   ├── lecture_renderer.py
│   ├── slide_renderer.py
│   ├── social_post_renderer.py
│   └── podcast_renderer.py
│
└── services/
    ├── task_service.py
    ├── task_repository.py
    ├── rag_service.py
    ├── llm_service.py
    ├── image_generation_service.py
    ├── tts_service.py
    └── storage_service.py
```

---

## 11. 推荐的迁移顺序

### 第一阶段：先改底座，不急着接新内容类型

优先做：

1. 把 `MvpContentType` 替换为更开放的 `ContentType`。
2. 新增 `ContentTypeProfile` 和 `registry.py`。
3. 把 lecture / slide_deck 的 generator、validator、renderer 注册进 profile。
4. 保持现有流程能跑通。

这一阶段不改变业务能力，只是解耦。

---

### 第二阶段：支持 unit 级 render

改造：

```text
unit_spec → elements → validate_unit → render_unit → publish_unit → merge_unit_result
```

新增节点：

```text
unit_renderer_node.py
publish_event_node.py
```

当前的 `renderer_node.py` 保留为 final assemble renderer。

---

### 第三阶段：改任务持久化和 partial preview

数据库加：

```python
outline
unit_results
render_units
partial_render_model
stream_events
```

API 加：

```text
GET /tasks/{task_id}/preview/partial
GET /tasks/{task_id}/events
GET /tasks/{task_id}/units
```

这一步完成后，教材和 PPT 就能“生成一页/节，前端显示一页/节”。

---

### 第四阶段：接入 social_post

因为推文最简单，适合用来验证 profile 架构。

新增：

```text
SocialPostSpec
SocialPostRenderModel
SocialPostProfile
SocialPostGenerator
SocialPostValidator
SocialPostRenderer
```

走 direct path，不进入 unit loop。

---

### 第五阶段：接入 podcast

新增：

```text
PodcastSpec
PodcastSegmentSpec
PodcastRenderModel
AudioScriptElement
AudioFileElement
TTSService
PodcastProfile
PodcastGenerator
PodcastValidator
PodcastRenderer
```

播客走 unit path，但 unit 是 segment。

---

### 第六阶段：强化教材和 PPT

教材增强：

```text
quiz element
interactive_task element
section-level render streaming
```

PPT 增强：

```text
slide-level render streaming
slide layout validator
slide render validator
repair / downgrade layout
```

---

## 12. 最关键的设计结论

你们接下来不应该把主工作流变成：

```python
if lecture:
    ...
elif slide_deck:
    ...
elif social_post:
    ...
elif podcast:
    ...
```

而应该变成：

```python
profile = get_profile(state.content_type)

if profile.requires_outline:
    run_outline_unit_path(profile)
else:
    run_direct_path(profile)
```

每种内容类型的差异交给 profile 处理：

```text
lecture profile      → section loop + interactive elements
slide_deck profile   → slide loop + strict layout validator
social_post profile  → direct generation
podcast profile      → segment loop + TTS
```

最终结构应该是：

```text
一个稳定的 workflow kernel
多个可插拔的 content type profile
一套 unit-level streaming 状态机制
每种内容类型独立维护自己的 schema / generator / validator / renderer
```

这样既能满足产品要求的流式输出，也能避免后续推文、播客、教材、PPT 继续把主工作流改成难以维护的巨型分支。
