from pydantic import Field

from app.schemas.base import MvpContentType, SchemaModel


class GenerationOptions(SchemaModel):
    language: str = "zh-CN"
    difficulty: str = "introductory"
    style: str = "educational"
    include_images: bool = True
    include_charts: bool = False
    include_mindmap: bool = False
    # TODO(MVP-options): Add PRD fields for audience, duration/slide count,
    # image style, citation policy, PDF options, and slide theme options.


class ContentGenerationRequest(SchemaModel):
    content_type: MvpContentType
    topic: str = Field(min_length=1)
    user_prompt: str = Field(min_length=1)
    system_prompt: str | None = None
    knowledge_base_ids: list[str] = Field(default_factory=list)
    generation_options: GenerationOptions = Field(default_factory=GenerationOptions)
    # TODO(MVP-request): Add validation rules for generation options by
    # content_type, for example lecture duration and slide deck page count.
