from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.state import ContentGenerationState, TaskStreamEvent
from app.workflows.nodes.helpers import unit_progress


def publish_unit_render(state: ContentGenerationState) -> dict[str, object]:
    unit_id = state.current_unit_id
    snapshot = state.render_units.get(unit_id or "") if unit_id else None
    if snapshot is None:
        return {"errors": state.errors + ["rendered unit snapshot is missing"], "current_node": "publish_unit_render"}
    event = TaskStreamEvent(
        event_id=f"event_{uuid4().hex[:12]}",
        task_id=state.request_id,
        type="unit_render_ready",
        unit_id=unit_id,
        payload={
            "render_fragment": snapshot.render_fragment,
            "order": snapshot.order,
            "status": snapshot.status,
        },
        created_at=datetime.now(UTC).isoformat(),
    )
    return {
        "stream_events": [*state.stream_events, event],
        "current_node": "publish_unit_render",
        "progress": unit_progress(state, "unit_render_ready", current_node="publish_unit_render"),
    }


__all__ = ["publish_unit_render"]
