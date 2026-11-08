from pathlib import Path

from app.core.task import TaskStatus
from app.schemas.outline import Outline, OutlineUnit
from app.schemas.render import LectureRenderModel, LectureRenderSection, RenderBlock
from app.schemas.request import ContentGenerationRequest
from app.schemas.specs import LectureSection, LectureSpec, TextBlock
from app.schemas.state import ContentGenerationState
from app.services.task_repository import SQLModelTaskRepository


def sqlite_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'contract.db'}"


def test_repository_saves_generation_artifacts_without_losing_task_summary(tmp_path: Path) -> None:
    repository = SQLModelTaskRepository(database_url=sqlite_url(tmp_path), echo=False, create_tables=True)
    request = ContentGenerationRequest(content_type="lecture", topic="AI basics", user_prompt="Generate a lecture")
    created = repository.create_task(request, task_id="task_contract")

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
        id="outline_task_contract",
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
    content_spec = LectureSpec(id="spec_task_contract", title="AI basics", sections=[section])
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
    state = ContentGenerationState(
        request_id=created.task_id,
        content_type="lecture",
        topic="AI basics",
        user_prompt="Generate a lecture",
        outline=outline,
        content_spec=content_spec,
        render_model=render_model,
        status=TaskStatus.completed,
        current_node="finalize_task",
        progress={"stage": "completed", "percent": 100},
    )

    saved = repository.save_state(created.task_id, state)
    loaded = repository.get_task(created.task_id)
    outline_artifact = repository.get_latest_artifact(created.task_id, "outline")
    content_spec_artifact = repository.get_latest_artifact(created.task_id, "content_spec")
    render_artifact = repository.get_latest_artifact(created.task_id, "final_render")

    assert saved is not None
    assert loaded is not None
    assert loaded.task_id == "task_contract"
    assert loaded.content_type == "lecture"
    assert loaded.status == TaskStatus.completed
    assert loaded.progress["percent"] == 100
    assert not hasattr(loaded, "outline")
    assert outline_artifact is not None
    assert content_spec_artifact is not None
    assert render_artifact is not None
    assert outline_artifact.payload == outline.model_dump(mode="json")
    assert content_spec_artifact.payload == content_spec.model_dump(mode="json")
    assert render_artifact.payload["render_model"] == render_model.model_dump(mode="json")
