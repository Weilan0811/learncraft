from fastapi import APIRouter, HTTPException, status

from app.schemas.export import ExportRequest, ExportResult
from app.schemas.request import ContentGenerationRequest
from app.schemas.task import PreviewResponse, TaskResult
from app.services.task_service import InMemoryTaskService


router = APIRouter()
task_service = InMemoryTaskService()


@router.post("/tasks", response_model=TaskResult, status_code=status.HTTP_201_CREATED)
def create_content_generation_task(request: ContentGenerationRequest) -> TaskResult:
    # TODO(MVP-task): Replace the synchronous in-memory task execution with an
    # async task runner so queued/running/completed states reflect real progress.
    return task_service.create_task(request)


@router.get("/tasks/{task_id}", response_model=TaskResult)
def get_content_generation_task(task_id: str) -> TaskResult:
    # TODO(MVP-task): Return node-level progress once workflow execution becomes
    # asynchronous: retrieving, planning, generating, rendering, exporting.
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


@router.post("/tasks/{task_id}/export", response_model=ExportResult)
def export_content_generation_task(task_id: str, request: ExportRequest) -> ExportResult:
    # TODO(MVP-export): Route export_type to real PDF/Slide JSON exporters and
    # return downloadable storage URLs instead of placeholder asset paths.
    export_result = task_service.export_task(task_id, request)
    if export_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return export_result
