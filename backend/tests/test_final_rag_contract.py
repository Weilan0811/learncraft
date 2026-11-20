import json
from pathlib import Path

from app.schemas.outline import Outline
from app.schemas.state import ContentGenerationState
from app.schemas.request import ContentGenerationRequest, AttachmentDoc
from app.generators.common.retrieval_formatter import retrieval_snapshot
from app.services.local_kb_service import LocalKBService
from app.services.task_repository import SQLModelTaskRepository
from app.workflows.nodes.validator_node import validate_outline, route_after_outline_validation
from knowledge.engine import kb_engine as kb


ROOT = Path(__file__).resolve().parents[2]


def recorded_state():
    snapshot = json.loads((ROOT / "backend/tests/fixtures/interactive_learning_snapshot.json").read_text(encoding="utf-8"))
    return ContentGenerationState(request_id=snapshot["task_id"],
        content_type=snapshot["request"]["content_type"], topic=snapshot["request"]["topic"],
        user_prompt=snapshot["request"]["user_prompt"], outline=Outline.model_validate(snapshot["outline"]),
        normalized_request={"max_section_count": 4})


def test_public_documents_have_unique_positional_chunk_ids():
    paths = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")), *sorted((ROOT / "knowledge/examples").glob("*.md"))]
    chunks = [chunk for path in paths for chunk in kb.chunks_from_text(str(path.relative_to(ROOT)), path.stem,
              path.read_text(encoding="utf-8"))]
    assert chunks
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
    assert all("::section-" in chunk.chunk_id and "::chunk-" in chunk.chunk_id for chunk in chunks)


def test_actual_outline_is_published_only_after_validation():
    state = recorded_state()
    result = validate_outline(state)
    assert result["outline_validation_report"]["passed"]
    assert len(result["stream_events"]) == 1
    state = state.model_copy(update=result)
    assert route_after_outline_validation(state) == "pass"
    assert "stream_events" not in validate_outline(state)


def test_actual_outline_exceeding_requested_limit_gets_only_one_repair():
    state = recorded_state().model_copy(update={"normalized_request": {"max_section_count": 3}})
    result = validate_outline(state)
    assert not result["outline_validation_report"]["passed"]
    assert "stream_events" not in result
    state = state.model_copy(update=result)
    assert route_after_outline_validation(state) == "repair"
    state.retry_counts["outline_repair"] = 1
    assert route_after_outline_validation(state) == "fail"


def test_unprovided_reference_and_blank_query_are_rejected():
    state = recorded_state()
    chunk = kb.chunk_markdown(ROOT / "knowledge/examples/workbench-guide.md")[0]
    state.outline.units[0].source_chunk_ids = [chunk.chunk_id]
    state.outline.units[0].retrieval_queries = [" "]
    result = validate_outline(state)
    assert not result["outline_validation_report"]["passed"]
    assert any("unavailable chunks" in error for error in result["errors"])
    assert any("retrieval_queries" in error for error in result["errors"])


def test_actual_retrieval_snapshot_and_text_cache_survive_sqlite_restart(tmp_path):
    snapshot = json.loads((ROOT / "backend/tests/fixtures/interactive_learning_snapshot.json").read_text(encoding="utf-8"))
    request = ContentGenerationRequest.model_validate(snapshot["request"])
    request.kb_mode = "materials_only"
    request.attachments = [AttachmentDoc(filename="workbench-guide.md",
        content=(ROOT / "knowledge/examples/workbench-guide.md").read_text(encoding="utf-8"))]
    result = LocalKBService(method="keyword").retrieve(request, "planning", queries=["资源重试"])
    assert result.chunks
    database_url = "sqlite:///" + (tmp_path / "tasks.db").as_posix()
    repository = SQLModelTaskRepository(database_url=database_url)
    task = repository.create_task(request)
    state = recorded_state().model_copy(update={"request_id": task.task_id, "outline": None,
        "planning_chunks": result.chunks, "retrieval_records": {"planning": {
            "results": result.query_results, "context": retrieval_snapshot(result.chunks)}}})
    repository.save_state(task.task_id, state)
    repository.engine.dispose()
    restarted = SQLModelTaskRepository(database_url=database_url)
    artifact = restarted.get_latest_artifact(task.task_id, "retrieval_record")
    assert artifact.payload["context"][0]["id"] == result.chunks[0].id
    assert artifact.payload["context"][0]["shown_content"] == result.chunks[0].content[:500]
    reference = restarted.list_references(task.task_id)[0]
    assert len(reference.chunk_id) == 64
    assert restarted.get_reference_text(reference.chunk_id) == result.chunks[0].content.strip()
    restarted.engine.dispose()
