# Interactive HTML 设计实现文档

## 1. 文档定位

本文档记录 `interactive_html` 相关新增 Schema、组件、Workflow、接口、Validator 和实施顺序。实现目标是在现有内容生成框架中新增在线互动 HTML、离线 HTML 讲义和个性化讲义补充能力。

---

## 2. 实施阶段总览

| 阶段 | 目标 | 核心产物 |
|---|---|---|
| P0 | 在线互动 HTML 闭环 | `InteractiveHtmlSpec`、在线渲染、学习 Session、LearningEvent |
| P1 | 离线 HTML 讲义闭环 | `OfflineHandoutSpec`、答题记录摘要、总结知识卡片、离线渲染 |
| P2 | Adaptive Agent 个性化补充 | `LearnerState`、`PersonalizedHandoutPatch`、个性化补充讲义 |
| P3 | 个性化讲义改写与学习指引 | 局部讲解改写、复习建议、拓展学习指引 |

---

## 3. 新增模块

| 模块 | 阶段 | 职责 |
|---|---|---|
| `InteractiveHtmlProfile` | P0 | 注册 `interactive_html` 内容类型 |
| `InteractiveHtmlOutlineGenerator` | P0 | 生成课程级 Outline |
| `InteractiveHtmlUnitSpecGenerator` | P0 | 逐 Section 生成 `InteractiveHtmlSectionSpec` |
| `InteractiveHtmlValidator` | P0 | 校验在线课程内容、Block、互动题和渲染契约 |
| `InteractiveHtmlRenderer` | P0 | 渲染在线互动 HTML |
| `LearningSessionService` | P0 | 创建和维护学习 Session |
| `LearningEventService` | P0 | 记录学生学习事件 |
| `OfflineHandoutAssembler` | P1 | 从在线课程派生离线讲义 |
| `SummaryKnowledgeCardGenerator` | P1 | 为离线讲义生成总结知识卡片 |
| `OfflineHandoutRenderer` | P1 | 渲染离线 HTML 讲义 |
| `LearnerStateService` | P2 | 维护学生学习状态 |
| `AdaptiveLearningGraph` | P2 | 分析学习事件并生成个性化讲义补丁 |
| `PersonalizedHandoutPatchService` | P2 | 保存、校验和应用个性化补丁 |
| `PersonalizedHandoutRewriter` | P3 | 改写个性化讲义局部讲解 |
| `LearningGuidanceGenerator` | P3 | 生成复习点和拓展学习指引 |

---

## 4. ContentTypeProfile

```python
ContentTypeProfile(
    content_type="interactive_html",
    generation_mode="unit_loop",
    unit_type="interactive_section",
    requires_outline=True,
    supports_unit_streaming=True,
    planner_prompt_name="interactive_html_outline.md",
    unit_spec_prompt_name="interactive_html_unit_spec.md",
    spec_schema=InteractiveHtmlSpec,
    unit_spec_schema=InteractiveHtmlSectionSpec,
    render_model_schema=InteractiveHtmlRenderModel,
    renderer_factory=InteractiveHtmlRendererFactory,
    generator_name="interactive_html",
    element_policy=InteractiveHtmlElementPolicy,
    exporter_types=["html", "zip"]
)
```

内容类型关系：

| 内容类型 | generation_mode | unit_type | 输出 |
|---|---|---|---|
| `lecture` | `unit_loop` | `section` | 讲义 |
| `slide_deck` | `unit_loop` | `slide` | Slides |
| `interactive_html` | `unit_loop` | `interactive_section` | 在线互动 HTML |
| `social_post` | `direct` | `article` | 微信文章 |

离线讲义通过独立的 `OfflineHandoutAssembler` 从 `InteractiveHtmlSpec` 派生生成。

---

## 5. 核心 Schema

### 5.1 InteractiveHtmlOutline

```ts
export type InteractiveHtmlOutline = {
  content_type: "interactive_html"
  title: string
  lesson_goal: string
  audience: string
  difficulty: "introductory" | "intermediate" | "advanced"
  estimated_minutes?: number

  sections: {
    section_id: string
    title: string
    learning_goal: string
    target_concepts: string[]
    key_questions?: string[]
    source_refs?: string[]
  }[]
}
```

生成要求：

1. Outline 只定义课程结构。
2. Section 只包含目标、概念和关键问题。
3. Block 编排由 Unit Spec Generator 完成。

### 5.2 InteractiveHtmlSpec

```ts
export type InteractiveHtmlSpec = {
  content_type: "interactive_html"
  lesson_id: string
  title: string
  subtitle?: string

  meta: {
    language: string
    audience: string
    difficulty: "introductory" | "intermediate" | "advanced"
    estimated_minutes?: number
  }

  pedagogy: {
    tutor_tone: "guided" | "encouraging" | "socratic"
    interaction_density: "low" | "medium" | "high"
    terminology_level: "low" | "medium" | "high"
  }

  sections: InteractiveHtmlSectionSpec[]
  citations: Citation[]
  assets: AssetRef[]

  export_options: {
    interactive_html: boolean
    zip?: boolean
  }
}
```

### 5.3 InteractiveHtmlSectionSpec

```ts
export type InteractiveHtmlSectionSpec = {
  section_id: string
  title: string
  learning_goal: string

  concepts: ConceptRef[]
  blocks: LessonBlock[]
  citations: CitationRef[]

  completion_check?: {
    required_interaction_ids: string[]
    min_correct_count?: number
  }
}
```

---

## 6. 在线 LessonBlock Registry

### 6.1 BaseLessonBlock

```ts
export type BaseLessonBlock = {
  block_id: string
  type: string
  title?: string
  visible_by_default?: boolean
  tutor_message?: string
  citations?: CitationRef[]
}
```

### 6.2 LessonBlock

```ts
export type LessonBlock =
  | HeadingBlock
  | ParagraphBlock
  | ConceptCardBlock
  | CalloutBlock
  | ExampleBlock
  | SummaryBlock
  | AnimatedFlowBlock
  | CaseCompareBlock
  | ContextInspectorBlock
  | StepperBlock
  | SingleChoiceBlock
  | MultipleChoiceBlock
  | ShortAnswerBlock
  | DragMatchBlock
  | SequenceBlock
  | FlashcardBlock
  | SocraticChatBlock
  | ScenarioBlock
```

---

## 7. 内容型 Block

```ts
export type HeadingBlock = BaseLessonBlock & {
  type: "heading"
  level: 2 | 3 | 4
  text: string
}

export type ParagraphBlock = BaseLessonBlock & {
  type: "paragraph"
  text: string
}

export type ConceptCardBlock = BaseLessonBlock & {
  type: "concept_card"
  concept_id: string
  explanation: string
  key_terms?: string[]
}

export type CalloutBlock = BaseLessonBlock & {
  type: "callout"
  variant: "tip" | "important" | "warning" | "reflection"
  content: string
}

export type ExampleBlock = BaseLessonBlock & {
  type: "example"
  scenario: string
  explanation: string
  takeaway: string
}

export type SummaryBlock = BaseLessonBlock & {
  type: "summary"
  points: string[]
}
```

---

## 8. 展示增强 Block

### 8.1 AnimatedFlowBlock

```ts
export type AnimatedFlowBlock = BaseLessonBlock & {
  type: "animated_flow"
  steps: {
    step_id: string
    title: string
    description: string
    visual_label?: string
    tutor_message?: string
  }[]
  playback: {
    mode: "manual" | "auto" | "both"
    default_interval_ms?: number
  }
}
```

### 8.2 CaseCompareBlock

```ts
export type CaseCompareBlock = BaseLessonBlock & {
  type: "case_compare"
  cases: {
    case_id: string
    title: string
    content: string
    tags?: string[]
    variant?: "default" | "good" | "weak" | "warning"
  }[]
  takeaway?: string
}
```

### 8.3 ContextInspectorBlock

```ts
export type ContextInspectorBlock = BaseLessonBlock & {
  type: "context_inspector"
  items: {
    item_id: string
    label: string
    description: string
    selected_by_default?: boolean
    effect_explanation?: string
  }[]
  result_description?: string
}
```

### 8.4 StepperBlock

```ts
export type StepperBlock = BaseLessonBlock & {
  type: "stepper"
  steps: {
    title: string
    description: string
  }[]
}
```

---

## 9. 互动型 Block

### 9.1 BaseInteractionBlock

```ts
export type BaseInteractionBlock = BaseLessonBlock & {
  interaction_id: string
  target_concepts: string[]

  purpose:
    | "check_understanding"
    | "detect_misconception"
    | "guide_reflection"
    | "collect_opinion"
    | "choose_learning_path"

  feedback_policy: FeedbackPolicy
  adaptation_policy?: AdaptationPolicy
}
```

### 9.2 FeedbackPolicy

```ts
export type FeedbackPolicy = {
  immediate_feedback: boolean
  show_explanation_after_answer: boolean
  feedback_tone: "encouraging" | "corrective" | "socratic"
}
```

### 9.3 AdaptationPolicy

```ts
export type AdaptationPolicy = {
  enabled: boolean
  allowed_actions?: AdaptationAction[]

  decision_guidance?: {
    when_to_intervene: string[]
    when_to_feedback_only: string[]
    preferred_support?: Array<
      | "hint"
      | "simplified_explanation"
      | "concrete_example"
      | "followup_question"
      | "misconception_note"
      | "review_suggestion"
    >
  }

  max_patch_blocks?: number
}
```

### 9.4 AdaptationAction

```ts
export type AdaptationAction =
  | "feedback_only"
  | "show_hint"
  | "insert_simplified_explanation"
  | "insert_concrete_example"
  | "insert_followup_question"
  | "insert_misconception_note"
  | "rewrite_explanation_for_student"
  | "add_review_suggestion"
  | "add_extension_guide"
```

### 9.5 SingleChoiceBlock

```ts
export type SingleChoiceBlock = BaseInteractionBlock & {
  type: "single_choice"
  question: string
  options: {
    option_id: string
    text: string
    is_correct: boolean
    feedback?: string
  }[]
  explanation: string
}
```

### 9.6 MultipleChoiceBlock

```ts
export type MultipleChoiceBlock = BaseInteractionBlock & {
  type: "multiple_choice"
  question: string
  options: {
    option_id: string
    text: string
    is_correct: boolean
    feedback?: string
  }[]
  explanation: string
  min_correct_required?: number
}
```

### 9.7 ShortAnswerBlock

```ts
export type ShortAnswerBlock = BaseInteractionBlock & {
  type: "short_answer"
  question: string
  placeholder?: string
  reference_points: string[]
  min_length?: number
  discussion_mode?: boolean
}
```

### 9.8 DragMatchBlock

```ts
export type DragMatchBlock = BaseInteractionBlock & {
  type: "drag_match"
  instruction: string
  items: {
    item_id: string
    text: string
    correct_target_id: string
  }[]
  targets: {
    target_id: string
    label: string
    description?: string
  }[]
  explanation: string
}
```

### 9.9 SequenceBlock

```ts
export type SequenceBlock = BaseInteractionBlock & {
  type: "sequence"
  instruction: string
  items: {
    item_id: string
    text: string
    correct_order: number
  }[]
  explanation: string
}
```

### 9.10 FlashcardBlock

```ts
export type FlashcardBlock = BaseLessonBlock & {
  type: "flashcard"
  cards: {
    card_id: string
    front: string
    back: string
  }[]
}
```

---

## 10. 对话教学 Block

### 10.1 SocraticChatBlock

```ts
export type SocraticChatBlock = BaseInteractionBlock & {
  type: "socratic_chat"
  goal: string
  rounds: {
    round_id: string
    question: string
    options?: {
      option_id: string
      text: string
      feedback: string
      is_preferred?: boolean
    }[]
    expected_points?: string[]
    tutor_followup?: string
  }[]
}
```

### 10.2 ScenarioBlock

```ts
export type ScenarioBlock = BaseInteractionBlock & {
  type: "scenario"
  scenario_title: string
  background: string
  role?: string
  scenes: {
    scene_id: string
    task: string
    context: string
    choices: {
      choice_id: string
      text: string
      feedback: string
      is_preferred?: boolean
    }[]
  }[]
}
```

---

## 11. 在线元素策略

```ts
export type InteractiveHtmlElementPolicy = {
  generate_process_images: false
  generate_mindmaps: false
  generated_assets: []
}
```

在线课程元素处理规则：

| 元素 | 处理方式 |
|---|---|
| 过程图片 | 默认关闭 |
| 思维导图 | 默认关闭 |
| 总结知识卡片 | 归入离线讲义生成流程 |
| 互动视觉效果 | 由前端组件和 CSS 实现 |

---

## 12. P0 在线互动 HTML 生成 Workflow

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
initialize_interactive_html_units
  ↓
retrieve_for_unit
  ↓
generate_unit_spec
  ↓
validate_unit_spec
  ↓
render_unit_preview
  ↓
merge_unit_result
  ↓
should_continue_units
  ↓
assemble_interactive_html_spec
  ↓
validate_content
  ↓
interactive_html_renderer
  ↓
finalize_task
```

最小新增节点：

| 节点 | 职责 |
|---|---|
| `initialize_interactive_html_units` | 根据 Outline 初始化 Section 生成队列 |
| `assemble_interactive_html_spec` | 组装完整在线互动课程 Spec |
| `interactive_html_renderer` | 渲染在线互动 HTML |

P0 在线生成流程不调用图片生成、思维导图生成和总结知识卡片生成节点。

---

## 13. P0 学习事件闭环

### 13.1 LearningEvent

```ts
export type LearningEvent = {
  event_id: string
  lesson_id: string
  session_id: string
  section_id: string
  block_id: string
  interaction_id?: string

  event_type:
    | "single_choice_answered"
    | "multiple_choice_answered"
    | "short_answer_submitted"
    | "drag_match_submitted"
    | "sequence_submitted"
    | "socratic_round_answered"
    | "scenario_choice_selected"
    | "hint_requested"
    | "confused_clicked"

  payload: {
    selected_option_ids?: string[]
    ordered_item_ids?: string[]
    match_pairs?: Record<string, string>
    answer_text?: string
    confidence?: "low" | "medium" | "high"
    time_spent_seconds?: number
  }

  created_at: string
}
```

### 13.2 事件提交流程

```text
create_learning_session
  ↓
student_interacts_with_block
  ↓
submit_learning_event
  ↓
evaluate_with_block_feedback_policy
  ↓
save_learning_event
  ↓
return_immediate_feedback
```

P0 阶段的即时反馈优先使用题目自带 `feedback_policy`、选项反馈和参考解释。

---

## 14. P1 离线 HTML 讲义 Schema

### 14.1 OfflineHandoutSpec

```ts
export type OfflineHandoutSpec = {
  content_type: "offline_html_handout"
  handout_id: string
  lesson_id: string
  session_id?: string

  title: string
  subtitle?: string

  meta: {
    language: string
    audience: string
    generated_at: string
  }

  sections: {
    section_id: string
    title: string
    learning_goal: string
    blocks: HandoutBlock[]
  }[]

  learning_summary?: AnswerRecordSummaryBlock
  assets: AssetRef[]
  citations: CitationRef[]
}
```

### 14.2 HandoutBlock

```ts
export type HandoutBlock =
  | HeadingBlock
  | ParagraphBlock
  | ConceptCardBlock
  | CalloutBlock
  | ExampleBlock
  | SummaryBlock
  | StaticStepperBlock
  | StaticCaseCompareBlock
  | ContextTableBlock
  | SummaryKnowledgeCardBlock
  | AnswerRecordSummaryBlock
  | PersonalizedNoteBlock
  | ReviewSuggestionBlock
  | ExtensionGuideBlock
```

### 14.3 SummaryKnowledgeCardBlock

```ts
export type SummaryKnowledgeCardBlock = BaseLessonBlock & {
  type: "summary_knowledge_card"
  asset_id?: string
  image_prompt?: string
  alt: string
  caption?: string
}
```

### 14.4 AnswerRecordSummaryBlock

```ts
export type AnswerRecordSummaryBlock = BaseLessonBlock & {
  type: "answer_record_summary"
  records: {
    interaction_id: string
    question: string
    student_answer: string
    result?: "correct" | "wrong" | "partial" | "open"
    summary: string
  }[]
}
```

---

## 15. P1 离线 HTML 讲义生成 Workflow

```text
load_interactive_html_spec
  ↓
load_learning_events
  ↓
strip_interaction_blocks
  ↓
convert_display_blocks_for_handout
  ↓
generate_answer_record_summary
  ↓
generate_summary_knowledge_card
  ↓
assemble_offline_handout_spec
  ↓
validate_offline_handout
  ↓
offline_handout_renderer
  ↓
export_offline_html
```

转换规则：

| 原 Block | 离线讲义处理 |
|---|---|
| heading / paragraph / concept_card / callout / example / summary | 保留 |
| animated_flow / stepper | 转为静态步骤说明 |
| case_compare | 保留为案例对比 |
| context_inspector | 转为上下文说明表 |
| single_choice / multiple_choice / short_answer | 移入答题记录摘要 |
| drag_match / sequence | 移入答题记录摘要 |
| flashcard | 转为静态问答卡片 |
| socratic_chat / scenario | 提炼为情景任务记录与学习提示 |
| summary_knowledge_card | 在离线讲义总结部分生成并展示 |

### 15.1 离线知识卡片生成策略

```ts
export type OfflineHandoutElementPolicy = {
  generate_summary_knowledge_card: true
  summary_card: {
    position: "lesson_summary"
    style: "hand_drawn_note_card"
    count: 1
    purpose: "summarize_lesson_core_concepts"
  }
}
```

---

## 16. P2 AdaptiveLearningGraph

### 16.1 LearnerState

```ts
export type LearnerState = {
  session_id: string
  lesson_id: string

  mastery: Record<string, number>

  misconceptions: {
    concept_id: string
    description: string
    evidence_event_ids: string[]
    confidence: number
  }[]

  preferred_support:
    | "example"
    | "analogy"
    | "step_by_step"
    | "visual"
    | "practice"

  interaction_summary: {
    total_answered: number
    correct_count: number
    wrong_count: number
    partial_count: number
    short_answer_count: number
    help_requested_count: number
  }

  updated_at: string
}
```

### 16.2 AdaptiveLearningGraph 流程

```text
load_learning_events
  ↓
load_interactive_html_spec
  ↓
load_or_initialize_learner_state
  ↓
evaluate_learning_events
  ↓
update_learner_state
  ↓
adaptive_agent_observe_decide
  ↓
generate_personalized_handout_patch
  ↓
validate_personalized_handout_patch
  ↓
save_learner_state
  ↓
save_patch
  ↓
return_adaptive_result
```

### 16.3 ReAct 决策结构

```text
Observe:
  读取 LearningEvent、source block、section goal、LearnerState。

Reason:
  判断理解状态、误区、回答质量和干预必要性。

Act:
  选择 feedback_only、show_hint、insert_concrete_example、insert_misconception_note 等动作。

Check:
  校验补丁 target、operation、block 类型、长度和安全性。

Return:
  返回即时反馈与个性化讲义补丁。
```

---

## 17. P2 PersonalizedHandoutPatch

```ts
export type PersonalizedHandoutPatch = {
  patch_id: string
  lesson_id: string
  session_id: string

  target: {
    section_id: string
    source_block_id?: string
    position:
      | "after_source_block"
      | "before_section_summary"
      | "end_of_section"
      | "handout_review_section"
  }

  operation:
    | "insert_explanation"
    | "insert_concrete_example"
    | "insert_misconception_note"
    | "insert_followup_question"

  blocks: PersonalizedNoteBlock[]

  source_event_ids: string[]
  reason: string
  priority: "low" | "medium" | "high"
  created_at: string
}
```

### 17.1 PersonalizedNoteBlock

```ts
export type PersonalizedNoteBlock = BaseLessonBlock & {
  type: "personalized_note"
  source_event_ids: string[]
  target_concepts: string[]
  note_type:
    | "simplified_explanation"
    | "concrete_example"
    | "misconception_note"
    | "followup_question"
  content: string
}
```

### 17.2 个性化补丁应用流程

```text
load_offline_handout_spec
  ↓
load_personalized_handout_patches
  ↓
apply_personalized_patches
  ↓
validate_personalized_offline_handout
  ↓
render_personalized_offline_html
```

---

## 18. P3 个性化讲义改写与学习指引

### 18.1 扩展 Patch Operation

```ts
export type AdvancedPersonalizedPatchOperation =
  | "rewrite_explanation_for_student"
  | "add_review_suggestion"
  | "add_extension_guide"
  | "add_followup_practice"
```

### 18.2 ReviewSuggestionBlock

```ts
export type ReviewSuggestionBlock = BaseLessonBlock & {
  type: "review_suggestion"
  target_concepts: string[]
  suggestions: string[]
  reason: string
}
```

### 18.3 ExtensionGuideBlock

```ts
export type ExtensionGuideBlock = BaseLessonBlock & {
  type: "extension_guide"
  target_concepts: string[]
  directions: {
    title: string
    description: string
    difficulty: "introductory" | "intermediate" | "advanced"
  }[]
}
```

---

## 19. API 设计

### 19.1 创建在线互动课程任务

```http
POST /api/content-generation/tasks
```

请求核心字段：

```json
{
  "content_type": "interactive_html",
  "topic": "生成式 AI 如何理解你的问题？",
  "user_prompt": "生成一份面向初学者的互动式 HTML 课程",
  "knowledge_base_ids": ["default"],
  "generation_options": {
    "language": "zh-CN",
    "difficulty": "introductory",
    "style": "educational",
    "interaction_density": "medium"
  }
}
```

响应：

```json
{
  "task_id": "task_xxx",
  "status": "pending"
}
```

### 19.2 查询任务与在线预览

```http
GET /api/content-generation/tasks/{task_id}
```

响应增加：

```json
{
  "task_id": "task_xxx",
  "status": "completed",
  "content_type": "interactive_html",
  "preview": {
    "interactive_html_url": "/preview/lesson_xxx/index.html",
    "render_model": {}
  }
}
```

### 19.3 创建学习 Session

```http
POST /api/interactive-lessons/{lesson_id}/sessions
```

响应：

```json
{
  "session_id": "session_xxx",
  "lesson_id": "lesson_xxx",
  "state": {}
}
```

### 19.4 提交学习事件

```http
POST /api/interactive-lessons/{lesson_id}/sessions/{session_id}/events
```

请求：

```json
{
  "section_id": "sec_001",
  "block_id": "quiz_001",
  "interaction_id": "interaction_001",
  "event_type": "single_choice_answered",
  "payload": {
    "selected_option_ids": ["A"],
    "confidence": "medium",
    "time_spent_seconds": 12
  }
}
```

P0 响应：

```json
{
  "feedback": {
    "message": "你的选择已记录，请继续学习下一部分。",
    "tone": "encouraging"
  },
  "event_saved": true
}
```

P2 响应增加：

```json
{
  "feedback": {
    "message": "你的选择说明你已经理解检索增强的基本作用。",
    "tone": "encouraging"
  },
  "learner_state_delta": {},
  "patch_created": true
}
```

### 19.5 查询学习状态

```http
GET /api/interactive-lessons/{lesson_id}/sessions/{session_id}/state
```

### 19.6 生成离线 HTML 讲义

```http
POST /api/interactive-lessons/{lesson_id}/sessions/{session_id}/offline-handout
```

请求：

```json
{
  "format": "html",
  "include_answer_summary": true,
  "include_summary_knowledge_card": true,
  "include_personalized_notes": false,
  "include_review_suggestions": false
}
```

响应：

```json
{
  "handout_id": "handout_xxx",
  "status": "completed",
  "offline_html_url": "/preview/handouts/handout_xxx/index.html"
}
```

### 19.7 生成个性化补充

```http
POST /api/interactive-lessons/{lesson_id}/sessions/{session_id}/adaptive-patches
```

响应：

```json
{
  "status": "completed",
  "patch_count": 3,
  "patch_ids": ["patch_001", "patch_002", "patch_003"]
}
```

### 19.8 查询离线讲义

```http
GET /api/interactive-lessons/{lesson_id}/sessions/{session_id}/offline-handout/{handout_id}
```

---

## 20. Validator 设计

### 20.1 Outline Validator

| 检查项 | 要求 |
|---|---|
| Section 数量 | 符合课程长度 |
| 学习目标 | 每个 Section 有明确 learning_goal |
| 概念覆盖 | target_concepts 非空 |
| 引用关联 | source_refs 可追溯 |

### 20.2 Unit Spec Validator

| 检查项 | 要求 |
|---|---|
| Block 合法性 | type 属于在线 Block Registry |
| 内容完整性 | Section 包含讲解、示例或互动检查 |
| 互动题合法性 | 单选唯一正确答案，多选至少一个正确答案 |
| 简答题合法性 | reference_points 非空 |
| 对话一致性 | socratic_chat / scenario 的任务与反馈一致 |
| AdaptationPolicy | action 属于允许枚举 |
| 引用覆盖 | 关键讲解 Block 有 citations |
| 渲染契约 | Block 能映射到前端组件 |

### 20.3 Offline Handout Validator

| 检查项 | 要求 |
|---|---|
| 交互控件移除 | 离线讲义不包含可操作互动控件 |
| 核心讲解保留 | 保留课程核心说明、案例、总结 |
| 展示静态化 | 动画、流程和对话模块能转为静态内容 |
| 答题摘要完整 | 关键学习事件被摘要 |
| 总结卡片 | 存在合法的 `summary_knowledge_card` |
| 导出稳定 | HTML 渲染成功 |

### 20.4 Patch Validator

| 检查项 | 要求 |
|---|---|
| target 存在 | section_id 与 source_block_id 可定位 |
| operation 合法 | operation 属于阶段允许的补丁白名单 |
| block 合法 | blocks 只包含 handout 可渲染 Block |
| source_event_ids | 能追溯到学习事件 |
| 长度控制 | 个性化补充内容长度受控 |
| 安全性 | 不包含未授权 HTML / JS |
| 相关性 | 补丁内容与 target_concepts 和 source events 相关 |

---

## 21. Prompt 文件

### 21.1 `interactive_html_outline.md`

输出：

1. 课程标题。
2. 课程目标。
3. 面向对象。
4. 难度。
5. Section 列表。
6. Section 的学习目标、核心概念、关键问题。

规则：

1. 不输出具体 Block 类型。
2. 不规划互动题位置。
3. 不规划图片和思维导图。
4. 不规划 Adaptive Agent 的具体动作。

### 21.2 `interactive_html_unit_spec.md`

输出：

1. 一个完整 `InteractiveHtmlSectionSpec`。
2. 有序 `blocks`。
3. 讲解、案例、展示增强和互动内容的顺序。
4. 互动题的 `feedback_policy` 和 `adaptation_policy`。
5. citations。

规则：

1. 不生成 HTML 字符串。
2. 不生成 CSS 或 JS。
3. 不要求每种 Block 都出现。
4. 互动题服务于目标概念。
5. 内容适合纵向教材式阅读。

### 21.3 `offline_handout_assembler.md`

输出：

1. `OfflineHandoutSpec`。
2. 静态化后的讲义 blocks。
3. 答题记录摘要。
4. 总结知识卡片需求。

规则：

1. 移除在线互动控件。
2. 保留核心讲解和案例。
3. 将动画、对话、情景任务转换为静态复习内容。
4. 生成适合离线阅读的结构。

### 21.4 `summary_knowledge_card.md`

输出：

1. 一张手绘风知识卡片的 image prompt。
2. alt 文本。
3. caption。

规则：

1. 概括整节课核心内容。
2. 使用笔记式、手绘风、知识卡片视觉风格。
3. 内容聚焦复习，不承载新的复杂知识点。

### 21.5 `adaptive_learning_decision.md`

输出：

1. 即时反馈。
2. LearnerState 更新建议。
3. 是否生成个性化讲义补丁。
4. 补丁动作类型。
5. 补丁目标位置。
6. 生成原因。

规则：

1. 根据 LearningEvent、source block 和 LearnerState 做决策。
2. 使用允许的 AdaptationAction。
3. 补丁内容服务当前学生的个性化讲义。
4. 每个补丁可追溯到 source_event_ids。

### 21.6 `personalized_handout_patch.md`

输出：

1. `PersonalizedHandoutPatch`。
2. `PersonalizedNoteBlock[]`。
3. target 与 operation。
4. reason 与 source_event_ids。

规则：

1. 内容清晰、短小、适合复习。
2. 与学生互动反馈直接相关。
3. 不输出 HTML / CSS / JS。
4. 不改变原始在线互动课程 Spec。

---

## 22. 前端组件映射

| block type | 前端组件 | 在线版 | 离线版 |
|---|---|---|---|
| `heading` | `HeadingBlock` | 支持 | 支持 |
| `paragraph` | `ParagraphBlock` | 支持 | 支持 |
| `concept_card` | `ConceptCardBlock` | 支持 | 支持 |
| `callout` | `CalloutBlock` | 支持 | 支持 |
| `example` | `ExampleBlock` | 支持 | 支持 |
| `summary` | `SummaryBlock` | 支持 | 支持 |
| `animated_flow` | `AnimatedFlowBlock` | 动画播放 | 静态步骤 |
| `case_compare` | `CaseCompareBlock` | Tabs / Cards | 静态对比 |
| `context_inspector` | `ContextInspectorBlock` | 可勾选 | 静态说明 |
| `stepper` | `StepperBlock` | 可切换 | 静态步骤 |
| `single_choice` | `SingleChoiceBlock` | 可作答 | 答题摘要 |
| `multiple_choice` | `MultipleChoiceBlock` | 可作答 | 答题摘要 |
| `short_answer` | `ShortAnswerBlock` | 可输入 | 答题摘要 |
| `drag_match` | `DragMatchBlock` | 可拖拽 | 答题摘要 |
| `sequence` | `SequenceBlock` | 可排序 | 答题摘要 |
| `flashcard` | `FlashcardBlock` | 可翻卡 | 静态卡片 |
| `socratic_chat` | `SocraticChatBlock` | 多轮对话 | 学习记录摘要 |
| `scenario` | `ScenarioBlock` | 情景选择 | 情景任务摘要 |
| `summary_knowledge_card` | `SummaryKnowledgeCardBlock` | 无 | 支持 |
| `answer_record_summary` | `AnswerRecordSummaryBlock` | 无 | 支持 |
| `personalized_note` | `PersonalizedNoteBlock` | 可选 | 支持 |
| `review_suggestion` | `ReviewSuggestionBlock` | 无 | 支持 |
| `extension_guide` | `ExtensionGuideBlock` | 无 | 支持 |

---

## 23. 数据存储建议

### 23.1 lesson 表

| 字段 | 说明 |
|---|---|
| `lesson_id` | 课程 ID |
| `task_id` | 生成任务 ID |
| `content_type` | interactive_html |
| `interactive_html_spec` | 在线互动课程 Spec |
| `render_model` | 在线版渲染模型 |
| `assets` | 资源引用 |
| `created_at` | 创建时间 |

### 23.2 learning_session 表

| 字段 | 说明 |
|---|---|
| `session_id` | 学习 Session ID |
| `lesson_id` | 课程 ID |
| `learner_state` | 当前学习状态 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### 23.3 learning_event 表

| 字段 | 说明 |
|---|---|
| `event_id` | 学习事件 ID |
| `session_id` | Session ID |
| `lesson_id` | 课程 ID |
| `section_id` | Section ID |
| `block_id` | Block ID |
| `interaction_id` | Interaction ID |
| `event_type` | 事件类型 |
| `payload` | 事件数据 |
| `created_at` | 创建时间 |

### 23.4 offline_handout 表

| 字段 | 说明 |
|---|---|
| `handout_id` | 讲义 ID |
| `session_id` | Session ID |
| `lesson_id` | 课程 ID |
| `offline_handout_spec` | 离线讲义 Spec |
| `html_url` | HTML 预览地址 |
| `pdf_url` | PDF 地址 |
| `created_at` | 创建时间 |

### 23.5 personalized_handout_patch 表

| 字段 | 说明 |
|---|---|
| `patch_id` | 补丁 ID |
| `session_id` | Session ID |
| `lesson_id` | 课程 ID |
| `target` | 补丁目标 |
| `operation` | 补丁动作 |
| `blocks` | 补丁内容 |
| `source_event_ids` | 来源事件 |
| `created_at` | 创建时间 |

---

## 24. 实施顺序

### P0：在线互动 HTML 闭环

1. 新增 `InteractiveHtmlSpec`。
2. 新增 `InteractiveHtmlSectionSpec`。
3. 新增在线 `LessonBlock` Registry。
4. 新增 `InteractiveHtmlProfile`。
5. 新增 outline prompt。
6. 新增 unit spec prompt。
7. 接入 `unit_loop`。
8. 渲染在线互动 HTML。
9. 新增学习 Session。
10. 新增 LearningEvent 接口。
11. 前端组件提交互动事件。

### P1：离线 HTML 讲义闭环

1. 新增 `OfflineHandoutSpec`。
2. 新增 `OfflineHandoutAssembler`。
3. 新增 `answer_record_summary.md` 或对应生成逻辑。
4. 新增 `summary_knowledge_card.md`。
5. 新增 `SummaryKnowledgeCardGenerator`。
6. 新增 `OfflineHandoutRenderer`。
7. 支持离线 HTML 预览与导出。

### P2：Adaptive Agent 个性化补充

1. 新增 LearnerState 更新逻辑。
2. 新增 `AdaptiveLearningGraph`。
3. 新增 `PersonalizedHandoutPatch`。
4. 新增 `personalized_handout_patch.md`。
5. 新增 Patch Validator。
6. 将个性化补丁应用到离线讲义。

### P3：个性化讲义改写与学习指引

1. 支持个性化局部讲解改写。
2. 支持推荐复习点。
3. 支持拓展学习指引。
4. 支持后续练习建议。
5. 支持增强版个性化讲义导出。
