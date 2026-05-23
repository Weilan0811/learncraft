from app.exporters.html_exporter import HTMLExporter
from app.schemas.export import ExportRequest
from app.schemas.learning import CreateSessionRequest, LearningEventPayload, SubmitEventRequest
from app.schemas.render.interactive_html import InteractiveHtmlRenderModel, InteractiveHtmlRenderedUnit
from app.schemas.render.social_post import SocialPostRenderModel
from app.schemas.specs.interactive_html import InteractiveHtmlMeta, InteractiveHtmlSectionSpec, InteractiveHtmlSpec, InteractiveHtmlTeachingBlock
from app.services.learning_service import InMemoryLearningService
from app.services.storage_service import LocalStorageService


def _interactive_render_model() -> InteractiveHtmlRenderModel:
    return InteractiveHtmlRenderModel(
        lesson_id="lesson_1",
        title="互动课",
        sections=[
            InteractiveHtmlRenderedUnit(
                section_id="unit_1",
                title="第一节",
                learning_goal="理解核心概念",
                style_scope_id="ih-scope-unit_1",
                html_fragment='<section id="unit_1" class="ih-unit ih-scope-unit_1" data-section-id="unit_1"><article data-block-id="b1" data-block-type="intro"><h3>核心概念</h3><p>核心讲解。</p></article></section>',
                css_fragment=".ih-scope-unit_1 { color: #111; }",
            )
        ],
    )


def _interactive_spec() -> InteractiveHtmlSpec:
    return InteractiveHtmlSpec(
        lesson_id="lesson_1",
        title="互动课",
        meta=InteractiveHtmlMeta(audience="学习者"),
        sections=[
            InteractiveHtmlSectionSpec(
                section_id="unit_1",
                title="第一节",
                learning_goal="理解核心概念",
                teaching_flow=[InteractiveHtmlTeachingBlock(block_id="b1", block_type="intro", title="核心概念", teaching_role="explain", content_goal="讲解")],
            )
        ],
    )


def test_html_exporter_requires_session_id_for_interactive_html(tmp_path) -> None:
    exporter = HTMLExporter(storage_service=LocalStorageService(storage_root=tmp_path))

    result = exporter.export(
        "task_1",
        _interactive_render_model(),
        ExportRequest(export_type="html"),
        content_spec=_interactive_spec(),
    )

    assert result.status == "failed"
    assert result.metadata["error"] == "interactive_html handout export requires session_id"


def test_html_exporter_exports_interactive_html_offline_handout(tmp_path) -> None:
    service = InMemoryLearningService()
    session = service.create_session("lesson_1", CreateSessionRequest())
    service.submit_event(
        "lesson_1",
        session.session_id,
        SubmitEventRequest(
            section_id="unit_1",
            block_id="b1",
            interaction_id=None,
            event_type="short_answer_submitted",
            payload=LearningEventPayload(answer_text="我的理解是先读材料再回答。"),
        ),
    )
    storage = LocalStorageService(storage_root=tmp_path)
    exporter = HTMLExporter(storage_service=storage, learning_service=service)

    result = exporter.export(
        "task_1",
        _interactive_render_model(),
        ExportRequest(export_type="html", export_options={"session_id": session.session_id}),
        content_spec=_interactive_spec(),
    )

    assert result.status == "success"
    assert result.metadata["render_type"] == "offline_html_handout"
    assert result.metadata["session_id"] == session.session_id
    exported = storage.read_bytes("export_task_1_offline_handout").decode("utf-8")
    assert "ih-app--offline" in exported
    assert "核心讲解" in exported
    assert "我的理解是先读材料再回答。" in exported
    assert "summary_card_asset_id" not in result.metadata


def test_html_exporter_does_not_add_extra_summary_card(tmp_path) -> None:
    service = InMemoryLearningService()
    session = service.create_session("lesson_1", CreateSessionRequest())
    storage = LocalStorageService(storage_root=tmp_path)
    exporter = HTMLExporter(storage_service=storage, learning_service=service)

    result = exporter.export(
        "task_1",
        _interactive_render_model(),
        ExportRequest(export_type="html", export_options={"session_id": session.session_id}),
        content_spec=_interactive_spec(),
    )

    assert result.status == "success"
    exported = storage.read_bytes("export_task_1_offline_handout").decode("utf-8")
    assert "summary-card" not in exported


def test_html_exporter_keeps_social_post_export_behavior(tmp_path) -> None:
    exporter = HTMLExporter(storage_service=LocalStorageService(storage_root=tmp_path))
    model = SocialPostRenderModel(
        title="标题",
        digest="摘要",
        template="daily",
        html="<article>hello</article>",
        article_json={"title": "标题"},
    )

    result = exporter.export("task_social", model, ExportRequest(export_type="html"))

    assert result.status == "success"
    assert result.metadata["render_type"] == "social_post"
    assert result.metadata["article_json_asset_id"] == "export_task_social_article_json"
