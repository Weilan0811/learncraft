"""
P0 Interactive HTML schemas: LessonBlock registry, Outline, Spec, SectionSpec.

All 17 online block types are defined:
  - 基础阅读类: heading, paragraph, concept_card, callout, example, summary
  - 展示增强类: animated_flow, case_compare, context_inspector, stepper
  - 互动练习类: single_choice, multiple_choice, short_answer, drag_match, sequence, flashcard
  - 对话教学类: socratic_chat, scenario
"""

from typing import Literal, Annotated
from pydantic import Field, model_validator
from app.schemas.base import SchemaModel


# ---------------------------------------------------------------------------
# Shared reference types
# ---------------------------------------------------------------------------

class CitationRef(SchemaModel):
    source_id: str
    chunk_id: str | None = None
    excerpt: str | None = None


class AssetRef(SchemaModel):
    asset_id: str
    asset_type: Literal["image", "css", "js"] = "image"
    url: str | None = None


class ConceptRef(SchemaModel):
    concept_id: str
    name: str
    description: str | None = None


# ---------------------------------------------------------------------------
# Feedback & adaptation policies
# ---------------------------------------------------------------------------

class FeedbackPolicy(SchemaModel):
    immediate_feedback: bool = True
    show_explanation_after_answer: bool = True
    feedback_tone: Literal["encouraging", "corrective", "socratic"] = "encouraging"


AdaptationAction = Literal[
    "feedback_only",
    "show_hint",
    "insert_simplified_explanation",
    "insert_concrete_example",
    "insert_followup_question",
    "insert_misconception_note",
    "rewrite_explanation_for_student",
    "add_review_suggestion",
    "add_extension_guide",
]


class AdaptationDecisionGuidance(SchemaModel):
    when_to_intervene: list[str] = Field(default_factory=list)
    when_to_feedback_only: list[str] = Field(default_factory=list)
    preferred_support: list[
        Literal[
            "hint",
            "simplified_explanation",
            "concrete_example",
            "followup_question",
            "misconception_note",
            "review_suggestion",
        ]
    ] = Field(default_factory=list)


class AdaptationPolicy(SchemaModel):
    enabled: bool = False
    allowed_actions: list[AdaptationAction] = Field(default_factory=list)
    decision_guidance: AdaptationDecisionGuidance | None = None
    max_patch_blocks: int | None = None


# ---------------------------------------------------------------------------
# Base blocks
# ---------------------------------------------------------------------------

class BaseLessonBlock(SchemaModel):
    block_id: str
    type: str
    title: str | None = None
    visible_by_default: bool = True
    tutor_message: str | None = None
    citations: list[CitationRef] = Field(default_factory=list)


class BaseInteractionBlock(BaseLessonBlock):
    interaction_id: str
    target_concepts: list[str] = Field(default_factory=list)
    purpose: Literal[
        "check_understanding",
        "detect_misconception",
        "guide_reflection",
        "collect_opinion",
        "choose_learning_path",
    ] = "check_understanding"
    feedback_policy: FeedbackPolicy = Field(default_factory=FeedbackPolicy)
    adaptation_policy: AdaptationPolicy | None = None


# ---------------------------------------------------------------------------
# 基础阅读类 blocks
# ---------------------------------------------------------------------------

class HeadingBlock(BaseLessonBlock):
    type: Literal["heading"] = "heading"
    level: Literal[2, 3, 4] = 2
    text: str


class ParagraphBlock(BaseLessonBlock):
    type: Literal["paragraph"] = "paragraph"
    text: str


class ConceptCardBlock(BaseLessonBlock):
    type: Literal["concept_card"] = "concept_card"
    concept_id: str
    explanation: str
    key_terms: list[str] = Field(default_factory=list)


class CalloutBlock(BaseLessonBlock):
    type: Literal["callout"] = "callout"
    variant: Literal["tip", "important", "warning", "reflection"] = "tip"
    content: str


class ExampleBlock(BaseLessonBlock):
    type: Literal["example"] = "example"
    scenario: str
    explanation: str
    takeaway: str


class SummaryBlock(BaseLessonBlock):
    type: Literal["summary"] = "summary"
    points: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 展示增强类 blocks
# ---------------------------------------------------------------------------

class AnimatedFlowStep(SchemaModel):
    step_id: str
    title: str
    description: str
    visual_label: str | None = None
    tutor_message: str | None = None


class AnimatedFlowPlayback(SchemaModel):
    mode: Literal["manual", "auto", "both"] = "manual"
    default_interval_ms: int | None = None


class AnimatedFlowBlock(BaseLessonBlock):
    type: Literal["animated_flow"] = "animated_flow"
    steps: list[AnimatedFlowStep] = Field(default_factory=list)
    playback: AnimatedFlowPlayback = Field(default_factory=AnimatedFlowPlayback)


class CaseCompareCase(SchemaModel):
    case_id: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    variant: Literal["default", "good", "weak", "warning"] = "default"


class CaseCompareBlock(BaseLessonBlock):
    type: Literal["case_compare"] = "case_compare"
    cases: list[CaseCompareCase] = Field(default_factory=list)
    takeaway: str | None = None


class ContextInspectorItem(SchemaModel):
    item_id: str
    label: str
    description: str
    selected_by_default: bool = False
    effect_explanation: str | None = None


class ContextInspectorBlock(BaseLessonBlock):
    type: Literal["context_inspector"] = "context_inspector"
    items: list[ContextInspectorItem] = Field(default_factory=list)
    result_description: str | None = None


class StepperStep(SchemaModel):
    title: str
    description: str


class StepperBlock(BaseLessonBlock):
    type: Literal["stepper"] = "stepper"
    steps: list[StepperStep] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 互动练习类 blocks (with BaseInteractionBlock)
# ---------------------------------------------------------------------------

class SingleChoiceOption(SchemaModel):
    option_id: str
    text: str
    is_correct: bool
    feedback: str | None = None


class SingleChoiceBlock(BaseInteractionBlock):
    type: Literal["single_choice"] = "single_choice"
    question: str
    options: list[SingleChoiceOption] = Field(default_factory=list)
    explanation: str

    @model_validator(mode="after")
    def _exactly_one_correct(self) -> "SingleChoiceBlock":
        correct = [o for o in self.options if o.is_correct]
        if len(self.options) > 0 and len(correct) != 1:
            raise ValueError("single_choice must have exactly one correct option")
        return self


class MultipleChoiceOption(SchemaModel):
    option_id: str
    text: str
    is_correct: bool
    feedback: str | None = None


class MultipleChoiceBlock(BaseInteractionBlock):
    type: Literal["multiple_choice"] = "multiple_choice"
    question: str
    options: list[MultipleChoiceOption] = Field(default_factory=list)
    explanation: str
    min_correct_required: int | None = None


class ShortAnswerBlock(BaseInteractionBlock):
    type: Literal["short_answer"] = "short_answer"
    question: str
    placeholder: str | None = None
    reference_points: list[str] = Field(default_factory=list)
    min_length: int | None = None
    discussion_mode: bool = False


class DragMatchItem(SchemaModel):
    item_id: str
    text: str
    correct_target_id: str


class DragMatchTarget(SchemaModel):
    target_id: str
    label: str
    description: str | None = None


class DragMatchBlock(BaseInteractionBlock):
    type: Literal["drag_match"] = "drag_match"
    instruction: str
    items: list[DragMatchItem] = Field(default_factory=list)
    targets: list[DragMatchTarget] = Field(default_factory=list)
    explanation: str


class SequenceItem(SchemaModel):
    item_id: str
    text: str
    correct_order: int


class SequenceBlock(BaseInteractionBlock):
    type: Literal["sequence"] = "sequence"
    instruction: str
    items: list[SequenceItem] = Field(default_factory=list)
    explanation: str


class Flashcard(SchemaModel):
    card_id: str
    front: str
    back: str


class FlashcardBlock(BaseLessonBlock):
    type: Literal["flashcard"] = "flashcard"
    cards: list[Flashcard] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 对话教学类 blocks
# ---------------------------------------------------------------------------

class SocraticRoundOption(SchemaModel):
    option_id: str
    text: str
    feedback: str
    is_preferred: bool = False


class SocraticRound(SchemaModel):
    round_id: str
    question: str
    options: list[SocraticRoundOption] = Field(default_factory=list)
    expected_points: list[str] = Field(default_factory=list)
    tutor_followup: str | None = None


class SocraticChatBlock(BaseInteractionBlock):
    type: Literal["socratic_chat"] = "socratic_chat"
    goal: str
    rounds: list[SocraticRound] = Field(default_factory=list)


class SceneChoice(SchemaModel):
    choice_id: str
    text: str
    feedback: str
    is_preferred: bool = False


class Scene(SchemaModel):
    scene_id: str
    task: str
    context: str
    choices: list[SceneChoice] = Field(default_factory=list)


class ScenarioBlock(BaseInteractionBlock):
    type: Literal["scenario"] = "scenario"
    scenario_title: str
    background: str
    role: str | None = None
    scenes: list[Scene] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# LessonBlock discriminated union
# ---------------------------------------------------------------------------

LessonBlock = Annotated[
    HeadingBlock
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
    | ScenarioBlock,
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# InteractiveHtmlOutline
# ---------------------------------------------------------------------------

class InteractiveHtmlSectionReference(SchemaModel):
    """Used inside outline — defines section skeleton, no blocks."""
    section_id: str
    title: str
    learning_goal: str
    target_concepts: list[str] = Field(default_factory=list)
    key_questions: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)


class InteractiveHtmlOutline(SchemaModel):
    content_type: Literal["interactive_html"] = "interactive_html"
    title: str
    lesson_goal: str
    audience: str
    difficulty: Literal["introductory", "intermediate", "advanced"] = "introductory"
    estimated_minutes: int | None = None
    sections: list[InteractiveHtmlSectionReference] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# InteractiveHtmlSectionSpec  (one Section = ordered LessonBlock[])
# ---------------------------------------------------------------------------

class InteractiveHtmlSectionSpec(SchemaModel):
    section_id: str
    title: str
    learning_goal: str
    concepts: list[ConceptRef] = Field(default_factory=list)
    blocks: list[LessonBlock] = Field(default_factory=list)
    citations: list[CitationRef] = Field(default_factory=list)
    completion_check: "CompletionCheck | None" = None


class CompletionCheck(SchemaModel):
    required_interaction_ids: list[str] = Field(default_factory=list)
    min_correct_count: int | None = None


# ---------------------------------------------------------------------------
# InteractiveHtmlSpec  (assembled course)
# ---------------------------------------------------------------------------

class InteractiveHtmlPedagogy(SchemaModel):
    tutor_tone: Literal["guided", "encouraging", "socratic"] = "guided"
    interaction_density: Literal["low", "medium", "high"] = "medium"
    terminology_level: Literal["low", "medium", "high"] = "medium"


class InteractiveHtmlExportOptions(SchemaModel):
    interactive_html: bool = True
    zip: bool = False


class InteractiveHtmlSpec(SchemaModel):
    content_type: Literal["interactive_html"] = "interactive_html"
    lesson_id: str
    title: str
    subtitle: str | None = None
    meta: "InteractiveHtmlMeta"
    pedagogy: InteractiveHtmlPedagogy = Field(default_factory=InteractiveHtmlPedagogy)
    sections: list[InteractiveHtmlSectionSpec] = Field(default_factory=list)
    citations: list[CitationRef] = Field(default_factory=list)
    assets: list[AssetRef] = Field(default_factory=list)
    export_options: InteractiveHtmlExportOptions = Field(default_factory=InteractiveHtmlExportOptions)


class InteractiveHtmlMeta(SchemaModel):
    language: str = "zh-CN"
    audience: str
    difficulty: Literal["introductory", "intermediate", "advanced"] = "introductory"
    estimated_minutes: int | None = None


# ---------------------------------------------------------------------------
# Element policy  (no images / mindmaps in online course)
# ---------------------------------------------------------------------------

class InteractiveHtmlElementPolicy(SchemaModel):
    generate_process_images: bool = False
    generate_mindmaps: bool = False
    generated_assets: list[str] = Field(default_factory=list)
