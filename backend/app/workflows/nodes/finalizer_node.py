from datetime import UTC, datetime
from uuid import uuid4

from app.core.task import TaskStatus
from app.schemas.state import ContentGenerationState, TaskStreamEvent, WorkflowError
from app.workflows.nodes.helpers import build_progress, ensure_monotonic_progress


def finalize_task(state: ContentGenerationState) -> dict[str, object]:
    completed = not state.errors
    event = TaskStreamEvent(
        event_id=f"event_{uuid4().hex[:12]}",
        task_id=state.request_id,
        type="task_completed" if completed else "task_failed",
        payload={"status": "completed" if completed else "failed", "errors": state.errors},
        created_at=datetime.now(UTC).isoformat(),
    )
    return {
        "status": TaskStatus.completed if completed else TaskStatus.failed,
        "stream_events": [*state.stream_events, event],
        "current_node": "finalize_task",
        "progress": ensure_monotonic_progress(
            state.progress,
            build_progress(
                stage="completed" if completed else "failed",
                current_node="finalize_task",
                completed_units=len(state.completed_unit_ids),
                total_units=len(state.pending_unit_ids),
            ),
        ),
    }


def fail_task(state: ContentGenerationState) -> dict[str, object]:
    workflow_errors = list(state.workflow_errors)
    workflow_errors.append(
        WorkflowError(
            stage=state.current_node or "workflow",
            code="workflow_validation_failed",
            message="; ".join(state.errors) if state.errors else "Content generation workflow failed.",
            recoverable=False,
        )
    )
    event = TaskStreamEvent(
        event_id=f"event_{uuid4().hex[:12]}",
        task_id=state.request_id,
        type="task_failed",
        payload={"errors": state.errors},
        created_at=datetime.now(UTC).isoformat(),
    )
    return {
        "status": TaskStatus.failed,
        "workflow_errors": workflow_errors,
        "stream_events": [*state.stream_events, event],
        "current_node": "fail_task",
        "progress": ensure_monotonic_progress(state.progress, build_progress(stage="failed", current_node="fail_task")),
    }


__all__ = ["finalize_task", "fail_task"]
