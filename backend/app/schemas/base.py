from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ContentType = Literal[
    "lecture",
    "slide_deck",
    "social_post",
    "podcast_script",
    "interactive_html",
    "video_script",
    "project_task",
    "quiz_pack",
    "learning_path",
]
# Runtime generation support is controlled by app.content_types.registry.
# Schema boundaries intentionally accept future content types so they can be
# introduced without changing every request/state DTO again.

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

ExportType = Literal["pdf", "slide_json", "image_assets", "pptx", "markdown", "html", "audio"]
# TODO(export-extension): Enable only formats with concrete exporter
# implementations in production request validation.

Metadata = dict[str, Any]


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class VersionedSchema(SchemaModel):
    id: str
    version: str
    metadata: Metadata = Field(default_factory=dict)
