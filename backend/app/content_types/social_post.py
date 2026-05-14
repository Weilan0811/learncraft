from app.content_types.base import ContentTypeProfile, ElementPolicy
from app.renderers.social_post_renderer import SocialPostRenderer
from app.schemas.render import SocialPostRenderModel
from app.schemas.specs import SocialPostSpec


def build_social_post_profile() -> ContentTypeProfile:
    return ContentTypeProfile(
        content_type="social_post",
        generation_mode="direct",
        unit_type="article",
        requires_outline=False,
        supports_unit_streaming=False,
        planner_prompt_name="social_post_outline.md",
        unit_spec_prompt_name="social_post_draft.md",
        spec_schema=SocialPostSpec,
        unit_spec_schema=SocialPostSpec,
        render_model_schema=SocialPostRenderModel,
        renderer_factory=SocialPostRenderer,
        generator_name="social_post",
        element_policy=ElementPolicy(
            allowed_elements=("image",),
            default_required_elements=("image",),
            optional_elements=(),
        ),
        exporter_types=("html", "image_assets"),
    )
