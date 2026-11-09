from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, update
from sqlmodel import Session, select

from app.core.asset import AssetStatus
from app.models.content_generation_asset import ContentGenerationAsset
from app.schemas.render import PodcastRenderModel
from app.schemas.specs import PodcastSpec, SocialPostSpec
from app.schemas.state import ContentGenerationState


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class AssetRegistration:
    """A generated resource derived from the workflow state."""

    asset_id: str
    asset_type: str
    uri: str
    status: str
    unit_id: str | None = None
    mime_type: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class AssetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, task_id: str, registration: AssetRegistration) -> ContentGenerationAsset:
        row = self.session.get(ContentGenerationAsset, registration.asset_id)
        now = _now()
        if row is None:
            row = ContentGenerationAsset(
                asset_id=registration.asset_id,
                task_id=task_id,
                unit_id=registration.unit_id,
                asset_type=registration.asset_type,
                uri=registration.uri,
                mime_type=registration.mime_type,
                status=registration.status,
                error_message=registration.error_message,
                retry_count=registration.retry_count,
                metadata_json=dict(registration.metadata),
                created_at=now,
                updated_at=now,
            )
        elif row.status != AssetStatus.retrying.value:
            row.unit_id = registration.unit_id
            row.asset_type = registration.asset_type
            row.uri = registration.uri
            row.mime_type = registration.mime_type
            row.status = registration.status
            row.error_message = registration.error_message
            row.retry_count = max(row.retry_count or 0, registration.retry_count)
            row.metadata_json = {**(row.metadata_json or {}), **registration.metadata}
            row.updated_at = now
        self.session.add(row)
        return row

    def get(self, task_id: str, asset_id: str) -> ContentGenerationAsset | None:
        row = self.session.get(ContentGenerationAsset, asset_id)
        if row is None or row.task_id != task_id:
            return None
        return row

    def list_assets(
        self,
        task_id: str,
        *,
        statuses: set[str] | None = None,
    ) -> list[ContentGenerationAsset]:
        statement = select(ContentGenerationAsset).where(ContentGenerationAsset.task_id == task_id)
        if statuses:
            statement = statement.where(ContentGenerationAsset.status.in_(sorted(statuses)))
        statement = statement.order_by(ContentGenerationAsset.created_at, ContentGenerationAsset.asset_id)
        return list(self.session.exec(statement).all())

    def summary(self, task_id: str) -> dict[str, int]:
        rows = self.session.execute(
            select(ContentGenerationAsset.status, func.count(ContentGenerationAsset.asset_id))
            .where(ContentGenerationAsset.task_id == task_id)
            .group_by(ContentGenerationAsset.status)
        ).all()
        counts = {str(status): int(count) for status, count in rows}
        return {
            "total": sum(counts.values()),
            "failed": counts.get(AssetStatus.failed.value, 0) + counts.get(AssetStatus.missing.value, 0),
            "retrying": counts.get(AssetStatus.retrying.value, 0),
        }

    def mark_retrying(self, task_id: str, asset_id: str) -> bool:
        result = self.session.execute(
            update(ContentGenerationAsset)
            .where(ContentGenerationAsset.task_id == task_id)
            .where(ContentGenerationAsset.asset_id == asset_id)
            .where(
                ContentGenerationAsset.status.in_(
                    [AssetStatus.failed.value, AssetStatus.missing.value]
                )
            )
            .values(status=AssetStatus.retrying.value, updated_at=_now())
        )
        return bool(result.rowcount)

    def count_retrying(self, task_id: str) -> int:
        return int(
            self.session.execute(
                select(func.count(ContentGenerationAsset.asset_id))
                .where(ContentGenerationAsset.task_id == task_id)
                .where(ContentGenerationAsset.status == AssetStatus.retrying.value)
            ).scalar_one()
        )


def make_resource_id(task_id: str, base_asset_id: str) -> str:
    """Return a task-scoped primary key that fits the 64 character column."""
    raw = f"{task_id}:{base_asset_id}"
    if len(raw) <= 64:
        return raw
    digest = hashlib.sha1(base_asset_id.encode("utf-8")).hexdigest()[:24]
    return f"{task_id}:{digest}"


def collect_state_assets(task_id: str, state: ContentGenerationState) -> list[AssetRegistration]:
    """Derive retryable resources from the generation state.

    Registration happens here instead of inside workflow nodes so every path
    (unit images, social-post slots, podcast segments) is described by the same
    state snapshot that the repository already persists.
    """
    if isinstance(state.content_spec, SocialPostSpec):
        return _social_post_assets(task_id, state.content_spec)
    if isinstance(state.content_spec, PodcastSpec):
        return _podcast_assets(task_id, state.content_spec, state.render_model)
    return _element_assets(task_id, state)


def _social_post_assets(task_id: str, spec: SocialPostSpec) -> list[AssetRegistration]:
    slots = {slot.slot_id: slot for slot in spec.image_slots}
    raw_fallbacks = spec.metadata.get("image_fallbacks")
    fallback_errors = raw_fallbacks if isinstance(raw_fallbacks, dict) else {}
    registrations: list[AssetRegistration] = []
    for asset in spec.image_assets:
        slot = slots.get(asset.slot_id)
        if slot is None:
            continue
        base_asset_id = f"{spec.id}_{asset.slot_id}"
        placeholder = (asset.error_message or "").startswith("fallback placeholder")
        failed = asset.slot_id in fallback_errors or placeholder or asset.status == "failed"
        if failed:
            status = AssetStatus.failed.value
        elif asset.status in {"generated", "uploaded"}:
            status = AssetStatus.generated.value
        else:
            status = AssetStatus.pending.value
        if failed:
            error_message = str(fallback_errors.get(asset.slot_id) or asset.error_message or "图片生成失败")
        else:
            error_message = None
        width = asset.width if isinstance(asset.width, int) else None
        height = asset.height if isinstance(asset.height, int) else None
        registrations.append(
            AssetRegistration(
                asset_id=make_resource_id(task_id, base_asset_id),
                asset_type="image",
                uri=asset.public_url or asset.local_path or asset.wechat_url or "",
                status=status,
                error_message=error_message,
                metadata={
                    "content_type": "social_post",
                    "base_asset_id": base_asset_id,
                    "slot_id": asset.slot_id,
                    "target_path": slot.target_path,
                    "title": slot.caption,
                    "description": slot.prompt_en,
                    "aspect_ratio": _provider_aspect_ratio(slot.aspect_ratio),
                    "layout": "image_text",
                    "visual_type": slot.visual_type,
                    "purpose": slot.purpose,
                    "context_summary": slot.context_summary,
                    "width": width,
                    "height": height,
                },
            )
        )
    return registrations


def _podcast_assets(
    task_id: str,
    spec: PodcastSpec,
    render_model: object,
) -> list[AssetRegistration]:
    if not isinstance(render_model, PodcastRenderModel):
        return []
    registrations: list[AssetRegistration] = []
    for segment in render_model.segments:
        base_asset_id = f"{spec.id}_{segment.order:03d}"
        if segment.status == "generated":
            status = AssetStatus.generated.value
        elif segment.status == "failed":
            status = AssetStatus.failed.value
        else:
            status = AssetStatus.pending.value
        registrations.append(
            AssetRegistration(
                asset_id=make_resource_id(task_id, base_asset_id),
                asset_type="audio",
                uri=segment.audio_url or "",
                status=status,
                error_message=segment.error_message,
                retry_count=segment.retry_count,
                metadata={
                    "content_type": "podcast_script",
                    "base_asset_id": base_asset_id,
                    "segment_id": segment.segment_id,
                    "order": segment.order,
                    "speaker": segment.speaker,
                    "voice": segment.voice,
                    "text": segment.text,
                    "title": f"第 {segment.order} 段 · {segment.speaker}",
                },
            )
        )
    return registrations


def _element_assets(task_id: str, state: ContentGenerationState) -> list[AssetRegistration]:
    elements = {element.id: element for element in state.elements}
    registrations: dict[str, AssetRegistration] = {}
    for unit_id, result in state.unit_results.items():
        for request in result.element_requests.values():
            if request.type != "image":
                continue
            element = elements.get(request.element_id)
            if element is None:
                continue
            fallback = bool(element.metadata.get("fallback"))
            if fallback or element.status == "failed":
                status = AssetStatus.failed.value
            elif element.status == "completed":
                status = AssetStatus.generated.value
            else:
                status = AssetStatus.pending.value
            error_message = element.metadata.get("reason") if (fallback or element.status == "failed") else None
            file_format = element.format or ""
            mime_type = "image/svg+xml" if file_format == "svg" else (f"image/{file_format}" if file_format else None)
            base_asset_id = element.id
            registrations[base_asset_id] = AssetRegistration(
                asset_id=make_resource_id(task_id, base_asset_id),
                asset_type="image",
                uri=element.asset_url,
                unit_id=request.source_outline_unit_id or request.source_unit_id or unit_id,
                mime_type=mime_type,
                status=status,
                error_message=str(error_message) if error_message else None,
                retry_count=element.retry_count,
                metadata={
                    "content_type": state.content_type,
                    "base_asset_id": base_asset_id,
                    "element_id": element.id,
                    "title": request.title,
                    "description": element.prompt or request.instruction,
                    "instruction": request.instruction,
                    "purpose": request.purpose,
                    "aspect_ratio": str(request.constraints.get("aspect_ratio", "16:9")),
                    "layout": str(request.context.get("layout", "image_text")),
                    "style": request.constraints.get("style"),
                    "format": element.format,
                    "width": element.width,
                    "height": element.height,
                    "model": element.model,
                },
            )
    return list(registrations.values())


def sync_assets_from_state(session: Session, task_id: str, state: ContentGenerationState) -> dict[str, int]:
    """Upsert every resource carried by the state and return the task summary."""
    repository = AssetRepository(session)
    for registration in collect_state_assets(task_id, state):
        repository.upsert(task_id, registration)
    return repository.summary(task_id)


def _provider_aspect_ratio(aspect_ratio: str) -> str:
    if aspect_ratio == "2.35:1":
        return "21:9"
    return aspect_ratio


__all__ = [
    "AssetRegistration",
    "AssetRepository",
    "collect_state_assets",
    "make_resource_id",
    "sync_assets_from_state",
]
