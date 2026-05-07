from app.core.task import TaskStatus
from app.schemas.state import ContentGenerationState, WorkflowError


def finalize_task(state: ContentGenerationState) -> dict[str, object]:
    return {
        "status": TaskStatus.completed if not state.errors else TaskStatus.failed,
        "current_node": "finalize_task",
        "progress": {
            "current_stage": "completed" if not state.errors else "failed",
            "completed_units": len(state.completed_unit_ids),
            "total_units": len(state.pending_unit_ids),
            "percent": 100,
        },
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
        "progress": {"current_stage": "failed", "percent": 100},
    }


__all__ = ["finalize_task", "fail_task"]
