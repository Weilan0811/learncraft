from sqlmodel import SQLModel, create_engine

from app.models import InteractiveLearningEvent, InteractiveLearningSession  # noqa: F401
from app.schemas.learning import CreateSessionRequest, LearningEventPayload, SubmitEventRequest
from app.services.learning_repository import SQLModelLearningRepository
from app.services.learning_service import LearningService


SECTION_TITLES = {"s1": "第一节 基础", "s2": "第二节 进阶"}
CONCEPT_MAP = {"i1": ["概念A"], "i2": ["概念A", "概念B"], "i3": ["概念C"], "i4": ["概念C"]}


def _service(tmp_path) -> LearningService:
    engine = create_engine(f"sqlite:///{tmp_path / 'summary.db'}", future=True)
    SQLModel.metadata.create_all(engine)
    return LearningService(SQLModelLearningRepository(engine))


def _submit(service: LearningService, session_id: str, **kwargs) -> None:
    service.submit_event("lesson_1", session_id, SubmitEventRequest(**kwargs))


def test_summary_reports_accuracy_weak_sections_and_concepts(tmp_path) -> None:
    service = _service(tmp_path)
    session = service.create_session("lesson_1", CreateSessionRequest())

    _submit(
        service, session.session_id,
        section_id="s1", interaction_id="i1", event_type="single_choice_answered",
        payload=LearningEventPayload(selected_option_ids=["a"], is_correct=True, time_spent_seconds=20),
    )
    _submit(
        service, session.session_id,
        section_id="s1", interaction_id="i2", event_type="single_choice_answered",
        payload=LearningEventPayload(selected_option_ids=["b"], is_correct=False, time_spent_seconds=30),
    )
    _submit(
        service, session.session_id,
        section_id="s1", interaction_id="i2", event_type="hint_requested",
        payload=LearningEventPayload(),
    )
    _submit(
        service, session.session_id,
        section_id="s2", interaction_id="i3", event_type="multiple_choice_answered",
        payload=LearningEventPayload(selected_option_ids=["a", "c"], is_correct=True),
    )
    _submit(
        service, session.session_id,
        section_id="s2", interaction_id="i4", event_type="single_choice_answered",
        payload=LearningEventPayload(selected_option_ids=["a"], is_correct=True),
    )
    _submit(
        service, session.session_id,
        section_id="s2", interaction_id="i4", event_type="short_answer_submitted",
        payload=LearningEventPayload(answer_text="只写了思路，没有评分"),
    )

    summary = service.build_summary(
        "lesson_1",
        session.session_id,
        section_titles=SECTION_TITLES,
        concept_map=CONCEPT_MAP,
    )

    assert summary.total_answered == 5
    assert summary.total_scored == 4
    assert summary.total_correct == 3
    assert summary.accuracy == 0.75
    assert summary.help_requested_count == 1
    assert summary.total_time_spent_seconds == 50
    assert summary.answered_sections == 2
    assert summary.total_sections == 2
    assert summary.completion_rate == 1.0

    first, second = summary.section_progress
    assert first.section_id == "s1"
    assert first.title == "第一节 基础"
    assert first.accuracy == 0.5
    assert first.is_weak is True
    assert second.section_id == "s2"
    assert second.accuracy == 1.0
    assert second.is_weak is False

    assert [item.concept for item in summary.weak_concepts] == ["概念A", "概念B"]
    assert summary.weak_concepts[0].score == 3
    assert summary.weak_concepts[0].sections == ["s1"]
    assert summary.review_sections == ["s1"]
    assert "答对 3/4 题" in summary.summary_text


def test_summary_without_answers_is_empty(tmp_path) -> None:
    service = _service(tmp_path)
    session = service.create_session("lesson_1", CreateSessionRequest())

    summary = service.build_summary("lesson_1", session.session_id)

    assert summary.total_answered == 0
    assert summary.accuracy is None
    assert summary.section_progress == []
    assert summary.weak_concepts == []
    assert summary.summary_text == "尚无学习记录。"
