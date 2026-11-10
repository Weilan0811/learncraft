"""Rule-based adaptive brief derived from a learning session summary."""

from dataclasses import dataclass, field
from typing import Callable, Literal

from pydantic import ValidationError

from app.schemas.learning import AdaptiveBriefEvidence, AdaptiveBriefResponse, SessionSummaryResponse
from app.schemas.request import ContentGenerationRequest
from app.schemas.render.interactive_html import InteractiveHtmlRenderModel
from app.schemas.specs.interactive_html import InteractiveHtmlSpec
from app.services.learning_service import LearningService
from app.services.task_repository import SQLModelTaskRepository


Difficulty = Literal["introductory", "intermediate", "advanced"]
DIFFICULTY_VALUES = {"introductory", "intermediate", "advanced"}


class NoLearningEvidenceError(ValueError):
    """Raised when a session has no answered interaction to build a brief from."""


@dataclass
class LessonContext:
    title: str = ""
    difficulty: str | None = None
    section_titles: dict[str, str] = field(default_factory=dict)
    concept_map: dict[str, list[str]] = field(default_factory=dict)
    source_request: ContentGenerationRequest | None = None


def resolve_task_id(lesson_id: str) -> str:
    for prefix in ("partial_lesson_", "lesson_"):
        if lesson_id.startswith(prefix):
            return lesson_id[len(prefix):]
    return lesson_id


def load_lesson_context(
    lesson_id: str, *, repository: SQLModelTaskRepository | None = None,
) -> LessonContext:
    """Read lesson title, section titles and interaction concepts from artifacts."""
    if repository is None:
        from app.api.content_generation import task_service

        repository = task_service.repository
    task_id = resolve_task_id(lesson_id)
    task = repository.get_task(task_id)
    context = LessonContext()
    if task is not None and isinstance(task.request_payload, dict):
        try:
            context.source_request = ContentGenerationRequest.model_validate(task.request_payload)
        except ValidationError:
            context.source_request = None

    spec = _load_spec(repository, task_id)
    if spec is not None:
        context.title = spec.title or context.title
        context.difficulty = spec.meta.difficulty
        for section in spec.sections:
            if not section.interaction_specs:
                continue
            context.section_titles[section.section_id] = section.title
            for interaction in section.interaction_specs:
                if interaction.target_concepts:
                    context.concept_map[interaction.interaction_id] = list(interaction.target_concepts)

    render = _load_render(repository, task_id)
    if render is not None:
        context.title = context.title or render.title
        for section in render.sections:
            if not section.interaction_manifest:
                continue
            context.section_titles.setdefault(section.section_id, section.title)
            for interaction in section.interaction_manifest:
                if interaction.target_concepts:
                    context.concept_map.setdefault(interaction.interaction_id, list(interaction.target_concepts))

    context.title = context.title or ((task.topic or "") if task else "")
    context.title = context.title or lesson_id
    return context


def _load_spec(repository: object, task_id: str) -> InteractiveHtmlSpec | None:
    artifact = repository.get_latest_artifact(task_id, "content_spec")
    payload = getattr(artifact, "payload", None)
    if not isinstance(payload, dict):
        return None
    try:
        return InteractiveHtmlSpec.model_validate(payload)
    except ValidationError:
        return None


def _load_render(repository: object, task_id: str) -> InteractiveHtmlRenderModel | None:
    artifact = repository.get_latest_artifact(task_id, "final_render")
    payload = getattr(artifact, "payload", None)
    if not isinstance(payload, dict):
        return None
    try:
        return InteractiveHtmlRenderModel.model_validate(payload)
    except ValidationError:
        return None


class AdaptiveBriefService:
    def __init__(
        self,
        learning_service: LearningService,
        lesson_context_provider: Callable[[str], LessonContext] | None = None,
    ) -> None:
        self.learning_service = learning_service
        self.lesson_context_provider = lesson_context_provider or load_lesson_context

    def build(
        self,
        lesson_id: str,
        session_id: str,
        difficulty: str | None = None,
    ) -> AdaptiveBriefResponse:
        context = self.lesson_context_provider(lesson_id)
        summary = self.learning_service.build_summary(
            lesson_id,
            session_id,
            section_titles=context.section_titles,
            concept_map=context.concept_map,
        )
        if summary.total_answered == 0:
            raise NoLearningEvidenceError("尚无答题记录，无法生成复习建议")

        concept_names = [item.concept for item in summary.weak_concepts]
        review_titles = [
            context.section_titles.get(section_id, section_id)
            for section_id in summary.review_sections
        ]
        suggested = _suggest_difficulty(summary, difficulty, context.difficulty)
        return AdaptiveBriefResponse(
            lesson_id=lesson_id,
            session_id=session_id,
            topic_suggestion=_topic_suggestion(context.title, concept_names, bool(review_titles)),
            focus_prompt=_focus_prompt(concept_names, review_titles),
            source_request=context.source_request,
            weak_concepts=concept_names,
            review_sections=summary.review_sections,
            suggested_difficulty=suggested,
            evidence=AdaptiveBriefEvidence(
                accuracy=summary.accuracy,
                total_answered=summary.total_answered,
                help_requested_count=summary.help_requested_count,
                weak_concepts=concept_names,
                review_sections=summary.review_sections,
            ),
        )


def _suggest_difficulty(
    summary: SessionSummaryResponse,
    requested: str | None,
    original: str | None,
) -> Difficulty:
    if requested in DIFFICULTY_VALUES:
        return requested  # type: ignore[return-value]
    fallback: Difficulty = original if original in DIFFICULTY_VALUES else "introductory"  # type: ignore[assignment]
    if summary.accuracy is None:
        return fallback
    if summary.accuracy < 0.5:
        return "introductory"
    if summary.accuracy >= 0.85 and summary.help_requested_count <= 1:
        return "advanced"
    return fallback


def _topic_suggestion(title: str, concepts: list[str], has_review_sections: bool) -> str:
    if concepts:
        return f"{title}：薄弱点复习（{'、'.join(concepts[:3])}）"
    if has_review_sections:
        return f"{title}：重点章节复习"
    return f"{title}：巩固练习"


def _focus_prompt(concepts: list[str], review_titles: list[str]) -> str:
    sections = "、".join(review_titles) if review_titles else "本次学习涉及的相关章节"
    if concepts:
        return (
            f"请为同一位学习者生成一份复习型互动讲义。重点讲清以下薄弱概念：{'、'.join(concepts[:5])}。"
            f"优先重讲章节：{sections}。针对易错点补充讲解、例题与即时反馈，"
            "保持原讲义的教学语气与知识范围，不要引入未学过的前置知识。"
        )
    return (
        f"请为同一位学习者生成一份复习型互动讲义。按本次答题情况巩固以下章节：{sections}。"
        "补充讲解、例题与即时反馈，保持原讲义的教学语气与知识范围，不要引入未学过的前置知识。"
    )
