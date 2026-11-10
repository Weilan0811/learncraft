import json
from functools import partial
from pathlib import Path
from html import escape

import pytest
from sqlmodel import Session

from app.models import ContentGenerationArtifact
from app.core.task import TaskStatus
from app.exporters.html_exporter import HTMLExporter
from app.schemas.export import ExportRequest
from app.schemas.learning import CreateSessionRequest, LearningEventPayload, SubmitEventRequest
from app.schemas.request import ContentGenerationRequest
from app.schemas.outline import Outline
from app.schemas.specs.interactive_html import InteractiveHtmlSectionSpec
from app.schemas.state import ContentGenerationState, RenderUnitSnapshot, UnitGenerationResult
from app.services.adaptive_brief_service import AdaptiveBriefService, load_lesson_context
from app.services.artifact_repository import ArtifactRepository
from app.services.learning_repository import SQLModelLearningRepository
from app.services.learning_service import LearningService
from app.services.task_repository import SQLModelTaskRepository
from app.services.storage_service import LocalStorageService
from app.workflows.nodes.assembler_node import assemble_content_spec
from app.workflows.nodes.renderer_node import interactive_html_renderer
from app.workflows.nodes.unit_renderer_node import _build_partial_render_model


@pytest.fixture
def saved_lesson(tmp_path):
    snapshot = json.loads(
        (Path(__file__).parent / "fixtures" / "interactive_learning_snapshot.json").read_text(encoding="utf-8")
    )
    database_url = f"sqlite:///{tmp_path / 'tasks.db'}"
    repository = SQLModelTaskRepository(database_url)
    repository.create_task(ContentGenerationRequest.model_validate(snapshot["request"]), task_id=snapshot["task_id"])
    with Session(repository.engine) as session:
        artifacts = ArtifactRepository(session)
        artifacts.upsert_artifact(snapshot["task_id"], "content_spec", snapshot["spec"])
        artifacts.upsert_artifact(snapshot["task_id"], "final_render", snapshot["final_render"])
        session.commit()
    yield snapshot, repository, database_url
    repository.engine.dispose()


@pytest.fixture
def lesson_state(saved_lesson):
    snapshot, _, _ = saved_lesson
    request = ContentGenerationRequest.model_validate(snapshot["request"])
    section = InteractiveHtmlSectionSpec.model_validate(snapshot["spec"]["sections"][0])
    unit = RenderUnitSnapshot(
        unit_id=section.section_id, order=1, content_type=request.content_type, status="rendered",
        render_fragment=snapshot["final_render"]["render_model"]["sections"][0],
    )
    return ContentGenerationState(
        request_id=snapshot["task_id"], content_type=request.content_type, topic=request.topic,
        user_prompt=request.user_prompt, raw_request=request.model_dump(mode="json"),
        normalized_request=request.generation_options.model_dump(mode="json"),
        outline=Outline.model_validate(snapshot["outline"]), pending_unit_ids=[section.section_id],
        unit_results={section.section_id: UnitGenerationResult(unit_id=section.section_id, unit_spec=section)},
        render_units={section.section_id: unit},
    )


def test_partial_answers_survive_final_render_restart_and_export(saved_lesson, lesson_state, tmp_path) -> None:
    snapshot, repository, database_url = saved_lesson
    state = lesson_state
    state.partial_render_model = _build_partial_render_model(state, state.render_units)
    repository.save_unit_snapshot(state.request_id, state)
    partial_id = state.partial_render_model.lesson_id
    learning = LearningService(SQLModelLearningRepository(repository.engine))
    session = learning.create_session(partial_id, CreateSessionRequest())
    section = next(iter(state.unit_results.values())).unit_spec
    interaction = section.interaction_specs[0]
    answer = next(option for option in interaction.options if option.is_correct is False)
    learning.submit_event(partial_id, session.session_id, SubmitEventRequest(
        section_id=section.section_id, interaction_id=interaction.interaction_id,
        event_type=interaction.event_type,
        payload=LearningEventPayload(selected_option_ids=[answer.id], is_correct=answer.is_correct),
    ))

    state.content_spec = assemble_content_spec(state)["content_spec"]
    state.render_model = interactive_html_renderer(state)["render_model"]
    repository.save_state(state.request_id, state)
    repository.engine.dispose()

    restarted = SQLModelTaskRepository(database_url)
    try:
        learning = LearningService(SQLModelLearningRepository(restarted.engine))
        final_id = state.render_model.lesson_id
        assert partial_id == final_id == snapshot["spec"]["lesson_id"]
        assert learning.get_session_state(final_id, session.session_id).total_events == 1
        assert learning.build_summary(final_id, session.session_id).total_answered == 1
        second_session = learning.create_session(final_id, CreateSessionRequest())
        assert second_session.session_id != session.session_id
        assert learning.get_session_state(final_id, second_session.session_id).total_events == 0

        storage = LocalStorageService(storage_root=tmp_path / "exports")
        result = HTMLExporter(storage_service=storage, learning_service=learning).export(
            state.request_id, state.render_model,
            ExportRequest(export_type="html", export_options={"session_id": session.session_id}),
            content_spec=state.content_spec,
        )
        assert result.status == "success"
        html = storage.read_bytes(result.metadata["asset_id"]).decode("utf-8")
        assert session.session_id in html
        assert f"<strong>学生回答：</strong>{escape(answer.text)}" in html
    finally:
        restarted.engine.dispose()


def test_load_lesson_context_reads_saved_spec(saved_lesson) -> None:
    snapshot, repository, _ = saved_lesson
    spec = snapshot["spec"]
    section = spec["sections"][0]

    context = load_lesson_context(spec["lesson_id"], repository=repository)

    assert context.title == spec["title"]
    assert context.difficulty == spec["meta"]["difficulty"]
    assert context.section_titles == {section["section_id"]: section["title"]}
    assert context.concept_map == {
        interaction["interaction_id"]: interaction["target_concepts"]
        for interaction in section["interaction_specs"] if interaction["target_concepts"]
    }


def test_adaptive_brief_restores_original_request_after_restart(saved_lesson) -> None:
    snapshot, repository, database_url = saved_lesson
    lesson_id = snapshot["spec"]["lesson_id"]
    section = snapshot["spec"]["sections"][0]
    interaction = section["interaction_specs"][0]
    learning = LearningService(SQLModelLearningRepository(repository.engine))
    session = learning.create_session(lesson_id, CreateSessionRequest())
    learning.submit_event(
        lesson_id, session.session_id,
        SubmitEventRequest(
            section_id=section["section_id"],
            interaction_id=interaction["interaction_id"],
            event_type=interaction["event_type"],
            payload=LearningEventPayload(),
        ),
    )
    repository.engine.dispose()

    restarted = SQLModelTaskRepository(database_url)
    try:
        service = AdaptiveBriefService(
            LearningService(SQLModelLearningRepository(restarted.engine)),
            partial(load_lesson_context, repository=restarted),
        )
        brief = service.build(lesson_id, session.session_id)

        assert brief.evidence.total_answered == 1
        assert brief.model_dump(mode="json")["source_request"] == snapshot["request"]
    finally:
        restarted.engine.dispose()


@pytest.mark.parametrize("spec_state", ["missing", "invalid"])
def test_load_lesson_context_falls_back_to_saved_final_render(saved_lesson, spec_state) -> None:
    snapshot, repository, _ = saved_lesson
    artifact = repository.get_latest_artifact(snapshot["task_id"], "content_spec")
    with Session(repository.engine) as session:
        stored = session.get(ContentGenerationArtifact, artifact.artifact_id)
        if spec_state == "missing":
            session.delete(stored)
        else:
            stored.payload = {key: value for key, value in stored.payload.items() if key != "title"}
            session.add(stored)
        session.commit()

    render = snapshot["final_render"]["render_model"]
    section = render["sections"][0]
    context = load_lesson_context(f"partial_lesson_{snapshot['task_id']}", repository=repository)

    assert context.title == render["title"]
    assert context.section_titles == {section["section_id"]: section["title"]}
    assert context.concept_map == {
        interaction["interaction_id"]: interaction["target_concepts"]
        for interaction in section["interaction_manifest"] if interaction["target_concepts"]
    }
    assert context.source_request.model_dump(mode="json") == snapshot["request"]


@pytest.mark.parametrize("task_status", ["running", "failed"])
@pytest.mark.parametrize("final_state", ["missing", "invalid"])
def test_partial_render_supplies_context_and_weak_concepts(saved_lesson, lesson_state, task_status, final_state) -> None:
    snapshot, repository, _ = saved_lesson
    state = lesson_state
    state.status = TaskStatus(task_status)
    state.partial_render_model = _build_partial_render_model(state, state.render_units)
    repository.save_state(state.request_id, state)
    spec_artifact = repository.get_latest_artifact(state.request_id, "content_spec")
    final_artifact = repository.get_latest_artifact(state.request_id, "final_render")
    with Session(repository.engine) as session:
        session.delete(session.get(ContentGenerationArtifact, spec_artifact.artifact_id))
        final = session.get(ContentGenerationArtifact, final_artifact.artifact_id)
        if final_state == "missing":
            session.delete(final)
        else:
            payload = final.payload.copy()
            payload["render_model"] = {
                key: value for key, value in payload["render_model"].items() if key != "lesson_id"
            }
            final.payload = payload
            session.add(final)
        session.commit()

    lesson_id = state.partial_render_model.lesson_id
    section = next(iter(state.unit_results.values())).unit_spec
    interaction = section.interaction_specs[0]
    answer = next(option for option in interaction.options if option.is_correct is False)
    learning = LearningService(SQLModelLearningRepository(repository.engine))
    session = learning.create_session(lesson_id, CreateSessionRequest())
    learning.submit_event(lesson_id, session.session_id, SubmitEventRequest(
        section_id=section.section_id, interaction_id=interaction.interaction_id,
        event_type=interaction.event_type,
        payload=LearningEventPayload(selected_option_ids=[answer.id], is_correct=answer.is_correct),
    ))
    context = load_lesson_context(lesson_id, repository=repository)
    brief = AdaptiveBriefService(learning, partial(load_lesson_context, repository=repository)).build(
        lesson_id, session.session_id,
    )

    assert context.title == state.partial_render_model.title
    assert context.section_titles == {section.section_id: section.title}
    assert context.concept_map[interaction.interaction_id] == interaction.target_concepts
    assert set(brief.weak_concepts) == set(interaction.target_concepts)
    assert brief.review_sections == [section.section_id]
    assert section.title in brief.focus_prompt
    assert brief.source_request.model_dump(mode="json") == snapshot["request"]
