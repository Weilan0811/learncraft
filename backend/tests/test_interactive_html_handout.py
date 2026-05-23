from app.renderers.interactive_html_handout import InteractiveHtmlStaticHandoutRenderer
from app.schemas.learning import LearningEventPayload, SubmitEventRequest
from app.schemas.render.interactive_html import (
    InteractionRenderRef,
    InteractiveHtmlRenderBlockRef,
    InteractiveHtmlRenderModel,
    InteractiveHtmlRenderedUnit,
)
from app.schemas.specs.interactive_html import (
    InteractiveHtmlInteractionOption,
    InteractiveHtmlInteractionSpec,
    InteractiveHtmlMeta,
    InteractiveHtmlSectionSpec,
    InteractiveHtmlSpec,
    InteractiveHtmlTeachingBlock,
)
from app.services.storage_service import LocalStorageService


def _section_spec() -> InteractiveHtmlSectionSpec:
    return InteractiveHtmlSectionSpec(
        section_id="unit_1",
        title="检索增强生成",
        learning_goal="理解 RAG 的检索和生成流程",
        teaching_flow=[
            InteractiveHtmlTeachingBlock(block_id="unit_1_intro", block_type="intro", title="导入", teaching_role="set_context", content_goal="建立背景"),
            InteractiveHtmlTeachingBlock(block_id="unit_1_q1", block_type="single_choice", title="检查", teaching_role="diagnose", content_goal="检查理解", interaction_id="i_q1"),
        ],
        interaction_specs=[
            InteractiveHtmlInteractionSpec(
                interaction_id="i_q1",
                block_id="unit_1_q1",
                type="single_choice",
                event_type="single_choice_answered",
                prompt="RAG 首先做什么？",
                options=[
                    InteractiveHtmlInteractionOption(id="a", text="检索资料", is_correct=True, feedback="正确"),
                    InteractiveHtmlInteractionOption(id="b", text="直接输出", is_correct=False, feedback="再想想"),
                ],
                target_concepts=["RAG 流程"],
            )
        ],
    )


def _content_spec() -> InteractiveHtmlSpec:
    return InteractiveHtmlSpec(
        lesson_id="lesson_1",
        title="RAG 入门",
        meta=InteractiveHtmlMeta(audience="初学者"),
        sections=[_section_spec()],
    )


def _render_model(image_src: str = "/api/assets/course_image/download") -> InteractiveHtmlRenderModel:
    return InteractiveHtmlRenderModel(
        lesson_id="lesson_1",
        title="RAG 入门",
        sections=[
            InteractiveHtmlRenderedUnit(
                section_id="unit_1",
                title="检索增强生成",
                learning_goal="理解 RAG 的检索和生成流程",
                style_scope_id="ih-scope-unit_1",
                html_fragment=f"""
                <section id="unit_1" class="ih-unit ih-scope-unit_1" data-section-id="unit_1">
                  <article class="ih-block ih-block--intro" data-block-id="unit_1_intro" data-block-type="intro">
                    <h3>什么是 RAG</h3>
                    <p>RAG 会先检索资料，再组织生成回答。</p>
                    <img src="{image_src}" alt="课程配图" />
                  </article>
                  <article class="ih-block ih-block--quiz" data-block-id="unit_1_q1" data-block-type="quiz">
                    <p>RAG 首先做什么？</p>
                    <button class="ih-btn" data-ih-action="single-choice" data-interaction-id="i_q1" data-option-id="a">检索资料</button>
                    <textarea data-ih-input-for="i_q1"></textarea>
                  </article>
                </section>
                """,
                css_fragment=".ih-scope-unit_1 { color: #111827; }",
                block_manifest=[
                    InteractiveHtmlRenderBlockRef(block_id="unit_1_intro", type="intro", title="什么是 RAG", teaching_role="set_context"),
                    InteractiveHtmlRenderBlockRef(block_id="unit_1_q1", type="quiz", title="检查", teaching_role="diagnose", interaction_ids=["i_q1"]),
                ],
                interaction_manifest=[
                    InteractionRenderRef(interaction_id="i_q1", section_id="unit_1", type="single_choice", target_concepts=["RAG 流程"], event_type="single_choice_answered")
                ],
            )
        ],
    )


def _event() -> dict:
    request = SubmitEventRequest(
        section_id="unit_1",
        block_id="unit_1_q1",
        interaction_id="i_q1",
        event_type="single_choice_answered",
        payload=LearningEventPayload(selected_option_ids=["a"], correct_option_ids=["a"], is_correct=True),
    )
    return {
        "event_id": "event_1",
        "lesson_id": "lesson_1",
        "session_id": "session_1",
        "section_id": request.section_id,
        "block_id": request.block_id,
        "interaction_id": request.interaction_id,
        "event_type": request.event_type,
        "payload": request.payload.model_dump(),
        "created_at": "2026-05-22T00:00:00+00:00",
    }


def test_static_handout_preserves_online_shell_and_removes_only_interaction_controls(tmp_path) -> None:
    html = InteractiveHtmlStaticHandoutRenderer(storage_service=LocalStorageService(storage_root=tmp_path)).render(
        _content_spec(),
        _render_model(),
        [_event()],
        session_id="session_1",
    )

    assert 'class="ih-app ih-app--offline"' in html
    assert "ih-sidebar" in html
    assert "ih-module-card" in html
    assert "--ih-primary: #6d5dfc" in html
    assert "--ih-bg: #f7f4ef" in html
    assert 'data-ih-offline-nav="unit_1"' in html
    assert "function activateOfflineSection" in html
    assert ".ih-scope-unit_1 { color: #111827; }" in html
    assert "RAG 会先检索资料" in html
    assert '<button class="ih-btn"' not in html
    assert "<textarea" not in html
    assert "data-ih-action" not in html
    assert "答题记录" in html
    assert "学生回答" in html
    assert "检索资料" in html
    assert "summary-card" not in html


def test_static_handout_uses_frontend_preview_navigation_pattern(tmp_path) -> None:
    second_unit = _render_model().sections[0].model_copy(
        update={
            "section_id": "unit_2",
            "title": "第二节",
            "learning_goal": "继续学习",
            "style_scope_id": "ih-scope-unit_2",
            "html_fragment": '<section id="unit_2" class="ih-unit ih-scope-unit_2" data-section-id="unit_2"><article class="ih-block" data-block-id="unit_2_intro" data-block-type="intro"><h3>第二节</h3><p>第二节内容。</p></article></section>',
            "css_fragment": ".ih-scope-unit_2 { color: #222; }",
        }
    )
    model = _render_model().model_copy(update={"sections": [_render_model().sections[0], second_unit]})

    html = InteractiveHtmlStaticHandoutRenderer(storage_service=LocalStorageService(storage_root=tmp_path)).render(
        _content_spec(),
        model,
        [_event()],
        session_id="session_1",
    )

    assert '<button class="ih-nav__link active" type="button" data-ih-offline-nav="unit_1">' in html
    assert '<button class="ih-nav__link" type="button" data-ih-offline-nav="unit_2">' in html
    assert 'data-ih-offline-section="unit_1"' in html
    assert 'data-ih-offline-section="unit_2" hidden' in html


def test_static_handout_inlines_service_asset_images(tmp_path) -> None:
    storage = LocalStorageService(storage_root=tmp_path)
    storage.save_bytes(
        asset_id="course_image",
        filename="course_image.png",
        content=b"fake-image",
        content_type="image/png",
        kind="image",
    )

    html = InteractiveHtmlStaticHandoutRenderer(storage_service=storage).render(
        _content_spec(),
        _render_model(),
        [_event()],
        session_id="session_1",
    )

    assert 'src="data:image/png;base64,ZmFrZS1pbWFnZQ=="' in html
    assert "/api/assets/course_image/download" not in html
