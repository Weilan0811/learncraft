import json
from pathlib import Path

from app.generators.social_post_generator import SocialPostGenerator
from app.schemas.specs import ImageSlotPlan
from app.schemas.specs.social_post import ImageSlot, WechatArticleDraft, WechatBriefOutline
from app.schemas.state import ContentGenerationState, RetrievedChunk


PROMPT_ROOT = Path("backend/app/prompts")


def test_social_post_prompt_templates_accept_runtime_variables() -> None:
    payload = {
        "user_request": json.dumps({"topic": "agent workflow"}, ensure_ascii=False),
        "generation_options": json.dumps({"language": "zh-CN"}, ensure_ascii=False),
        "retrieved_chunks": json.dumps([{"id": "chunk_1", "content": "workflow notes"}], ensure_ascii=False),
        "outline": json.dumps({"topic": "agent workflow"}, ensure_ascii=False),
        "draft": json.dumps({"meta": {"title": "agent workflow"}}, ensure_ascii=False),
    }
    prompt_paths = [
        PROMPT_ROOT / "planner" / "social_post_outline.md",
        PROMPT_ROOT / "generator" / "social_post_draft.md",
        PROMPT_ROOT / "generator" / "social_post_image.md",
    ]

    for path in prompt_paths:
        formatted = path.read_text(encoding="utf-8").format(**payload)
        assert "agent workflow" in formatted
        assert "{user_request}" not in formatted
        assert "{{ user_request }}" not in formatted


def test_social_post_prompts_embed_wechat_writing_standards() -> None:
    outline_prompt = (PROMPT_ROOT / "planner" / "social_post_outline.md").read_text(encoding="utf-8")
    draft_prompt = (PROMPT_ROOT / "generator" / "social_post_draft.md").read_text(encoding="utf-8")
    image_prompt = (PROMPT_ROOT / "generator" / "social_post_image.md").read_text(encoding="utf-8")

    for text in (outline_prompt, draft_prompt, image_prompt):
        assert "docs/general.md" in text
        assert "docs/wechat.md" in text

    outline_markers = [
        "问题链",
        "讲清楚问题",
        "搭出结构",
        "给出判断",
        "标题党",
    ]
    for marker in outline_markers:
        assert marker in outline_prompt

    draft_markers = [
        "技术博主的个人分享",
        "不是教材，也不是产品文档",
        "每段 3-5 行",
        "不要超过 5 行",
        "标题建议控制在 20 字以内",
        "digest",
        "不要写“以上就是关于 X 的完整梳理”",
        "不要写“希望这篇文章能帮你建立起更系统的认知”",
        "结尾不是总结，是收束",
        "只给结论，不给推导过程",
        "引用外部观点后，要说明本文如何理解和使用该观点",
        "不要把论文摘要、产品介绍或新闻稿直接改写成文章",
        "一篇文章最多 1 条",
    ]
    for marker in draft_markers:
        assert marker in draft_prompt

    image_markers = [
        "公众号封面图",
        "推荐 2.35:1",
        "每 600-800 字配一张",
        "配图要承担解释功能",
        "避免纯装饰性插图",
    ]
    for marker in image_markers:
        assert marker in image_prompt


def test_social_post_real_mode_generator_uses_structured_prompt_sequence(monkeypatch) -> None:
    chunk = RetrievedChunk(
        id="chunk_1",
        source_id="doc_1",
        source_title="Workflow notes",
        content="Direct workflow keeps social posts out of the unit loop.",
    )
    state = ContentGenerationState(
        request_id="task_prompt",
        content_type="social_post",
        topic="Agent workflow",
        user_prompt="Write a WeChat article.",
        raw_request={"content_type": "social_post", "topic": "Agent workflow"},
        normalized_request={"language": "zh-CN"},
        planning_chunks=[chunk],
    )

    class RealSettings:
        provider_mode = "real"

    class FakeLLM:
        def __init__(self) -> None:
            self.schemas: list[str] = []

        def generate_structured(self, prompt: str, schema):
            self.schemas.append(schema.__name__)
            assert "Agent workflow" in prompt
            if schema is WechatBriefOutline:
                return WechatBriefOutline(
                    topic="Agent workflow",
                    article_type="engineering_practice",
                    writing_angle="Explain direct workflow clearly.",
                    core_question="How should social posts be generated?",
                    central_thesis="Use a direct workflow for single-artifact social posts.",
                    sections=[
                        {
                            "section_id": "sec-01",
                            "title": "Problem",
                            "core_question": "Why not unit loop?",
                            "key_points": ["It is one article."],
                            "evidence_refs": [{"chunk_id": "chunk_1", "title": "Workflow notes"}],
                        },
                        {
                            "section_id": "sec-02",
                            "title": "Workflow",
                            "core_question": "How does it run?",
                            "key_points": ["Generate outline, draft, image slots."],
                            "evidence_refs": [{"chunk_id": "chunk_1", "title": "Workflow notes"}],
                        },
                        {
                            "section_id": "sec-03",
                            "title": "Validation",
                            "core_question": "What is checked?",
                            "key_points": ["Validate structure and render HTML."],
                            "evidence_refs": [{"chunk_id": "chunk_1", "title": "Workflow notes"}],
                        },
                    ],
                )
            if schema is WechatArticleDraft:
                return WechatArticleDraft(
                    meta={"title": "Agent workflow", "digest": "A direct workflow article for WeChat preview."},
                    headline={"title": "Agent workflow", "body": ["Direct workflows fit single-article output."]},
                    sections=[
                        {"section_id": "sec-01", "cn": "Problem", "blocks": [{"type": "paragraph", "text": "One article needs one path."}], "citation_refs": [{"chunk_id": "chunk_1"}]},
                        {"section_id": "sec-02", "cn": "Workflow", "blocks": [{"type": "paragraph", "text": "Generate draft then render HTML."}], "citation_refs": [{"chunk_id": "chunk_1"}]},
                        {"section_id": "sec-03", "cn": "Validation", "blocks": [{"type": "paragraph", "text": "Check slots and HTML."}], "citation_refs": [{"chunk_id": "chunk_1"}]},
                    ],
                )
            if schema is ImageSlotPlan:
                return ImageSlotPlan(
                    image_slots=[
                        ImageSlot(
                            slot_id="cover",
                            target="meta.cover_image",
                            target_path="meta.cover_image",
                            aspect_ratio="2.35:1",
                            caption="Cover",
                            visual_type="cover",
                            purpose="Show the article theme.",
                            context_summary="Agent workflow",
                            prompt_en="Professional WeChat cover about agent workflow.",
                        )
                    ]
                )
            raise AssertionError(schema)

    class FakeImageService:
        def generate_image(self, title: str, description: str, aspect_ratio: str = "16:9", asset_id: str | None = None):
            from app.schemas.elements import ImageElement

            return ImageElement(
                id=asset_id or title,
                title=title,
                prompt=description,
                asset_url=f"/api/assets/{asset_id}/download",
                alt_text=title,
                width=1024,
                height=576,
            )

    fake_llm = FakeLLM()
    monkeypatch.setattr("app.generators.social_post_generator.get_settings", lambda: RealSettings())
    monkeypatch.setattr("app.generators.social_post_generator.get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(
        "app.generators.social_post_generator.get_image_generation_service",
        lambda: FakeImageService(),
    )

    spec = SocialPostGenerator().generate(state)

    assert spec.title == "Agent workflow"
    assert [slot.slot_id for slot in spec.image_slots] == ["cover"]
    assert fake_llm.schemas == ["WechatBriefOutline", "WechatArticleDraft", "ImageSlotPlan"]


def test_social_post_real_mode_normalizes_missing_citations_and_provider_cover_ratio(monkeypatch) -> None:
    state = ContentGenerationState(
        request_id="task_prompt",
        content_type="social_post",
        topic="Agent workflow",
        user_prompt="Write a WeChat article.",
        raw_request={"content_type": "social_post", "topic": "Agent workflow"},
        normalized_request={"language": "zh-CN"},
        planning_chunks=[],
        retrieved_chunks=[],
    )

    class RealSettings:
        provider_mode = "real"

    class FakeLLM:
        def generate_structured(self, prompt: str, schema):
            if schema is WechatBriefOutline:
                return WechatBriefOutline(
                    topic="Agent workflow",
                    article_type="engineering_practice",
                    writing_angle="Explain direct workflow clearly.",
                    core_question="How should social posts be generated?",
                    central_thesis="Use a direct workflow for single-artifact social posts.",
                    sections=[
                        {"section_id": "sec-01", "title": "Problem", "core_question": "Why not unit loop?"},
                        {"section_id": "sec-02", "title": "Workflow", "core_question": "How does it run?"},
                        {"section_id": "sec-03", "title": "Validation", "core_question": "What is checked?"},
                    ],
                )
            if schema is WechatArticleDraft:
                return WechatArticleDraft(
                    meta={"title": "Agent workflow", "digest": "A direct workflow article for WeChat preview."},
                    headline={"title": "Agent workflow", "body": ["Direct workflows fit single-article output."]},
                    sections=[
                        {"section_id": "sec-01", "cn": "Problem", "blocks": [{"type": "paragraph", "text": "One article needs one path."}]},
                        {"section_id": "sec-02", "cn": "Workflow", "blocks": [{"type": "paragraph", "text": "Generate draft then render HTML."}]},
                        {"section_id": "sec-03", "cn": "Validation", "blocks": [{"type": "paragraph", "text": "Check slots and HTML."}]},
                    ],
                )
            if schema is ImageSlotPlan:
                return ImageSlotPlan(
                    image_slots=[
                        ImageSlot(
                            slot_id="cover",
                            target="meta.cover_image",
                            target_path="meta.cover_image",
                            aspect_ratio="2.35:1",
                            caption="Cover",
                            visual_type="cover",
                            purpose="Show the article theme.",
                            context_summary="Agent workflow",
                            prompt_en="Professional WeChat cover about agent workflow.",
                        ),
                        ImageSlot(
                            slot_id="headline",
                            target="headline.image",
                            target_path="headline.image",
                            aspect_ratio="16:9",
                            caption="Headline",
                            visual_type="workflow_diagram",
                            purpose="Show the workflow.",
                            context_summary="Agent workflow",
                            prompt_en="Professional WeChat workflow diagram.",
                        ),
                    ]
                )
            raise AssertionError(schema)

    class FakeImageService:
        def __init__(self) -> None:
            self.aspect_ratios: list[str] = []

        def generate_image(self, title: str, description: str, aspect_ratio: str = "16:9", asset_id: str | None = None):
            from app.schemas.elements import ImageElement

            self.aspect_ratios.append(aspect_ratio)
            return ImageElement(
                id=asset_id or title,
                title=title,
                prompt=description,
                asset_url=f"/api/assets/{asset_id}/download",
                alt_text=title,
                width=1024,
                height=576,
            )

    fake_image_service = FakeImageService()
    monkeypatch.setattr("app.generators.social_post_generator.get_settings", lambda: RealSettings())
    monkeypatch.setattr("app.generators.social_post_generator.get_llm_service", lambda: FakeLLM())
    monkeypatch.setattr("app.generators.social_post_generator.get_image_generation_service", lambda: fake_image_service)

    spec = SocialPostGenerator().generate(state)

    assert all(section.citation_refs for section in spec.draft.sections)
    assert all(block.citation_refs for section in spec.draft.sections for block in section.blocks if hasattr(block, "citation_refs"))
    assert [asset.status for asset in spec.image_assets] == ["generated", "generated"]
    assert fake_image_service.aspect_ratios == ["21:9", "16:9"]


def test_social_post_real_mode_llm_failure_is_not_silent_fallback(monkeypatch) -> None:
    state = ContentGenerationState(
        request_id="task_prompt_failure",
        content_type="social_post",
        topic="Agent workflow",
        user_prompt="Write a WeChat article.",
        raw_request={"content_type": "social_post", "topic": "Agent workflow"},
        normalized_request={"language": "zh-CN"},
    )

    class RealSettings:
        provider_mode = "real"

    class FailingLLM:
        def generate_structured(self, prompt: str, schema):
            raise RuntimeError("schema validation failed")

    monkeypatch.setattr("app.generators.social_post_generator.get_settings", lambda: RealSettings())
    monkeypatch.setattr("app.generators.social_post_generator.get_llm_service", lambda: FailingLLM())

    try:
        SocialPostGenerator().generate(state)
    except RuntimeError as exc:
        assert "social_post_outline_generation failed" in str(exc)
        assert "schema validation failed" in str(exc)
    else:
        raise AssertionError("real-mode LLM failure should not silently fall back")
