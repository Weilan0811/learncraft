from typing import Literal

from pydantic import Field

from app.schemas.base import Metadata, SchemaModel


class BaseElement(SchemaModel):
    id: str
    type: str
    title: str
    metadata: Metadata = Field(default_factory=dict)


class TextElement(BaseElement):
    type: Literal["text"] = "text"
    content: str
    citations: list[str] = Field(default_factory=list)


class ImageElement(BaseElement):
    type: Literal["image"] = "image"
    prompt: str
    asset_url: str
    alt_text: str


class ChartElement(BaseElement):
    type: Literal["chart"] = "chart"
    chart_type: Literal["bar", "line", "pie"] = "bar"
    description: str | None = None
    x_axis: dict[str, object] = Field(default_factory=dict)
    y_axis: dict[str, object] = Field(default_factory=dict)
    series: list[dict[str, object]] = Field(default_factory=list)


class MindmapElement(BaseElement):
    type: Literal["mindmap"] = "mindmap"
    markdown: str


class TableElement(BaseElement):
    type: Literal["table"] = "table"
    columns: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)


class QuizElement(BaseElement):
    type: Literal["quiz"] = "quiz"
    questions: list[dict[str, object]] = Field(default_factory=list)


class Citation(BaseElement):
    type: Literal["citation"] = "citation"
    source_id: str
    source_title: str
    content: str
    url: str | None = None


ContentElement = TextElement | ImageElement | ChartElement | MindmapElement | TableElement | QuizElement | Citation
