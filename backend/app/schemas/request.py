from pydantic import Field

from app.schemas.base import ExportType, MvpContentType, SchemaModel


class GenerationOptions(SchemaModel):
    language: str = "zh-CN"
    difficulty: str = "introductory"
    style: str = "educational"
    include_images: bool = True
    include_charts: bool = False
    include_mindmap: bool = False


class ContentGenerationRequest(SchemaModel):
    content_type: MvpContentType
    topic: str = Field(min_length=1)
    user_prompt: str = Field(min_length=1)
    system_prompt: str | None = None
    knowledge_base_ids: list[str] = Field(default_factory=list)
    output_formats: list[ExportType] = Field(default_factory=lambda: ["preview"])
    generation_options: GenerationOptions = Field(default_factory=GenerationOptions)
