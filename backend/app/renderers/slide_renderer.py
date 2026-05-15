from html import escape
from textwrap import shorten

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
from app.schemas.specs import SlideDeckSpec, SlideSpecElement, SlideSpecPage


SLIDE_WIDTH = 960
SLIDE_HEIGHT = 540


class SlideRenderer:
    def render(self, spec: SlideDeckSpec, elements: list[ContentElement]) -> SlideRenderModel:
        pages = [self.render_unit(slide, elements, spec) for slide in spec.slides]
        return self.assemble(spec, pages)

    def render_unit(self, slide: SlideSpecPage, elements: list[ContentElement], spec: SlideDeckSpec) -> SlidePageModel:
        element_lookup = {element.id: element for element in elements}
        theme = _theme_for_slide(spec, slide.order)
        page_elements = _render_slide_page(slide, element_lookup, theme, spec)
        return SlidePageModel(
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

    def assemble(self, spec: SlideDeckSpec, pages: list[SlidePageModel]) -> SlideRenderModel:
        return SlideRenderModel(title=spec.title, pages=pages)


def _theme_for_slide(spec: SlideDeckSpec, order: int) -> KitTheme:
    metadata_theme = spec.metadata.get("theme") if isinstance(spec.metadata.get("theme"), dict) else {}
    theme_colors = metadata_theme.get("themeColors") if isinstance(metadata_theme, dict) else None
    colors = theme_colors if isinstance(theme_colors, list) and theme_colors else ["#0B4F7A", "#2563EB", "#0F766E"]
    return KitTheme(
        backgroundColor="#FFFFFF" if order % 2 else "#F8FAFC",
        themeColors=[str(color) for color in colors],
        fontColor="#111827",
        fontName=str(metadata_theme.get("fontName", "Arial")) if isinstance(metadata_theme, dict) else "Arial",
    )


def _background_for_layout(layout: str, theme: KitTheme) -> KitSlideBackground:
    return KitSlideBackground(type="solid", color=theme.backgroundColor)


def _render_slide_page(
    slide: SlideSpecPage,
    element_lookup: dict[str, ContentElement],
    theme: KitTheme,
    spec: SlideDeckSpec,
) -> list[KitSlideElement]:
    text_items = _collect_text_items(slide)
    visual_refs = _collect_visual_refs(slide, element_lookup)

    if slide.layout == "visual_summary":
        return _render_visual_summary(slide, text_items, visual_refs, theme)
    return _render_image_text(slide, text_items, visual_refs, theme)


def _collect_text_items(slide: SlideSpecPage) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for element in slide.elements:
        if element.type != "text" or not element.content:
            continue
        role = str(element.metadata.get("role") or "explanation")
        if role == "title":
            continue
        items.append(
            {
                "id": element.id,
                "role": role,
                "content": element.content.strip(),
                "name": str(element.metadata.get("name") or role),
            }
        )

    if not any(item["role"] in {"explanation", "body"} for item in items):
        items.insert(0, {"id": f"{slide.id}_explanation_auto", "role": "explanation", "content": slide.core_message, "name": "explanation"})

    if not any(item["role"] == "takeaway" for item in items) and slide.core_message:
        items.append(
            {
                "id": f"{slide.id}_takeaway_auto",
                "role": "takeaway",
                "content": slide.core_message,
                "name": "takeaway",
            }
        )
    return _deduplicate_items(items)


def _deduplicate_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item["role"], item["content"])
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _collect_visual_refs(
    slide: SlideSpecPage,
    element_lookup: dict[str, ContentElement],
) -> list[dict[str, object]]:
    refs: list[dict[str, object]] = []
    for spec_element in slide.elements:
        if spec_element.type != "element_ref" or not spec_element.element_id:
            continue
        referenced = element_lookup.get(spec_element.element_id)
        if referenced is None:
            continue
        role = str(spec_element.metadata.get("role") or referenced.type)
        refs.append({"spec": spec_element, "element": referenced, "role": role})
    return refs[:1]


def _render_image_text(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    visual_refs: list[dict[str, object]],
    theme: KitTheme,
) -> list[KitSlideElement]:
    elements = _standard_header(slide, theme, title_width=500)

    explanation = _content_by_role(text_items, "explanation") or slide.core_message
    elements.append(
        _text(
            f"{slide.id}_explanation",
            "Explanation",
            64,
            152,
            490,
            60,
            explanation,
            theme,
            font_size=20,
            color="#1F2937",
            line_height=1.4,
        )
    )

    bullet_content = _content_by_role(text_items, "bullet_list")
    if bullet_content:
        elements.append(
            _text(
                f"{slide.id}_bullet_list",
                "Bullet list",
                64,
                222,
                490,
                140,
                bullet_content,
                theme,
                font_size=17,
                color="#334155",
                line_height=1.45,
            )
        )

    if visual_refs:
        elements.append(_shape(f"{slide.id}_visual_panel", 576, 148, 320, 232, "#F1F5F9", radius=18, outline="#E2E8F0"))
        visual = _visual_element(visual_refs[0], 594, 166, 284, 196, theme)
        if visual is not None:
            elements.append(visual)
    else:
        elements.extend(
            _feature_block(
                f"{slide.id}_visual_fallback",
                "核心信息",
                slide.core_message,
                576,
                152,
                310,
                180,
                theme,
                fill="#F8FAFC",
                accent=theme.themeColors[0],
            )
        )

    elements.extend(_takeaway_bar(slide, text_items, theme, top=420))
    return elements


def _render_visual_summary(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    visual_refs: list[dict[str, object]],
    theme: KitTheme,
) -> list[KitSlideElement]:
    elements = _standard_header(slide, theme, title_width=760)

    if visual_refs:
        elements.append(_shape(f"{slide.id}_visual_back", 64, 152, 540, 260, "#F1F5F9", radius=18, outline="#E2E8F0"))
        visual = _visual_element(visual_refs[0], 82, 168, 504, 228, theme)
        if visual is not None:
            elements.append(visual)
    else:
        elements.extend(
            _feature_block(
                f"{slide.id}_visual_fallback",
                "结构总览",
                slide.core_message,
                64,
                152,
                540,
                240,
                theme,
                fill="#F8FAFC",
                accent=theme.themeColors[0],
            )
        )

    summary_text = _content_by_role(text_items, "summary_text") or slide.core_message
    elements.extend(
        _feature_block(
            f"{slide.id}_summary",
            "总结",
            summary_text,
            624,
            152,
            272,
            260,
            theme,
            fill="#EFF6FF",
            accent=theme.themeColors[0],
        )
    )

    elements.extend(_takeaway_bar(slide, text_items, theme, top=440))
    return elements


def _standard_header(slide: SlideSpecPage, theme: KitTheme, title_width: int) -> list[KitSlideElement]:
    return [
        _text(
            f"{slide.id}_title",
            "Title",
            64,
            44,
            title_width,
            66,
            slide.title,
            theme,
            font_size=34,
            bold=True,
            color="#0F172A",
            line_height=1.15,
        ),
        _line(f"{slide.id}_accent_line", 64, 124, 86, theme.themeColors[0], stroke_width=4),
        _line(f"{slide.id}_divider", 150, 126, 736, "#CBD5E1", stroke_width=1),
    ]


def _feature_block(
    block_id: str,
    label: str,
    content: str,
    left: int,
    top: int,
    width: int,
    height: int,
    theme: KitTheme,
    fill: str,
    accent: str | None = None,
) -> list[KitSlideElement]:
    accent_color = accent or theme.themeColors[0]
    return [
        _shape(f"{block_id}_shape", left, top, width, height, fill, radius=16, outline="#E2E8F0"),
        _shape(f"{block_id}_accent", left, top, 7, height, accent_color, radius=8),
        _text(
            f"{block_id}_label",
            "Block label",
            left + 20,
            top + 14,
            width - 36,
            24,
            label,
            theme,
            font_size=14,
            bold=True,
            color=accent_color,
        ),
        _text(
            f"{block_id}_text",
            "Block text",
            left + 20,
            top + 40,
            width - 36,
            height - 48,
            _fit_text(content, 150 if height < 100 else 230),
            theme,
            font_size=17 if height >= 100 else 16,
            color="#1F2937",
            line_height=1.3,
        ),
    ]


def _takeaway_bar(slide: SlideSpecPage, text_items: list[dict[str, str]], theme: KitTheme, top: int) -> list[KitSlideElement]:
    takeaway = _content_by_role(text_items, "takeaway") or slide.core_message
    if not takeaway:
        return []
    return [
        _shape(f"{slide.id}_takeaway_shape", 92, top, 776, 58, "#F8FAFC", radius=14, outline="#E2E8F0"),
        _text(
            f"{slide.id}_takeaway_text",
            "Takeaway",
            112,
            top + 12,
            736,
            34,
            f"核心点：{_fit_text(takeaway, 92)}",
            theme,
            font_size=18,
            bold=True,
            color=theme.themeColors[0],
            align="center",
            vertical_align="middle",
        ),
    ]


def _visual_element(ref: dict[str, object], left: int, top: int, width: int, height: int, theme: KitTheme) -> KitSlideElement | None:
    referenced = ref["element"]
    if getattr(referenced, "type", None) == "image" and getattr(referenced, "asset_url", None):
        return KitImageElement(
            id=referenced.id,
            name=getattr(referenced, "alt_text", referenced.title),
            left=left,
            top=top,
            width=width,
            height=height,
            rotate=0,
            src=referenced.asset_url,
            fixedRatio=True,
            radius=14,
            shadow=KitElementShadow(x=0, y=14, blur=26, color="rgba(15, 23, 42, 0.16)"),
        )
    if getattr(referenced, "type", None) == "mindmap" and getattr(referenced, "markdown", None):
        return KitTextElement(
            id=referenced.id,
            name=referenced.title,
            left=left,
            top=top,
            width=width,
            height=height,
            rotate=0,
            content=_preformatted(_fit_text(referenced.markdown, 420)),
            defaultFontName=theme.fontName,
            defaultColor="#334155",
            fontSize=13,
            fill="#F8FAFC",
            radius=12,
            outline=KitElementOutline(width=1, color="#CBD5E1", style="solid"),
            lineHeight=1.28,
        )
    return None


def _content_by_role(text_items: list[dict[str, str]], role: str) -> str:
    for item in text_items:
        if item["role"] == role and item["content"]:
            return item["content"]
    return ""


def _shape(
    element_id: str,
    left: int,
    top: int,
    width: int,
    height: int,
    fill: str,
    radius: int = 0,
    outline: str | None = None,
) -> KitShapeElement:
    return KitShapeElement(
        id=element_id,
        name="Shape",
        left=left,
        top=top,
        width=width,
        height=height,
        rotate=0,
        shape="roundRect" if radius else "rect",
        fill=fill,
        opacity=1,
        radius=radius or None,
        outline=KitElementOutline(width=1, color=outline, style="solid") if outline else None,
    )


def _line(element_id: str, left: int, top: int, width: int, color: str, stroke_width: int) -> KitLineElement:
    return KitLineElement(
        id=element_id,
        name="Divider",
        left=left,
        top=top,
        width=width,
        height=2,
        rotate=0,
        start=(0, 0),
        end=(width, 0),
        color=color,
        strokeWidth=stroke_width,
        style="solid",
    )


def _text(
    element_id: str,
    name: str,
    left: int,
    top: int,
    width: int,
    height: int,
    content: str,
    theme: KitTheme,
    font_size: int,
    color: str,
    bold: bool | None = None,
    align: str | None = None,
    vertical_align: str | None = None,
    line_height: float = 1.35,
) -> KitTextElement:
    return KitTextElement(
        id=element_id,
        name=name,
        left=left,
        top=top,
        width=width,
        height=height,
        rotate=0,
        content=_rich_text(content),
        defaultFontName=theme.fontName,
        defaultColor=color,
        fontSize=font_size,
        bold=bold,
        align=align,  # type: ignore[arg-type]
        verticalAlign=vertical_align,  # type: ignore[arg-type]
        fill="transparent",
        opacity=1,
        lineHeight=line_height,
    )


def _rich_text(value: str) -> str:
    lines = [line.strip() for line in str(value).splitlines() if line.strip()]
    if not lines:
        return "<p></p>"
    paragraphs = []
    for line in lines:
        normalized = line.lstrip("-•* ")
        if line.startswith(("-", "•", "*")):
            paragraphs.append(f"<p>• {escape(normalized)}</p>")
        else:
            paragraphs.append(f"<p>{escape(line)}</p>")
    return "".join(paragraphs)


def _preformatted(value: str) -> str:
    return f"<pre>{escape(value)}</pre>"


def _fit_text(value: str, max_chars: int) -> str:
    normalized = " ".join(str(value).split())
    return shorten(normalized, width=max_chars, placeholder="…")
