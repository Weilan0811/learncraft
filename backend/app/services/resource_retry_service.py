from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session

from app.core.asset import AssetStatus
from app.core.provider_config import redact_secrets
from app.core.task import TaskStatus
from app.models.content_generation_asset import ContentGenerationAsset
from app.models.content_generation_task import ContentGenerationTask
from app.renderers.social_post_renderer import SocialPostRenderer
from app.schemas.elements import AudioFileElement
from app.schemas.render import PodcastExportFile, PodcastRenderModel
from app.schemas.resources import FailedResourceListResponse, ResourceRetryResponse, TaskResource
from app.schemas.specs import ImageAsset, SocialPostSpec
from app.services.artifact_repository import ArtifactRepository
from app.services.asset_repository import AssetRepository
from app.services.audio_assembler_service import AudioAssemblerService
from app.services.image_generation_service import get_image_generation_service
from app.services.storage_service import LocalStorageService
from app.services.task_repository import SQLModelTaskRepository, now_utc
from app.services.tts_service import get_tts_service


RETRYABLE_TASK_STATUSES = {
    TaskStatus.completed.value,
    TaskStatus.failed.value,
    TaskStatus.interrupted.value,
}
RETRYABLE_ASSET_STATUSES = {AssetStatus.failed.value, AssetStatus.missing.value}


class ResourceNotFound(LookupError):
    pass


class RetryNotAllowed(RuntimeError):
    pass


class RetryConflict(RuntimeError):
    pass


@dataclass
class ImageRetryResult:
    asset_id: str
    url: str
    format: str | None = None
    width: int | None = None
    height: int | None = None
    provider: str | None = None
    model: str | None = None


@dataclass
class AudioRetryResult:
    asset_id: str
    url: str
    format: str = "mp3"
    byte_size: int | None = None


def list_failed_resources(
    repository: SQLModelTaskRepository,
    task_id: str,
) -> FailedResourceListResponse | None:
    with Session(repository.engine) as session:
        task = session.get(ContentGenerationTask, task_id)
        if task is None:
            return None
        assets = AssetRepository(session).list_assets(task_id, statuses=RETRYABLE_ASSET_STATUSES)
        return FailedResourceListResponse(
            task_id=task_id,
            resources=[_to_resource(task, asset) for asset in assets],
        )


def submit_retry(
    repository: SQLModelTaskRepository,
    task_id: str,
    resource_id: str,
) -> ResourceRetryResponse:
    with Session(repository.engine) as session:
        task = session.get(ContentGenerationTask, task_id)
        if task is None:
            raise ResourceNotFound("Task not found")
        assets = AssetRepository(session)
        asset = assets.get(task_id, resource_id)
        if asset is None:
            raise ResourceNotFound("Resource not found")
        if asset.status not in RETRYABLE_ASSET_STATUSES:
            raise RetryConflict("该资源当前不是失败状态，无需重试。")
        blocked_reason = _blocked_reason(task, asset)
        if blocked_reason is not None:
            raise RetryNotAllowed(blocked_reason)
        if assets.count_retrying(task_id) > 0:
            raise RetryConflict("该任务已有资源正在重试，请稍后再试。")
        if not assets.mark_retrying(task_id, resource_id):
            raise RetryConflict("资源状态已变化，请刷新后重试。")
        session.commit()
        retry_count = int(asset.retry_count or 0)
    return ResourceRetryResponse(task_id=task_id, resource_id=resource_id, retry_count=retry_count)


def execute_retry(repository: SQLModelTaskRepository, task_id: str, resource_id: str) -> None:
    """Run one resource retry in the background and persist the outcome."""
    with Session(repository.engine) as session:
        asset = AssetRepository(session).get(task_id, resource_id)
        if asset is None or asset.status != AssetStatus.retrying.value:
            return
        asset_type = asset.asset_type
        metadata = dict(asset.metadata_json or {})
        retry_count = int(asset.retry_count or 0) + 1

    base_asset_id = str(metadata.get("base_asset_id") or resource_id)
    new_asset_id = f"{base_asset_id}_r{retry_count}"
    try:
        if asset_type == "image":
            result: ImageRetryResult | AudioRetryResult = _generate_image(metadata, new_asset_id)
        elif asset_type == "audio":
            result = _generate_audio(metadata, new_asset_id)
        else:
            raise RuntimeError(f"Unsupported resource type: {asset_type}")
    except Exception as exc:
        _mark_failed(repository, task_id, resource_id, retry_count, str(exc))
        return

    _apply_success(repository, task_id, resource_id, retry_count, asset_type, metadata, result)


def _generate_image(metadata: dict[str, Any], asset_id: str) -> ImageRetryResult:
    image = get_image_generation_service().generate_image(
        title=str(metadata.get("title") or ""),
        description=str(metadata.get("description") or ""),
        aspect_ratio=str(metadata.get("aspect_ratio") or "16:9"),
        asset_id=asset_id,
        layout=str(metadata.get("layout") or "image_text"),
    )
    return ImageRetryResult(
        asset_id=asset_id,
        url=image.asset_url,
        format=image.format,
        width=image.width if isinstance(image.width, int) else None,
        height=image.height if isinstance(image.height, int) else None,
        provider=str(image.metadata.get("provider")) if image.metadata.get("provider") else None,
        model=image.model or str(image.metadata.get("model") or "") or None,
    )


def _generate_audio(metadata: dict[str, Any], asset_id: str) -> AudioRetryResult:
    audio = get_tts_service().synthesize(
        text=str(metadata.get("text") or ""),
        voice=str(metadata.get("voice") or ""),
        asset_id=asset_id,
    )
    return AudioRetryResult(
        asset_id=asset_id,
        url=audio.audio_url,
        format=audio.format,
        byte_size=audio.byte_size,
    )


def _mark_failed(
    repository: SQLModelTaskRepository,
    task_id: str,
    resource_id: str,
    retry_count: int,
    message: str,
) -> None:
    with Session(repository.engine) as session:
        asset = AssetRepository(session).get(task_id, resource_id)
        if asset is None or asset.status != AssetStatus.retrying.value:
            return
        asset.status = AssetStatus.failed.value
        asset.error_message = redact_secrets(message)
        asset.retry_count = retry_count
        asset.updated_at = now_utc()
        session.add(asset)
        task = session.get(ContentGenerationTask, task_id)
        if task is not None:
            _refresh_summary(session, task)
        session.commit()


def _apply_success(
    repository: SQLModelTaskRepository,
    task_id: str,
    resource_id: str,
    retry_count: int,
    asset_type: str,
    metadata: dict[str, Any],
    result: ImageRetryResult | AudioRetryResult,
) -> None:
    with Session(repository.engine) as session:
        asset = AssetRepository(session).get(task_id, resource_id)
        task = session.get(ContentGenerationTask, task_id)
        if asset is None or task is None or asset.status != AssetStatus.retrying.value:
            return
        try:
            if asset_type == "image":
                assert isinstance(result, ImageRetryResult)
                _apply_image_retry(session, task, asset, metadata, result)
            elif asset_type == "audio":
                assert isinstance(result, AudioRetryResult)
                _apply_audio_retry(session, task, metadata, result, retry_count)
            asset.status = AssetStatus.generated.value
            asset.uri = result.url
            asset.mime_type = _image_mime(result.format) if isinstance(result, ImageRetryResult) else _audio_mime(result.format)
            asset.error_message = None
            asset.retry_count = retry_count
            asset.metadata_json = {
                **metadata,
                "latest_asset_id": result.asset_id,
                "path": result.url,
                **(
                    {"format": result.format, "width": result.width, "height": result.height}
                    if isinstance(result, ImageRetryResult)
                    else {"format": result.format}
                ),
            }
            asset.updated_at = now_utc()
            session.add(asset)
            _invalidate_exports(session, task)
            _refresh_summary(session, task)
            session.commit()
        except Exception as exc:
            session.rollback()
            _record_preview_failure(session, task_id, resource_id, retry_count, exc)


def _record_preview_failure(
    session: Session,
    task_id: str,
    resource_id: str,
    retry_count: int,
    exc: Exception,
) -> None:
    asset = session.get(ContentGenerationAsset, resource_id)
    if asset is None:
        return
    asset.status = AssetStatus.failed.value
    asset.error_message = redact_secrets(f"资源已生成，但更新预览失败：{exc}")
    asset.retry_count = retry_count
    asset.updated_at = now_utc()
    session.add(asset)
    task = session.get(ContentGenerationTask, task_id)
    if task is not None:
        _refresh_summary(session, task)
    session.commit()


def _apply_image_retry(
    session: Session,
    task: ContentGenerationTask,
    asset: ContentGenerationAsset,
    metadata: dict[str, Any],
    result: ImageRetryResult,
) -> None:
    artifacts = ArtifactRepository(session)
    base_asset_id = str(metadata.get("base_asset_id") or "")
    if task.content_type == "social_post":
        _refresh_social_post(task, artifacts, base_asset_id, str(metadata.get("slot_id") or ""), result)
        return
    targets: list[tuple[str, str | None]] = []
    if asset.unit_id:
        targets.append(("unit_render", asset.unit_id))
    targets.extend([("partial_render", None), ("final_render", None)])
    for artifact_type, unit_id in targets:
        artifact = artifacts.get_latest_artifact(task.task_id, artifact_type, unit_id)
        if artifact is None:
            continue
        payload = copy.deepcopy(artifact.payload)
        if _replace_image_reference(payload, base_asset_id, result):
            artifacts.upsert_artifact(task.task_id, artifact_type, payload, unit_id=unit_id)


def _replace_image_reference(payload: Any, base_asset_id: str, result: ImageRetryResult) -> bool:
    changed = False
    if isinstance(payload, dict):
        if payload.get("id") == base_asset_id and (
            "asset_url" in payload or "src" in payload
        ):
            if "asset_url" in payload:
                payload["asset_url"] = result.url
            if "src" in payload:
                payload["src"] = result.url
            block_metadata = payload.get("metadata")
            if isinstance(block_metadata, dict):
                block_metadata.pop("fallback", None)
                block_metadata.pop("reason", None)
                if result.width is not None:
                    block_metadata["width"] = result.width
                if result.height is not None:
                    block_metadata["height"] = result.height
                if result.format:
                    block_metadata["format"] = result.format
            changed = True
        for value in list(payload.values()):
            if _replace_image_reference(value, base_asset_id, result):
                changed = True
    elif isinstance(payload, list):
        for item in payload:
            if _replace_image_reference(item, base_asset_id, result):
                changed = True
    return changed


def _refresh_social_post(
    task: ContentGenerationTask,
    artifacts: ArtifactRepository,
    base_asset_id: str,
    slot_id: str,
    result: ImageRetryResult,
) -> None:
    spec_artifact = artifacts.get_latest_artifact(task.task_id, "content_spec")
    if spec_artifact is None:
        raise RuntimeError("内容规格缺失，无法更新推文图片。")
    spec = SocialPostSpec.model_validate(spec_artifact.payload)
    assets: list[ImageAsset] = []
    found = False
    for image in spec.image_assets:
        if image.slot_id == slot_id:
            found = True
            assets.append(
                image.model_copy(
                    update={
                        "status": "generated",
                        "public_url": result.url,
                        "local_path": result.url,
                        "error_message": None,
                        "width": result.width,
                        "height": result.height,
                    }
                )
            )
        else:
            assets.append(image)
    if not found:
        assets.append(
            ImageAsset(
                slot_id=slot_id,
                status="generated",
                public_url=result.url,
                local_path=result.url,
                width=result.width,
                height=result.height,
            )
        )
    spec_metadata = dict(spec.metadata)
    fallbacks = spec_metadata.get("image_fallbacks")
    if isinstance(fallbacks, dict):
        remaining = {key: value for key, value in fallbacks.items() if key != slot_id}
        if remaining:
            spec_metadata["image_fallbacks"] = remaining
        else:
            spec_metadata.pop("image_fallbacks", None)
    updated_spec = spec.model_copy(update={"image_assets": assets, "metadata": spec_metadata})
    artifacts.upsert_artifact(task.task_id, "content_spec", updated_spec.model_dump(mode="json"))
    render_model = SocialPostRenderer().render(updated_spec, [])
    payload = render_model.model_dump(mode="json")
    artifacts.upsert_artifact(
        task.task_id,
        "final_render",
        {"content_type": "social_post", "render_model": payload},
    )
    artifacts.upsert_artifact(task.task_id, "partial_render", payload)


def _apply_audio_retry(
    session: Session,
    task: ContentGenerationTask,
    metadata: dict[str, Any],
    result: AudioRetryResult,
    retry_count: int,
) -> None:
    artifacts = ArtifactRepository(session)
    artifact = artifacts.get_latest_artifact(task.task_id, "final_render")
    if artifact is None:
        raise RuntimeError("播客渲染结果缺失，无法更新音频。")
    payload = copy.deepcopy(artifact.payload)
    raw_model = payload.get("render_model") if isinstance(payload, dict) and isinstance(payload.get("render_model"), dict) else payload
    model = PodcastRenderModel.model_validate(raw_model)
    segment_id = str(metadata.get("segment_id") or "")
    order = int(metadata.get("order") or 0)
    segments = [
        segment.model_copy(
            update={
                "audio_url": result.url,
                "status": "generated",
                "error_message": None,
                "retry_count": retry_count,
            }
        )
        if segment.segment_id == segment_id
        else segment
        for segment in model.segments
    ]
    new_audio = AudioFileElement(
        id=result.asset_id,
        title=f"{metadata.get('voice') or 'voice'} audio",
        speaker=str(metadata.get("speaker") or "Person1"),
        voice=str(metadata.get("voice") or "Ethan"),
        audio_url=result.url,
        format=result.format,
        byte_size=result.byte_size,
        order=order,
    )
    audio_assets = sorted(
        [asset for asset in model.audio_assets if asset.order != order] + [new_audio],
        key=lambda asset: asset.order,
    )
    warnings = [warning for warning in model.warnings if not warning.startswith(segment_id)]
    export_files = [file for file in model.export_files if file.file_type != "audio"]
    final_audio_url: str | None = None
    if segments and all(segment.status == "generated" for segment in segments):
        try:
            record = AudioAssemblerService().assemble(
                asset_id=f"{_podcast_spec_id(metadata, task.task_id)}_final_audio",
                title=model.title,
                audio_assets=audio_assets,
                storage_service=LocalStorageService(),
            )
            if record is not None:
                final_audio_url = record.url
                export_files.insert(0, PodcastExportFile(file_type="audio", url=record.url, label="Full audio"))
        except Exception as exc:
            warnings.append(f"final audio assembly failed: {exc}")
    manifest = LocalStorageService().save_bytes(
        asset_id=f"{_podcast_spec_id(metadata, task.task_id)}_audio_manifest",
        filename=f"{_podcast_spec_id(metadata, task.task_id)}_audio_manifest.json",
        content=json.dumps(
            {
                "title": model.title,
                "podcast_name": model.podcast_name,
                "podcast_tagline": model.podcast_tagline,
                "final_audio_url": final_audio_url,
                "segments": [segment.model_dump(mode="json") for segment in segments],
            },
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8"),
        content_type="application/json",
        kind="audio",
        metadata={"content_type": "podcast_script", "render_type": "audio_manifest"},
    )
    updated = model.model_copy(
        update={
            "segments": segments,
            "audio_assets": audio_assets,
            "final_audio_url": final_audio_url,
            "audio_manifest_url": manifest.url,
            "export_files": export_files,
            "warnings": warnings,
        }
    )
    artifacts.upsert_artifact(
        task.task_id,
        "final_render",
        {"content_type": "podcast_script", "render_model": updated.model_dump(mode="json")},
    )
    artifacts.upsert_artifact(task.task_id, "partial_render", updated.model_dump(mode="json"))


def _podcast_spec_id(metadata: dict[str, Any], task_id: str) -> str:
    base_asset_id = str(metadata.get("base_asset_id") or "")
    if "_" in base_asset_id:
        return base_asset_id.rsplit("_", 1)[0]
    return f"podcast_{task_id}"


def _invalidate_exports(session: Session, task: ContentGenerationTask) -> None:
    progress = dict(task.progress or {})
    progress.pop("export_files", None)
    task.progress = progress
    manifest = ArtifactRepository(session).get_latest_artifact(task.task_id, "export_manifest")
    if manifest is not None:
        session.delete(manifest)
    session.add(task)


def _refresh_summary(session: Session, task: ContentGenerationTask) -> None:
    progress = dict(task.progress or {})
    progress["resource_summary"] = AssetRepository(session).summary(task.task_id)
    task.progress = progress
    task.updated_at = now_utc()
    session.add(task)


def _to_resource(task: ContentGenerationTask, asset: ContentGenerationAsset) -> TaskResource:
    metadata = asset.metadata_json or {}
    blocked_reason = _blocked_reason(task, asset)
    return TaskResource(
        resource_id=asset.asset_id,
        asset_type=asset.asset_type,
        status=asset.status,
        unit_id=asset.unit_id,
        title=str(metadata.get("title")) if metadata.get("title") else None,
        error_message=asset.error_message,
        retry_count=int(asset.retry_count or 0),
        retryable=blocked_reason is None,
        retry_blocked_reason=blocked_reason,
        updated_at=asset.updated_at,
    )


def _blocked_reason(task: ContentGenerationTask, asset: ContentGenerationAsset) -> str | None:
    if str(task.status) not in RETRYABLE_TASK_STATUSES:
        return "任务仍在生成中，暂时无法重试。"
    metadata = asset.metadata_json or {}
    if not metadata.get("base_asset_id"):
        return "该资源缺少重试所需的生成参数。"
    if asset.asset_type == "image":
        if not str(metadata.get("description") or "").strip():
            return "该图片缺少生成描述，无法重试。"
    elif asset.asset_type == "audio":
        if not str(metadata.get("text") or "").strip() or not metadata.get("voice"):
            return "该语音分段缺少文本或音色，无法重试。"
    else:
        return "不支持的资源类型。"
    return None


def _image_mime(file_format: str | None) -> str | None:
    if not file_format:
        return None
    if file_format == "svg":
        return "image/svg+xml"
    if file_format in {"jpg", "jpeg"}:
        return "image/jpeg"
    return f"image/{file_format}"


def _audio_mime(file_format: str | None) -> str | None:
    if file_format == "wav":
        return "audio/wav"
    if file_format:
        return "audio/mpeg"
    return None
