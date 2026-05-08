from html import escape

from app.schemas.elements import ContentElement
from app.schemas.render import (
    KitElementOutline,
    KitElementShadow,
    KitImageElement,
    KitLineElement,
    KitShapeElement,
    KitSlideBackground,
    KitSlideElement,
    KitSlidePage,
    KitTextElement,
    KitTheme,
    SlidePageModel,
    SlideRenderModel,
)
from app.schemas.specs import SlideDeckSpec


SLIDE_WIDTH = 960
SLIDE_HEIGHT = 540


class SlideRenderer:
    def render(self, spec: SlideDeckSpec, elements: list[ContentElement]) -> SlideRenderModel:
        element_lookup = {element.id: element for element in elements}
        pages: list[SlidePageModel] = []
        for slide in spec.slides:
            theme = _theme_for_slide(spec, slide.order or len(pages) + 1)
            page_elements = _base_elements(slide.id, slide.title, slide.core_message, theme, slide.layout)
            visual_index = 0
            for spec_element in slide.elements:
                if spec_element.type != "element_ref" or not spec_element.element_id:
                    continue
                referenced = element_lookup.get(spec_element.element_id)
                if referenced is None:
                    continue
                visual_box = _visual_box(slide.layout, visual_index)
                if referenced.type == "image" and getattr(referenced, "asset_url", None):
                    page_elements.append(
                        KitImageElement(
                            id=referenced.id,
                            name=getattr(referenced, "alt_text", referenced.title),
                            left=visual_box["left"],
                            top=visual_box["top"],
                            width=visual_box["width"],
                            height=visual_box["height"],
                            rotate=0,
                            src=referenced.asset_url,
                            fixedRatio=True,
                            radius=18,
                            shadow=KitElementShadow(x=0, y=16, blur=32, color="rgba(15, 23, 42, 0.18)"),
                        )
                    )
                    visual_index += 1
                elif referenced.type == "mindmap" and getattr(referenced, "markdown", None):
                    page_elements.append(
                        KitTextElement(
                            id=referenced.id,
                            name=referenced.title,
                            left=visual_box["left"],
                            top=visual_box["top"],
                            width=visual_box["width"],
                            height=min(visual_box["height"], 180),
                            rotate=0,
                            content=_preformatted(referenced.markdown),
                            defaultFontName=theme.fontName,
                            defaultColor="#334155",
                            fontSize=14,
                            fill="#F8FAFC",
                            radius=16,
                            outline=KitElementOutline(width=1, color="#CBD5E1", style="solid"),
                            lineHeight=1.35,
                        )
                    )
                    visual_index += 1
            pages.append(
                SlidePageModel(
                    page=KitSlidePage(
                        id=slide.id,
                        title=slide.title,
                        width=SLIDE_WIDTH,
                        height=SLIDE_HEIGHT,
                        background=_background_for_layout(slide.layout, theme),
                        theme=theme,
                        elements=page_elements,
                        speakerNotes=slide.speaker_notes,
                    )
                )
            )
        return SlideRenderModel(title=spec.title, pages=pages)


def _theme_for_slide(spec: SlideDeckSpec, order: int) -> KitTheme:
    metadata_theme = spec.metadata.get("theme") if isinstance(spec.metadata.get("theme"), dict) else {}
    theme_colors = metadata_theme.get("themeColors") if isinstance(metadata_theme, dict) else None
    colors = theme_colors if isinstance(theme_colors, list) and theme_colors else ["#2563EB", "#0F766E", "#F59E0B"]
    return KitTheme(
        backgroundColor="#FFFFFF" if order % 2 else "#F8FAFC",
        themeColors=[str(color) for color in colors],
        fontColor="#111827",
        fontName=str(metadata_theme.get("fontName", "Arial")) if isinstance(metadata_theme, dict) else "Arial",
    )


def _background_for_layout(layout: str, theme: KitTheme) -> KitSlideBackground:
    if layout in {"section-divider", "cover"}:
        return KitSlideBackground(
            type="gradient",
            gradient={
                "type": "linear",
                "rotate": 135,
                "colors": [
                    {"pos": 0, "color": "#F8FAFC"},
                    {"pos": 1, "color": "#DBEAFE"},
                ],
            },
        )
    return KitSlideBackground(type="solid", color=theme.backgroundColor)


def _base_elements(slide_id: str, title: str, core_message: str, theme: KitTheme, layout: str) -> list[KitSlideElement]:
    if layout in {"section-divider", "cover"}:
        return [
            KitShapeElement(
                id=f"{slide_id}_accent",
                left=68,
                top=96,
                width=92,
                height=8,
                rotate=0,
                shape="roundRect",
                fill=theme.themeColors[0],
                radius=8,
            ),
            KitTextElement(
                id=f"{slide_id}_title",
                name="Title",
                left=68,
                top=130,
                width=700,
                height=128,
                rotate=0,
                content=_paragraph(title),
                defaultFontName=theme.fontName,
                defaultColor="#0F172A",
                fontSize=44,
                bold=True,
                lineHeight=1.1,
            ),
            KitTextElement(
                id=f"{slide_id}_body",
                name="Core message",
                left=72,
                top=282,
                width=620,
                height=112,
                rotate=0,
                content=_paragraph(core_message),
                defaultFontName=theme.fontName,
                defaultColor="#334155",
                fontSize=24,
                lineHeight=1.35,
            ),
        ]

    title_width = 530 if layout in {"title-content-visual", "visual-left-content-right"} else 760
    body_left = 72 if layout != "visual-left-content-right" else 430
    body_width = 510 if layout != "visual-left-content-right" else 450
    return [
        KitTextElement(
            id=f"{slide_id}_title",
            name="Title",
            left=64,
            top=54,
            width=title_width,
            height=70,
            rotate=0,
            content=_paragraph(title),
            defaultFontName=theme.fontName,
            defaultColor="#111827",
            fontSize=34,
            bold=True,
            lineHeight=1.15,
        ),
        KitLineElement(
            id=f"{slide_id}_divider",
            name="Divider",
            left=64,
            top=136,
            width=title_width,
            height=2,
            rotate=0,
            start=(0, 0),
            end=(title_width, 0),
            color=theme.themeColors[0],
            strokeWidth=3,
        ),
        KitShapeElement(
            id=f"{slide_id}_message_box",
            name="Message box",
            left=body_left - 18,
            top=176,
            width=body_width + 36,
            height=178,
            rotate=0,
            shape="roundRect",
            fill="#EFF6FF",
            opacity=1,
            radius=20,
            outline=KitElementOutline(width=1, color="#BFDBFE", style="solid"),
        ),
        KitTextElement(
            id=f"{slide_id}_body",
            name="Core message",
            left=body_left,
            top=202,
            width=body_width,
            height=126,
            rotate=0,
            content=_paragraph(core_message),
            defaultFontName=theme.fontName,
            defaultColor="#1E3A8A",
            fontSize=23,
            bold=True,
            lineHeight=1.35,
            verticalAlign="middle",
        ),
    ]


def _visual_box(layout: str, index: int) -> dict[str, int]:
    if layout == "visual-left-content-right":
        return {"left": 64, "top": 178 + index * 174, "width": 300, "height": 168}
    if layout == "summary-cards":
        return {"left": 90 + index * 280, "top": 340, "width": 240, "height": 136}
    return {"left": 625, "top": 158 + index * 178, "width": 270, "height": 152}


def _paragraph(value: str) -> str:
    return f"<p>{escape(value)}</p>"


def _preformatted(value: str) -> str:
    return f"<pre>{escape(value)}</pre>"
