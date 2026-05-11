from typing import Literal

from pydantic import Field

from app.schemas.base import SchemaModel


class KitTheme(SchemaModel):
    backgroundColor: str
    themeColors: list[str] = Field(min_length=1)
    fontColor: str
    fontName: str


class KitSlideBackgroundImage(SchemaModel):
    src: str
    size: Literal["cover", "contain", "repeat"] = "cover"


class KitSlideGradientStop(SchemaModel):
    pos: float = Field(ge=0, le=1)
    color: str


class KitSlideGradient(SchemaModel):
    type: Literal["linear", "radial"] = "linear"
    rotate: int | None = None
    colors: list[KitSlideGradientStop] = Field(default_factory=list)


class KitSlideBackground(SchemaModel):
    type: Literal["solid", "gradient", "image"] = "solid"
    color: str | None = None
    image: KitSlideBackgroundImage | None = None
    gradient: KitSlideGradient | None = None


class KitElementShadow(SchemaModel):
    x: int
    y: int
    blur: int
    color: str


class KitElementOutline(SchemaModel):
    width: int | None = None
    color: str | None = None
    style: Literal["solid", "dashed", "dotted"] | None = None


class KitBaseElement(SchemaModel):
    id: str
    type: str
    left: float
    top: float
    width: float
    height: float
    rotate: float
    name: str | None = None


class KitTextElement(KitBaseElement):
    type: Literal["text"] = "text"
    content: str
    defaultFontName: str | None = None
    defaultColor: str | None = None
    fontSize: int | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    align: Literal["left", "center", "right", "justify"] | None = None
    verticalAlign: Literal["top", "middle", "bottom"] | None = None
    fill: str | None = None
    opacity: float | None = Field(default=None, ge=0, le=1)
    lineHeight: float | None = None
    radius: int | None = None
    outline: KitElementOutline | None = None
    shadow: KitElementShadow | None = None


class KitImageElement(KitBaseElement):
    type: Literal["image"] = "image"
    src: str
    fixedRatio: bool | None = None
    radius: int | None = None
    opacity: float | None = Field(default=None, ge=0, le=1)
    shadow: KitElementShadow | None = None


class KitShapeElement(KitBaseElement):
    type: Literal["shape"] = "shape"
    shape: Literal["rect", "roundRect", "ellipse"] | None = None
    fill: str | None = None
    opacity: float | None = Field(default=None, ge=0, le=1)
    radius: int | None = None
    outline: KitElementOutline | None = None
    shadow: KitElementShadow | None = None


class KitLineElement(KitBaseElement):
    type: Literal["line"] = "line"
    start: tuple[float, float]
    end: tuple[float, float]
    color: str
    style: Literal["solid", "dashed", "dotted"] | None = None
    strokeWidth: int | None = None


class KitTableCellStyle(SchemaModel):
    bold: bool | None = None
    italic: bool | None = None
    color: str | None = None
    backcolor: str | None = None
    align: Literal["left", "center", "right", "justify"] | None = None
    fontSize: int | None = None


class KitTableCell(SchemaModel):
    id: str
    text: str
    colspan: int | None = None
    rowspan: int | None = None
    style: KitTableCellStyle | None = None


class KitTableElement(KitBaseElement):
    type: Literal["table"] = "table"
    data: list[list[KitTableCell]]
    outline: KitElementOutline | None = None
    fontSize: int | None = None
    fontName: str | None = None
    textColor: str | None = None


KitSlideElement = KitTextElement | KitImageElement | KitShapeElement | KitLineElement | KitTableElement


class KitSlidePage(SchemaModel):
    id: str
    title: str
    width: int
    height: int
    background: KitSlideBackground | None = None
    theme: KitTheme
    elements: list[KitSlideElement] = Field(default_factory=list)
    speakerNotes: str | None = None


class SlidePageModel(SchemaModel):
    version: Literal["scenekit.slide/v1"] = "scenekit.slide/v1"
    page: KitSlidePage


class SlideRenderModel(SchemaModel):
    render_type: Literal["slide_deck"] = "slide_deck"
    title: str
    pages: list[SlidePageModel] = Field(default_factory=list)
