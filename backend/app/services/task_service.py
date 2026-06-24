from pydantic import TypeAdapter

from app.core.task import TaskStatus
from app.schemas.export import ExportFile, ExportRequest, ExportResult
from app.schemas.render import RenderModel
from app.schemas.specs import ContentSpec
from app.schemas.request import ContentGenerationRequest
from app.schemas.task import PartialPreviewResponse, TaskEventsResponse, TaskResult, TaskUnitsResponse, UnitPreviewResponse, UnitTextResponse, PreviewResponse
from app.services.task_repository import SQLModelTaskRepository
from app.services.unit_text_service import build_unit_text_response
from app.schemas.state import ContentGenerationState
from app.workflows.content_generation_graph import run_content_generation, stream_content_generation
from app.workflows.routers import get_exporter
from app.content_types.registry import get_content_type_profile


render_model_adapter = TypeAdapter(RenderModel)
content_spec_adapter = TypeAdapter(ContentSpec)


class PersistentTaskService:
    def __init__(self, repository: SQLModelTaskRepository | None = None) -> None:
        self.repository = repository or SQLModelTaskRepository()

    def create_task(self, request: ContentGenerationRequest) -> TaskResult:
        task = self.repository.create_task(request)
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
            for update in stream_content_generation(request, request_id=task_id):
                partial_state = ContentGenerationState.model_validate(update)
                self.repository.save_state(task_id, partial_state)
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

    def get_task(self, task_id: str) -> TaskResult | None:
        task = self.repository.get_task(task_id)
        return self.repository.to_task_result(task) if task else None

    def get_preview(self, task_id: str) -> PreviewResponse | None:
        task = self.repository.get_task(task_id)
        artifact = self.repository.get_latest_artifact(task_id, "final_render") if task else None
        payload = artifact.payload if artifact is not None else (task.render_model if task else None)
        if task is None or payload is None:
            return None
        render_model = render_model_adapter.validate_python(payload)
        return PreviewResponse(content_type=task.content_type, render_model=render_model)

    def get_partial_preview(self, task_id: str) -> PartialPreviewResponse | None:
        task = self.repository.get_task(task_id)
        artifact = self.repository.get_latest_artifact(task_id, "partial_render") if task else None
        payload = artifact.payload if artifact is not None else (task.partial_render_model if task else None)
        if task is None or payload is None:
            return None
        render_model = render_model_adapter.validate_python(payload)
        return PartialPreviewResponse(content_type=task.content_type, render_model=render_model)

    def get_events(self, task_id: str) -> TaskEventsResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        events = self.repository.list_events(task_id)
        if events:
            return TaskEventsResponse(
                task_id=task_id,
                events=[
                    {
                        "event_id": event.id,
                        "task_id": event.task_id,
                        "type": event.event_type,
                        "unit_id": event.unit_id,
                        "payload": event.payload,
                        "created_at": event.created_at.isoformat(),
                    }
                    for event in events
                ],
            )
        return TaskEventsResponse(task_id=task_id, events=task.stream_events)

    def get_units(self, task_id: str) -> TaskUnitsResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        artifacts = [artifact for artifact in self.repository.list_artifacts(task_id) if artifact.artifact_type == "unit_render"]
        units = [artifact.payload for artifact in artifacts] if artifacts else list(task.render_units.values())
        units = sorted(units, key=lambda item: int(item.get("order", 0)))
        return TaskUnitsResponse(task_id=task_id, units=units)

    def get_unit_preview(self, task_id: str, unit_id: str) -> UnitPreviewResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        snapshot = task.render_units.get(unit_id)
        if snapshot is None:
            return None
        return UnitPreviewResponse.model_validate(snapshot)

    def get_unit_text(self, task_id: str, unit_id: str) -> UnitTextResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        snapshot = task.render_units.get(unit_id)
        if snapshot is None:
            return None
        return build_unit_text_response(task_id, snapshot)

    def export_task(self, task_id: str, request: ExportRequest) -> ExportResult | None:
        task = self.repository.get_task(task_id)
        if task is None or task.render_model is None:
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
        render_model = render_model_adapter.validate_python(task.render_model)
        content_spec = content_spec_adapter.validate_python(task.content_spec) if task.content_spec else None
        result = exporter.export(task_id, render_model, request, asset_ids=task.asset_ids, content_spec=content_spec)
        export_files = [*self.repository.to_task_result(task).export_files, ExportFile(type=request.export_type, url=result.file_url)]
        self.repository.update_export_files(task_id, export_files)
        return result


InMemoryTaskService = PersistentTaskService
