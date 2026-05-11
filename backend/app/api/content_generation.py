from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.schemas.export import ExportRequest, ExportResult
from app.schemas.request import ContentGenerationRequest
from app.schemas.task import PartialPreviewResponse, TaskEventsResponse, TaskResult, TaskUnitsResponse, UnitPreviewResponse, PreviewResponse
from app.services.task_service import InMemoryTaskService


router = APIRouter()
task_service = InMemoryTaskService()


@router.post("/tasks", response_model=TaskResult, status_code=status.HTTP_201_CREATED)
def create_content_generation_task(request: ContentGenerationRequest, background_tasks: BackgroundTasks) -> TaskResult:
    # TODO(MVP-task): Replace the synchronous in-memory task execution with an
    # async task runner so queued/running/completed states reflect real progress.
    task = task_service.create_task(request)
    background_tasks.add_task(task_service.run_task, task.task_id)
    return task


@router.get("/tasks/{task_id}", response_model=TaskResult)
def get_content_generation_task(task_id: str) -> TaskResult:
    # TODO(MVP-task): Return node-level progress once workflow execution becomes
    # asynchronous: retrieving, planning, generating, and rendering.
    task = task_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("/tasks/{task_id}/preview", response_model=PreviewResponse)
def get_content_generation_preview(task_id: str) -> PreviewResponse:
    # TODO(MVP-preview): Serve persisted render_model snapshots so previews are
    # repeatable after process restart and can support user editing/regeneration.
    preview = task_service.get_preview(task_id)
    if preview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task preview not found")
    return preview


@router.get("/tasks/{task_id}/events", response_model=TaskEventsResponse)
def get_content_generation_events(task_id: str) -> TaskEventsResponse:
    events = task_service.get_events(task_id)
    if events is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return events


@router.get("/tasks/{task_id}/preview/partial", response_model=PartialPreviewResponse)
def get_content_generation_partial_preview(task_id: str) -> PartialPreviewResponse:
    preview = task_service.get_partial_preview(task_id)
    if preview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task partial preview not found")
    return preview


@router.get("/tasks/{task_id}/units", response_model=TaskUnitsResponse)
def get_content_generation_units(task_id: str) -> TaskUnitsResponse:
    units = task_service.get_units(task_id)
    if units is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return units


@router.get("/tasks/{task_id}/units/{unit_id}/preview", response_model=UnitPreviewResponse)
def get_content_generation_unit_preview(task_id: str, unit_id: str) -> UnitPreviewResponse:
    preview = task_service.get_unit_preview(task_id, unit_id)
    if preview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task unit preview not found")
    return preview


@router.post("/tasks/{task_id}/export", response_model=ExportResult)
def export_content_generation_task(task_id: str, request: ExportRequest) -> ExportResult:
    # TODO(MVP-export): Route export_type to real PDF/Slide JSON exporters and
    # return downloadable storage URLs instead of placeholder asset paths.
    export_result = task_service.export_task(task_id, request)
    if export_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return export_result
