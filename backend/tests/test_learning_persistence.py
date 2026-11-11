import pytest
from sqlmodel import SQLModel, create_engine

from app.models import InteractiveLearningEvent, InteractiveLearningSession  # noqa: F401
from app.schemas.learning import CreateSessionRequest, LearningEventPayload, SubmitEventRequest
from app.services.learning_repository import SQLModelLearningRepository
from app.services.learning_service import LearningService


def _engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'learning.db'}", future=True)
    SQLModel.metadata.create_all(engine)
    return engine


def _service(engine) -> LearningService:
    return LearningService(SQLModelLearningRepository(engine))


def test_session_and_events_survive_service_restart(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'learning.db'}"
    engine = _engine(tmp_path)
    service = _service(engine)
    session = service.create_session("lesson_1", CreateSessionRequest())
    service.submit_event(
        "lesson_1",
        session.session_id,
        SubmitEventRequest(
            section_id="unit_1",
            block_id="unit_1_q1",
            interaction_id="i_q1",
            event_type="single_choice_answered",
            payload=LearningEventPayload(selected_option_ids=["a"], is_correct=True),
        ),
    )

    restarted = _service(create_engine(database_url, future=True))

    state = restarted.get_session_state("lesson_1", session.session_id)
    events = restarted.list_events("lesson_1", session.session_id)

    assert state.total_events == 1
    assert state.interaction_summary["total_answered"] == 1
    assert len(events) == 1
    assert events[0]["interaction_id"] == "i_q1"


def test_learning_service_rejects_foreign_lesson_session(tmp_path) -> None:
    service = _service(_engine(tmp_path))
    session = service.create_session("lesson_1", CreateSessionRequest())

    with pytest.raises(ValueError):
        service.get_session_state("lesson_2", session.session_id)


@pytest.mark.parametrize("existing_partial_session", [False, True])
def test_partial_and_final_ids_access_same_session_only(tmp_path, existing_partial_session) -> None:
    engine = _engine(tmp_path)
    repository = SQLModelLearningRepository(engine)
    service = LearningService(repository)
    partial_id = "partial_lesson_task_learning"
    final_id = "lesson_task_learning"
    if existing_partial_session:
        session_id = repository.create_session(partial_id)["session_id"]
    else:
        created = service.create_session(partial_id, CreateSessionRequest())
        session_id = created.session_id
        assert created.lesson_id == final_id

    service.submit_event(partial_id, session_id, SubmitEventRequest(
        section_id="unit_1", interaction_id="i_q1", event_type="single_choice_answered",
        payload=LearningEventPayload(is_correct=True),
    ))

    restarted = _service(create_engine(f"sqlite:///{tmp_path / 'learning.db'}", future=True))
    assert restarted.build_summary(final_id, session_id).total_answered == 1
    assert len(restarted.list_events(final_id, session_id)) == 1
    assert restarted.get_session_state(final_id, session_id).lesson_id == final_id
    with pytest.raises(ValueError):
        restarted.list_events("partial_lesson_task_foreign", session_id)
    restarted.repository.engine.dispose()
    engine.dispose()
