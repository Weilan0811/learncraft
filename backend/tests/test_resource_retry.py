from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import wave
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.asset import AssetStatus
from app.core.task import TaskStatus
from app.main import app
from app.schemas.elements import AudioFileElement, ImageElement
from app.schemas.export import ExportFile
from app.schemas.outline import Outline, OutlineUnit
from app.schemas.render import LectureRenderModel, LectureRenderSection, PodcastRenderModel, RenderBlock
from app.schemas.render.podcast import PodcastAudioSegment
from app.schemas.request import ContentGenerationRequest
from app.schemas.specs import (
    ElementReferenceBlock,
    ElementRequest,
    LectureSection,
    LectureSpec,
    PodcastSpec,
    SocialPostSpec,
    TextBlock,
)
from app.schemas.state import ContentGenerationState, RenderUnitSnapshot, UnitGenerationResult
from app.services import resource_retry_service as resources
from app.services.asset_repository import AssetRegistration, AssetRepository
from app.services.storage_service import LocalStorageService
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_service import PersistentTaskService


class FakeImageService:
    def __init__(self, error: str | None = None) -> None:
        self.error = error
        self.calls: list[dict[str, object]] = []

    def generate_image(self, title, description, aspect_ratio="16:9", asset_id=None, layout="image_text"):
        self.calls.append(
            {
                "title": title,
                "description": description,
                "aspect_ratio": aspect_ratio,
                "asset_id": asset_id,
                "layout": layout,
            }
        )
        if self.error:
            raise RuntimeError(self.error)
        return ImageElement(
            id=str(asset_id),
            title=title,
            prompt=description,
            asset_url=f"/api/assets/{asset_id}/download",
            alt_text=title,
            width=1024,
            height=576,
            format="png",
            model="fake-image",
            metadata={"provider": "fake", "model": "fake-image", "width": 1024, "height": 576, "format": "png"},
        )


class FakeTTSService:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def synthesize(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        self.calls.append({"text": text, "voice": voice, "asset_id": asset_id})
        record = LocalStorageService().save_bytes(
            asset_id=asset_id,
            filename=f"{asset_id}.wav",
            content=_wav_bytes(),
            content_type="audio/wav",
            kind="audio",
            metadata={"provider": "fake", "voice": voice, "format": "wav"},
        )
        return AudioFileElement(
            id=record.asset_id,
            title=f"{voice} audio",
            speaker="Person2" if voice == "Cherry" else "Person1",
            voice=voice,
            audio_url=record.url,
            format="wav",
            byte_size=record.byte_size,
            order=0,
        )


def _wav_bytes() -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 800)
    return buffer.getvalue()


def make_repository(tmp_path: Path) -> SQLModelTaskRepository:
    return SQLModelTaskRepository(
        database_url=f"sqlite:///{tmp_path / 'retry.db'}",
        echo=False,
        create_tables=True,
    )


def get_asset(repository: SQLModelTaskRepository, task_id: str, resource_id: str):
    with Session(repository.engine) as session:
        asset = AssetRepository(session).get(task_id, resource_id)
        if asset is not None:
            session.expunge(asset)
        return asset


def set_asset_failed(repository: SQLModelTaskRepository, task_id: str, resource_id: str) -> None:
    with Session(repository.engine) as session:
        asset = AssetRepository(session).get(task_id, resource_id)
        assert asset is not None
        asset.status = AssetStatus.failed.value
        asset.updated_at = datetime.now(UTC)
        session.add(asset)
        session.commit()


def create_lecture_task_with_failed_image(repository: SQLModelTaskRepository) -> tuple[str, str]:
    created = repository.create_task(
        ContentGenerationRequest(content_type="lecture", topic="Retry topic", user_prompt="Generate")
    )
    task_id = created.task_id
    unit_id = "unit_001"
    request = ElementRequest(
        element_id="img_001",
        type="image",
        title="Concept diagram",
        purpose="Explain the concept",
        instruction="Draw a concept diagram",
        source_content_type="lecture",
        source_unit_id=unit_id,
        source_outline_unit_id=unit_id,
        context={"layout": "image_text"},
        constraints={"aspect_ratio": "16:9", "style": "educational"},
    )
    element = ImageElement(
        id="img_001",
        title="Concept diagram",
        prompt="Draw a concept diagram",
        asset_url="/api/assets/img_001_placeholder/download",
        alt_text="Concept diagram placeholder",
        metadata={"fallback": True, "reason": "provider down"},
    )
    section = LectureSection(
        id=unit_id,
        outline_unit_id=unit_id,
        order=1,
        title="Foundations",
        summary="Core message",
        blocks=[
            TextBlock(id="block_text", title="Intro", content="Keep this text."),
            ElementReferenceBlock(id="block_image", title="Diagram", element_id="img_001"),
        ],
        source_chunk_ids=[],
    )
    spec = LectureSpec(id="spec_lecture", title="Retry topic", sections=[section])
    render_model = LectureRenderModel(
        title="Retry topic",
        sections=[
            LectureRenderSection(
                id=unit_id,
                title="Foundations",
                render_blocks=[
                    RenderBlock(id="block_text", type="text", title="Intro", content="Keep this text."),
                    RenderBlock(
                        id="img_001",
                        type="image",
                        title="Concept diagram",
                        asset_url="/api/assets/img_001_placeholder/download",
                        metadata={"prompt": "Draw a concept diagram", "fallback": True, "reason": "provider down"},
                    ),
                ],
            )
        ],
    )
    outline = Outline(
        id="outline_retry",
        content_type="lecture",
        title="Retry topic",
        units=[
            OutlineUnit(
                id=unit_id,
                order=1,
                unit_type="section",
                title="Foundations",
                goal="Understand",
                core_message="Core message",
            )
        ],
        sections=[],
    )
    state = ContentGenerationState(
        request_id=task_id,
        content_type="lecture",
        topic="Retry topic",
        user_prompt="Generate",
        outline=outline,
        unit_results={
            unit_id: UnitGenerationResult(
                unit_id=unit_id,
                status="completed",
                unit_spec=section,
                element_requests={"img_001": request},
                elements={"img_001": element},
            )
        },
        elements=[element],
        content_spec=spec,
        render_model=render_model,
        partial_render_model=render_model,
        render_units={
            unit_id: RenderUnitSnapshot(
                unit_id=unit_id,
                order=1,
                content_type="lecture",
                status="rendered",
                render_fragment=render_model.sections[0].model_dump(mode="json"),
            )
        },
        status=TaskStatus.completed,
        current_node="finalize_task",
        progress={"stage": "completed", "percent": 100},
    )
    repository.save_state(task_id, state)
    repository.update_export_files(task_id, [ExportFile(type="pdf", url="/api/assets/old_export/download")])
    assets = resources.list_failed_resources(repository, task_id)
    assert assets is not None
    assert len(assets.resources) == 1
    return task_id, assets.resources[0].resource_id


def create_podcast_task_with_failed_segment(repository: SQLModelTaskRepository) -> tuple[str, str]:
    created = repository.create_task(
        ContentGenerationRequest(content_type="podcast_script", topic="Podcast retry", user_prompt="Generate")
    )
    task_id = created.task_id
    spec = PodcastSpec(
        id=f"podcast_{task_id}",
        version="content.spec/v1",
        title="Podcast retry",
        podcast_name="Retry FM",
        podcast_tagline="Short show",
        raw_dialogue="Person1: hello\nPerson2: hi",
    )
    first_asset_id = f"{spec.id}_001"
    record = LocalStorageService().save_bytes(
        asset_id=first_asset_id,
        filename=f"{first_asset_id}.wav",
        content=_wav_bytes(),
        content_type="audio/wav",
        kind="audio",
        metadata={"provider": "fake", "format": "wav"},
    )
    render_model = PodcastRenderModel(
        title="Podcast retry",
        podcast_name="Retry FM",
        podcast_tagline="Short show",
        script_text="Person1: hello\nPerson2: hi",
        segments=[
            PodcastAudioSegment(
                segment_id="seg_001",
                order=1,
                speaker="Person1",
                voice="Ethan",
                text="hello",
                audio_url=record.url,
                status="generated",
            ),
            PodcastAudioSegment(
                segment_id="seg_002",
                order=2,
                speaker="Person2",
                voice="Cherry",
                text="hi",
                status="failed",
                error_message="TTS quota exceeded",
                retry_count=1,
            ),
        ],
        audio_assets=[
            AudioFileElement(
                id=record.asset_id,
                title="Ethan audio",
                speaker="Person1",
                voice="Ethan",
                audio_url=record.url,
                format="wav",
                byte_size=record.byte_size,
                order=1,
            )
        ],
    )
    state = ContentGenerationState(
        request_id=task_id,
        content_type="podcast_script",
        topic="Podcast retry",
        user_prompt="Generate",
        content_spec=spec,
        render_model=render_model,
        partial_render_model=render_model,
        status=TaskStatus.completed,
        current_node="finalize_task",
        progress={"stage": "completed", "percent": 100},
    )
    repository.save_state(task_id, state)
    listing = resources.list_failed_resources(repository, task_id)
    assert listing is not None
    assert len(listing.resources) == 1
    return task_id, listing.resources[0].resource_id


def test_retry_image_success_updates_preview_and_invalidates_exports(tmp_path, monkeypatch) -> None:
    repository = make_repository(tmp_path)
    task_id, resource_id = create_lecture_task_with_failed_image(repository)
    fake = FakeImageService()
    monkeypatch.setattr(resources, "get_image_generation_service", lambda: fake)

    submitted = resources.submit_retry(repository, task_id, resource_id)
    assert submitted.status == "retrying"
    resources.execute_retry(repository, task_id, resource_id)

    assert fake.calls[0]["description"] == "Draw a concept diagram"
    assert fake.calls[0]["aspect_ratio"] == "16:9"
    assert "img_001_r1" in str(fake.calls[0]["asset_id"])
    asset = get_asset(repository, task_id, resource_id)
    assert asset is not None
    assert asset.status == AssetStatus.generated.value
    assert asset.retry_count == 1
    assert "img_001_r1" in asset.uri

    task = repository.get_task(task_id)
    assert task is not None
    assert "export_files" not in task.progress
    assert task.progress["resource_summary"] == {"total": 1, "failed": 0, "retrying": 0}
    assert repository.get_latest_artifact(task_id, "export_manifest") is None

    preview = PersistentTaskService(repository=repository).get_preview(task_id)
    assert preview is not None
    blocks = {block.id: block for section in preview.render_model.sections for block in section.render_blocks}
    assert blocks["block_text"].content == "Keep this text."
    assert "img_001_r1" in (blocks["img_001"].asset_url or "")
    assert blocks["img_001"].metadata.get("fallback") is None

    unit_artifact = repository.get_latest_artifact(task_id, "unit_render", "unit_001")
    assert unit_artifact is not None
    unit_block = next(
        block
        for block in unit_artifact.payload["render_fragment"]["render_blocks"]
        if block["id"] == "img_001"
    )
    assert "img_001_r1" in unit_block["asset_url"]

    listing = resources.list_failed_resources(repository, task_id)
    assert listing is not None
    assert listing.resources == []


def test_retry_image_failure_records_error_and_keeps_old_preview(tmp_path, monkeypatch) -> None:
    repository = make_repository(tmp_path)
    task_id, resource_id = create_lecture_task_with_failed_image(repository)
    fake = FakeImageService(error="provider exploded")
    monkeypatch.setattr(resources, "get_image_generation_service", lambda: fake)

    resources.submit_retry(repository, task_id, resource_id)
    resources.execute_retry(repository, task_id, resource_id)

    asset = get_asset(repository, task_id, resource_id)
    assert asset is not None
    assert asset.status == AssetStatus.failed.value
    assert asset.retry_count == 1
    assert "provider exploded" in (asset.error_message or "")
    preview = PersistentTaskService(repository=repository).get_preview(task_id)
    assert preview is not None
    blocks = {block.id: block for section in preview.render_model.sections for block in section.render_blocks}
    assert blocks["img_001"].asset_url == "/api/assets/img_001_placeholder/download"
    task = repository.get_task(task_id)
    assert task is not None
    assert task.progress["export_files"]
    listing = resources.list_failed_resources(repository, task_id)
    assert listing is not None
    assert len(listing.resources) == 1
    assert listing.resources[0].retry_count == 1


def test_retry_rejects_duplicate_and_unavailable_resources(tmp_path, monkeypatch) -> None:
    repository = make_repository(tmp_path)
    task_id, resource_id = create_lecture_task_with_failed_image(repository)
    monkeypatch.setattr(resources, "get_image_generation_service", lambda: FakeImageService())

    resources.submit_retry(repository, task_id, resource_id)
    try:
        resources.submit_retry(repository, task_id, resource_id)
    except resources.RetryConflict:
        pass
    else:
        raise AssertionError("duplicate retry should be rejected")
    resources.execute_retry(repository, task_id, resource_id)

    repository.update_task(task_id, status=TaskStatus.running.value)
    set_asset_failed(repository, task_id, resource_id)

    listing = resources.list_failed_resources(repository, task_id)
    assert listing is not None
    assert listing.resources[0].retryable is False
    assert "生成中" in (listing.resources[0].retry_blocked_reason or "")
    try:
        resources.submit_retry(repository, task_id, resource_id)
    except resources.RetryNotAllowed:
        pass
    else:
        raise AssertionError("retry should be blocked while the task is running")


def test_failed_resource_list_reports_retrying_state(tmp_path, monkeypatch) -> None:
    repository = make_repository(tmp_path)
    task_id, resource_id = create_lecture_task_with_failed_image(repository)
    monkeypatch.setattr(resources, "get_image_generation_service", lambda: FakeImageService())

    resources.submit_retry(repository, task_id, resource_id)

    listing = resources.list_failed_resources(repository, task_id)
    assert listing is not None
    assert len(listing.resources) == 1
    item = listing.resources[0]
    assert item.status == "retrying"
    assert item.retryable is False
    assert item.retry_blocked_reason == "该资源正在重试。"
    assert item.resource_key == "img_001"
    resources.execute_retry(repository, task_id, resource_id)


def test_retry_rejects_resource_without_parameters(tmp_path) -> None:
    repository = make_repository(tmp_path)
    created = repository.create_task(
        ContentGenerationRequest(content_type="lecture", topic="Old task", user_prompt="Generate")
    )
    repository.update_task(created.task_id, status=TaskStatus.completed.value)
    with Session(repository.engine) as session:
        AssetRepository(session).upsert(
            created.task_id,
            AssetRegistration(
                asset_id=f"{created.task_id}:img_legacy",
                asset_type="image",
                uri="/api/assets/img_legacy_placeholder/download",
                status=AssetStatus.failed.value,
                error_message="legacy failure",
                metadata={"base_asset_id": "img_legacy", "title": "Legacy"},
            ),
        )
        session.commit()

    listing = resources.list_failed_resources(repository, created.task_id)
    assert listing is not None
    assert listing.resources[0].retryable is False
    assert "缺少生成描述" in (listing.resources[0].retry_blocked_reason or "")
    try:
        resources.submit_retry(repository, created.task_id, listing.resources[0].resource_id)
    except resources.RetryNotAllowed:
        pass
    else:
        raise AssertionError("legacy resource without parameters must not be retryable")


def test_retry_social_post_slot_refreshes_content_and_preview(tmp_path, monkeypatch) -> None:
    from app.generators.social_post_generator import SocialPostGenerator

    repository = make_repository(tmp_path)
    created = repository.create_task(
        ContentGenerationRequest(content_type="social_post", topic="Agent design", user_prompt="Write")
    )
    base_state = ContentGenerationState(
        request_id=created.task_id,
        content_type="social_post",
        topic="Agent design",
        user_prompt="Write",
        status=TaskStatus.running,
        raw_request={},
    )
    spec = SocialPostGenerator().generate(base_state)
    failed_slot = spec.image_slots[0]
    base_asset_id = f"{spec.id}_{failed_slot.slot_id}"
    spec = spec.model_copy(
        update={
            "image_assets": [
                asset.model_copy(
                    update={
                        "status": "generated",
                        "public_url": f"/api/assets/{base_asset_id}_placeholder/download",
                        "error_message": "fallback placeholder (quota)",
                    }
                )
                if asset.slot_id == failed_slot.slot_id
                else asset
                for asset in spec.image_assets
            ],
            "metadata": {**spec.metadata, "image_fallbacks": {failed_slot.slot_id: "quota"}},
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
    repository.save_state(created.task_id, state)
    listing = resources.list_failed_resources(repository, created.task_id)
    assert listing is not None
    assert len(listing.resources) == 1
    monkeypatch.setattr(resources, "get_image_generation_service", lambda: FakeImageService())

    resources.submit_retry(repository, created.task_id, listing.resources[0].resource_id)
    resources.execute_retry(repository, created.task_id, listing.resources[0].resource_id)

    spec_artifact = repository.get_latest_artifact(created.task_id, "content_spec")
    assert spec_artifact is not None
    updated_spec = SocialPostSpec.model_validate(spec_artifact.payload)
    updated_asset = next(asset for asset in updated_spec.image_assets if asset.slot_id == failed_slot.slot_id)
    assert "r1" in (updated_asset.public_url or "")
    assert "image_fallbacks" not in updated_spec.metadata

    preview = PersistentTaskService(repository=repository).get_preview(created.task_id)
    assert preview is not None
    preview_asset = next(asset for asset in preview.render_model.preview_assets if asset.slot_id == failed_slot.slot_id)
    assert "r1" in (preview_asset.public_url or "")
    remaining = resources.list_failed_resources(repository, created.task_id)
    assert remaining is not None
    assert remaining.resources == []


def test_retry_podcast_segment_reassembles_audio(tmp_path, monkeypatch) -> None:
    repository = make_repository(tmp_path)
    task_id, resource_id = create_podcast_task_with_failed_segment(repository)
    fake_tts = FakeTTSService()
    monkeypatch.setattr(resources, "get_tts_service", lambda: fake_tts)

    resources.submit_retry(repository, task_id, resource_id)
    resources.execute_retry(repository, task_id, resource_id)

    assert fake_tts.calls[0]["text"] == "hi"
    assert fake_tts.calls[0]["voice"] == "Cherry"
    preview = PersistentTaskService(repository=repository).get_preview(task_id)
    assert preview is not None
    assert preview.render_model.final_audio_url
    segments = {segment.segment_id: segment for segment in preview.render_model.segments}
    assert segments["seg_002"].status == "generated"
    assert segments["seg_002"].retry_count == 2
    assert "r2" in (segments["seg_002"].audio_url or "")
    export_types = [file.file_type for file in preview.render_model.export_files]
    assert "audio" in export_types
    task = repository.get_task(task_id)
    assert task is not None
    assert task.progress["resource_summary"] == {"total": 2, "failed": 0, "retrying": 0}


def test_failed_resource_endpoints(tmp_path, monkeypatch) -> None:
    repository = make_repository(tmp_path)
    service = PersistentTaskService(repository=repository)
    monkeypatch.setattr("app.api.content_generation.task_service", service)
    monkeypatch.setattr(resources, "get_image_generation_service", lambda: FakeImageService())
    task_id, resource_id = create_lecture_task_with_failed_image(repository)
    client = TestClient(app)

    listing = client.get(f"/api/content-generation/tasks/{task_id}/failed-resources")
    assert listing.status_code == 200
    payload = listing.json()
    assert payload["task_id"] == task_id
    assert payload["resources"][0]["resource_id"] == resource_id
    assert payload["resources"][0]["retryable"] is True
    assert payload["resources"][0]["asset_type"] == "image"

    retry = client.post(f"/api/content-generation/tasks/{task_id}/resources/{resource_id}/retry")
    assert retry.status_code == 202
    assert retry.json()["status"] == "retrying"

    after = client.get(f"/api/content-generation/tasks/{task_id}/failed-resources")
    assert after.status_code == 200
    assert after.json()["resources"] == []
    preview = client.get(f"/api/content-generation/tasks/{task_id}/preview")
    assert preview.status_code == 200
    blocks = {
        block["id"]: block
        for section in preview.json()["render_model"]["sections"]
        for block in section["render_blocks"]
    }
    assert "r1" in blocks["img_001"]["asset_url"]

    missing_task = client.get("/api/content-generation/tasks/task_missing/failed-resources")
    assert missing_task.status_code == 404
    missing_resource = client.post(
        f"/api/content-generation/tasks/{task_id}/resources/resource_missing/retry"
    )
    assert missing_resource.status_code == 404
