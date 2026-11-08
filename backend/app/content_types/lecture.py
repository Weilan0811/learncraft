from app.content_types.base import ContentTypeProfile, ElementPolicy
from app.renderers.lecture_renderer import LectureRenderer
from app.schemas.render import LectureRenderModel
from app.schemas.specs import LectureSection, LectureSpec


def build_lecture_profile() -> ContentTypeProfile:
    return ContentTypeProfile(
        content_type="lecture",
        generation_mode="unit_loop",
        unit_type="section",
        requires_outline=True,
        supports_unit_streaming=False,
        planner_prompt_name="lecture_outline.md",
        unit_spec_prompt_name="lecture_spec.md",
        spec_schema=LectureSpec,
        unit_spec_schema=LectureSection,
        render_model_schema=LectureRenderModel,
        renderer_factory=LectureRenderer,
        generator_name="lecture_unit_spec",
        element_policy=ElementPolicy(
            allowed_elements=("image",),
            default_required_elements=("image",),
            optional_elements=(),
        ),
        exporter_types=("pdf", "markdown", "html", "image_assets"),
    )
