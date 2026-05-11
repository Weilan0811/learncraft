from pydantic import Field
from datetime import datetime

from app.core.task import TaskStatus
from app.schemas.base import ContentType, SchemaModel
from app.schemas.export import ExportFile, ExportResult
from app.schemas.render import RenderModel
from app.schemas.state import RenderUnitSnapshot, TaskStreamEvent


class TaskResult(SchemaModel):
    task_id: str
    status: TaskStatus
    content_type: ContentType
    preview_url: str | None = None
    export_files: list[ExportFile] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    current_node: str | None = None
    progress: dict[str, object] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PreviewResponse(SchemaModel):
    content_type: ContentType
    render_model: RenderModel


class PartialPreviewResponse(PreviewResponse):
    is_partial: bool = True


class TaskEventsResponse(SchemaModel):
    task_id: str
    events: list[TaskStreamEvent] = Field(default_factory=list)


class TaskUnitsResponse(SchemaModel):
    task_id: str
    units: list[RenderUnitSnapshot] = Field(default_factory=list)


class UnitPreviewResponse(RenderUnitSnapshot):
    pass


class StoredTask(SchemaModel):
    result: TaskResult
    preview: PreviewResponse | None = None
    export_result: ExportResult | None = None
