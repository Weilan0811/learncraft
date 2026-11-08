from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import ensure_sqlite_parent_directory, get_settings
from app.core.task import TaskStatus
from app.models import ContentGenerationArtifact, ContentGenerationReference, ContentGenerationTask, KnowledgeChunkCache
from app.schemas.export import ExportFile
from app.schemas.request import ContentGenerationRequest
from app.schemas.task import TaskResult
from app.schemas.state import ContentGenerationState
from app.services.artifact_repository import ArtifactRepository
from app.workflows.nodes.helpers import build_progress, ensure_monotonic_progress


def now_utc() -> datetime:
    return datetime.now(UTC)


class SQLModelTaskRepository:
    def __init__(self, database_url: str | None = None, echo: bool | None = None, create_tables: bool | None = None) -> None:
        settings = get_settings()
        resolved_url = database_url or settings.DATABASE_URL
        ensure_sqlite_parent_directory(resolved_url)
        self.engine = create_engine(
            resolved_url,
            echo=settings.db_log_echo if echo is None else echo,
            future=True,
        )
        if create_tables is None:
            create_tables = resolved_url.startswith("sqlite")
        if create_tables:
            SQLModel.metadata.create_all(self.engine)
            self._ensure_sqlite_schema()

    def create_task(
        self,
        request: ContentGenerationRequest,
        task_id: str | None = None,
        platform_context: dict[str, str | None] | None = None,
    ) -> ContentGenerationTask:
        platform_context = platform_context or {}
        task = ContentGenerationTask(
            task_id=task_id or f"task_{uuid4().hex[:12]}",
            platform_log_id=platform_context.get("platform_log_id"),
            platform_user_id=platform_context.get("platform_user_id"),
            platform_session_id=platform_context.get("platform_session_id"),
            content_type=request.content_type,
            topic=request.topic,
            status=TaskStatus.queued,
            progress=build_progress(stage="queued", current_node=None),
            request_payload=request.model_dump(mode="json"),
        )
        with Session(self.engine) as session:
            session.add(task)
            session.commit()
            session.refresh(task)
            return self._detach(session, task)

    def get_task(self, task_id: str) -> ContentGenerationTask | None:
        with Session(self.engine) as session:
            task = session.get(ContentGenerationTask, task_id)
            return self._detach(session, task)

    def mark_running(self, task_id: str) -> ContentGenerationTask | None:
        return self.update_task(
            task_id,
            status=TaskStatus.running,
            progress=build_progress(stage="running", current_node="run_task"),
            started_at=now_utc(),
        )

    def save_state(self, task_id: str, state: ContentGenerationState) -> ContentGenerationTask | None:
        task = self.get_task(task_id)
        progress = ensure_monotonic_progress(
            task.progress if task else {},
            state.progress or build_progress(stage=str(state.status), current_node=state.current_node),
        )
        if state.current_node:
            progress["current_node"] = state.current_node

        outline = state.outline.model_dump(mode="json") if state.outline else None
        render_model = state.render_model.model_dump(mode="json") if state.render_model else None
        content_spec = state.content_spec.model_dump(mode="json") if state.content_spec else None

        with Session(self.engine) as session:
            task_row = session.get(ContentGenerationTask, task_id)
            if task_row is None:
                return None

            artifacts = ArtifactRepository(session)
            if outline:
                artifacts.upsert_artifact(task_id, "outline", outline)
            if content_spec:
                artifacts.upsert_artifact(task_id, "content_spec", content_spec)
            if render_model:
                artifacts.upsert_artifact(
                    task_id,
                    "final_render",
                    {"content_type": task_row.content_type, "render_model": render_model},
                )
            self._save_unit_artifacts(artifacts, task_id, state)
            artifacts.append_references(task_id, "planning", state.planning_chunks)
            if state.current_unit_id and state.current_unit_context:
                artifacts.append_references(task_id, "unit_spec", state.current_unit_context, unit_id=state.current_unit_id)

            task_row.status = str(state.status)
            task_row.progress = progress
            task_row.error_message = state.errors[-1] if state.errors else None
            if state.status in {TaskStatus.completed, TaskStatus.failed}:
                task_row.completed_at = now_utc()
            task_row.updated_at = now_utc()
            session.add(task_row)
            session.commit()
            session.refresh(task_row)
            return self._detach(session, task_row)

    def save_unit_snapshot(self, task_id: str, state: ContentGenerationState) -> ContentGenerationTask | None:
        with Session(self.engine) as session:
            task_row = session.get(ContentGenerationTask, task_id)
            if task_row is None:
                return None

            progress = ensure_monotonic_progress(
                task_row.progress, state.progress or build_progress(stage=str(state.status), current_node=state.current_node)
            )
            if state.current_node:
                progress["current_node"] = state.current_node
            task_row.progress = progress
            task_row.error_message = state.errors[-1] if state.errors else None
            task_row.updated_at = now_utc()

            self._save_unit_artifacts(ArtifactRepository(session), task_id, state)
            session.add(task_row)
            session.commit()
            session.refresh(task_row)
            return self._detach(session, task_row)

    @staticmethod
    def _save_unit_artifacts(artifacts: ArtifactRepository, task_id: str, state: ContentGenerationState) -> None:
        if state.partial_render_model:
            artifacts.upsert_artifact(
                task_id, "partial_render", state.partial_render_model.model_dump(mode="json")
            )
        for unit_id, result in state.unit_results.items():
            unit_spec = result.unit_spec.model_dump(mode="json") if result.unit_spec else None
            if unit_spec:
                artifacts.upsert_artifact(
                    task_id, "unit_spec", unit_spec, unit_id=unit_id,
                )
        for unit_id, snapshot in state.render_units.items():
            artifacts.upsert_artifact(
                task_id, "unit_render", snapshot.model_dump(mode="json"), unit_id=unit_id,
            )
        for unit_id, chunks in state.unit_context_map.items():
            artifacts.append_references(task_id, "unit_spec", chunks, unit_id=unit_id)

    def append_references(
        self,
        task_id: str,
        chunks: list[object],
        *,
        unit_id: str | None = None,
    ) -> list[ContentGenerationReference]:
        with Session(self.engine) as session:
            records = ArtifactRepository(session).append_references(task_id, "reference", chunks, unit_id=unit_id)
            session.commit()
            for record in records:
                session.refresh(record)
                session.expunge(record)
            return records

    def update_export_files(self, task_id: str, export_files: list[ExportFile]) -> ContentGenerationTask | None:
        payload = {"files": [file.model_dump(mode="json") for file in export_files]}
        with Session(self.engine) as session:
            task = session.get(ContentGenerationTask, task_id)
            if task is None:
                return None
            ArtifactRepository(session).upsert_artifact(task_id, "export_manifest", payload)
            progress = dict(task.progress or {})
            progress["export_files"] = payload["files"]
            task.progress = progress
            task.updated_at = now_utc()
            session.add(task)
            session.commit()
            session.refresh(task)
            return self._detach(session, task)

    def update_task(self, task_id: str, **updates: object) -> ContentGenerationTask | None:
        with Session(self.engine) as session:
            task = session.get(ContentGenerationTask, task_id)
            if task is None:
                return None
            progress = dict(task.progress or {})
            for key, value in updates.items():
                if value is None:
                    continue
                if key == "current_node":
                    progress["current_node"] = value
                elif key == "errors":
                    errors = [str(item) for item in value] if isinstance(value, list) else [str(value)]
                    task.error_message = errors[-1] if errors else None
                elif key == "render_units" and isinstance(value, dict):
                    artifacts = ArtifactRepository(session)
                    for unit_id, snapshot in value.items():
                        if isinstance(snapshot, dict):
                            artifacts.upsert_artifact(task_id, "unit_render", snapshot, unit_id=str(unit_id))
                elif hasattr(task, key):
                    setattr(task, key, value)
            if progress:
                task.progress = progress
            task.updated_at = now_utc()
            session.add(task)
            session.commit()
            session.refresh(task)
            return self._detach(session, task)

    def list_artifacts(self, task_id: str) -> list[ContentGenerationArtifact]:
        with Session(self.engine) as session:
            rows = session.exec(select(ContentGenerationArtifact).where(ContentGenerationArtifact.task_id == task_id)).all()
            for row in rows:
                session.expunge(row)
            return list(rows)

    def get_artifact(self, task_id: str, artifact_id: str) -> ContentGenerationArtifact | None:
        with Session(self.engine) as session:
            artifact = session.exec(
                select(ContentGenerationArtifact)
                .where(ContentGenerationArtifact.task_id == task_id)
                .where(ContentGenerationArtifact.artifact_id == artifact_id)
            ).first()
            if artifact is not None:
                session.expunge(artifact)
            return artifact

    def list_references(
        self,
        task_id: str,
        *,
        stage: str | None = None,
        unit_id: str | None = None,
    ) -> list[ContentGenerationReference]:
        del stage
        with Session(self.engine) as session:
            statement = select(ContentGenerationReference).where(ContentGenerationReference.task_id == task_id)
            if unit_id is not None:
                statement = statement.where(ContentGenerationReference.unit_id == unit_id)
            statement = statement.order_by(ContentGenerationReference.unit_id, ContentGenerationReference.rank, ContentGenerationReference.created_at)
            rows = session.exec(statement).all()
            for row in rows:
                session.expunge(row)
            return list(rows)

    def get_reference_text(self, chunk_id: str) -> str:
        with Session(self.engine) as session:
            cache = session.get(KnowledgeChunkCache, chunk_id)
            return cache.text if cache else ""

    def list_cached_chunks(self) -> list[KnowledgeChunkCache]:
        with Session(self.engine) as session:
            rows = session.exec(select(KnowledgeChunkCache)).all()
            for row in rows:
                session.expunge(row)
            return list(rows)

    def list_events(self, task_id: str) -> list[object]:
        del task_id
        return []

    def list_metrics(self, task_id: str) -> list[object]:
        del task_id
        return []

    def get_latest_artifact(self, task_id: str, artifact_type: str, unit_id: str | None = None) -> ContentGenerationArtifact | None:
        with Session(self.engine) as session:
            artifact = ArtifactRepository(session).get_latest_artifact(task_id, artifact_type, unit_id)
            if artifact is not None:
                session.expunge(artifact)
            return artifact

    def _ensure_sqlite_schema(self) -> None:
        if self.engine.dialect.name != "sqlite":
            return
        inspector = inspect(self.engine)
        if not inspector.has_table("content_generation_task"):
            return
        columns = {column["name"] for column in inspector.get_columns("content_generation_task")}
        with self.engine.begin() as connection:
            if "error_message" not in columns:
                connection.execute(text("ALTER TABLE content_generation_task ADD COLUMN error_message TEXT"))

    def to_task_result(self, task: ContentGenerationTask) -> TaskResult:
        progress = dict(task.progress or {})
        export_files = [ExportFile.model_validate(file) for file in progress.get("export_files", []) if isinstance(file, dict)]
        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus(task.status),
            content_type=task.content_type,
            preview_url=f"/api/content-generation/tasks/{task.task_id}/preview" if task.status == TaskStatus.completed else None,
            export_files=export_files,
            errors=[task.error_message] if task.error_message else [],
            current_node=str(progress.get("current_node")) if progress.get("current_node") else None,
            progress=progress,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    @staticmethod
    def _detach(session: Session, task: ContentGenerationTask | None) -> ContentGenerationTask | None:
        if task is not None:
            session.expunge(task)
        return task


def collect_asset_ids_from_state(state: ContentGenerationState) -> list[str]:
    ids: list[str] = []
    for element in state.elements:
        if element.type in {"image", "audio_file"}:
            ids.append(element.id)
    if state.render_model and getattr(state.render_model, "audio_assets", None):
        ids.extend([element.id for element in state.render_model.audio_assets])
    return sorted(set(ids))


def collect_asset_ids_from_render_model_urls(urls: Iterable[str]) -> list[str]:
    ids: list[str] = []
    for url in urls:
        marker = "/api/assets/"
        if marker not in url:
            continue
        remainder = url.split(marker, 1)[1]
        asset_id = remainder.split("/", 1)[0]
        if asset_id:
            ids.append(asset_id)
    return sorted(set(ids))
