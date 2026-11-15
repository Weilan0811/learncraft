from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import ContentType, SchemaModel


class AttachmentDoc(SchemaModel):
    """A user-supplied material attached to one generation task.

    Plain markdown/text content for now (no multipart upload); the material is
    chunked into the task's own retrieval namespace and can be searched on its
    own (materials_only) or fused with the platform KB (fused).
    """

    filename: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=200_000)


class GenerationOptions(SchemaModel):
    language: str = "zh-CN"
    audience: str | None = None
    difficulty: Literal["introductory", "intermediate", "advanced"] = "introductory"
    style: str = "educational"

    duration_minutes: int | None = None
    section_count: int | None = None
    slide_count: int | None = None
    max_section_count: int = 8
    max_slide_count: int = 12
    output_depth: Literal["brief", "standard", "detailed"] = "standard"

    image_style: str | None = None
    citation_policy: Literal["none", "light", "strict"] = "light"
    allow_fallback: bool = False

    slide_theme: str | None = None
    speaker_notes: bool = True
    pdf_options: dict[str, object] = Field(default_factory=dict)


class ContentGenerationRequest(SchemaModel):
    content_type: ContentType
    topic: str = Field(min_length=1)
    user_prompt: str = Field(min_length=1)
    system_prompt: str | None = None
    knowledge_base_ids: list[str] = Field(default_factory=list)
    # Task-scoped user materials and how the retriever should use them:
    # platform        -> ignore attachments, search the platform KB only (default)
    # materials_only  -> search attached materials only
    # fused           -> search both and merge rankings (attachment slightly favored)
    attachments: list[AttachmentDoc] = Field(default_factory=list)
    kb_mode: Literal["platform", "materials_only", "fused"] = "platform"
    generation_options: GenerationOptions = Field(default_factory=GenerationOptions)
    generation_options_fields_set: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_generation_options(self):
        options = self.generation_options
        if len(self.attachments) > 10:
            raise ValueError("at most 10 attachments per task")
        if self.kb_mode == "materials_only" and not self.attachments:
            raise ValueError("kb_mode=materials_only requires at least one attachment")
        if self.kb_mode == "fused" and not self.attachments:
            self.kb_mode = "platform"  # nothing to fuse: degrade quietly
        if self.content_type == "slide_deck":
            if options.slide_count is not None and not 1 <= options.slide_count <= 30:
                raise ValueError("slide_count must be between 1 and 30")
            if options.max_slide_count is not None and not 1 <= options.max_slide_count <= 30:
                raise ValueError("max_slide_count must be between 1 and 30")
            if options.slide_count is not None:
                options.max_slide_count = options.slide_count
        if self.content_type == "lecture":
            if options.duration_minutes is not None and options.duration_minutes <= 0:
                raise ValueError("duration_minutes must be greater than 0")
            if options.section_count is not None and not 1 <= options.section_count <= 30:
                raise ValueError("section_count must be between 1 and 30")
            if options.max_section_count is not None and not 1 <= options.max_section_count <= 30:
                raise ValueError("max_section_count must be between 1 and 30")
            if options.section_count is not None:
                options.max_section_count = options.section_count
        if not self.generation_options_fields_set:
            self.generation_options_fields_set = sorted(options.model_fields_set)
        return self
