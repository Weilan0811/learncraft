import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlmodel import Session, select

from app.models.content_generation_artifact import ContentGenerationArtifact
from app.models.content_generation_reference import ContentGenerationReference
from app.models.knowledge_chunk_cache import KnowledgeChunkCache


def _now() -> datetime:
    return datetime.now(UTC)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:24]}"


def normalize_knowledge_text(text: str) -> str:
    return text.strip().replace("\r\n", "\n")


def make_chunk_id(text: str) -> str:
    normalized = normalize_knowledge_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def make_reference_id(task_id: str, unit_id: str | None, chunk_id: str, source_path: str) -> str:
    raw = "|".join([task_id, unit_id or "", chunk_id, source_path])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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
        del unit_order, status, source_node, schema_name, schema_version
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
                artifact_id=_id("artifact"),
                task_id=task_id,
                artifact_type=artifact_type,
                unit_id=unit_id,
                version=1,
                payload=payload,
                created_at=now,
                updated_at=now,
            )
        else:
            artifact.version += 1
            artifact.payload = payload
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
        del stage, artifact_id, retrieval_query
        records: list[ContentGenerationReference] = []
        for rank, chunk in enumerate(chunks, start=1):
            record = self.upsert_reference(task_id=task_id, unit_id=unit_id, item=chunk, rank=rank)
            if record is not None:
                records.append(record)
        return records

    def upsert_reference(
        self,
        *,
        task_id: str,
        unit_id: str | None,
        item: object,
        rank: int | None = None,
    ) -> ContentGenerationReference | None:
        content = _item_text(item)
        if not content:
            return None
        normalized = normalize_knowledge_text(content)
        if not normalized:
            return None
        metadata = dict(getattr(item, "metadata", {}) or {})
        source_path = _first_string(metadata.get("path"), getattr(item, "source_id", None), getattr(item, "id", None), "unknown")
        source_title = _first_string(metadata.get("title"), getattr(item, "source_title", None), None)
        score = getattr(item, "score", None)
        chunk_id = make_chunk_id(normalized)
        now = _now()

        cache = self.session.get(KnowledgeChunkCache, chunk_id)
        if cache is None:
            cache = KnowledgeChunkCache(chunk_id=chunk_id, text=normalized, created_at=now, last_seen_at=now)
        else:
            cache.last_seen_at = now
        self.session.add(cache)

        reference_id = make_reference_id(task_id, unit_id, chunk_id, source_path)
        reference = self.session.get(ContentGenerationReference, reference_id)
        if reference is None:
            reference = ContentGenerationReference(
                reference_id=reference_id,
                task_id=task_id,
                unit_id=unit_id,
                chunk_id=chunk_id,
                source_path=source_path,
                source_title=source_title,
                rank=rank,
                score=score,
                created_at=now,
            )
        else:
            reference.rank = rank
            reference.score = score
        self.session.add(reference)
        return reference

    def get_latest_artifact(
        self, task_id: str, artifact_type: str, unit_id: str | None = None
    ) -> ContentGenerationArtifact | None:
        statement = (
            select(ContentGenerationArtifact)
            .where(ContentGenerationArtifact.task_id == task_id)
            .where(ContentGenerationArtifact.artifact_type == artifact_type)
            .order_by(ContentGenerationArtifact.version.desc(), ContentGenerationArtifact.updated_at.desc())
        )
        if unit_id is None:
            statement = statement.where(ContentGenerationArtifact.unit_id.is_(None))
        else:
            statement = statement.where(ContentGenerationArtifact.unit_id == unit_id)
        return self.session.exec(statement).first()


def _item_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("text") or item.get("content") or "")
    return str(getattr(item, "text", None) or getattr(item, "content", None) or "")


def _first_string(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return ""
