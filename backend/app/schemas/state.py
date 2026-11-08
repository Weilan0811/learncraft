import operator
from typing import Annotated, Literal

from pydantic import Field

from app.core.task import TaskStatus
from app.schemas.base import ContentType, SchemaModel
from app.schemas.elements import ContentElement
from app.schemas.outline import Outline
from app.schemas.observability import GenerationMetric
from app.schemas.render import RenderModel
from app.schemas.specs import ContentSpec, ElementRequest, InteractiveHtmlSectionSpec, LectureSection, SlideSpecPage


class RetrievedChunk(SchemaModel):
    id: str
    source_id: str
    source_title: str
    content: str
    score: float = 1.0
    metadata: dict[str, object] = Field(default_factory=dict)


class RetrievalStatus(SchemaModel):
    state: Literal["disabled", "ok", "empty", "failed"] = "disabled"
    chunk_count: int = 0
    message: str = "知识库检索当前已关闭，未使用知识库资料。"


class WorkflowError(SchemaModel):
    stage: str
    code: str
    message: str
    detail: dict[str, object] = Field(default_factory=dict)
    recoverable: bool = True


class WorkflowLogEntry(SchemaModel):
    timestamp: str
    level: Literal["debug", "info", "warning", "error"]
    event: str
    message: str
    task_id: str
    content_type: str
    node: str | None = None
    unit_id: str | None = None
    detail: dict[str, object] = Field(default_factory=dict)


class RenderUnitSnapshot(SchemaModel):
    unit_id: str
    order: int
    content_type: str
    status: Literal["pending", "rendered", "failed"] = "pending"
    render_fragment: dict[str, object] = Field(default_factory=dict)
    updated_at: str | None = None
    errors: list[str] = Field(default_factory=list)


class TaskStreamEvent(SchemaModel):
    event_id: str
    task_id: str
    type: Literal[
        "task_started",
        "outline_ready",
        "unit_started",
        "unit_spec_ready",
        "element_ready",
        "unit_render_ready",
        "audio_segment_ready",
        "direct_spec_ready",
        "direct_render_ready",
        "task_completed",
        "task_failed",
    ]
    unit_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    created_at: str


class ElementStatus(SchemaModel):
    element_id: str
    type: Literal["image", "mindmap"]
    status: Literal["pending", "generating", "completed", "failed", "skipped"] = "pending"
    retry_count: int = 0
    error: str | None = None


class UnitGenerationResult(SchemaModel):
    unit_id: str
    status: Literal["pending", "completed", "failed"] = "pending"
    unit_spec: LectureSection | SlideSpecPage | InteractiveHtmlSectionSpec | None = None
    element_requests: dict[str, ElementRequest] = Field(default_factory=dict)
    elements: dict[str, ContentElement] = Field(default_factory=dict)
    validation_report: dict[str, object] | None = None
    errors: list[WorkflowError] = Field(default_factory=list)


class ContentGenerationState(SchemaModel):
    request_id: str
    content_type: ContentType
    topic: str
    user_prompt: str
    system_prompt: str | None = None
    knowledge_base_ids: list[str] = Field(default_factory=list)
    retrieval_status: RetrievalStatus = Field(default_factory=RetrievalStatus)
    raw_request: dict[str, object] = Field(default_factory=dict)
    normalized_request: dict[str, object] | None = None
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    planning_chunks: list[RetrievedChunk] = Field(default_factory=list)
    current_unit_context: list[RetrievedChunk] = Field(default_factory=list)
    unit_context_map: dict[str, list[RetrievedChunk]] = Field(default_factory=dict)
    outline: Outline | None = None
    outline_validation_report: dict[str, object] | None = None
    pending_unit_ids: list[str] = Field(default_factory=list)
    completed_unit_ids: list[str] = Field(default_factory=list)
    failed_unit_ids: list[str] = Field(default_factory=list)
    current_unit_index: int = 0
    current_unit_id: str | None = None
    current_unit_spec: LectureSection | SlideSpecPage | InteractiveHtmlSectionSpec | None = None
    current_unit_element_requests: list[ElementRequest] = Field(default_factory=list)
    current_unit_elements: Annotated[list[ContentElement], operator.add] = Field(default_factory=list)
    element_request: ElementRequest | None = None
    unit_results: dict[str, UnitGenerationResult] = Field(default_factory=dict)
    content_spec: ContentSpec | None = None
    elements: list[ContentElement] = Field(default_factory=list)
    element_status: dict[str, ElementStatus] = Field(default_factory=dict)
    render_units: dict[str, RenderUnitSnapshot] = Field(default_factory=dict)
    style_guide: dict | None = None
    partial_render_model: RenderModel | None = None
    stream_events: list[TaskStreamEvent] = Field(default_factory=list)
    render_model: RenderModel | None = None
    spec_validation_report: dict[str, object] | None = None
    validation_report: dict[str, object] | None = None
    retry_counts: dict[str, int] = Field(default_factory=dict)
    failed_element_requests: Annotated[list[ElementRequest], operator.add] = Field(default_factory=list)
    max_allowed_failed_units: int = 0
    errors: list[str] = Field(default_factory=list)
    workflow_errors: list[WorkflowError] = Field(default_factory=list)
    token_usage: dict[str, object] = Field(default_factory=dict)
    metrics: Annotated[list[GenerationMetric], operator.add] = Field(default_factory=list)
    logs: list[WorkflowLogEntry] = Field(default_factory=list)
    current_node: str | None = None
    progress: dict[str, object] | None = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.queued
    # TODO(MVP-observability): Add current_node, progress percentage, node
    # timings, retry records, and structured error details for task tracking.
