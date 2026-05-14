from app.generators.social_post_generator import SocialPostGenerator
from app.renderers.social_post_renderer import to_wechat_claw_article
from app.schemas.state import ContentGenerationState, RetrievedChunk
from app.validators.social_post_validator import SocialPostValidator
from app.workflows.nodes.direct_content_node import validate_direct_content


def build_state() -> ContentGenerationState:
    chunk = RetrievedChunk(
        id="chunk_1",
        source_id="doc_1",
        source_title="Workflow notes",
        content="Direct workflow is useful for content types that produce one artifact.",
    )
    return ContentGenerationState(
        request_id="task_social",
        content_type="social_post",
        topic="Direct workflow",
        user_prompt="Write a WeChat article about direct workflow.",
        planning_chunks=[chunk],
        retrieved_chunks=[chunk],
        normalized_request={"language": "zh-CN", "include_images": True},
    )


def test_stub_social_post_generator_builds_valid_article_with_cover_slot() -> None:
    spec = SocialPostGenerator().generate(build_state())
    report = SocialPostValidator().validate_pre_assets(spec, available_chunk_ids={"chunk_1"})

    assert report.ok is True
    assert spec.draft.meta.title
    assert len(spec.draft.sections) >= 3
    assert any(slot.slot_id == "cover" and slot.target_path == "meta.cover_image" for slot in spec.image_slots)
    assert all(section.citation_refs for section in spec.draft.sections)


def test_social_post_validator_rejects_duplicate_slots_and_invalid_target_path() -> None:
    spec = SocialPostGenerator().generate(build_state())
    first_slot = spec.image_slots[0]
    spec.image_slots.append(first_slot.model_copy(update={"target_path": "sections[99].image"}))

    report = SocialPostValidator().validate_pre_assets(spec, available_chunk_ids={"chunk_1"})

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert "image slot ids must be unique" in messages
    assert any("target_path" in message for message in messages)


def test_social_post_validator_requires_generated_cover_asset_for_final_validation() -> None:
    spec = SocialPostGenerator().generate(build_state())
    spec = spec.model_copy(update={"image_assets": []})

    report = SocialPostValidator().validate_final(spec, html="<article>No placeholders</article>")

    assert report.ok is False
    assert any("required image slot cover is missing a generated asset" == issue.message for issue in report.issues)


def test_direct_content_validation_does_not_duplicate_pre_asset_errors() -> None:
    spec = SocialPostGenerator().generate(build_state())
    spec.draft.sections[0].citation_refs = []
    spec = spec.model_copy(update={"article_json": to_wechat_claw_article(spec), "image_assets": []})
    state = build_state().model_copy(update={"content_spec": spec})

    result = validate_direct_content(state)

    assert result["errors"].count("section must include citation_refs") == 1
