from datetime import datetime
from typing import Literal

from pydantic import Field

from app.core.task import TaskStatus
from app.schemas.base import ContentType, SchemaModel
from app.schemas.export import ExportFile, ExportResult
from app.schemas.render import RenderModel
from app.schemas.state import RenderUnitSnapshot, TaskStreamEvent


class KnowledgeBaseStatus(SchemaModel):
    used: bool = False
    status: Literal["disabled", "ok", "empty", "failed"] = "disabled"
    chunk_count: int = 0
    message: str = "知识库检索当前已关闭，未使用知识库资料。"


class TaskResult(SchemaModel):
    task_id: str
    status: TaskStatus
    content_type: ContentType
    preview_url: str | None = None
    export_files: list[ExportFile] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    current_node: str | None = None
    progress: dict[str, object] = Field(default_factory=dict)
    knowledge_base: KnowledgeBaseStatus | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TaskListItem(SchemaModel):
    task_id: str
    topic: str | None = None
    content_type: ContentType
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    failed_resource_count: int = 0


class TaskListResponse(SchemaModel):
    items: list[TaskListItem] = Field(default_factory=list)
    page: int
    page_size: int
    total: int


class PreviewResponse(SchemaModel):
    content_type: ContentType
    render_model: RenderModel
    knowledge_base: KnowledgeBaseStatus | None = None


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


class UnitTextChunk(SchemaModel):
    chunk_id: str
    text: str


class UnitTextResponse(SchemaModel):
    task_id: str
    unit_id: str
    content_type: str
    title: str | None = None
    full_text: str
    chunks: list[UnitTextChunk] = Field(default_factory=list)


class StoredTask(SchemaModel):
    result: TaskResult
    preview: PreviewResponse | None = None
    export_result: ExportResult | None = None
