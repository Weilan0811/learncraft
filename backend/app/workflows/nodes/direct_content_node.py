from datetime import UTC, datetime
from uuid import uuid4

from app.generators.social_post_generator import SocialPostGenerator
from app.renderers.social_post_renderer import SocialPostRenderer, to_wechat_claw_article
from app.schemas.elements import ImageElement
from app.schemas.specs import SocialPostSpec
from app.schemas.state import ContentGenerationState, TaskStreamEvent
from app.validators.social_post_validator import SocialPostValidator
from app.workflows.nodes.helpers import build_progress, ensure_monotonic_progress


def generate_direct_content(state: ContentGenerationState) -> dict[str, object]:
    if state.content_type != "social_post":
        return {"errors": state.errors + [f"Unsupported direct content type: {state.content_type}"], "current_node": "generate_direct_content"}
    spec = SocialPostGenerator().generate(state)
    event = TaskStreamEvent(
        event_id=f"event_{uuid4().hex[:12]}",
        task_id=state.request_id,
        type="direct_spec_ready",
        payload={"title": spec.title, "image_slots": len(spec.image_slots)},
        created_at=datetime.now(UTC).isoformat(),
    )
    return {
        "content_spec": spec,
        "elements": _elements_from_spec(spec),
        "stream_events": [*state.stream_events, event],
        "current_node": "generate_direct_content",
        "progress": ensure_monotonic_progress(state.progress, build_progress(stage="generating_direct_content", current_node="generate_direct_content")),
    }


def validate_direct_content(state: ContentGenerationState) -> dict[str, object]:
    if not isinstance(state.content_spec, SocialPostSpec):
        return {"errors": state.errors + ["SocialPostSpec is required for direct validation"], "current_node": "validate_direct_content"}
    validator = SocialPostValidator()
    available_chunk_ids = {chunk.id for chunk in [*state.planning_chunks, *state.retrieved_chunks]}
    pre_report = validator.validate_pre_assets(state.content_spec, available_chunk_ids=available_chunk_ids)
    article_json = to_wechat_claw_article(state.content_spec)
    spec = state.content_spec.model_copy(update={"article_json": article_json, "validation_report": pre_report})
    final_report = validator.validate_final(spec)
    errors = [issue.message for issue in [*pre_report.issues, *final_report.issues] if issue.severity == "error"]
    return {
        "content_spec": spec.model_copy(update={"validation_report": final_report if final_report.issues else pre_report}),
        "validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "current_node": "validate_direct_content",
        "progress": ensure_monotonic_progress(state.progress, build_progress(stage="validating_direct_content", current_node="validate_direct_content")),
    }


def route_after_direct_validation(state: ContentGenerationState) -> str:
    report = state.validation_report or {}
    return "pass" if report.get("passed") else "fail"


def render_direct_content(state: ContentGenerationState) -> dict[str, object]:
    if not isinstance(state.content_spec, SocialPostSpec):
        return {"errors": state.errors + ["SocialPostSpec is required for direct rendering"], "current_node": "render_direct_content"}
    render_model = SocialPostRenderer().render(state.content_spec, state.elements)
    validator = SocialPostValidator()
    final_report = validator.validate_final(
        state.content_spec.model_copy(update={"article_json": render_model.article_json}),
        html=render_model.html,
    )
    errors = [issue.message for issue in final_report.issues if issue.severity == "error"]
    event = TaskStreamEvent(
        event_id=f"event_{uuid4().hex[:12]}",
        task_id=state.request_id,
        type="direct_render_ready",
        payload={"title": render_model.title, "template": render_model.template},
        created_at=datetime.now(UTC).isoformat(),
    )
    return {
        "render_model": render_model,
        "partial_render_model": render_model,
        "validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "stream_events": [*state.stream_events, event],
        "current_node": "render_direct_content",
        "progress": ensure_monotonic_progress(state.progress, build_progress(stage="rendering", current_node="render_direct_content")),
    }


def _elements_from_spec(spec: SocialPostSpec) -> list[ImageElement]:
    elements: list[ImageElement] = []
    slots = {slot.slot_id: slot for slot in spec.image_slots}
    for asset in spec.image_assets:
        slot = slots.get(asset.slot_id)
        if asset.status != "generated" or slot is None:
            continue
        elements.append(
            ImageElement(
                id=_asset_id_from_url(asset.public_url or asset.local_path or asset.wechat_url) or f"{spec.id}_{asset.slot_id}",
                title=slot.caption,
                prompt=slot.prompt_en,
                asset_url=asset.public_url or asset.local_path or asset.wechat_url or "",
                alt_text=slot.caption,
                width=asset.width,
                height=asset.height,
                metadata={"slot_id": asset.slot_id, "content_type": "social_post"},
            )
        )
    return elements


def _asset_id_from_url(url: str | None) -> str | None:
    if not url or "/api/assets/" not in url:
        return None
    return url.split("/api/assets/", 1)[1].split("/", 1)[0] or None


__all__ = [
    "generate_direct_content",
    "validate_direct_content",
    "route_after_direct_validation",
    "render_direct_content",
]
