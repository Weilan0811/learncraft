from pydantic import TypeAdapter

from app.core.task import TaskStatus
from app.schemas.export import ExportFile, ExportRequest, ExportResult
from app.schemas.render import RenderModel
from app.schemas.request import ContentGenerationRequest
from app.schemas.task import PartialPreviewResponse, TaskEventsResponse, TaskResult, TaskUnitsResponse, UnitPreviewResponse, PreviewResponse
from app.services.task_repository import SQLModelTaskRepository
from app.schemas.state import ContentGenerationState
from app.workflows.content_generation_graph import run_content_generation, stream_content_generation
from app.workflows.routers import get_exporter


render_model_adapter = TypeAdapter(RenderModel)


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
        if task is None or task.render_model is None:
            return None
        render_model = render_model_adapter.validate_python(task.render_model)
        return PreviewResponse(content_type=task.content_type, render_model=render_model)

    def get_partial_preview(self, task_id: str) -> PartialPreviewResponse | None:
        task = self.repository.get_task(task_id)
        if task is None or task.partial_render_model is None:
            return None
        render_model = render_model_adapter.validate_python(task.partial_render_model)
        return PartialPreviewResponse(content_type=task.content_type, render_model=render_model)

    def get_events(self, task_id: str) -> TaskEventsResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        return TaskEventsResponse(task_id=task_id, events=task.stream_events)

    def get_units(self, task_id: str) -> TaskUnitsResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        units = sorted(task.render_units.values(), key=lambda item: int(item.get("order", 0)))
        return TaskUnitsResponse(task_id=task_id, units=units)

    def get_unit_preview(self, task_id: str, unit_id: str) -> UnitPreviewResponse | None:
        task = self.repository.get_task(task_id)
        if task is None:
            return None
        snapshot = task.render_units.get(unit_id)
        if snapshot is None:
            return None
        return UnitPreviewResponse.model_validate(snapshot)

    def export_task(self, task_id: str, request: ExportRequest) -> ExportResult | None:
        task = self.repository.get_task(task_id)
        if task is None or task.render_model is None:
            return None
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
        result = exporter.export(task_id, render_model, request, asset_ids=task.asset_ids)
        export_files = [*self.repository.to_task_result(task).export_files, ExportFile(type=request.export_type, url=result.file_url)]
        self.repository.update_export_files(task_id, export_files)
        return result


InMemoryTaskService = PersistentTaskService
