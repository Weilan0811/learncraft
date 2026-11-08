from pathlib import Path

import pytest

from app.core.config import get_settings
from app.schemas.outline import Outline, OutlineUnit
from app.schemas.request import ContentGenerationRequest, GenerationOptions
from app.schemas.state import ContentGenerationState
from app.services.rag_service import get_rag_service
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_service import PersistentTaskService
from app.workflows.content_generation_graph import run_content_generation
from app.workflows.nodes.retriever_node import retrieve_for_planning, retrieve_for_unit


def build_request(content_type: str, **options: object) -> ContentGenerationRequest:
    return ContentGenerationRequest(
        content_type=content_type,
        topic="无资料生成验证",
        user_prompt="在没有知识库资料的情况下生成内容",
        generation_options=options or {},
    )


def test_default_rag_service_is_disabled_and_returns_no_chunks() -> None:
    service = get_rag_service()

    result = service.retrieve(build_request("lecture"), stage="planning")

    assert result.chunks == []
    assert result.status.state == "disabled"
    assert result.status.chunk_count == 0
    assert result.status.message


def test_retrieval_nodes_report_status_without_workflow_errors() -> None:
    unit = OutlineUnit(
        id="unit_001",
        order=1,
        unit_type="section",
        title="无资料",
        goal="理解无资料时的行为。",
        core_message="没有检索资料时仍然可以生成。",
    )
    state = ContentGenerationState(
        request_id="task_no_retrieval",
        content_type="lecture",
        topic="无资料",
        user_prompt="生成讲义",
        outline=Outline(id="outline_no_retrieval", content_type="lecture", title="无资料", units=[unit]),
        pending_unit_ids=[unit.id],
        current_unit_id=unit.id,
    )

    planning = retrieve_for_planning(state)
    assert planning["retrieved_chunks"] == []
    assert planning["retrieval_status"].state == "disabled"
    assert "workflow_errors" not in planning

    state = state.model_copy(update={"retrieval_status": planning["retrieval_status"]})
    unit_update = retrieve_for_unit(state)
    assert unit_update["current_unit_context"] == []
    assert unit_update["retrieval_status"].state == "disabled"
    assert "workflow_errors" not in unit_update


@pytest.mark.parametrize(
    "content_type",
    ["lecture", "slide_deck", "social_post", "podcast_script", "interactive_html"],
)
def test_all_content_types_generate_without_retrieval(
    content_type: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    monkeypatch.setenv("CONTENT_GENERATOR_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CONTENT_GENERATOR_LOG_ROOT", str(tmp_path / "logs"))
    monkeypatch.setenv("CONTENT_GENERATOR_DEBUG_ROOT", str(tmp_path / "debug"))
    get_settings.cache_clear()
    try:
        state = run_content_generation(build_request(content_type, section_count=1, slide_count=1, duration_minutes=1))
    finally:
        get_settings.cache_clear()

    assert state.status == "completed"
    assert state.retrieval_status.state == "disabled"
    assert state.planning_chunks == []
    assert state.retrieved_chunks == []
    assert "stub_chunk" not in state.model_dump_json()


def test_social_post_has_no_placeholder_citations_without_retrieval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    monkeypatch.setenv("CONTENT_GENERATOR_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CONTENT_GENERATOR_LOG_ROOT", str(tmp_path / "logs"))
    monkeypatch.setenv("CONTENT_GENERATOR_DEBUG_ROOT", str(tmp_path / "debug"))
    get_settings.cache_clear()
    try:
        state = run_content_generation(build_request("social_post"))
    finally:
        get_settings.cache_clear()

    assert state.content_spec is not None
    assert all(not section.citation_refs for section in state.content_spec.draft.sections)
    assert all(not section.evidence_refs for section in state.content_spec.outline.sections)
    assert "stub_chunk" not in state.content_spec.model_dump_json()


def test_task_and_preview_expose_disabled_knowledge_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    monkeypatch.setenv("CONTENT_GENERATOR_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CONTENT_GENERATOR_LOG_ROOT", str(tmp_path / "logs"))
    monkeypatch.setenv("CONTENT_GENERATOR_DEBUG_ROOT", str(tmp_path / "debug"))
    get_settings.cache_clear()
    try:
        repository = SQLModelTaskRepository(database_url=f"sqlite:///{tmp_path / 'tasks.db'}", echo=False)
        service = PersistentTaskService(repository=repository)
        created = service.create_task(build_request("lecture", section_count=1))
        service.run_task(created.task_id)

        task = service.get_task(created.task_id)
        preview = service.get_preview(created.task_id)
    finally:
        get_settings.cache_clear()

    assert task is not None
    assert task.knowledge_base is not None
    assert task.knowledge_base.used is False
    assert task.knowledge_base.status == "disabled"
    assert task.knowledge_base.chunk_count == 0
    assert task.knowledge_base.message
    assert preview is not None
    assert preview.knowledge_base is not None
    assert preview.knowledge_base.status == "disabled"
