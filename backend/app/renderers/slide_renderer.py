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
    KitTableCell,
    KitTableElement,
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
        element_lookup = {element.id: element for element in elements}
        pages: list[SlidePageModel] = []
        for slide in spec.slides:
            theme = _theme_for_slide(spec, slide.order or len(pages) + 1)
            page_elements = _render_slide_page(slide, element_lookup, theme, spec)
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
    colors = theme_colors if isinstance(theme_colors, list) and theme_colors else ["#0B4F7A", "#2563EB", "#0F766E"]
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
                    {"pos": 0, "color": "#FFFFFF"},
                    {"pos": 1, "color": "#E0F2FE"},
                ],
            },
        )
    return KitSlideBackground(type="solid", color=theme.backgroundColor)


def _render_slide_page(
    slide: SlideSpecPage,
    element_lookup: dict[str, ContentElement],
    theme: KitTheme,
    spec: SlideDeckSpec,
) -> list[KitSlideElement]:
    text_items = _collect_text_items(slide)
    visual_refs = _collect_visual_refs(slide, element_lookup)

    if slide.layout in {"cover", "section-divider"}:
        return _render_cover_like(slide, text_items, visual_refs, theme, spec.title)
    if slide.layout == "visual-left-content-right":
        return _render_visual_left_content_right(slide, text_items, visual_refs, theme)
    if slide.layout == "title-content-visual":
        return _render_title_content_visual(slide, text_items, visual_refs, theme)
    if slide.layout == "summary-cards":
        return _render_summary_cards(slide, text_items, visual_refs, theme)
    return _render_title_content(slide, text_items, visual_refs, theme)


def _collect_text_items(slide: SlideSpecPage) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for element in slide.elements:
        if element.type != "text" or not element.content:
            continue
        role = str(element.metadata.get("role") or "body")
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

    if not any(item["role"] == "body" for item in items):
        items.insert(0, {"id": f"{slide.id}_body_auto", "role": "body", "content": slide.core_message, "name": "body"})

    if not any(item["role"] in {"takeaway", "callout"} for item in items) and slide.core_message:
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


def _render_cover_like(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    visual_refs: list[dict[str, object]],
    theme: KitTheme,
    deck_title: str,
) -> list[KitSlideElement]:
    elements: list[KitSlideElement] = [
        _shape(f"{slide.id}_accent", 68, 88, 96, 8, theme.themeColors[0], radius=8),
        _text(
            f"{slide.id}_title",
            "Title",
            68,
            128,
            700,
            118,
            slide.title,
            theme,
            font_size=44,
            bold=True,
            color="#0F172A",
            line_height=1.12,
        ),
        _text(
            f"{slide.id}_subtitle",
            "Core message",
            72,
            264,
            640,
            92,
            _primary_body(text_items, slide.core_message),
            theme,
            font_size=24,
            color="#334155",
            line_height=1.35,
        ),
    ]
    if slide.layout == "cover":
        elements.append(
            _text(
                f"{slide.id}_deck_label",
                "Deck label",
                72,
                406,
                520,
                36,
                deck_title,
                theme,
                font_size=16,
                color="#64748B",
            )
        )
    if visual_refs:
        visual = _visual_element(visual_refs[0], 690, 152, 210, 150, theme)
        if visual is not None:
            elements.append(visual)
    return elements


def _render_title_content(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    visual_refs: list[dict[str, object]],
    theme: KitTheme,
) -> list[KitSlideElement]:
    elements = _standard_header(slide, theme, title_width=760)
    body_items = _body_items(text_items)
    if _looks_like_table(_content_by_role(text_items, "comparison")):
        table = _table_from_text(f"{slide.id}_comparison_table", _content_by_role(text_items, "comparison"), 142, 186, 676, 168, theme)
        if table is not None:
            elements.append(table)
            elements.extend(_takeaway_bar(slide, text_items, theme, top=402))
            return elements

    cards = _content_cards(slide, body_items[:3], theme, x=72, y=168, width=246, height=132, gap=24)
    if cards:
        elements.extend(cards)
    else:
        elements.extend(
            _feature_block(
                f"{slide.id}_main",
                "核心内容",
                _primary_body(text_items, slide.core_message),
                82,
                172,
                690,
                160,
                theme,
                fill="#F8FAFC",
            )
        )
    elements.extend(_takeaway_bar(slide, text_items, theme, top=408))
    return elements


def _render_title_content_visual(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    visual_refs: list[dict[str, object]],
    theme: KitTheme,
) -> list[KitSlideElement]:
    elements = _standard_header(slide, theme, title_width=560)
    left_items = _body_items(text_items)[:3]
    elements.extend(_vertical_blocks(slide, left_items, theme, x=64, y=160, width=480, max_bottom=410))

    if visual_refs:
        elements.append(_shape(f"{slide.id}_visual_panel", 582, 150, 310, 210, "#F1F5F9", radius=20, outline="#E2E8F0"))
        visual = _visual_element(visual_refs[0], 606, 172, 262, 166, theme)
        if visual is not None:
            elements.append(visual)
    else:
        elements.extend(
            _feature_block(
                f"{slide.id}_right_callout",
                "提示",
                _content_by_role(text_items, "callout") or _content_by_role(text_items, "example") or slide.core_message,
                590,
                166,
                280,
                170,
                theme,
                fill="#ECFDF5",
                accent="#0F766E",
            )
        )
    elements.extend(_takeaway_bar(slide, text_items, theme, top=426))
    return elements


def _render_visual_left_content_right(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    visual_refs: list[dict[str, object]],
    theme: KitTheme,
) -> list[KitSlideElement]:
    elements = _standard_header(slide, theme, title_width=760)
    if visual_refs:
        elements.append(_shape(f"{slide.id}_visual_back", 64, 160, 374, 236, "#F1F5F9", radius=18, outline="#E2E8F0"))
        visual = _visual_element(visual_refs[0], 82, 178, 338, 190, theme)
        if visual is not None:
            elements.append(visual)
        caption = _content_by_role(text_items, "caption")
        if caption:
            elements.append(_text(f"{slide.id}_caption", "Caption", 82, 374, 338, 40, caption, theme, font_size=13, color="#475569", align="center", bold=True))
    else:
        elements.extend(
            _feature_block(
                f"{slide.id}_visual_fallback",
                "核心信息",
                slide.core_message,
                64,
                172,
                350,
                180,
                theme,
                fill="#F8FAFC",
                accent=theme.themeColors[0],
            )
        )

    right_items = _body_items(text_items)[:4]
    elements.extend(_vertical_blocks(slide, right_items, theme, x=492, y=160, width=382, max_bottom=408))
    elements.extend(_takeaway_bar(slide, text_items, theme, top=430))
    return elements


def _render_summary_cards(
    slide: SlideSpecPage,
    text_items: list[dict[str, str]],
    visual_refs: list[dict[str, object]],
    theme: KitTheme,
) -> list[KitSlideElement]:
    elements = _standard_header(slide, theme, title_width=760)
    card_items = _card_items(text_items, slide.core_message)
    if len(card_items) <= 2:
        elements.extend(_content_cards(slide, card_items, theme, x=116, y=176, width=320, height=146, gap=36))
    else:
        elements.extend(_content_cards(slide, card_items[:4], theme, x=72, y=164, width=188, height=158, gap=24))
    if visual_refs:
        visual = _visual_element(visual_refs[0], 686, 342, 180, 100, theme)
        if visual is not None:
            elements.append(visual)
    elements.extend(_takeaway_bar(slide, text_items, theme, top=414))
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


def _content_cards(
    slide: SlideSpecPage,
    items: list[dict[str, str]],
    theme: KitTheme,
    x: int,
    y: int,
    width: int,
    height: int,
    gap: int,
) -> list[KitSlideElement]:
    elements: list[KitSlideElement] = []
    for index, item in enumerate(items):
        left = x + index * (width + gap)
        title = _role_label(item["role"], index + 1)
        elements.extend(
            _feature_block(
                f"{slide.id}_card_{index + 1}",
                title,
                item["content"],
                left,
                y,
                width,
                height,
                theme,
                fill=_card_fill(index),
                accent=theme.themeColors[index % len(theme.themeColors)],
            )
        )
    return elements


def _vertical_blocks(
    slide: SlideSpecPage,
    items: list[dict[str, str]],
    theme: KitTheme,
    x: int,
    y: int,
    width: int,
    max_bottom: int,
) -> list[KitSlideElement]:
    elements: list[KitSlideElement] = []
    if not items:
        return elements
    available = max_bottom - y
    block_height = max(70, min(116, (available - 14 * (len(items) - 1)) // len(items)))
    for index, item in enumerate(items):
        top = y + index * (block_height + 14)
        elements.extend(
            _feature_block(
                f"{slide.id}_block_{index + 1}",
                _role_label(item["role"], index + 1),
                item["content"],
                x,
                top,
                width,
                block_height,
                theme,
                fill=_card_fill(index),
                accent=theme.themeColors[index % len(theme.themeColors)],
            )
        )
    return elements


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


def _table_from_text(
    element_id: str,
    content: str,
    left: int,
    top: int,
    width: int,
    height: int,
    theme: KitTheme,
) -> KitTableElement | None:
    rows = []
    for line in content.splitlines():
        line = line.strip()
        if not line or set(line.replace("|", "").strip()) <= {"-", ":"}:
            continue
        if "|" not in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 2:
            rows.append(cells[:4])
    if len(rows) < 2:
        return None

    data: list[list[KitTableCell]] = []
    for row_index, row in enumerate(rows[:5]):
        data.append(
            [
                KitTableCell(
                    id=f"{element_id}_r{row_index}_c{col_index}",
                    text=_fit_text(cell, 36),
                    style={
                        "bold": row_index == 0,
                        "align": "center" if row_index == 0 else "left",
                        "backcolor": "#EFF6FF" if row_index == 0 else "#FFFFFF",
                        "fontSize": 14,
                    },
                )
                for col_index, cell in enumerate(row)
            ]
        )
    return KitTableElement(
        id=element_id,
        name="Comparison table",
        left=left,
        top=top,
        width=width,
        height=height,
        rotate=0,
        data=data,
        outline=KitElementOutline(width=1, color="#CBD5E1", style="solid"),
        fontSize=14,
        fontName=theme.fontName,
        textColor="#111827",
    )


def _body_items(text_items: list[dict[str, str]]) -> list[dict[str, str]]:
    preferred_roles = ["body", "bullet-list", "example", "comparison", "callout", "note"]
    result = [item for role in preferred_roles for item in text_items if item["role"] == role]
    return result or text_items[:2]


def _card_items(text_items: list[dict[str, str]], fallback: str) -> list[dict[str, str]]:
    items = [item for item in text_items if item["role"] not in {"takeaway", "caption"}]
    if len(items) == 1:
        parts = _split_points(items[0]["content"])
        if len(parts) >= 3:
            return [
                {"id": f"auto_{index}", "role": "bullet-list", "content": part, "name": "point"}
                for index, part in enumerate(parts[:4], 1)
            ]
    if not items:
        return [{"id": "auto_summary", "role": "body", "content": fallback, "name": "summary"}]
    return items


def _primary_body(text_items: list[dict[str, str]], fallback: str) -> str:
    return _content_by_role(text_items, "body") or fallback


def _content_by_role(text_items: list[dict[str, str]], role: str) -> str:
    for item in text_items:
        if item["role"] == role and item["content"]:
            return item["content"]
    return ""


def _split_points(content: str) -> list[str]:
    lines = [line.strip(" -•\t") for line in content.replace("；", "\n").replace(";", "\n").splitlines()]
    return [line for line in lines if line]


def _looks_like_table(content: str) -> bool:
    if not content:
        return False
    return sum(1 for line in content.splitlines() if "|" in line) >= 2


def _role_label(role: str, index: int) -> str:
    labels = {
        "body": "核心解释",
        "bullet-list": f"要点 {index}",
        "example": "例子",
        "comparison": "对比",
        "callout": "重点提示",
        "quote": "观点",
        "note": "注释",
        "caption": "图示说明",
    }
    return labels.get(role, f"要点 {index}")


def _card_fill(index: int) -> str:
    fills = ["#EFF6FF", "#ECFDF5", "#FFFBEB", "#F8FAFC"]
    return fills[index % len(fills)]


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
