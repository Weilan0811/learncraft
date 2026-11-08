from app.content_types.base import ContentTypeProfile, ElementPolicy
from app.renderers.slide_renderer import SlideRenderer
from app.schemas.render import SlideRenderModel
from app.schemas.specs import SlideDeckSpec, SlideSpecPage


def build_slide_deck_profile() -> ContentTypeProfile:
    return ContentTypeProfile(
        content_type="slide_deck",
        generation_mode="unit_loop",
        unit_type="slide",
        requires_outline=True,
        supports_unit_streaming=False,
        planner_prompt_name="slide_outline.md",
        unit_spec_prompt_name="slide_deck_spec.md",
        spec_schema=SlideDeckSpec,
        unit_spec_schema=SlideSpecPage,
        render_model_schema=SlideRenderModel,
        renderer_factory=SlideRenderer,
        generator_name="slide_unit_spec",
        element_policy=ElementPolicy(
            allowed_elements=("image",),
            default_required_elements=("image",),
            optional_elements=(),
        ),
        exporter_types=("slide_json", "image_assets"),
    )
