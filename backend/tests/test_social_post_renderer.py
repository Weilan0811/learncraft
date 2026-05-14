from pathlib import Path

from app.generators.social_post_generator import SocialPostGenerator
from app.renderers.social_post_renderer import SocialPostRenderer, to_wechat_claw_article
from app.schemas.state import ContentGenerationState, RetrievedChunk
from app.services.wechat_claw_renderer import WechatClawRenderer


def build_state() -> ContentGenerationState:
    chunk = RetrievedChunk(
        id="chunk_1",
        source_id="doc_1",
        source_title="Workflow notes",
        content="Direct workflow is useful for content types that produce one artifact.",
    )
    return ContentGenerationState(
        request_id="task_social_render",
        content_type="social_post",
        topic="Direct workflow",
        user_prompt="Write a WeChat article about direct workflow.",
        planning_chunks=[chunk],
        retrieved_chunks=[chunk],
        normalized_request={"language": "zh-CN", "include_images": True},
    )


def test_wechat_article_adapter_binds_cover_headline_and_section_images() -> None:
    spec = SocialPostGenerator().generate(build_state())
    spec.image_assets = [
        spec.image_assets[0].model_copy(
            update={"slot_id": "cover", "status": "generated", "local_path": "/api/assets/cover/download", "public_url": None}
        ),
        spec.image_assets[0].model_copy(
            update={"slot_id": "headline", "status": "generated", "local_path": "/api/assets/headline/download", "public_url": None}
        ),
        spec.image_assets[0].model_copy(
            update={"slot_id": "sec-01", "status": "generated", "local_path": "/api/assets/sec/download", "public_url": None}
        ),
    ]

    article = to_wechat_claw_article(spec)

    assert article["meta"]["cover_image"]["url"] == "/api/assets/cover/download"
    assert article["headline"]["image"]["url"] == "/api/assets/headline/download"
    assert article["sections"][0]["image"]["url"] == "/api/assets/sec/download"
    assert "citation_refs" not in article["sections"][0]


def test_wechat_claw_renderer_writes_html_and_json(tmp_path: Path) -> None:
    spec = SocialPostGenerator().generate(build_state())
    article = to_wechat_claw_article(spec)

    render_model = WechatClawRenderer(storage_root=tmp_path).render(
        task_id="task_social_render",
        article_json=article,
        check=True,
    )

    assert render_model.render_type == "social_post"
    assert render_model.html
    assert "Direct workflow" in render_model.html
    assert {file.file_type for file in render_model.export_files} == {"html", "json"}


def test_social_post_renderer_returns_preview_assets(tmp_path: Path) -> None:
    spec = SocialPostGenerator().generate(build_state())
    renderer = SocialPostRenderer(wechat_renderer=WechatClawRenderer(storage_root=tmp_path))

    render_model = renderer.render(spec, elements=[])

    assert render_model.render_type == "social_post"
    assert render_model.article_json["template"] == spec.draft.template
    assert render_model.preview_assets
