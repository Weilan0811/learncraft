from pydantic import Field

from app.core.task import TaskStatus
from app.schemas.base import MvpContentType, SchemaModel
from app.schemas.elements import ContentElement
from app.schemas.export import ExportResult
from app.schemas.outline import Outline
from app.schemas.render import RenderModel
from app.schemas.specs import ContentSpec


class RetrievedChunk(SchemaModel):
    id: str
    source_id: str
    source_title: str
    content: str
    score: float = 1.0
    metadata: dict[str, object] = Field(default_factory=dict)


class ContentGenerationState(SchemaModel):
    request_id: str
    content_type: MvpContentType
    topic: str
    user_prompt: str
    system_prompt: str | None = None
    knowledge_base_ids: list[str] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    outline: Outline | None = None
    content_spec: ContentSpec | None = None
    elements: list[ContentElement] = Field(default_factory=list)
    render_model: RenderModel | None = None
    export_result: ExportResult | None = None
    errors: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.queued
    # TODO(MVP-observability): Add current_node, progress percentage, node
    # timings, retry records, and structured error details for task tracking.
