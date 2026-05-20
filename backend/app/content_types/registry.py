from app.content_types.base import ContentTypeProfile
from app.content_types.interactive_html import build_interactive_html_profile
from app.content_types.lecture import build_lecture_profile
from app.content_types.podcast import build_podcast_profile
from app.content_types.slide_deck import build_slide_deck_profile
from app.content_types.social_post import build_social_post_profile
from app.schemas.base import ContentType


CONTENT_TYPE_PROFILES: dict[str, ContentTypeProfile] = {
    "lecture": build_lecture_profile(),
    "slide_deck": build_slide_deck_profile(),
    "social_post": build_social_post_profile(),
    "podcast_script": build_podcast_profile(),
    "interactive_html": build_interactive_html_profile(),
}


def get_content_type_profile(content_type: ContentType | str) -> ContentTypeProfile:
    try:
        return CONTENT_TYPE_PROFILES[str(content_type)]
    except KeyError as exc:
        supported = ", ".join(sorted(CONTENT_TYPE_PROFILES))
        raise ValueError(f"Unsupported content type: {content_type}. Registered content types: {supported}") from exc


def registered_content_types() -> tuple[str, ...]:
    return tuple(sorted(CONTENT_TYPE_PROFILES))
