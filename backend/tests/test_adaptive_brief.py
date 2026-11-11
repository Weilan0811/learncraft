import pytest
from sqlmodel import SQLModel, create_engine

from app.models import InteractiveLearningEvent, InteractiveLearningSession  # noqa: F401
from app.schemas.learning import CreateSessionRequest, LearningEventPayload, SubmitEventRequest
from app.services.adaptive_brief_service import (
    AdaptiveBriefService,
    LessonContext,
    NoLearningEvidenceError,
)
from app.services.learning_repository import SQLModelLearningRepository
from app.services.learning_service import LearningService


CONTEXT = LessonContext(
    title="提示工程入门",
    difficulty="intermediate",
    section_titles={"s1": "第一节 基础", "s2": "第二节 进阶"},
    concept_map={"i_answer": ["概念A"], "i_weak": ["概念A", "概念B"]},
)


def _prepare(tmp_path, *, correct: int = 0, wrong: int = 0, helps: int = 0):
    engine = create_engine(f"sqlite:///{tmp_path / 'brief.db'}", future=True)
    SQLModel.metadata.create_all(engine)
    service = LearningService(SQLModelLearningRepository(engine))
    session = service.create_session("lesson_1", CreateSessionRequest())
    for _ in range(correct):
        service.submit_event(
            "lesson_1",
            session.session_id,
            SubmitEventRequest(
                section_id="s1",
                interaction_id="i_answer",
                event_type="single_choice_answered",
                payload=LearningEventPayload(is_correct=True),
            ),
        )
    for _ in range(wrong):
        service.submit_event(
            "lesson_1",
            session.session_id,
            SubmitEventRequest(
                section_id="s2",
                interaction_id="i_weak",
                event_type="single_choice_answered",
                payload=LearningEventPayload(is_correct=False),
            ),
        )
    for _ in range(helps):
        service.submit_event(
            "lesson_1",
            session.session_id,
            SubmitEventRequest(
                section_id="s2",
                interaction_id="i_weak",
                event_type="hint_requested",
                payload=LearningEventPayload(),
            ),
        )
    return service, session, AdaptiveBriefService(service, lesson_context_provider=lambda _: CONTEXT)


def test_brief_uses_introductory_difficulty_for_low_accuracy(tmp_path) -> None:
    service, session, brief_service = _prepare(tmp_path, correct=1, wrong=3)

    brief = brief_service.build("lesson_1", session.session_id)

    assert brief.suggested_difficulty == "introductory"
    assert brief.evidence.accuracy == 0.25
    assert brief.weak_concepts == ["概念A", "概念B"]
    assert "概念A" in brief.topic_suggestion
    assert "请为同一位学习者生成一份复习型互动讲义" in brief.focus_prompt
    assert "第二节 进阶" in brief.focus_prompt


def test_brief_uses_advanced_difficulty_for_high_accuracy_without_help(tmp_path) -> None:
    _, session, brief_service = _prepare(tmp_path, correct=6)

    brief = brief_service.build("lesson_1", session.session_id)

    assert brief.suggested_difficulty == "advanced"
    assert brief.evidence.accuracy == 1.0


def test_brief_keeps_original_difficulty_when_accuracy_is_mixed(tmp_path) -> None:
    _, session, brief_service = _prepare(tmp_path, correct=3, wrong=1)

    brief = brief_service.build("lesson_1", session.session_id)

    assert brief.suggested_difficulty == "intermediate"


def test_explicit_difficulty_wins(tmp_path) -> None:
    _, session, brief_service = _prepare(tmp_path, correct=1, wrong=3)

    brief = brief_service.build("lesson_1", session.session_id, difficulty="advanced")

    assert brief.suggested_difficulty == "advanced"


def test_brief_requires_answered_interactions(tmp_path) -> None:
    _, session, brief_service = _prepare(tmp_path, helps=1)

    with pytest.raises(NoLearningEvidenceError):
        brief_service.build("lesson_1", session.session_id)
