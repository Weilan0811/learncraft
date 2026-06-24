from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import get_settings
from app.core.task import TaskStatus
from app.models import (
    ContentGenerationArtifact,
    ContentGenerationEvent,
    ContentGenerationMetric,
    ContentGenerationReference,
    ContentGenerationTask,
)
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
            current_node=None,
            progress=build_progress(stage="queued", current_node=None),
            request_payload=request.model_dump(mode="json"),
            generation_options=request.generation_options.model_dump(mode="json"),
            errors=[],
        )
        with Session(self.engine) as session:
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    def get_task(self, task_id: str) -> ContentGenerationTask | None:
        with Session(self.engine) as session:
            task = session.exec(select(ContentGenerationTask).where(ContentGenerationTask.task_id == task_id)).first()
            return self._detach(session, task)

    def mark_running(self, task_id: str) -> ContentGenerationTask | None:
        return self.update_task(
            task_id,
            status=TaskStatus.running,
            current_node="run_task",
            progress=build_progress(stage="running", current_node="run_task"),
            started_at=now_utc(),
        )

    def save_state(self, task_id: str, state: ContentGenerationState) -> ContentGenerationTask | None:
        asset_ids = collect_asset_ids_from_state(state)
        task = self.get_task(task_id)
        progress = ensure_monotonic_progress(
            task.progress if task else {},
            state.progress or build_progress(stage=str(state.status), current_node=state.current_node),
        )
        outline = state.outline.model_dump(mode="json") if state.outline else None
        render_model = state.render_model.model_dump(mode="json") if state.render_model else None
        partial_render_model = state.partial_render_model.model_dump(mode="json") if state.partial_render_model else None
        content_spec = state.content_spec.model_dump(mode="json") if state.content_spec else None
        unit_results = {unit_id: result.model_dump(mode="json") for unit_id, result in state.unit_results.items()}
        render_units = {unit_id: snapshot.model_dump(mode="json") for unit_id, snapshot in state.render_units.items()}
        stream_events = [event.model_dump(mode="json") for event in state.stream_events]
        metrics = [metric.model_dump(mode="json") for metric in state.metrics]

        with Session(self.engine) as session:
            task_row = session.exec(select(ContentGenerationTask).where(ContentGenerationTask.task_id == task_id)).first()
            if task_row is None:
                return None
            task_row.status = str(state.status)
            task_row.current_node = state.current_node
            task_row.progress = progress
            task_row.outline = outline
            task_row.render_model = render_model
            task_row.partial_render_model = partial_render_model
            task_row.content_spec = content_spec
            task_row.unit_results = unit_results
            task_row.render_units = render_units
            task_row.stream_events = stream_events
            task_row.elements = [element.model_dump(mode="json") for element in state.elements]
            task_row.logs = [entry.model_dump(mode="json") for entry in state.logs]
            task_row.asset_ids = asset_ids
            task_row.errors = state.errors
            task_row.preview_url = f"/api/content-generation/tasks/{task_id}/preview" if render_model else task_row.preview_url
            task_row.error_summary = state.errors[-1][:1000] if state.errors else None
            if state.status in {TaskStatus.completed, TaskStatus.failed}:
                task_row.completed_at = now_utc()
            task_row.updated_at = now_utc()

            artifacts = ArtifactRepository(session)
            outline_artifact_id = None
            if outline:
                outline_artifact_id = artifacts.upsert_artifact(
                    task_id, "outline", outline, status="final", source_node="plan_outline", schema_name=type(state.outline).__name__
                ).id
            if content_spec:
                artifacts.upsert_artifact(
                    task_id, "content_spec", content_spec, status="final", source_node="assemble_content_spec", schema_name=type(state.content_spec).__name__
                )
            if partial_render_model:
                artifacts.upsert_artifact(
                    task_id, "partial_render", partial_render_model, status="partial", source_node=state.current_node
                )
            if render_model:
                artifacts.upsert_artifact(
                    task_id, "final_render", render_model, status="final", source_node=state.current_node, schema_name=type(state.render_model).__name__
                )
            for unit_id, result in unit_results.items():
                unit_spec = result.get("unit_spec")
                if isinstance(unit_spec, dict):
                    artifacts.upsert_artifact(
                        task_id,
                        "unit_spec",
                        unit_spec,
                        unit_id=unit_id,
                        unit_order=unit_spec.get("order") if isinstance(unit_spec.get("order"), int) else None,
                        status=str(result.get("status") or "final"),
                        source_node="generate_unit_spec",
                    )
            for unit_id, snapshot in render_units.items():
                artifacts.upsert_artifact(
                    task_id,
                    "unit_render",
                    snapshot,
                    unit_id=unit_id,
                    unit_order=snapshot.get("order") if isinstance(snapshot.get("order"), int) else None,
                    status=str(snapshot.get("status") or "rendered"),
                    source_node="render_unit",
                )
            artifacts.append_references(task_id, "planning", state.planning_chunks, artifact_id=outline_artifact_id)
            for unit_id, chunks in state.unit_context_map.items():
                artifacts.append_references(task_id, "unit_spec", chunks, unit_id=unit_id)
            if state.current_unit_id and state.current_unit_context:
                artifacts.append_references(task_id, "unit_spec", state.current_unit_context, unit_id=state.current_unit_id)
            for event in stream_events:
                artifacts.append_event(task_id, event)
            for metric in metrics:
                artifacts.append_metric(task_id, metric)

            session.add(task_row)
            session.commit()
            session.refresh(task_row)
            return self._detach(session, task_row)

    def update_export_files(self, task_id: str, export_files: list[ExportFile]) -> ContentGenerationTask | None:
        return self.update_task(task_id, export_files=[file.model_dump(mode="json") for file in export_files])

    def update_task(self, task_id: str, **updates: object) -> ContentGenerationTask | None:
        with Session(self.engine) as session:
            task = session.exec(select(ContentGenerationTask).where(ContentGenerationTask.task_id == task_id)).first()
            if task is None:
                return None
            for key, value in updates.items():
                if value is not None:
                    setattr(task, key, value)
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
                .where(ContentGenerationArtifact.id == artifact_id)
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
        with Session(self.engine) as session:
            statement = select(ContentGenerationReference).where(ContentGenerationReference.task_id == task_id)
            if stage is not None:
                statement = statement.where(ContentGenerationReference.stage == stage)
            if unit_id is not None:
                statement = statement.where(ContentGenerationReference.unit_id == unit_id)
            rows = session.exec(statement).all()
            for row in rows:
                session.expunge(row)
            return list(rows)

    def list_events(self, task_id: str) -> list[ContentGenerationEvent]:
        with Session(self.engine) as session:
            rows = session.exec(select(ContentGenerationEvent).where(ContentGenerationEvent.task_id == task_id)).all()
            for row in rows:
                session.expunge(row)
            return list(rows)

    def list_metrics(self, task_id: str) -> list[ContentGenerationMetric]:
        with Session(self.engine) as session:
            rows = session.exec(select(ContentGenerationMetric).where(ContentGenerationMetric.task_id == task_id)).all()
            for row in rows:
                session.expunge(row)
            return list(rows)

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
        missing_defaults = {
            "unit_results": "{}",
            "render_units": "{}",
            "stream_events": "[]",
            "logs": "[]",
            "generation_options": "{}",
        }
        with self.engine.begin() as connection:
            string_columns = {
                "platform_log_id": "VARCHAR(64)",
                "platform_user_id": "VARCHAR(64)",
                "platform_session_id": "VARCHAR(64)",
                "topic": "VARCHAR(255)",
                "preview_url": "VARCHAR(512)",
                "error_summary": "VARCHAR(1000)",
            }
            for column_name, column_type in string_columns.items():
                if column_name not in columns:
                    connection.execute(text(f"ALTER TABLE content_generation_task ADD COLUMN {column_name} {column_type}"))
            if "outline" not in columns:
                connection.execute(text("ALTER TABLE content_generation_task ADD COLUMN outline JSON"))
            if "partial_render_model" not in columns:
                connection.execute(text("ALTER TABLE content_generation_task ADD COLUMN partial_render_model JSON"))
            for column_name, default_value in missing_defaults.items():
                if column_name not in columns:
                    connection.execute(
                        text(f"ALTER TABLE content_generation_task ADD COLUMN {column_name} JSON NOT NULL DEFAULT '{default_value}'")
                    )

    @staticmethod
    def to_task_result(task: ContentGenerationTask) -> TaskResult:
        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus(task.status),
            content_type=task.content_type,
            preview_url=f"/api/content-generation/tasks/{task.task_id}/preview" if task.render_model else None,
            export_files=[ExportFile.model_validate(file) for file in task.export_files],
            errors=task.errors,
            current_node=task.current_node,
            progress=task.progress,
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
