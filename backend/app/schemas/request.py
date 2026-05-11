from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import ContentType, SchemaModel


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

    include_images: bool = True
    include_charts: bool = False
    include_mindmap: bool = False
    image_style: str | None = None
    citation_policy: Literal["none", "light", "strict"] = "light"

    slide_theme: str | None = None
    speaker_notes: bool = True
    pdf_options: dict[str, object] = Field(default_factory=dict)


class ContentGenerationRequest(SchemaModel):
    content_type: ContentType
    topic: str = Field(min_length=1)
    user_prompt: str = Field(min_length=1)
    system_prompt: str | None = None
    knowledge_base_ids: list[str] = Field(default_factory=list)
    generation_options: GenerationOptions = Field(default_factory=GenerationOptions)

    @model_validator(mode="after")
    def validate_generation_options(self):
        options = self.generation_options
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
        return self
