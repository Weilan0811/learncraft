from app.content_types.base import ContentTypeProfile, ElementPolicy
from app.renderers.podcast_renderer import PodcastRenderer
from app.schemas.render import PodcastRenderModel
from app.schemas.specs import PodcastSpec


def build_podcast_profile() -> ContentTypeProfile:
    return ContentTypeProfile(
        content_type="podcast_script",
        generation_mode="direct",
        unit_type="podcast",
        requires_outline=False,
        supports_unit_streaming=False,
        planner_prompt_name="",
        unit_spec_prompt_name="podcast_script.md",
        spec_schema=PodcastSpec,
        unit_spec_schema=PodcastSpec,
        render_model_schema=PodcastRenderModel,
        renderer_factory=PodcastRenderer,
        generator_name="podcast",
        element_policy=ElementPolicy(
            allowed_elements=("audio_script", "audio_file"),
            default_required_elements=("audio_script", "audio_file"),
            optional_elements=(),
        ),
        exporter_types=("markdown", "audio"),
    )
