from app.core.task import TaskStatus
from app.schemas.state import ContentGenerationState, WorkflowError
from app.workflows.nodes.helpers import build_progress, ensure_monotonic_progress


def finalize_task(state: ContentGenerationState) -> dict[str, object]:
    return {
        "status": TaskStatus.completed if not state.errors else TaskStatus.failed,
        "current_node": "finalize_task",
        "progress": ensure_monotonic_progress(
            state.progress,
            build_progress(
                stage="completed" if not state.errors else "failed",
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
    return {
        "status": TaskStatus.failed,
        "workflow_errors": workflow_errors,
        "current_node": "fail_task",
        "progress": ensure_monotonic_progress(state.progress, build_progress(stage="failed", current_node="fail_task")),
    }


__all__ = ["finalize_task", "fail_task"]
