from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ContentType = Literal[
    "lecture",
    "slide_deck",
    "social_post",
    "podcast_script",
    "video_script",
    "project_task",
    "quiz_pack",
    "learning_path",
]

MvpContentType = Literal["lecture", "slide_deck"]

ElementType = Literal[
    "text",
    "image",
    "chart",
    "mindmap",
    "table",
    "quiz",
    "citation",
    "audio_script",
    "audio_file",
    "video_script",
    "interactive_task",
    "project_task",
]

ExportType = Literal["preview", "pdf", "slide_json", "image_assets", "pptx", "markdown", "html"]

Metadata = dict[str, Any]


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class VersionedSchema(SchemaModel):
    id: str
    version: str
    metadata: Metadata = Field(default_factory=dict)
