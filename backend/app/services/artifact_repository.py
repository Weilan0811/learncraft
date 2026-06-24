import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlmodel import Session, select

from app.models.content_generation_artifact import ContentGenerationArtifact
from app.models.content_generation_event import ContentGenerationEvent
from app.models.content_generation_metric import ContentGenerationMetric
from app.models.content_generation_reference import ContentGenerationReference
from app.schemas.observability import GenerationMetric


def _now() -> datetime:
    return datetime.now(UTC)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:24]}"


def _payload_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _content_hash(content: str | None) -> str | None:
    if not content:
        return None
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class ArtifactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_artifact(
        self,
        task_id: str,
        artifact_type: str,
        payload: dict[str, Any],
        unit_id: str | None = None,
        unit_order: int | None = None,
        status: str = "final",
        source_node: str | None = None,
        schema_name: str | None = None,
        schema_version: str | None = None,
    ) -> ContentGenerationArtifact:
        statement = (
            select(ContentGenerationArtifact)
            .where(ContentGenerationArtifact.task_id == task_id)
            .where(ContentGenerationArtifact.artifact_type == artifact_type)
        )
        if unit_id is None:
            statement = statement.where(ContentGenerationArtifact.unit_id.is_(None))
        else:
            statement = statement.where(ContentGenerationArtifact.unit_id == unit_id)
        artifact = self.session.exec(statement).first()
        now = _now()
        if artifact is None:
            artifact = ContentGenerationArtifact(
                id=_id("artifact"),
                task_id=task_id,
                artifact_type=artifact_type,
                unit_id=unit_id,
                unit_order=unit_order,
                status=status,
                schema_name=schema_name,
                schema_version=schema_version,
                payload=payload,
                payload_hash=_payload_hash(payload),
                source_node=source_node,
                created_at=now,
                updated_at=now,
            )
        else:
            artifact.version += 1
            artifact.unit_order = unit_order
            artifact.status = status
            artifact.schema_name = schema_name
            artifact.schema_version = schema_version
            artifact.payload = payload
            artifact.payload_hash = _payload_hash(payload)
            artifact.source_node = source_node
            artifact.updated_at = now
        self.session.add(artifact)
        return artifact

    def append_references(
        self,
        task_id: str,
        stage: str,
        chunks: list[object],
        artifact_id: str | None = None,
        unit_id: str | None = None,
        retrieval_query: str | None = None,
    ) -> list[ContentGenerationReference]:
        records: list[ContentGenerationReference] = []
        seen = {
            (row.stage, row.unit_id, row.chunk_id)
            for row in self.session.exec(select(ContentGenerationReference).where(ContentGenerationReference.task_id == task_id)).all()
        }
        for chunk in chunks:
            chunk_id = str(getattr(chunk, "id", ""))
            if not chunk_id or (stage, unit_id, chunk_id) in seen:
                continue
            metadata = dict(getattr(chunk, "metadata", {}) or {})
            content = str(getattr(chunk, "content", "") or "")
            record = ContentGenerationReference(
                id=_id("ref"),
                task_id=task_id,
                artifact_id=artifact_id,
                stage=stage,
                unit_id=unit_id,
                knowledge_base_id=metadata.get("knowledge_base_id") if isinstance(metadata.get("knowledge_base_id"), str) else None,
                chunk_id=chunk_id,
                source_id=str(getattr(chunk, "source_id", "") or "") or None,
                source_title=str(getattr(chunk, "source_title", "") or "") or None,
                score=getattr(chunk, "score", None),
                retrieval_query=retrieval_query,
                content_excerpt=content[:1000] if content else None,
                content_hash=_content_hash(content),
                metadata_json=metadata,
            )
            self.session.add(record)
            records.append(record)
            seen.add((stage, unit_id, chunk_id))
        return records

    def append_event(self, task_id: str, event: dict[str, Any]) -> ContentGenerationEvent:
        record = ContentGenerationEvent(
            id=str(event.get("event_id") or _id("event")),
            task_id=task_id,
            event_type=str(event.get("type") or event.get("event_type") or "workflow_event"),
            node=str(event.get("node")) if event.get("node") else None,
            unit_id=str(event.get("unit_id")) if event.get("unit_id") else None,
            payload=dict(event.get("payload") or {}),
        )
        self.session.merge(record)
        return record

    def append_metric(self, task_id: str, metric: dict[str, Any] | GenerationMetric) -> ContentGenerationMetric:
        data = metric.model_dump(mode="json") if isinstance(metric, GenerationMetric) else dict(metric)
        metadata = dict(data.get("metadata") or {})
        stream_index = metadata.get("stream_index")
        if stream_index is not None:
            existing = self.session.exec(select(ContentGenerationMetric).where(ContentGenerationMetric.task_id == task_id)).all()
            for row in existing:
                if row.metadata_json.get("stream_index") == stream_index:
                    return row
        record = ContentGenerationMetric(
            id=_id("metric"),
            task_id=task_id,
            node=str(data.get("node") or "unknown"),
            unit_id=str(data.get("unit_id")) if data.get("unit_id") else None,
            provider=str(data.get("provider")) if data.get("provider") else None,
            model=str(data.get("model")) if data.get("model") else None,
            duration_ms=data.get("duration_ms") if isinstance(data.get("duration_ms"), int) else None,
            prompt_tokens=data.get("prompt_tokens") if isinstance(data.get("prompt_tokens"), int) else None,
            completion_tokens=data.get("completion_tokens") if isinstance(data.get("completion_tokens"), int) else None,
            total_tokens=data.get("total_tokens") if isinstance(data.get("total_tokens"), int) else None,
            retry_count=int(data.get("retry_count") or 0),
            fallback_used=bool(data.get("fallback_used")),
            fallback_reason=str(data.get("fallback_reason")) if data.get("fallback_reason") else None,
            error_type=str(data.get("error_type")) if data.get("error_type") else None,
            metadata_json=metadata,
        )
        self.session.add(record)
        return record

    def get_latest_artifact(
        self, task_id: str, artifact_type: str, unit_id: str | None = None
    ) -> ContentGenerationArtifact | None:
        statement = (
            select(ContentGenerationArtifact)
            .where(ContentGenerationArtifact.task_id == task_id)
            .where(ContentGenerationArtifact.artifact_type == artifact_type)
            .order_by(ContentGenerationArtifact.updated_at.desc())
        )
        if unit_id is None:
            statement = statement.where(ContentGenerationArtifact.unit_id.is_(None))
        else:
            statement = statement.where(ContentGenerationArtifact.unit_id == unit_id)
        return self.session.exec(statement).first()
