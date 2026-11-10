import json
from functools import partial
from pathlib import Path

import pytest
from sqlmodel import Session

from app.schemas.learning import CreateSessionRequest, LearningEventPayload, SubmitEventRequest
from app.schemas.request import ContentGenerationRequest
from app.services.adaptive_brief_service import AdaptiveBriefService, load_lesson_context
from app.services.artifact_repository import ArtifactRepository
from app.services.learning_repository import SQLModelLearningRepository
from app.services.learning_service import LearningService
from app.services.task_repository import SQLModelTaskRepository


@pytest.fixture
def saved_lesson(tmp_path):
    snapshot = json.loads(
        (Path(__file__).parent / "fixtures" / "interactive_learning_snapshot.json").read_text(encoding="utf-8")
    )
    database_url = f"sqlite:///{tmp_path / 'tasks.db'}"
    repository = SQLModelTaskRepository(database_url)
    repository.create_task(ContentGenerationRequest.model_validate(snapshot["request"]), task_id=snapshot["task_id"])
    with Session(repository.engine) as session:
        artifacts = ArtifactRepository(session)
        artifacts.upsert_artifact(snapshot["task_id"], "content_spec", snapshot["spec"])
        artifacts.upsert_artifact(snapshot["task_id"], "final_render", snapshot["final_render"])
        session.commit()
    yield snapshot, repository, database_url
    repository.engine.dispose()


def test_load_lesson_context_reads_saved_spec(saved_lesson) -> None:
    snapshot, repository, _ = saved_lesson
    spec = snapshot["spec"]
    section = spec["sections"][0]

    context = load_lesson_context(spec["lesson_id"], repository=repository)

    assert context.title == spec["title"]
    assert context.difficulty == spec["meta"]["difficulty"]
    assert context.section_titles == {section["section_id"]: section["title"]}
    assert context.concept_map == {
        interaction["interaction_id"]: interaction["target_concepts"]
        for interaction in section["interaction_specs"] if interaction["target_concepts"]
    }


def test_adaptive_brief_restores_original_request_after_restart(saved_lesson) -> None:
    snapshot, repository, database_url = saved_lesson
    lesson_id = snapshot["spec"]["lesson_id"]
    section = snapshot["spec"]["sections"][0]
    interaction = section["interaction_specs"][0]
    learning = LearningService(SQLModelLearningRepository(repository.engine))
    session = learning.create_session(lesson_id, CreateSessionRequest())
    learning.submit_event(
        lesson_id, session.session_id,
        SubmitEventRequest(
            section_id=section["section_id"],
            interaction_id=interaction["interaction_id"],
            event_type=interaction["event_type"],
            payload=LearningEventPayload(),
        ),
    )
    repository.engine.dispose()

    restarted = SQLModelTaskRepository(database_url)
    try:
        service = AdaptiveBriefService(
            LearningService(SQLModelLearningRepository(restarted.engine)),
            partial(load_lesson_context, repository=restarted),
        )
        brief = service.build(lesson_id, session.session_id)

        assert brief.evidence.total_answered == 1
        assert brief.model_dump(mode="json")["source_request"] == snapshot["request"]
    finally:
        restarted.engine.dispose()
