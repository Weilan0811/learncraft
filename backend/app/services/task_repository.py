from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import get_settings
from app.core.task import TaskStatus
from app.models.content_generation_task import ContentGenerationTask
from app.schemas.export import ExportFile
from app.schemas.request import ContentGenerationRequest
from app.schemas.task import TaskResult
from app.schemas.state import ContentGenerationState
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

    def create_task(self, request: ContentGenerationRequest, task_id: str | None = None) -> ContentGenerationTask:
        task = ContentGenerationTask(
            task_id=task_id or f"task_{uuid4().hex[:12]}",
            content_type=request.content_type,
            status=TaskStatus.queued,
            current_node=None,
            progress=build_progress(stage="queued", current_node=None),
            request_payload=request.model_dump(mode="json"),
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
        return self.update_task(
            task_id,
            status=state.status,
            current_node=state.current_node,
            progress=progress,
            outline=state.outline.model_dump(mode="json") if state.outline else None,
            render_model=state.render_model.model_dump(mode="json") if state.render_model else None,
            partial_render_model=state.partial_render_model.model_dump(mode="json") if state.partial_render_model else None,
            content_spec=state.content_spec.model_dump(mode="json") if state.content_spec else None,
            unit_results={unit_id: result.model_dump(mode="json") for unit_id, result in state.unit_results.items()},
            render_units={unit_id: snapshot.model_dump(mode="json") for unit_id, snapshot in state.render_units.items()},
            stream_events=[event.model_dump(mode="json") for event in state.stream_events],
            elements=[element.model_dump(mode="json") for element in state.elements],
            logs=[entry.model_dump(mode="json") for entry in state.logs],
            asset_ids=asset_ids,
            errors=state.errors,
            completed_at=now_utc() if state.status in {TaskStatus.completed, TaskStatus.failed} else None,
        )

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
        }
        with self.engine.begin() as connection:
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
