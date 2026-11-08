from pathlib import Path

from sqlmodel import Session

from app.core.asset import AssetStatus
from app.core.task import TaskStatus
from app.schemas.elements import ImageElement
from app.schemas.render import PodcastRenderModel
from app.schemas.render.podcast import PodcastAudioSegment
from app.schemas.request import ContentGenerationRequest
from app.schemas.specs import ElementRequest, PodcastSpec, SocialPostSpec
from app.schemas.state import ContentGenerationState, UnitGenerationResult
from app.services.asset_repository import AssetRepository, AssetRegistration, collect_state_assets
from app.services.task_recovery import recover_interrupted_tasks
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_service import PersistentTaskService


def sqlite_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'resources.db'}"


def make_repository(tmp_path: Path) -> SQLModelTaskRepository:
    return SQLModelTaskRepository(database_url=sqlite_url(tmp_path), echo=False, create_tables=True)


def list_assets(repository: SQLModelTaskRepository, task_id: str):
    with Session(repository.engine) as session:
        return AssetRepository(session).list_assets(task_id)


def test_completed_lecture_task_registers_generated_images(tmp_path) -> None:
    repository = make_repository(tmp_path)
    service = PersistentTaskService(repository=repository)
    created = service.create_task(
        ContentGenerationRequest(content_type="lecture", topic="AI basics", user_prompt="Generate a lecture")
    )

    service.run_task(created.task_id)

    task = repository.get_task(created.task_id)
    assets = list_assets(repository, created.task_id)
    assert task is not None
    assert task.status == TaskStatus.completed
    assert assets, "lecture images must be registered for retry"
    assert all(asset.asset_type == "image" for asset in assets)
    assert all(asset.status == AssetStatus.generated.value for asset in assets)
    summary = task.progress["resource_summary"]
    assert summary["total"] == len(assets)
    assert summary["failed"] == 0
    assert summary["retrying"] == 0
    first = assets[0]
    assert first.metadata_json["description"]
    assert first.metadata_json["aspect_ratio"]
    assert first.metadata_json["layout"]


def test_save_state_registers_fallback_image_as_failed(tmp_path) -> None:
    repository = make_repository(tmp_path)
    created = repository.create_task(
        ContentGenerationRequest(content_type="lecture", topic="Fallback", user_prompt="Generate")
    )
    request = ElementRequest(
        element_id="img_fallback",
        type="image",
        title="Concept diagram",
        purpose="Explain the concept",
        instruction="Draw a concept diagram",
        source_content_type="lecture",
        source_unit_id="unit_001",
        source_outline_unit_id="unit_001",
        context={"layout": "image_text", "unit_title": "Foundations"},
        constraints={"aspect_ratio": "16:9", "style": "educational"},
    )
    element = ImageElement(
        id="img_fallback",
        title="Concept diagram",
        prompt="Draw a concept diagram",
        asset_url="/api/assets/img_fallback/download",
        alt_text="Concept diagram placeholder image",
        metadata={"fallback": True, "reason": "provider unavailable"},
    )
    state = ContentGenerationState(
        request_id=created.task_id,
        content_type="lecture",
        topic="Fallback",
        user_prompt="Generate",
        unit_results={
            "unit_001": UnitGenerationResult(
                unit_id="unit_001",
                status="completed",
                element_requests={"img_fallback": request},
                elements={"img_fallback": element},
            )
        },
        elements=[element],
        status=TaskStatus.completed,
        current_node="finalize_task",
        progress={"stage": "completed", "percent": 100},
    )

    saved = repository.save_state(created.task_id, state)

    assets = list_assets(repository, created.task_id)
    assert saved is not None
    assert len(assets) == 1
    asset = assets[0]
    assert asset.status == AssetStatus.failed.value
    assert asset.error_message == "provider unavailable"
    assert asset.metadata_json["description"] == "Draw a concept diagram"
    assert saved.progress["resource_summary"] == {"total": 1, "failed": 1, "retrying": 0}


def test_save_state_registers_social_post_slots(tmp_path) -> None:
    from app.generators.social_post_generator import SocialPostGenerator

    repository = make_repository(tmp_path)
    created = repository.create_task(
        ContentGenerationRequest(content_type="social_post", topic="Agent design", user_prompt="Write an article")
    )
    base_state = ContentGenerationState(
        request_id=created.task_id,
        content_type="social_post",
        topic="Agent design",
        user_prompt="Write an article",
        status=TaskStatus.running,
        raw_request={},
    )
    spec = SocialPostGenerator().generate(base_state)
    failed_slot = spec.image_slots[0]
    failed_base_id = f"{spec.id}_{failed_slot.slot_id}"
    assets = [
        asset.model_copy(
            update={
                "status": "generated",
                "public_url": f"/api/assets/{failed_base_id}_placeholder/download",
                "error_message": "fallback placeholder (image quota exceeded)",
            }
        )
        if asset.slot_id == failed_slot.slot_id
        else asset
        for asset in spec.image_assets
    ]
    spec = spec.model_copy(
        update={
            "image_assets": assets,
            "metadata": {**spec.metadata, "image_fallbacks": {failed_slot.slot_id: "image quota exceeded"}},
        }
    )
    state = base_state.model_copy(
        update={
            "content_spec": spec,
            "status": TaskStatus.completed,
            "current_node": "finalize_task",
            "progress": {"stage": "completed", "percent": 100},
        }
    )

    saved = repository.save_state(created.task_id, state)

    rows = list_assets(repository, created.task_id)
    assert saved is not None
    assert len(rows) == len(spec.image_slots)
    failed_rows = [row for row in rows if row.status == AssetStatus.failed.value]
    assert len(failed_rows) == 1
    assert failed_rows[0].error_message == "image quota exceeded"
    assert failed_rows[0].metadata_json["slot_id"] == failed_slot.slot_id
    assert failed_rows[0].metadata_json["description"] == failed_slot.prompt_en
    assert saved.progress["resource_summary"]["failed"] == 1


def test_save_state_registers_podcast_segments(tmp_path) -> None:
    repository = make_repository(tmp_path)
    created = repository.create_task(
        ContentGenerationRequest(content_type="podcast_script", topic="Agents", user_prompt="Write a podcast")
    )
    spec = PodcastSpec(
        id=f"podcast_{created.task_id}",
        version="content.spec/v1",
        title="Agents",
        podcast_name="Agent Talk",
        podcast_tagline="A short conversation",
        raw_dialogue="Person1: hello",
    )
    render_model = PodcastRenderModel(
        title="Agents",
        podcast_name="Agent Talk",
        podcast_tagline="A short conversation",
        script_text="Person1: hello",
        segments=[
            PodcastAudioSegment(
                segment_id="seg_001",
                order=1,
                speaker="Person1",
                voice="Ethan",
                text="hello",
                audio_url=f"/api/assets/{spec.id}_001/download",
                status="generated",
            ),
            PodcastAudioSegment(
                segment_id="seg_002",
                order=2,
                speaker="Person2",
                voice="Cherry",
                text="hi there",
                status="failed",
                error_message="TTS quota exceeded",
                retry_count=1,
            ),
        ],
    )
    state = ContentGenerationState(
        request_id=created.task_id,
        content_type="podcast_script",
        topic="Agents",
        user_prompt="Write a podcast",
        content_spec=spec,
        render_model=render_model,
        status=TaskStatus.completed,
        current_node="finalize_task",
        progress={"stage": "completed", "percent": 100},
    )

    saved = repository.save_state(created.task_id, state)

    rows = list_assets(repository, created.task_id)
    assert saved is not None
    assert len(rows) == 2
    by_segment = {row.metadata_json["segment_id"]: row for row in rows}
    assert by_segment["seg_001"].status == AssetStatus.generated.value
    assert by_segment["seg_001"].asset_type == "audio"
    assert by_segment["seg_002"].status == AssetStatus.failed.value
    assert by_segment["seg_002"].error_message == "TTS quota exceeded"
    assert by_segment["seg_002"].metadata_json["text"] == "hi there"
    assert by_segment["seg_002"].metadata_json["voice"] == "Cherry"
    assert saved.progress["resource_summary"] == {"total": 2, "failed": 1, "retrying": 0}


def test_collect_state_assets_uses_task_scoped_ids() -> None:
    request = ElementRequest(
        element_id="img_001",
        type="image",
        title="Diagram",
        purpose="Explain",
        instruction="Draw",
        source_content_type="lecture",
        source_unit_id="unit_001",
        source_outline_unit_id="unit_001",
    )
    element = ImageElement(
        id="img_001",
        title="Diagram",
        prompt="Draw",
        asset_url="/api/assets/img_001/download",
        alt_text="Diagram",
    )
    state = ContentGenerationState(
        request_id="task_a",
        content_type="lecture",
        topic="Topic",
        user_prompt="Generate",
        unit_results={
            "unit_001": UnitGenerationResult(
                unit_id="unit_001",
                element_requests={"img_001": request},
                elements={"img_001": element},
            )
        },
        elements=[element],
    )

    first = collect_state_assets("task_a", state)
    second = collect_state_assets("task_b", state)

    assert first[0].asset_id != second[0].asset_id
    assert first[0].asset_id.endswith("img_001")
    assert first[0].unit_id == "unit_001"


def test_recover_interrupted_tasks_marks_leftover_work(tmp_path) -> None:
    repository = make_repository(tmp_path)
    queued = repository.create_task(
        ContentGenerationRequest(content_type="lecture", topic="Queued", user_prompt="Generate")
    )
    running = repository.create_task(
        ContentGenerationRequest(content_type="lecture", topic="Running", user_prompt="Generate")
    )
    finished = repository.create_task(
        ContentGenerationRequest(content_type="lecture", topic="Finished", user_prompt="Generate")
    )
    repository.update_task(running.task_id, status=TaskStatus.running.value)
    repository.update_task(finished.task_id, status=TaskStatus.completed.value)
    with Session(repository.engine) as session:
        AssetRepository(session).upsert(
            running.task_id,
            AssetRegistration(
                asset_id=f"{running.task_id}:img_001",
                asset_type="image",
                uri="",
                status=AssetStatus.retrying.value,
                metadata={"description": "draw"},
            ),
        )
        session.commit()

    result = recover_interrupted_tasks(repository)

    assert result == {"interrupted_tasks": 2, "reset_assets": 1}
    for task_id in (queued.task_id, running.task_id):
        task = repository.get_task(task_id)
        assert task is not None
        assert task.status == TaskStatus.interrupted
        assert task.progress["stage"] == "interrupted"
        assert "服务重启" in (task.error_message or "")
    recovered_assets = list_assets(repository, running.task_id)
    assert recovered_assets[0].status == AssetStatus.failed.value
    recovered_task = repository.get_task(running.task_id)
    assert recovered_task is not None
    assert recovered_task.progress["resource_summary"] == {"total": 1, "failed": 1, "retrying": 0}
    completed = repository.get_task(finished.task_id)
    assert completed is not None
    assert completed.status == TaskStatus.completed
