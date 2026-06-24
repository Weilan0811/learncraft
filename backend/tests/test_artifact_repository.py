from pathlib import Path

from app.core.task import TaskStatus
from app.models.content_generation_artifact import ContentGenerationArtifact
from app.models.content_generation_event import ContentGenerationEvent
from app.models.content_generation_metric import ContentGenerationMetric
from app.models.content_generation_reference import ContentGenerationReference
from app.schemas.outline import Outline, OutlineUnit
from app.schemas.render import LectureRenderModel, LectureRenderSection, RenderBlock
from app.schemas.request import ContentGenerationRequest
from app.schemas.specs import LectureSection, LectureSpec, TextBlock
from app.schemas.state import ContentGenerationState, RetrievedChunk, TaskStreamEvent
from app.services.task_repository import SQLModelTaskRepository

from tests.test_task_persistence import sqlite_url


def _state_with_core_artifacts(task_id: str) -> ContentGenerationState:
    unit = OutlineUnit(
        id="unit_001",
        order=1,
        unit_type="section",
        title="Foundations",
        goal="Understand the basics.",
        core_message="AI systems turn inputs into useful outputs.",
        key_points=["Inputs", "Outputs"],
        source_chunk_ids=["chunk_1"],
    )
    outline = Outline(
        id=f"outline_{task_id}",
        content_type="lecture",
        title="AI basics",
        units=[unit],
        sections=[],
    )
    section = LectureSection(
        id="lecture_unit_001",
        outline_unit_id=unit.id,
        order=1,
        title=unit.title,
        summary=unit.core_message,
        blocks=[TextBlock(id="block_001", title="Intro", content="AI basics.")],
        source_chunk_ids=["chunk_1"],
    )
    content_spec = LectureSpec(id=f"spec_{task_id}", title="AI basics", sections=[section])
    render_model = LectureRenderModel(
        title="AI basics",
        sections=[
            LectureRenderSection(
                id="unit_001",
                title="Foundations",
                render_blocks=[RenderBlock(id="render_001", type="text", title="Intro", content="AI basics.")],
            )
        ],
    )
    return ContentGenerationState(
        request_id=task_id,
        content_type="lecture",
        topic="AI basics",
        user_prompt="Generate a lecture",
        planning_chunks=[
            RetrievedChunk(
                id="chunk_1",
                source_id="source_1",
                source_title="Overview",
                content="AI Agent overview content",
                score=0.9,
                metadata={"knowledge_base_id": "kb_ai"},
            )
        ],
        outline=outline,
        content_spec=content_spec,
        render_model=render_model,
        stream_events=[
            TaskStreamEvent(
                event_id="event_001",
                task_id=task_id,
                type="outline_ready",
                payload={"title": "AI basics"},
                created_at="2026-06-24T00:00:00+00:00",
            )
        ],
        status=TaskStatus.completed,
        current_node="finalize_task",
        progress={"stage": "completed", "percent": 100},
    )


def test_repository_writes_artifacts_references_events_and_keeps_legacy_readback(tmp_path: Path) -> None:
    repository = SQLModelTaskRepository(database_url=sqlite_url(tmp_path), echo=False, create_tables=True)
    request = ContentGenerationRequest(content_type="lecture", topic="AI basics", user_prompt="Generate a lecture")
    created = repository.create_task(
        request,
        task_id="task_artifacts",
        platform_context={
            "platform_log_id": "log_001",
            "platform_user_id": "user_001",
            "platform_session_id": "session_001",
        },
    )

    repository.save_state(created.task_id, _state_with_core_artifacts(created.task_id))
    loaded = repository.get_task(created.task_id)
    artifacts = repository.list_artifacts(created.task_id)
    references = repository.list_references(created.task_id)
    events = repository.list_events(created.task_id)

    assert loaded is not None
    assert loaded.platform_log_id == "log_001"
    assert loaded.platform_user_id == "user_001"
    assert loaded.platform_session_id == "session_001"
    assert loaded.topic == "AI basics"
    assert loaded.generation_options["allow_fallback"] is False
    assert loaded.generation_options["include_images"] is True
    assert loaded.outline["title"] == "AI basics"
    assert loaded.content_spec["title"] == "AI basics"
    assert loaded.render_model["title"] == "AI basics"
    assert {artifact.artifact_type for artifact in artifacts} >= {"outline", "content_spec", "final_render"}
    assert any(reference.chunk_id == "chunk_1" and reference.stage == "planning" for reference in references)
    assert any(event.event_type == "outline_ready" for event in events)


def test_sqlmodel_metadata_includes_new_generation_tables(tmp_path: Path) -> None:
    repository = SQLModelTaskRepository(database_url=sqlite_url(tmp_path), echo=False, create_tables=True)
    del repository

    assert ContentGenerationArtifact.__tablename__ == "content_generation_artifact"
    assert ContentGenerationReference.__tablename__ == "content_generation_reference"
    assert ContentGenerationEvent.__tablename__ == "content_generation_event"
    assert ContentGenerationMetric.__tablename__ == "content_generation_metric"
