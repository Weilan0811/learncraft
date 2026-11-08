from app.content_types.base import fixed_element_flags
from app.content_types.registry import get_content_type_profile
from app.core.task import TaskStatus
from app.core.config import get_settings
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.helpers import build_progress


def normalize_request(state: ContentGenerationState) -> dict[str, object]:
    options = state.raw_request.get("generation_options", {}) if state.raw_request else {}
    explicit_option_fields = set(state.raw_request.get("generation_options_fields_set", []) if state.raw_request else [])
    settings = get_settings()
    allow_fallback = (
        bool(options.get("allow_fallback", settings.allow_fallback))
        if isinstance(options, dict) and "allow_fallback" in explicit_option_fields
        else settings.allow_fallback
    )
    element_flags = fixed_element_flags(get_content_type_profile(state.content_type).element_policy)
    
    normalized = {
        "content_type": state.content_type,
        "topic": state.topic.strip(),
        "user_prompt": state.user_prompt.strip(),
        "language": str(options.get("language", "zh-CN")) if isinstance(options, dict) else "zh-CN",
        "audience": options.get("audience") if isinstance(options, dict) else None,
        "difficulty": str(options.get("difficulty", "introductory")) if isinstance(options, dict) else "introductory",
        "style": str(options.get("style", "educational")) if isinstance(options, dict) else "educational",
        "duration_minutes": options.get("duration_minutes") if isinstance(options, dict) else None,
        "section_count": options.get("section_count") if isinstance(options, dict) else None,
        "slide_count": options.get("slide_count") if isinstance(options, dict) else None,
        "max_section_count": options.get("max_section_count") if isinstance(options, dict) else 8,
        "max_slide_count": options.get("max_slide_count") if isinstance(options, dict) else 12,
        "output_depth": str(options.get("output_depth", "standard")) if isinstance(options, dict) else "standard",
        **element_flags,
        "image_style": options.get("image_style") if isinstance(options, dict) else None,
        "citation_policy": str(options.get("citation_policy", "light")) if isinstance(options, dict) else "light",
        "allow_fallback": allow_fallback,
        "slide_theme": options.get("slide_theme") if isinstance(options, dict) else None,
        "speaker_notes": bool(options.get("speaker_notes", True)) if isinstance(options, dict) else True,
    }
    
    if state.content_type == "slide_deck":
        if normalized["slide_count"] is not None:
            normalized["max_slide_count"] = normalized["slide_count"]
        if normalized["max_slide_count"] is None:
            normalized["max_slide_count"] = 12
    elif state.content_type == "lecture":
        if normalized["section_count"] is not None:
            normalized["max_section_count"] = normalized["section_count"]
        if normalized["max_section_count"] is None:
            normalized["max_section_count"] = 8
    
    return {
        "normalized_request": normalized,
        "current_node": "normalize_request",
        "status": TaskStatus.running,
        "progress": build_progress(stage="normalizing", current_node="normalize_request"),
    }
