from pydantic import TypeAdapter

from app.schemas.render import RenderModel
from app.schemas.render.social_post import SocialPostRenderModel
from app.schemas.specs import ContentSpec
from app.schemas.specs.social_post import (
    ImageAsset,
    ImageSlot,
    ImageSlotTarget,
    SocialPostSpec,
    WechatArticleDraft,
    WechatBriefOutline,
    WechatHeadline,
    WechatMeta,
    WechatOutlineSection,
    WechatSection,
    ParagraphBlock,
)


def build_social_post_spec() -> SocialPostSpec:
    outline = WechatBriefOutline(
        topic="AI agent workflows",
        article_type="engineering_practice",
        writing_angle="Explain how direct workflows keep small content types simple.",
        core_question="How should a backend route social posts without bloating the main graph?",
        central_thesis="A direct workflow keeps social posts isolated while reusing shared services.",
        title_candidates=["Direct workflow for social posts"],
        sections=[
            WechatOutlineSection(
                section_id="sec-01",
                title="Why direct workflow",
                core_question="Why not use a unit loop?",
                key_points=["Social posts are single artifacts"],
                evidence_refs=[{"chunk_id": "chunk_1", "title": "Workflow notes"}],
            ),
            WechatOutlineSection(
                section_id="sec-02",
                title="How it fits",
                core_question="How does it reuse infrastructure?",
                key_points=["Reuse storage and render snapshots"],
                evidence_refs=[{"chunk_id": "chunk_1", "title": "Workflow notes"}],
            ),
            WechatOutlineSection(
                section_id="sec-03",
                title="What to validate",
                core_question="What keeps output stable?",
                key_points=["Validate article and image binding"],
                evidence_refs=[{"chunk_id": "chunk_1", "title": "Workflow notes"}],
            ),
        ],
    )
    draft = WechatArticleDraft(
        meta=WechatMeta(title="Direct workflow", digest="A backend plan for rendering social posts with HTML preview."),
        headline=WechatHeadline(title="Direct workflow", body=["Social posts are best generated as one coherent article."]),
        sections=[
            WechatSection(
                section_id="sec-01",
                cn="Why direct workflow",
                blocks=[ParagraphBlock(text="A social post is one article rather than a sequence of slides.")],
                citation_refs=[{"chunk_id": "chunk_1", "title": "Workflow notes"}],
            ),
            WechatSection(
                section_id="sec-02",
                cn="How it fits",
                blocks=[ParagraphBlock(text="The direct path can reuse retrieval, assets, snapshots, and exporters.")],
                citation_refs=[{"chunk_id": "chunk_1", "title": "Workflow notes"}],
            ),
            WechatSection(
                section_id="sec-03",
                cn="What to validate",
                blocks=[ParagraphBlock(text="Validation protects title length, citation coverage, and image binding.")],
                citation_refs=[{"chunk_id": "chunk_1", "title": "Workflow notes"}],
            ),
        ],
    )
    return SocialPostSpec(
        id="social_task_1",
        title="Direct workflow",
        outline=outline,
        draft=draft,
        image_slots=[
            ImageSlot(
                slot_id="cover",
                target=ImageSlotTarget.cover,
                target_path="meta.cover_image",
                aspect_ratio="2.35:1",
                caption="Cover",
                purpose="Show the article theme.",
                context_summary="Direct workflow overview",
                prompt_en="Professional editorial cover about direct workflow architecture.",
            )
        ],
        image_assets=[ImageAsset(slot_id="cover", status="generated", local_path="/api/assets/cover/download")],
    )


def test_social_post_spec_enters_content_spec_union() -> None:
    spec = build_social_post_spec()

    parsed = TypeAdapter(ContentSpec).validate_python(spec.model_dump(mode="json"))

    assert isinstance(parsed, SocialPostSpec)
    assert parsed.content_type == "social_post"
    assert parsed.platform == "wechat"


def test_social_post_render_model_enters_render_union() -> None:
    render_model = SocialPostRenderModel(
        title="Direct workflow",
        digest="A backend plan for social posts.",
        template="deep-analysis",
        html="<article>Direct workflow</article>",
        article_json={"template": "deep-analysis", "meta": {"title": "Direct workflow"}},
    )

    parsed = TypeAdapter(RenderModel).validate_python(render_model.model_dump(mode="json"))

    assert isinstance(parsed, SocialPostRenderModel)
    assert parsed.render_type == "social_post"
