import re

from app.generators.unit_specs.slide_layout import choose_slide_layout, design_intent_for_layout
from app.schemas.outline import OutlineUnit
from app.schemas.specs import (
    BULLET_LIST_MAX,
    BULLET_LIST_MIN,
    BULLET_MAX_CN,
    EXPLANATION_MAX_SENTENCES,
    IMAGE_TEXT_SUMMARY_MAX_CN,
    RequiredElementSpec,
    SlideSpecElement,
    SlideSpecPage,
    SUMMARY_TEXT_MAX_SENTENCES,
    TAKEAWAY_MAX_CN,
    TITLE_MAX_CN,
    VISUAL_SUMMARY_SUMMARY_MAX_CN,
)
from app.schemas.state import ContentGenerationState


def normalize_slide_spec(spec: SlideSpecPage, unit: OutlineUnit, state: ContentGenerationState) -> SlideSpecPage:
    layout = spec.layout
    if layout not in ("image_text", "visual_summary"):
        layout = choose_slide_layout(unit)

    elements = _normalize_elements(spec, layout, unit)
    required_elements = _normalize_required_elements(spec, layout, unit, state, elements)
    speaker_notes = spec.speaker_notes or f"Explain this slide around the goal: {unit.goal}."
    design_intent = spec.design_intent or design_intent_for_layout(layout)
    layout_hints = dict(spec.layout_hints)
    layout_hints["supported_renderer"] = "scenekit.slide/v1"
    layout_hints["density"] = "rich" if layout == "visual_summary" else "balanced"

    visual_refs = [e for e in elements if e.type == "element_ref" and e.metadata.get("role") == "visual"]
    if visual_refs:
        layout_hints["primary_visual"] = visual_refs[0].element_id

    return SlideSpecPage(
        id=spec.id,
        outline_unit_id=spec.outline_unit_id,
        order=spec.order,
        title=spec.title,
        core_message=spec.core_message,
        layout=layout,
        design_intent=design_intent,
        theme_variant=spec.theme_variant,
        layout_hints=layout_hints,
        elements=elements,
        required_elements=required_elements,
        speaker_notes=speaker_notes,
        source_chunk_ids=spec.source_chunk_ids,
    )


def _normalize_elements(spec: SlideSpecPage, layout: str, unit: OutlineUnit) -> list[SlideSpecElement]:
    elements = list(spec.elements)

    if layout == "image_text":
        elements = _ensure_image_text_roles(elements, spec, unit)
    elif layout == "visual_summary":
        elements = _ensure_visual_summary_roles(elements, spec, unit)

    elements = _enforce_text_budget(elements, layout)

    return elements


def _ensure_image_text_roles(
    elements: list[SlideSpecElement],
    spec: SlideSpecPage,
    unit: OutlineUnit,
) -> list[SlideSpecElement]:
    slide_id = spec.id
    result: list[SlideSpecElement] = []
    lead_card: SlideSpecElement | None = None
    support_card: SlideSpecElement | None = None
    summary_text: SlideSpecElement | None = None
    visual_ref: SlideSpecElement | None = None

    title = _first_text_element(elements, "title")
    if title is None:
        title = SlideSpecElement(
            id=f"{slide_id}_title", type="text", content=unit.title[:TITLE_MAX_CN], metadata={"role": "title"},
        )
    result.append(title)

    for element in elements:
        role = str(element.metadata.get("role") or "")
        if element.type == "element_ref" and role == "visual" and visual_ref is None:
            visual_ref = element
            continue
        if element.type != "text" or role == "title":
            continue
        normalized_role = _image_text_role_for_existing_metadata(role, lead_card is not None)
        if normalized_role == "lead_card" and lead_card is None:
            lead_card = _as_card(element, "lead_card", _lead_label_for_role(role), _content_format_for(element, default="paragraph"))
        elif normalized_role == "support_card" and support_card is None:
            support_card = _as_card(element, "support_card", _support_label_for_role(role), _content_format_for(element, default="bullets"))
        elif normalized_role == "summary_text" and summary_text is None:
            summary_text = _as_summary_text(element)

    if lead_card is None:
        content = spec.core_message or unit.core_message or unit.title
        lead_card = SlideSpecElement(
            id=f"{slide_id}_lead_card",
            type="text",
            content=content,
            metadata={"role": "lead_card", "display_label": "核心解释", "content_format": "paragraph"},
        )
    if support_card is None:
        points = unit.key_points[:BULLET_LIST_MAX] if unit.key_points else ["核心概念", "关键关系"]
        bullet_content = "\n".join(f"• {p[:BULLET_MAX_CN]}" for p in points)
        support_card = SlideSpecElement(
            id=f"{slide_id}_support_card",
            type="text",
            content=bullet_content,
            metadata={"role": "support_card", "display_label": "关键要点", "content_format": "bullets"},
        )
    if summary_text is None:
        summary = spec.core_message or unit.core_message
        summary_text = SlideSpecElement(
            id=f"{slide_id}_summary_text",
            type="text",
            content=_strip_summary_prefix(summary),
            metadata={"role": "summary_text"},
        )
    summary_text = _ensure_distinct_summary_text(summary_text, lead_card, support_card, unit)

    result.extend([lead_card, support_card, summary_text])

    if visual_ref is None:
        image_id = f"image_{spec.id}"
        visual_ref = SlideSpecElement(
            id=f"{slide_id}_visual_ref", type="element_ref", element_id=image_id,
            metadata={"role": "visual", "placement": "primary"},
        )
    result.append(visual_ref)

    return result


def _ensure_visual_summary_roles(
    elements: list[SlideSpecElement],
    spec: SlideSpecPage,
    unit: OutlineUnit,
) -> list[SlideSpecElement]:
    slide_id = spec.id
    result: list[SlideSpecElement] = []
    title = _first_text_element(elements, "title")
    if title is None:
        title = SlideSpecElement(
            id=f"{slide_id}_title", type="text", content=unit.title[:TITLE_MAX_CN], metadata={"role": "title"},
        )
    result.append(title)

    summary_source = _first_text_element(elements, "summary_text") or _first_text_element(elements, "takeaway")
    if summary_source is None:
        bullet_source = _first_text_element(elements, "bullet_list")
        if bullet_source is not None:
            content = "。".join(line.strip(" •-\t") for line in (bullet_source.content or "").splitlines() if line.strip())
        else:
            content = spec.core_message or unit.core_message
        summary_source = SlideSpecElement(
            id=f"{slide_id}_summary_text",
            type="text",
            content=content,
            metadata={"role": "summary_text"},
        )
    result.append(_as_summary_text(summary_source))

    visual_ref = next((e for e in elements if e.type == "element_ref" and e.metadata.get("role") == "visual"), None)
    if visual_ref is None:
        image_id = f"image_{spec.id}"
        visual_ref = SlideSpecElement(
            id=f"{slide_id}_visual_ref", type="element_ref", element_id=image_id,
            metadata={"role": "visual", "placement": "primary"},
        )
    result.append(visual_ref)

    return result


def _first_text_element(elements: list[SlideSpecElement], role: str) -> SlideSpecElement | None:
    return next((e for e in elements if e.type == "text" and e.metadata.get("role") == role), None)


def _image_text_role_for_existing_metadata(role: str, has_lead_card: bool) -> str:
    if role in {"lead_card", "support_card", "summary_text"}:
        return role
    if role in {"explanation", "body", "comparison", "note", "caption"}:
        return "lead_card"
    if role in {"bullet_list", "bullet-list"}:
        return "support_card"
    if role == "example":
        return "support_card" if has_lead_card else "lead_card"
    if role in {"takeaway", "callout"}:
        return "summary_text"
    return "lead_card" if not has_lead_card else "support_card"


def _lead_label_for_role(role: str) -> str:
    labels = {
        "lead_card": "核心解释",
        "example": "例子",
        "comparison": "关键结论",
    }
    return labels.get(role, "核心解释")


def _support_label_for_role(role: str) -> str:
    labels = {
        "support_card": "关键要点",
        "bullet_list": "关键要点",
        "bullet-list": "关键要点",
        "example": "例子",
        "callout": "启发",
    }
    return labels.get(role, "关键要点")


def _content_format_for(element: SlideSpecElement, default: str) -> str:
    explicit = str(element.metadata.get("content_format") or "")
    if explicit in {"paragraph", "bullets"}:
        return explicit
    content = element.content or ""
    if any(line.strip().startswith(("•", "-", "*")) for line in content.splitlines()):
        return "bullets"
    return default


def _as_card(element: SlideSpecElement, role: str, fallback_label: str, fallback_format: str) -> SlideSpecElement:
    metadata = dict(element.metadata)
    metadata["role"] = role
    metadata["display_label"] = str(metadata.get("display_label") or fallback_label)
    metadata["content_format"] = _content_format_for(element, fallback_format)
    return element.model_copy(update={"metadata": metadata})


def _as_summary_text(element: SlideSpecElement) -> SlideSpecElement:
    return element.model_copy(
        update={
            "content": _strip_summary_prefix(element.content or ""),
            "metadata": {"role": "summary_text"},
        }
    )


def _ensure_distinct_summary_text(
    summary_text: SlideSpecElement,
    lead_card: SlideSpecElement,
    support_card: SlideSpecElement,
    unit: OutlineUnit,
) -> SlideSpecElement:
    summary = _normalized_text(summary_text.content or "")
    lead = _normalized_text(lead_card.content or "")
    if summary and lead and summary != lead:
        return summary_text
    replacement = _derive_summary_from_support(support_card, unit, lead)
    return summary_text.model_copy(update={"content": replacement})


def _derive_summary_from_support(support_card: SlideSpecElement, unit: OutlineUnit, lead: str) -> str:
    for line in (support_card.content or "").splitlines():
        cleaned = _strip_summary_prefix(line).lstrip("• -*\t ").strip("。；; ")
        if cleaned and _normalized_text(cleaned) != lead:
            return _truncate_chinese(f"重点关注{cleaned}", IMAGE_TEXT_SUMMARY_MAX_CN)
    if unit.goal and _normalized_text(unit.goal) != lead:
        return _truncate_chinese(unit.goal, IMAGE_TEXT_SUMMARY_MAX_CN)
    return _truncate_chinese(f"{unit.title}需要形成清晰判断", IMAGE_TEXT_SUMMARY_MAX_CN)


def _normalized_text(text: str) -> str:
    return re.sub(r"\s+", "", _strip_summary_prefix(text)).strip("。；;，,")


def _enforce_text_budget(elements: list[SlideSpecElement], layout: str) -> list[SlideSpecElement]:
    result = []
    for element in elements:
        if element.type != "text" or not element.content:
            result.append(element)
            continue

        role = str(element.metadata.get("role") or "")
        content = element.content

        if role == "title":
            content = _truncate_chinese(content, TITLE_MAX_CN)
        elif role in {"lead_card", "support_card"}:
            content_format = str(element.metadata.get("content_format") or "paragraph")
            if content_format == "bullets":
                max_items = BULLET_LIST_MAX if role == "support_card" else 3
                lines = [line.strip() for line in content.splitlines() if line.strip()]
                lines = lines[:max_items]
                lines = [f"• {line.lstrip('• -').strip()[:BULLET_MAX_CN]}" for line in lines]
                if not lines:
                    lines = ["• 核心信息"]
                content = "\n".join(lines)
            else:
                content = _truncate_sentences(content, EXPLANATION_MAX_SENTENCES)
        elif role == "explanation":
            content = _truncate_sentences(content, EXPLANATION_MAX_SENTENCES)
        elif role == "bullet_list":
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            lines = lines[:BULLET_LIST_MAX]
            lines = [f"• {line.lstrip('• -').strip()[:BULLET_MAX_CN]}" for line in lines]
            if len(lines) < BULLET_LIST_MIN:
                while len(lines) < BULLET_LIST_MIN:
                    lines.append("• ...")
            content = "\n".join(lines)
        elif role == "summary_text":
            max_cn = IMAGE_TEXT_SUMMARY_MAX_CN if layout == "image_text" else VISUAL_SUMMARY_SUMMARY_MAX_CN
            content = _truncate_chinese(_strip_summary_prefix(_truncate_sentences(content, SUMMARY_TEXT_MAX_SENTENCES)), max_cn)
        elif role == "takeaway":
            content = _truncate_chinese(content, TAKEAWAY_MAX_CN)

        result.append(element.model_copy(update={"content": content}))

    return result


def _truncate_chinese(text: str, max_cn: int) -> str:
    cn_count = 0
    for i, ch in enumerate(text):
        if "\u4e00" <= ch <= "\u9fff":
            cn_count += 1
            if cn_count > max_cn:
                return text[:i] + "…"
    return text


def _truncate_sentences(text: str, max_sentences: int) -> str:
    parts = re.split(r"([。！？；.!?;])", text)
    sentences: list[str] = []
    current = ""
    count = 0
    for part in parts:
        current += part
        if re.match(r"[。！？；.!?;]", part):
            sentences.append(current)
            current = ""
            count += 1
            if count >= max_sentences:
                break
    if current.strip():
        sentences.append(current)
    return "".join(sentences[:max_sentences])


def _strip_summary_prefix(text: str) -> str:
    return re.sub(r"^\s*(核心点|总结|结论)\s*[:：]\s*", "", text).strip()


def _normalize_required_elements(
    spec: SlideSpecPage,
    layout: str,
    unit: OutlineUnit,
    state: ContentGenerationState,
    elements: list[SlideSpecElement],
) -> list[RequiredElementSpec]:
    visual_refs = [e for e in elements if e.type == "element_ref" and e.metadata.get("role") == "visual"]
    if not visual_refs:
        return spec.required_elements

    visual_element_id = visual_refs[0].element_id
    existing = {r.element_id for r in spec.required_elements}

    result = [r for r in spec.required_elements if r.type == "image"]

    if visual_element_id not in existing:
        if layout == "image_text":
            instruction = (
                "Create a low-density teaching illustration asset for a slide, not a full slide. "
                "The image will appear in a medium-sized right-side panel. "
                "Show one clear scene, object, metaphor, or simple action. "
                "Use realistic illustration, hand-drawn sketch, or clean educational illustration style. "
                "No title bar, no header, no footer, no slide border, no lecture card layout. "
                "No infographic. No flowchart. No architecture diagram. No mind map. "
                "No dense arrows. No multiple panels. No small text. "
                "Use at most 1-3 short labels only if necessary. "
                "The image must remain readable in a compact slide image area. "
                f"Topic: {unit.title}. Core message: {unit.core_message}."
            )
            style = "clean educational illustration, realistic diagram, hand-drawn sketch"
            aspect_ratio = "4:3"
        else:
            instruction = (
                "Create a wide landscape summary diagram asset for the upper area of a teaching slide, not a full slide. "
                "Use a clear framework diagram, flowchart, process diagram, or structured summary diagram. "
                "The diagram should fit a wide horizontal canvas. "
                "Keep the main content inside a centered safe area with generous margins. "
                "Use 3-5 major nodes and at most 2 hierarchy levels. "
                "Use large readable labels with at most one short line per node. "
                "No outer title, no top banner, no footer, no bottom explanation bar, no slide border. "
                "Avoid numbered large cards, dense arrows, dense small text, poster layout, and full PowerPoint slide screenshot. "
                f"Topic: {unit.title}. Core message: {unit.core_message}."
            )
            style = "infographic, flowchart, framework diagram, process diagram"
            aspect_ratio = "21:9"

        result.append(RequiredElementSpec(
            element_id=visual_element_id,
            type="image",
            title=f"{unit.title} visual",
            purpose=f"Support the {layout} slide with a {'low-density illustration' if layout == 'image_text' else 'structured summary diagram'}.",
            instruction=instruction,
            style=style,
            aspect_ratio=aspect_ratio,
            source_unit_id=spec.id,
            source_outline_unit_id=unit.id,
            source_chunk_ids=spec.source_chunk_ids,
            priority="high",
        ))

    return result
