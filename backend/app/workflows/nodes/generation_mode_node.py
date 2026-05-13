from app.content_types.registry import get_content_type_profile
from app.schemas.state import ContentGenerationState


def route_generation_mode(state: ContentGenerationState) -> dict[str, object]:
    return {"current_node": "route_generation_mode"}


def route_generation_mode_choice(state: ContentGenerationState) -> str:
    return get_content_type_profile(state.content_type).generation_mode


__all__ = ["route_generation_mode", "route_generation_mode_choice"]
