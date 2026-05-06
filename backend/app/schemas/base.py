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
# TODO(schema-extension): When enabling non-MVP content types, add their Spec,
# Renderer, Exporter, frontend type, and workflow route at the same time.

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
# TODO(export-extension): Enable only formats with concrete exporter
# implementations in production request validation.

Metadata = dict[str, Any]


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class VersionedSchema(SchemaModel):
    id: str
    version: str
    metadata: Metadata = Field(default_factory=dict)
