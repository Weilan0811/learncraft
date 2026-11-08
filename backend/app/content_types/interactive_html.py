from app.content_types.base import ContentTypeProfile, ElementPolicy
from app.renderers.interactive_html_composer import InteractiveHtmlComposer
from app.renderers.interactive_html_renderer import InteractiveHtmlRenderer
from app.schemas.render.interactive_html import InteractiveHtmlRenderModel
from app.schemas.specs.interactive_html import InteractiveHtmlSectionSpec, InteractiveHtmlSpec


def build_interactive_html_profile() -> ContentTypeProfile:
    return ContentTypeProfile(
        content_type="interactive_html",
        generation_mode="unit_loop",
        unit_type="interactive_section",
        requires_outline=True,
        supports_unit_streaming=True,
        planner_prompt_name="interactive_html_outline.md",
        unit_spec_prompt_name="interactive_html_unit_spec.md",
        spec_schema=InteractiveHtmlSpec,
        unit_spec_schema=InteractiveHtmlSectionSpec,
        render_model_schema=InteractiveHtmlRenderModel,
        renderer_factory=InteractiveHtmlRenderer,
        generator_name="interactive_html",
        element_policy=ElementPolicy(
            allowed_elements=(),
            default_required_elements=(),
            optional_elements=(),
        ),
        exporter_types=("html",),
    )
