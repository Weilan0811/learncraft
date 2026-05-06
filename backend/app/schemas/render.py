from typing import Literal

from pydantic import Field

from app.schemas.base import Metadata, SchemaModel


class RenderBlock(SchemaModel):
    id: str
    type: str
    title: str | None = None
    content: str | None = None
    asset_url: str | None = None
    metadata: Metadata = Field(default_factory=dict)


class LectureRenderSection(SchemaModel):
    id: str
    title: str
    render_blocks: list[RenderBlock] = Field(default_factory=list)


class LectureRenderModel(SchemaModel):
    render_type: Literal["lecture_page"] = "lecture_page"
    title: str
    objectives: list[str] = Field(default_factory=list)
    sections: list[LectureRenderSection] = Field(default_factory=list)
    printable_model: dict[str, object] = Field(default_factory=dict)
    # TODO(MVP-pdf): Replace printable_model dict with a typed print/PDF model
    # covering table of contents, page size, margins, headers, and references.


class SlidePageModel(SchemaModel):
    version: Literal["scenekit.slide/v1"] = "scenekit.slide/v1"
    page: dict[str, object]
    # TODO(MVP-slide-render): Replace page dict with the official
    # scene-content-kit page schema once the renderer package is integrated.


class SlideRenderModel(SchemaModel):
    render_type: Literal["slide_deck"] = "slide_deck"
    title: str
    pages: list[SlidePageModel] = Field(default_factory=list)


RenderModel = LectureRenderModel | SlideRenderModel
