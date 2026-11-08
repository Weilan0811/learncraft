from pydantic import TypeAdapter

from app.core.task import TaskStatus
from app.schemas.artifacts import (
    ContentArtifactDetailResponse,
    ContentArtifactListResponse,
    ContentArtifactRecord,
    GenerationMetricListResponse,
    ReferenceChunk,
    ReferenceChunksResponse,
)
from app.schemas.export import ExportFile, ExportRequest, ExportResult
from app.schemas.render import RenderModel
from app.schemas.specs import ContentSpec
from app.schemas.request import ContentGenerationRequest
from app.schemas.task import PartialPreviewResponse, TaskEventsResponse, TaskResult, TaskUnitsResponse, UnitPreviewResponse, UnitTextResponse, PreviewResponse
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_event_store import TaskEventStore
from app.services.unit_text_service import build_unit_text_response
from app.schemas.state import ContentGenerationState
from app.workflows.content_generation_graph import run_content_generation, stream_content_generation
from app.workflows.routers import get_exporter
from app.content_types.registry import get_content_type_profile


render_model_adapter = TypeAdapter(RenderModel)
content_spec_adapter = TypeAdapter(ContentSpec)


class PersistentTaskService:
    def __init__(self, repository: SQLModelTaskRepository | None = None, event_store: TaskEventStore | None = None) -> None:
        self.repository = repository or SQLModelTaskRepository()
        self.event_store = event_store or TaskEventStore()

    def create_task(
        self,
        request: ContentGenerationRequest,
        platform_context: dict[str, str | None] | None = None,
    ) -> TaskResult:
        task = self.repository.create_task(request, platform_context=platform_context)
        return self.repository.to_task_result(task)

    def run_task(self, task_id: str) -> None:
        task = self.repository.get_task(task_id)
        if task is None:
            return
        self.repository.mark_running(task_id)
        try:
            request = ContentGenerationRequest.model_validate(task.request_payload)
            # state = run_content_generation(request, request_id=task_id)
            final_state = None
            for update in stream_content_generation(
                request, request_id=task_id, persist_unit_snapshot=self._save_unit_snapshot
            ):
                partial_state = ContentGenerationState.model_validate(update)
                self.repository.save_state(task_id, partial_state)
                self.event_store.save_events(task_id, partial_state.stream_events)
                final_state = partial_state

        except Exception as exc:
            running = self.repository.get_task(task_id)
            progress = dict(running.progress if running else {})
            progress.update({"stage": "failed", "display_stage": "failed", "current_stage": "failed", "percent": 100})
            self.repository.update_task(
                task_id,
                status=TaskStatus.failed,
                current_node="run_task",
                progress=progress,
                errors=[str(exc)],
            )
            return
            
        # self.repository.save_state(task_id, state)
        if final_state is not None:
            self.repository.save_state(task_id, final_state)

    def _save_unit_snapshot(self, task_id: str, state: ContentGenerationState) -> None:
        self.repository.save_unit_snapshot(task_id, state)
        self.event_store.save_events(task_id, state.stream_events)

    def get_task(self, task_id: str) -> TaskResult | None:
        task = self.repository.get_task(task_id)
        return self.repository.to_task_result(task) if task else None

    def get_preview(self, task_id: str) -> PreviewResponse | None:
        task = self.repository.get_task(task_id)
        artifact = self.repository.get_latest_artifact(task_id, "final_render") if task else None
        payload = _render_payload(artifact.payload if artifact is not None else None)
        if task is None or payload is None:
            return None
        render_model = render_model_adapter.validate_python(payload)
        return PreviewResponse(content_type=task.content_type, render_model=render_model)

    def get_partial_preview(self, task_id: str) -> PartialPreviewResponse | None:
        task = self.repository.get_task(task_id)
        artifact = self.repository.get_latest_artifact(task_id, "partial_render") if task else None
        payload = _render_payload(artifact.payload if artifact is not None else None)
        if task is None or payload is None:
            return None
        render_model = render_model_adapter.validate_python(payload)
        return PartialPreviewResponse(content_type=task.content_type, render_model=render_model)

    def get_events(self, task_id: str) -> TaskEventsResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        return TaskEventsResponse(task_id=task_id, events=self.event_store.get_events(task_id))

    def get_units(self, task_id: str) -> TaskUnitsResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        artifacts = [artifact for artifact in self.repository.list_artifacts(task_id) if artifact.artifact_type == "unit_render"]
        units = [artifact.payload for artifact in artifacts]
        units = sorted(units, key=lambda item: int(item.get("order", 0)))
        return TaskUnitsResponse(task_id=task_id, units=units)

    def get_unit_preview(self, task_id: str, unit_id: str) -> UnitPreviewResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        artifact = self.repository.get_latest_artifact(task_id, "unit_render", unit_id)
        snapshot = artifact.payload if artifact else None
        if snapshot is None:
            return None
        return UnitPreviewResponse.model_validate(snapshot)

    def get_unit_text(self, task_id: str, unit_id: str) -> UnitTextResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        artifact = self.repository.get_latest_artifact(task_id, "unit_render", unit_id)
        snapshot = artifact.payload if artifact else None
        if snapshot is None:
            return None
        return build_unit_text_response(task_id, snapshot)

    def list_artifacts(self, task_id: str) -> ContentArtifactListResponse | None:
        if self.repository.get_task(task_id) is None:
            return None
        return ContentArtifactListResponse(
            task_id=task_id,
            artifacts=[_artifact_record(artifact) for artifact in self.repository.list_artifacts(task_id)],
        )

    def get_artifact(self, task_id: str, artifact_id: str) -> ContentArtifactDetailResponse | None:
        if self.repository.get_task(task_id) is None:
            return None
        artifact = self.repository.get_artifact(task_id, artifact_id)
        if artifact is None:
            return None
        return ContentArtifactDetailResponse(task_id=task_id, artifact=_artifact_record(artifact))

    def get_outline_artifact(self, task_id: str) -> ContentArtifactDetailResponse | None:
        if self.repository.get_task(task_id) is None:
            return None
        artifact = self.repository.get_latest_artifact(task_id, "outline")
        if artifact is None:
            return None
        return ContentArtifactDetailResponse(task_id=task_id, artifact=_artifact_record(artifact))

    def list_references(
        self,
        task_id: str,
        *,
        stage: str | None = None,
        unit_id: str | None = None,
    ) -> ReferenceChunksResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        references = self.repository.list_references(task_id, stage=stage, unit_id=unit_id)
        return ReferenceChunksResponse(
            task_id=task_id,
            unit_id=unit_id,
            content_type=task.content_type,
            title=_reference_response_title(task, unit_id, self.repository),
            chunks=[_reference_chunk(reference, self.repository.get_reference_text(reference.chunk_id)) for reference in references],
        )

    def list_metrics(self, task_id: str) -> GenerationMetricListResponse | None:
        if self.repository.get_task(task_id) is None:
            return None
        return GenerationMetricListResponse(task_id=task_id, metrics=[])

    def export_task(self, task_id: str, request: ExportRequest) -> ExportResult | None:
        task = self.repository.get_task(task_id)
        final_render = self.repository.get_latest_artifact(task_id, "final_render") if task else None
        render_payload = _render_payload(final_render.payload if final_render else None)
        if task is None or render_payload is None:
            return None
        profile = get_content_type_profile(task.content_type)
        if request.export_type not in profile.exporter_types:
            return ExportResult(
                export_type=request.export_type,
                file_url="",
                status="failed",
                metadata={"error": f"Unsupported export type for {task.content_type}: {request.export_type}", "task_id": task_id},
            )
        try:
            exporter = get_exporter(request.export_type)
        except ValueError:
            return ExportResult(
                export_type=request.export_type,
                file_url="",
                status="failed",
                metadata={"error": f"Unsupported export type: {request.export_type}", "task_id": task_id},
            )
        content_spec_artifact = self.repository.get_latest_artifact(task_id, "content_spec")
        render_model = render_model_adapter.validate_python(render_payload)
        content_spec = content_spec_adapter.validate_python(content_spec_artifact.payload) if content_spec_artifact else None
        result = exporter.export(task_id, render_model, request, asset_ids=[], content_spec=content_spec)
        export_files = [*self.repository.to_task_result(task).export_files, ExportFile(type=request.export_type, url=result.file_url)]
        self.repository.update_export_files(task_id, export_files)
        return result


InMemoryTaskService = PersistentTaskService


def _artifact_record(artifact) -> ContentArtifactRecord:
    return ContentArtifactRecord(
        id=artifact.artifact_id,
        task_id=artifact.task_id,
        artifact_type=artifact.artifact_type,
        unit_id=artifact.unit_id,
        version=artifact.version,
        payload=artifact.payload,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


def _reference_chunk(reference, text: str) -> ReferenceChunk:
    return ReferenceChunk(
        chunk_id=reference.chunk_id,
        path=reference.source_path,
        title=reference.source_title or reference.source_path or reference.chunk_id,
        text=text,
        rank=reference.rank,
        score=reference.score,
    )


def _reference_response_title(task, unit_id: str | None, repository: SQLModelTaskRepository) -> str | None:
    if unit_id is None:
        return task.topic
    artifact = repository.get_latest_artifact(task.task_id, "unit_render", unit_id)
    snapshot = artifact.payload if artifact else None
    if isinstance(snapshot, dict):
        render_fragment = snapshot.get("render_fragment")
        if isinstance(render_fragment, dict) and isinstance(render_fragment.get("title"), str):
            return render_fragment["title"]
    outline_artifact = repository.get_latest_artifact(task.task_id, "outline")
    if outline_artifact and isinstance(outline_artifact.payload, dict):
        units = outline_artifact.payload.get("units")
        if isinstance(units, list):
            for unit in units:
                if isinstance(unit, dict) and unit.get("id") == unit_id and isinstance(unit.get("title"), str):
                    return unit["title"]
    return None


def _render_payload(payload: dict | None) -> dict | None:
    if payload is None:
        return None
    render_model = payload.get("render_model")
    return render_model if isinstance(render_model, dict) else payload
