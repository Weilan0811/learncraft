from app.generators.social_post_generator import SocialPostGenerator
from app.schemas.state import ContentGenerationState, RetrievedChunk
from app.validators.social_post_validator import SocialPostValidator


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
