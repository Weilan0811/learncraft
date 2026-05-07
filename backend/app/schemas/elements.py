from typing import Literal

from pydantic import Field

from app.schemas.base import Metadata, SchemaModel


class BaseElement(SchemaModel):
    id: str
    type: str
    title: str
    status: Literal["pending", "generating", "completed", "failed", "skipped"] = "completed"
    source_unit_id: str | None = None
    source_outline_unit_id: str | None = None
    source_chunk_ids: list[str] = Field(default_factory=list)
    metadata: Metadata = Field(default_factory=dict)
    generation_info: Metadata = Field(default_factory=dict)


class TextElement(BaseElement):
    type: Literal["text"] = "text"
    content: str
    citations: list[str] = Field(default_factory=list)


class ImageElement(BaseElement):
    type: Literal["image"] = "image"
    prompt: str
    asset_url: str
    alt_text: str
    width: int | None = None
    height: int | None = None
    format: str | None = None
    model: str | None = None
    retry_count: int = 0
    # TODO(MVP-image): Add generation parameters required by PRD acceptance:
    # width, height, format, model, retry count, and source section id.


class ChartElement(BaseElement):
    type: Literal["chart"] = "chart"
    chart_type: Literal["bar", "line", "pie"] = "bar"
    description: str | None = None
    x_axis: dict[str, object] = Field(default_factory=dict)
    y_axis: dict[str, object] = Field(default_factory=dict)
    series: list[dict[str, object]] = Field(default_factory=list)
    # TODO(P1-chart): Promote x_axis/y_axis/series to typed schemas that map
    # losslessly to ECharts options and static export artifacts.


class MindmapElement(BaseElement):
    type: Literal["mindmap"] = "mindmap"
    markdown: str
    render_hints: Metadata = Field(default_factory=dict)
    # TODO(P1-mindmap): Track generated SVG/PNG asset URLs for PDF and Slide
    # embedding after Markmap rendering is implemented.


class TableElement(BaseElement):
    type: Literal["table"] = "table"
    columns: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)


class QuizElement(BaseElement):
    type: Literal["quiz"] = "quiz"
    questions: list[dict[str, object]] = Field(default_factory=list)
    # TODO(P1-quiz): Replace dict questions with typed single-choice,
    # multi-choice, and short-answer schemas.


class Citation(BaseElement):
    type: Literal["citation"] = "citation"
    source_id: str
    source_title: str
    content: str
    url: str | None = None


ContentElement = TextElement | ImageElement | ChartElement | MindmapElement | TableElement | QuizElement | Citation
