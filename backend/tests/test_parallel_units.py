import threading
import time

from app.schemas.outline import Outline, OutlineUnit
from app.schemas.state import ContentGenerationState, RenderUnitSnapshot, TaskStreamEvent, UnitGenerationResult
from app.workflows.parallel_units import build_unit_batches


def test_build_unit_batches_groups_units_by_concurrency() -> None:
    assert build_unit_batches(["unit-1", "unit-2", "unit-3", "unit-4", "unit-5"], concurrency=2) == [
        ["unit-1", "unit-2"],
        ["unit-3", "unit-4"],
        ["unit-5"],
    ]


def test_build_unit_batches_clamps_invalid_concurrency_to_one() -> None:
    assert build_unit_batches(["unit-1", "unit-2"], concurrency=0) == [["unit-1"], ["unit-2"]]


def test_build_unit_batches_handles_empty_units() -> None:
    assert build_unit_batches([], concurrency=3) == []


def test_generate_units_parallel_runs_batch_concurrently_and_merges_in_outline_order(monkeypatch) -> None:
    from app.workflows import parallel_units

    active = 0
    max_active = 0
    lock = threading.Lock()

    def fake_process_unit_pipeline(state: ContentGenerationState, unit_id: str):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        try:
            time.sleep(0.05)
        finally:
            with lock:
                active -= 1
        order = int(unit_id.rsplit("-", 1)[1])
        return parallel_units.UnitPipelineResult(
            unit_id=unit_id,
            unit_result=UnitGenerationResult(unit_id=unit_id, status="completed"),
            render_unit=RenderUnitSnapshot(
                unit_id=unit_id,
                order=order,
                content_type="lecture",
                status="rendered",
                render_fragment={"id": unit_id, "title": unit_id, "render_blocks": []},
            ),
            stream_events=[
                TaskStreamEvent(
                    event_id=f"event_{unit_id}",
                    task_id=state.request_id,
                    type="unit_render_ready",
                    unit_id=unit_id,
                    payload={"order": order},
                    created_at="2026-06-24T00:00:00Z",
                )
            ],
        )

    monkeypatch.setattr(parallel_units, "process_unit_pipeline", fake_process_unit_pipeline)
    state = ContentGenerationState(
        request_id="task_parallel_units",
        content_type="lecture",
        topic="AI basics",
        user_prompt="Generate a lecture",
        normalized_request={},
        outline=Outline(
            id="outline_parallel",
            content_type="lecture",
            title="AI basics",
            units=[
                OutlineUnit(id="unit-1", order=1, unit_type="section", title="One", goal="G", core_message="M"),
                OutlineUnit(id="unit-2", order=2, unit_type="section", title="Two", goal="G", core_message="M"),
                OutlineUnit(id="unit-3", order=3, unit_type="section", title="Three", goal="G", core_message="M"),
            ],
        ),
        pending_unit_ids=["unit-1", "unit-2", "unit-3"],
    )

    update = parallel_units.generate_units_parallel(state, concurrency=2)

    assert max_active == 2
    assert update["completed_unit_ids"] == ["unit-1", "unit-2", "unit-3"]
    # Dict insertion follows completion order; the outline order guarantee is
    # carried by completed_unit_ids and by assemble_content_spec.
    assert sorted(update["unit_results"]) == ["unit-1", "unit-2", "unit-3"]
    assert sorted(update["render_units"]) == ["unit-1", "unit-2", "unit-3"]
    assert sorted(event.unit_id for event in update["stream_events"]) == ["unit-1", "unit-2", "unit-3"]
    assert update["current_node"] == "generate_units_parallel"
