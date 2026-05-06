from uuid import uuid4

from app.schemas.export import ExportFile, ExportRequest, ExportResult
from app.schemas.request import ContentGenerationRequest
from app.schemas.task import PreviewResponse, StoredTask, TaskResult
from app.workflows.content_generation_graph import run_content_generation


class InMemoryTaskService:
    _tasks: dict[str, StoredTask] = {}

    def create_task(self, request: ContentGenerationRequest) -> TaskResult:
        task_id = f"task_{uuid4().hex[:12]}"
        state = run_content_generation(request, request_id=task_id)
        export_files: list[ExportFile] = []
        if state.export_result is not None:
            export_files.append(ExportFile(type=state.export_result.export_type, url=state.export_result.file_url))

        result = TaskResult(
            task_id=task_id,
            status=state.status,
            content_type=state.content_type,
            preview_url=f"/api/content-generation/tasks/{task_id}/preview",
            export_files=export_files,
            errors=state.errors,
        )
        preview = PreviewResponse(content_type=state.content_type, render_model=state.render_model) if state.render_model else None
        self._tasks[task_id] = StoredTask(result=result, preview=preview, export_result=state.export_result)
        return result

    def get_task(self, task_id: str) -> TaskResult | None:
        stored = self._tasks.get(task_id)
        return stored.result if stored else None

    def get_preview(self, task_id: str) -> PreviewResponse | None:
        stored = self._tasks.get(task_id)
        return stored.preview if stored else None

    def export_task(self, task_id: str, request: ExportRequest) -> ExportResult | None:
        stored = self._tasks.get(task_id)
        if stored is None:
            return None
        suffix = "json" if request.export_type == "slide_json" else str(request.export_type)
        result = ExportResult(
            export_type=request.export_type,
            file_url=f"/api/assets/export/{task_id}.{suffix}",
            status="success",
            metadata={"stub": True, "task_id": task_id},
        )
        stored.export_result = result
        stored.result.export_files = [ExportFile(type=request.export_type, url=result.file_url)]
        return result
