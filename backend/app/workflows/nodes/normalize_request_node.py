from app.core.task import TaskStatus
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.helpers import build_progress


def normalize_request(state: ContentGenerationState) -> dict[str, object]:
    options = state.raw_request.get("generation_options", {}) if state.raw_request else {}
    
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
        "include_images": bool(options.get("include_images", True)) if isinstance(options, dict) else True,
        "include_charts": bool(options.get("include_charts", False)) if isinstance(options, dict) else False,
        "include_mindmap": bool(options.get("include_mindmap", False)) if isinstance(options, dict) else False,
        "image_style": options.get("image_style") if isinstance(options, dict) else None,
        "citation_policy": str(options.get("citation_policy", "light")) if isinstance(options, dict) else "light",
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
