import json
import os
import re
from html import escape
from typing import cast

from app.core.config import get_settings
from app.schemas.outline import OutlineUnit
from app.schemas.specs import (
    BULLET_LIST_MAX,
    BULLET_LIST_MIN,
    BULLET_MAX_CN,
    ElementReferenceBlock,
    EXPLANATION_MAX_SENTENCES,
    IMAGE_TEXT_REQUIRED_ROLES,
    IMAGE_TEXT_SUMMARY_MAX_CN,
    InteractiveHtmlSectionSpec,
    LectureSection,
    RequiredElementSpec,
    SlideSpecElement,
    SlideSpecPage,
    SUMMARY_TEXT_MAX_SENTENCES,
    TAKEAWAY_MAX_CN,
    TextBlock,
    TITLE_MAX_CN,
    VISUAL_SUMMARY_SUMMARY_MAX_CN,
    VISUAL_SUMMARY_REQUIRED_ROLES,
)
from app.schemas.state import ContentGenerationState
from app.services.llm_service import get_llm_service


def build_lecture_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> LectureSection:
    settings = get_settings()

    if settings.provider_mode == "stub":
        return build_lecture_unit_spec_fallback(state, unit, chunk_ids)

    try:
        return generate_lecture_unit_spec_with_llm(state, unit, chunk_ids)
    except Exception:
        return build_lecture_unit_spec_fallback(state, unit, chunk_ids)


def build_slide_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> SlideSpecPage:
    settings = get_settings()

    if settings.provider_mode == "stub":
        return normalize_slide_spec(build_slide_unit_spec_fallback(state, unit, chunk_ids), unit, state)

    try:
        raw_spec = generate_slide_unit_spec_with_llm(state, unit, chunk_ids)
        return normalize_slide_spec(raw_spec, unit, state)
    except Exception:
        return normalize_slide_spec(build_slide_unit_spec_fallback(state, unit, chunk_ids), unit, state)


def build_interactive_html_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> InteractiveHtmlSectionSpec:
    settings = get_settings()

    if settings.provider_mode == "stub":
        return build_interactive_html_unit_spec_fallback(state, unit, chunk_ids)

    try:
        return generate_interactive_html_unit_spec_with_llm(state, unit, chunk_ids)
    except Exception:
        return build_interactive_html_unit_spec_fallback(state, unit, chunk_ids)


def normalize_slide_spec(spec: SlideSpecPage, unit: OutlineUnit, state: ContentGenerationState) -> SlideSpecPage:
    layout = spec.layout
    if layout not in ("image_text", "visual_summary"):
        layout = _choose_slide_layout(unit)

    elements = _normalize_elements(spec, layout, unit)
    required_elements = _normalize_required_elements(spec, layout, unit, state, elements)
    speaker_notes = spec.speaker_notes or f"Explain this slide around the goal: {unit.goal}."
    design_intent = spec.design_intent or _design_intent_for_layout(layout)
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
        normalized_role = _image_text_role_for_legacy(role, lead_card is not None)
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


def _image_text_role_for_legacy(role: str, has_lead_card: bool) -> str:
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


def generate_lecture_unit_spec_with_llm(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> LectureSection:
    unit_spec_id = f"lecture_{unit.id}"
    prompt = _build_unit_spec_prompt("lecture", state, unit, unit_spec_id, chunk_ids)
    llm_service = get_llm_service()
    return cast(LectureSection, llm_service.generate_structured(prompt=prompt, schema=LectureSection))


def generate_slide_unit_spec_with_llm(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> SlideSpecPage:
    unit_spec_id = f"slide_{unit.id}"
    prompt = _build_unit_spec_prompt("slide_deck", state, unit, unit_spec_id, chunk_ids)
    llm_service = get_llm_service()
    return cast(SlideSpecPage, llm_service.generate_structured(prompt=prompt, schema=SlideSpecPage))


def generate_interactive_html_unit_spec_with_llm(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> InteractiveHtmlSectionSpec:
    unit_spec_id = unit.id
    prompt = _build_unit_spec_prompt("interactive_html", state, unit, unit_spec_id, chunk_ids)
    llm_service = get_llm_service()
    return cast(InteractiveHtmlSectionSpec, llm_service.generate_structured(prompt=prompt, schema=InteractiveHtmlSectionSpec))


def repair_unit_spec_with_llm(
    state: ContentGenerationState,
    unit: OutlineUnit,
    chunk_ids: list[str],
    validation_errors: list[str],
) -> LectureSection | SlideSpecPage | InteractiveHtmlSectionSpec:
    content_type = state.content_type
    if content_type == "slide_deck":
        unit_spec_id = f"slide_{unit.id}"
        schema = SlideSpecPage
    elif content_type == "interactive_html":
        unit_spec_id = unit.id
        schema = InteractiveHtmlSectionSpec
    else:
        unit_spec_id = f"lecture_{unit.id}"
        schema = LectureSection
    prompt = _build_unit_spec_repair_prompt(content_type, state, unit, unit_spec_id, chunk_ids, validation_errors)
    llm_service = get_llm_service()
    repaired = llm_service.generate_structured(prompt=prompt, schema=schema)
    if isinstance(repaired, SlideSpecPage):
        return normalize_slide_spec(repaired, unit, state)
    return repaired


def _build_unit_spec_prompt(
    content_type: str,
    state: ContentGenerationState,
    unit: OutlineUnit,
    unit_spec_id: str,
    chunk_ids: list[str],
) -> str:
    template_path = _get_unit_spec_template_path(content_type)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    retrieval_results = _format_retrieval_results(state.current_unit_context or [])
    generation_options = json.dumps(state.normalized_request, ensure_ascii=False, indent=2)
    outline_unit_json = json.dumps(unit.model_dump(), ensure_ascii=False, indent=2)

    return template.format(
        unit_spec_id=unit_spec_id,
        outline_unit=outline_unit_json,
        retrieval_results=retrieval_results,
        generation_options=generation_options,
    )


def _get_unit_spec_template_path(content_type: str) -> str:
    prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts", "generator")
    if content_type == "slide_deck":
        return os.path.join(prompts_dir, "slide_deck_spec.md")
    if content_type == "interactive_html":
        return os.path.join(prompts_dir, "interactive_html_unit_spec.md")
    return os.path.join(prompts_dir, "lecture_spec.md")


def _build_unit_spec_repair_prompt(
    content_type: str,
    state: ContentGenerationState,
    unit: OutlineUnit,
    unit_spec_id: str,
    chunk_ids: list[str],
    validation_errors: list[str],
) -> str:
    generation_prompt = _build_unit_spec_prompt(content_type, state, unit, unit_spec_id, chunk_ids)
    invalid_spec = state.current_unit_spec.model_dump(mode="json") if state.current_unit_spec else None
    repair_contract = {
        "content_type": content_type,
        "unit_spec_id": unit_spec_id,
        "outline_unit_id": unit.id,
        "outline_unit_order": unit.order,
        "validation_errors": validation_errors,
        "invalid_unit_spec": invalid_spec,
    }
    if content_type == "interactive_html":
        id_contract = {
            "section_id": unit_spec_id,
            "title": unit.title,
            "learning_goal": unit.goal,
        }
    else:
        id_contract = {
            "id": unit_spec_id,
            "outline_unit_id": unit.id,
            "order": unit.order,
        }
    return (
        f"{generation_prompt}\n\n"
        "## Repair context\n"
        "The previous unit spec failed workflow validation. Regenerate the full unit spec from scratch, using the same schema.\n"
        "Use the validation errors and invalid unit spec below only as diagnostic input. Do not copy invalid values unless they satisfy the contract.\n"
        "Hard contract for this unit:\n"
        f"{json.dumps(id_contract, ensure_ascii=False, indent=2)}\n\n"
        "Validation errors and previous invalid output:\n"
        f"{json.dumps(repair_contract, ensure_ascii=False, indent=2)}\n\n"
        "Return only corrected JSON for the requested schema."
    )


def _format_retrieval_results(chunks: list) -> str:
    if not chunks:
        return "No retrieval results."

    formatted = []
    for i, chunk in enumerate(chunks, 1):
        chunk_id = getattr(chunk, "id", f"chunk_{i}")
        source_title = getattr(chunk, "source_title", "")
        score = getattr(chunk, "score", 0.0)
        content = getattr(chunk, "content", "")[:500]
        formatted.append(f"[chunk_id={chunk_id}]")
        if source_title:
            formatted.append(f"source_title: {source_title}")
        formatted.append(f"score: {score}")
        formatted.append(f"content: {content}")
        formatted.append("")

    return "\n".join(formatted)


def build_lecture_unit_spec_fallback(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> LectureSection:
    section_id = f"lecture_{unit.id}"
    options = state.normalized_request or {}
    include_images = bool(options.get("include_images", True))
    include_mindmap = bool(options.get("include_mindmap", False))

    required_elements: list[RequiredElementSpec] = []
    blocks = [
        TextBlock(
            id=f"{section_id}_intro",
            title=f"{unit.title}: core idea",
            content=(
                f"{unit.core_message}\n\n"
                f"This section helps learners reach the goal: {unit.goal}. Start from the core idea, then connect each "
                "detail back to the larger learning path."
            ),
            citations=chunk_ids,
        )
    ]

    if include_images:
        image_spec = _image_spec_for_unit(
            unit=unit,
            unit_spec_id=section_id,
            request_id=state.request_id,
            chunk_ids=chunk_ids,
            aspect_ratio="4:3",
            style=str(options.get("image_style") or "clean educational illustration"),
            purpose="Use a visual only where it makes the concept easier to understand than text alone.",
            instruction=(
                f"Create a local illustration asset for '{unit.title}', meant to be embedded inside a lecture section. "
                f"Show the core message: {unit.core_message}. Use a focused diagram, timeline, process graphic, or "
                "concept illustration with a clear hierarchy and concise labels. Do not create a full presentation slide, "
                "slide title, banner, footer, agenda, summary panel, or page-like teaching layout. Avoid decorative "
                "backgrounds, tiny text, unrelated people, and vague stock imagery."
            ),
        )
        required_elements.append(image_spec)
        blocks.append(
            ElementReferenceBlock(
                id=f"{section_id}_image_ref",
                title=image_spec.title,
                element_id=image_spec.element_id,
            )
        )

    points = unit.key_points or ["core concept", "key relationship", "application scenario"]
    blocks.append(
        TextBlock(
            id=f"{section_id}_details",
            title=f"{unit.title}: detailed explanation",
            content="\n\n".join(
                f"{index}. {point}: explain what this means, why it matters, and how it connects to '{unit.title}'."
                for index, point in enumerate(points, 1)
            ),
            citations=chunk_ids,
        )
    )

    if include_mindmap:
        mindmap_spec = _mindmap_spec_for_unit(
            unit=unit,
            unit_spec_id=section_id,
            request_id=state.request_id,
            chunk_ids=chunk_ids,
            purpose="Summarize the structure only when the section has several related concepts.",
            instruction=(
                f"Create Markmap-compatible Markdown with root '{unit.title}'. Use at most 3 levels and 3-5 first-level "
                "branches covering definitions, key points, relationships, and applications. Keep node labels short."
            ),
        )
        required_elements.append(mindmap_spec)
        blocks.append(
            ElementReferenceBlock(
                id=f"{section_id}_mindmap_ref",
                title=mindmap_spec.title,
                element_id=mindmap_spec.element_id,
            )
        )

    blocks.append(
        TextBlock(
            id=f"{section_id}_summary",
            title=f"{unit.title}: wrap-up",
            content=(
                f"After this section, learners should be able to restate '{unit.core_message}' in their own words and "
                "use the listed points as a compact review framework."
            ),
            citations=chunk_ids,
        )
    )

    return LectureSection(
        id=section_id,
        outline_unit_id=unit.id,
        order=unit.order,
        title=unit.title,
        summary=unit.core_message,
        learning_goal=unit.goal,
        source_chunk_ids=chunk_ids,
        required_elements=required_elements,
        blocks=blocks,
    )


def build_slide_unit_spec_fallback(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> SlideSpecPage:
    slide_id = f"slide_{unit.id}"
    layout = _choose_slide_layout(unit)
    options = state.normalized_request or {}

    if layout == "visual_summary":
        return _build_visual_summary_fallback(slide_id, unit, state, chunk_ids, options)

    return _build_image_text_fallback(slide_id, unit, state, chunk_ids, options)


def _build_image_text_fallback(
    slide_id: str,
    unit: OutlineUnit,
    state: ContentGenerationState,
    chunk_ids: list[str],
    options: dict[str, object],
) -> SlideSpecPage:
    image_id = f"image_{state.request_id}_{unit.id}"
    points = unit.key_points[:BULLET_LIST_MAX] if unit.key_points else ["核心概念", "关键关系"]
    bullet_content = "\n".join(f"• {p[:BULLET_MAX_CN]}" for p in points)
    if len(points) < BULLET_LIST_MIN:
        while len(points) < BULLET_LIST_MIN:
            bullet_content += "\n• …"
            points.append("…")

    elements = [
        SlideSpecElement(id=f"{slide_id}_title", type="text", content=unit.title[:TITLE_MAX_CN], metadata={"role": "title"}),
        SlideSpecElement(
            id=f"{slide_id}_lead_card",
            type="text",
            content=unit.core_message,
            metadata={"role": "lead_card", "display_label": "核心解释", "content_format": "paragraph"},
        ),
        SlideSpecElement(
            id=f"{slide_id}_support_card",
            type="text",
            content=bullet_content,
            metadata={"role": "support_card", "display_label": "关键要点", "content_format": "bullets"},
        ),
        SlideSpecElement(id=f"{slide_id}_summary_text", type="text", content=unit.core_message[:IMAGE_TEXT_SUMMARY_MAX_CN], metadata={"role": "summary_text"}),
        SlideSpecElement(id=f"{slide_id}_visual_ref", type="element_ref", element_id=image_id, metadata={"role": "visual", "placement": "primary"}),
    ]

    required_elements = [
        RequiredElementSpec(
            element_id=image_id,
            type="image",
            title=f"{unit.title} illustration",
            purpose="Support the image_text slide with a low-density teaching visual.",
            instruction=(
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
            ),
            style=str(options.get("image_style") or "clean educational illustration, realistic diagram"),
            aspect_ratio="4:3",
            source_unit_id=slide_id,
            source_outline_unit_id=unit.id,
            source_chunk_ids=chunk_ids,
            priority="high",
        ),
    ]

    return SlideSpecPage(
        id=slide_id,
        outline_unit_id=unit.id,
        order=unit.order,
        title=unit.title,
        core_message=unit.core_message,
        layout="image_text",
        design_intent=_design_intent_for_layout("image_text"),
        theme_variant="teaching-clean",
        layout_hints={"density": "balanced", "supported_renderer": "scenekit.slide/v1", "primary_visual": image_id},
        required_elements=required_elements,
        speaker_notes=f"Explain this slide around the goal: {unit.goal}.",
        source_chunk_ids=chunk_ids,
        elements=elements,
    )


def _build_visual_summary_fallback(
    slide_id: str,
    unit: OutlineUnit,
    state: ContentGenerationState,
    chunk_ids: list[str],
    options: dict[str, object],
) -> SlideSpecPage:
    image_id = f"image_{state.request_id}_{unit.id}"

    elements = [
        SlideSpecElement(id=f"{slide_id}_title", type="text", content=unit.title[:TITLE_MAX_CN], metadata={"role": "title"}),
        SlideSpecElement(id=f"{slide_id}_summary_text", type="text", content=unit.core_message, metadata={"role": "summary_text"}),
        SlideSpecElement(id=f"{slide_id}_visual_ref", type="element_ref", element_id=image_id, metadata={"role": "visual", "placement": "primary"}),
    ]

    required_elements = [
        RequiredElementSpec(
            element_id=image_id,
            type="image",
            title=f"{unit.title} summary diagram",
            purpose="Support the visual_summary slide with a structured summary diagram.",
            instruction=(
                "Create a wide landscape summary diagram asset for the upper area of a teaching slide, not a full slide. "
                "Use a clear framework diagram, flowchart, process diagram, or structured summary diagram. "
                "The diagram should fit a wide horizontal canvas. "
                "Keep the main content inside a centered safe area with generous margins. "
                "Use 3-5 major nodes and at most 2 hierarchy levels. "
                "Use large readable labels with at most one short line per node. "
                "No outer title, no top banner, no footer, no bottom explanation bar, no slide border. "
                "Avoid numbered large cards, dense arrows, dense small text, poster layout, and full PowerPoint slide screenshot. "
                f"Topic: {unit.title}. Core message: {unit.core_message}."
            ),
            style=str(options.get("image_style") or "infographic, flowchart, framework diagram"),
            aspect_ratio="21:9",
            source_unit_id=slide_id,
            source_outline_unit_id=unit.id,
            source_chunk_ids=chunk_ids,
            priority="high",
        ),
    ]

    return SlideSpecPage(
        id=slide_id,
        outline_unit_id=unit.id,
        order=unit.order,
        title=unit.title,
        core_message=unit.core_message,
        layout="visual_summary",
        design_intent=_design_intent_for_layout("visual_summary"),
        theme_variant="teaching-clean",
        layout_hints={"density": "rich", "supported_renderer": "scenekit.slide/v1", "primary_visual": image_id},
        required_elements=required_elements,
        speaker_notes=f"Explain this slide around the goal: {unit.goal}.",
        source_chunk_ids=chunk_ids,
        elements=elements,
    )


def _image_spec_for_unit(
    unit: OutlineUnit,
    unit_spec_id: str,
    request_id: str,
    chunk_ids: list[str],
    aspect_ratio: str,
    style: str,
    purpose: str,
    instruction: str,
) -> RequiredElementSpec:
    return RequiredElementSpec(
        element_id=f"image_{request_id}_{unit.id}",
        type="image",
        title=f"{unit.title} visual explanation",
        purpose=purpose,
        instruction=instruction,
        style=style,
        aspect_ratio=aspect_ratio,
        source_unit_id=unit_spec_id,
        source_outline_unit_id=unit.id,
        source_chunk_ids=chunk_ids,
        priority="high",
    )


def _mindmap_spec_for_unit(
    unit: OutlineUnit,
    unit_spec_id: str,
    request_id: str,
    chunk_ids: list[str],
    purpose: str,
    instruction: str,
) -> RequiredElementSpec:
    return RequiredElementSpec(
        element_id=f"mindmap_{request_id}_{unit.id}",
        type="mindmap",
        title=f"{unit.title} knowledge map",
        purpose=purpose,
        instruction=instruction,
        source_unit_id=unit_spec_id,
        source_outline_unit_id=unit.id,
        source_chunk_ids=chunk_ids,
        priority="medium",
    )


def _choose_slide_layout(unit: OutlineUnit) -> str:
    if unit.visual_strategy in ("image_text", "visual_summary"):
        return unit.visual_strategy
    if unit.visual_strategy in ("process", "timeline", "comparison", "summary"):
        return "visual_summary"
    return "image_text"


def _design_intent_for_layout(layout: str) -> str:
    intents = {
        "image_text": "Pair the core explanation with a supporting teaching visual.",
        "visual_summary": "Present a structured summary diagram with concise text.",
    }
    return intents.get(layout, intents["image_text"])


def build_interactive_html_unit_spec_fallback(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> InteractiveHtmlSectionSpec:
    """Stub fallback producing a valid InteractiveHtmlSectionSpec — differentiated by module_type."""
    from app.schemas.specs.interactive_html import (
        AnimatedFlowBlock,
        AnimatedFlowPlayback,
        AnimatedFlowStep,
        CalloutBlock,
        CaseCompareBlock,
        CaseCompareCase,
        ConceptCardBlock,
        ContextInspectorBlock,
        ContextInspectorItem,
        DragMatchBlock,
        DragMatchItem,
        DragMatchTarget,
        FeedbackPolicy,
        Flashcard,
        FlashcardBlock,
        HeadingBlock,
        MultipleChoiceBlock,
        MultipleChoiceOption,
        ParagraphBlock,
        SequenceBlock,
        SequenceItem,
        ShortAnswerBlock,
        SingleChoiceBlock,
        SingleChoiceOption,
        SocraticChatBlock,
        SocraticRound,
        SocraticRoundOption,
        ScenarioBlock,
        Scene,
        SceneChoice,
        SummaryBlock,
    )

    section_id = unit.id
    mod = unit.module_type or _infer_module_type(unit.order, unit.title)
    points = unit.key_points or ["核心概念", "关键关系", "实践应用"]
    core = unit.core_message or unit.goal

    if mod == "hero":
        blocks = [
            HeadingBlock(block_id=f"{section_id}_h", level=2, text=unit.title),
            ParagraphBlock(block_id=f"{section_id}_p", text=f"{core}\n\n本课程将带你逐步理解核心概念、观察完整流程、分析真实案例，并通过互动练习检验学习成果。"),
            CalloutBlock(block_id=f"{section_id}_tip", variant="tip", content="建议按顺序学习各个模块，完成互动练习以巩固理解。预计学习时间 15-20 分钟。"),
        ]

    elif mod == "concept":
        p0 = points[0] if len(points) > 0 else "核心定义"
        p1 = points[1] if len(points) > 1 else "工作原理"
        p2 = points[2] if len(points) > 2 else "实际应用"
        blocks = [
            HeadingBlock(block_id=f"{section_id}_h", level=3, text=f"理解{p0}、{p1}与{p2}"),
            ParagraphBlock(block_id=f"{section_id}_intro", text=f"要理解{unit.title}，首先需要掌握几个核心概念。这些概念之间紧密关联，共同构成了本课程的知识基础。"),
            ConceptCardBlock(block_id=f"{section_id}_cc1", concept_id=f"{section_id}_c1", explanation=f"{p0}是{unit.title}领域中最基础的概念。{core}。掌握{p0}有助于建立对整体框架的初步理解，也为后续深入学习{p1}和{p2}打下基础。", key_terms=[p0, "基础概念", "入门理解"]),
            ConceptCardBlock(block_id=f"{section_id}_cc2", concept_id=f"{section_id}_c2", explanation=f"{p1}描述了{unit.title}的核心运作机制。理解{p1}需要结合{p0}的基础知识，二者相互补充。在实践中，{p1}决定了系统的效率和准确性。", key_terms=[p1, "核心机制", "运作原理"]),
            ConceptCardBlock(block_id=f"{section_id}_cc3", concept_id=f"{section_id}_c3", explanation=f"{p2}是{p0}和{p1}在真实场景中的体现。通过实际案例可以更直观地理解抽象概念。学习{p2}能帮助你将理论知识转化为实践能力。", key_terms=[p2, "实践应用", "案例学习"]),
            ParagraphBlock(block_id=f"{section_id}_bridge", text=f"以上三个概念——{p0}、{p1}和{p2}——相互关联、层层递进。{p0}是起点，{p1}是过程，{p2}是结果。建议结合后续的流程展示和案例分析来加深理解。"),
            CalloutBlock(block_id=f"{section_id}_imp", variant="important", content=f"记住：{p0}→{p1}→{p2} 构成了{unit.title}的完整知识链路。不要孤立地学习每个概念，要关注它们之间的联系。"),
        ]

    elif mod == "flow":
        steps_data = [
            ("提出问题", "学习者或用户提出需要解决的问题。问题越清晰、越具体，后续处理的效果越好。", "提问"),
            ("分析处理", "系统对输入进行分析和理解。这个阶段将原始问题转化为可处理的结构化信息。", "分析"),
            ("检索匹配", "从知识库或资料中查找相关信息。找到的资料越相关，输出的质量越高。", "检索"),
            ("生成结果", "基于分析和检索结果，系统生成结构化的输出内容。", "生成"),
            ("呈现反馈", "将生成的内容以合适的形式呈现给用户，并收集反馈用于持续改进。", "呈现"),
        ]
        blocks = [
            HeadingBlock(block_id=f"{section_id}_h", level=3, text=f"{unit.title}的完整过程"),
            ParagraphBlock(block_id=f"{section_id}_intro", text=f"了解{unit.title}的完整流程有助于建立系统性的认知。以下流程展示了从输入到输出的关键步骤，每一步都有其独特的作用和价值。"),
            AnimatedFlowBlock(
                block_id=f"{section_id}_flow",
                steps=[AnimatedFlowStep(step_id=f"{section_id}_s{i}", title=t, description=d, visual_label=v, tutor_message=f"步骤 {i+1}：{t}。{d}") for i, (t, d, v) in enumerate(steps_data)],
                playback=AnimatedFlowPlayback(mode="both", default_interval_ms=1500),
            ),
            CalloutBlock(block_id=f"{section_id}_tip", variant="tip", content="提示：你可以点击「播放动画」自动浏览整个流程，也可以点击「下一步」逐步查看每个环节的详细说明。"),
        ]

    elif mod == "case":
        blocks = [
            HeadingBlock(block_id=f"{section_id}_h", level=3, text=f"{unit.title}：不同做法的对比"),
            ParagraphBlock(block_id=f"{section_id}_intro", text=f"在{unit.title}中，不同的做法会产生截然不同的效果。下面通过两个案例的对比，帮助你理解什么是好的实践，什么是需要避免的做法。"),
            CaseCompareBlock(
                block_id=f"{section_id}_cases",
                cases=[
                    CaseCompareCase(case_id=f"{section_id}_good", title="推荐做法", content=f"充分准备、结构清晰、目标明确的{unit.title}方式。提前了解受众需求，选择合适的表达方式，并提供充分的上下文信息，这样产出的结果更准确、更有针对性。", tags=["推荐", "准确", "高效"], variant="good"),
                    CaseCompareCase(case_id=f"{section_id}_weak", title="不推荐的做法", content=f"信息不足、目标模糊、缺乏结构的{unit.title}方式。没有明确说明需求，缺少必要的背景信息，导致结果泛泛而谈，无法满足实际需要。", tags=["效率低", "结果模糊", "需要改进"], variant="weak"),
                ],
                takeaway=f"核心教训：充分准备和明确目标能极大提升{unit.title}的效果。不要省略关键信息，不要模糊表达需求。",
            ),
            CalloutBlock(block_id=f"{section_id}_imp", variant="important", content="在做选择时，始终问自己：目标是什么？受众是谁？我需要什么样的输出？这三个问题能帮助你做出更好的决策。"),
        ]

    elif mod == "socratic":
        blocks = [
            HeadingBlock(block_id=f"{section_id}_h", level=3, text=f"深入思考：{unit.title}"),
            ParagraphBlock(block_id=f"{section_id}_intro", text=f"让我们通过几轮问答来深入探究{unit.title}。请阅读每一轮的问题，选择一个你认同的回答，也可以输入自己的想法。这个对话过程将帮助你建立更深刻的理解。"),
            SocraticChatBlock(
                block_id=f"{section_id}_socratic",
                interaction_id=f"interaction_{section_id}",
                goal=f"通过三轮递进式对话，引导学生深入理解{core}",
                target_concepts=points[:3],
                purpose="guide_reflection",
                feedback_policy=FeedbackPolicy(immediate_feedback=True, show_explanation_after_answer=True, feedback_tone="socratic"),
                rounds=[
                    SocraticRound(
                        round_id=f"{section_id}_r1",
                        question=f"在你看来，{unit.title}最关键的要素是什么？为什么这个要素如此重要？",
                        options=[
                            SocraticRoundOption(option_id=f"{section_id}_r1a", text="充分的输入信息，因为信息越完整，后续处理越准确。", feedback="很好的观察。信息确实是基础——没有足够的信息，任何系统都难以给出有针对性的回答。但这个回答还可以进一步深入：除了信息量，信息的质量和组织方式也同样重要。", is_preferred=True),
                            SocraticRoundOption(option_id=f"{section_id}_r1b", text="速度最重要，越快越好。", feedback="速度固然重要，但如果牺牲了质量和准确性，快速反而可能导致问题。思考一下：在学习和理解场景中，你真的只关心速度吗？", is_preferred=False),
                            SocraticRoundOption(option_id=f"{section_id}_r1c", text="只要技术够先进就行，其他不重要。", feedback="技术是工具，不是目的。再先进的技术，如果没有明确的目标和合适的应用场景，也难以发挥价值。", is_preferred=False),
                        ],
                        expected_points=["输入信息的完整性和质量是基础", "单一要素无法保证好的结果"],
                    ),
                    SocraticRound(
                        round_id=f"{section_id}_r2",
                        question=f"假设你要向一个完全不懂{unit.title}的朋友解释它的价值，你会怎么组织你的解释？",
                        options=[
                            SocraticRoundOption(option_id=f"{section_id}_r2a", text="从生活场景切入，用类比帮助理解，再逐步引入核心概念。", feedback="非常好的策略！从熟悉到陌生、从具体到抽象是最有效的学习路径。这也正是好的教学内容应该遵循的原则。", is_preferred=True),
                            SocraticRoundOption(option_id=f"{section_id}_r2b", text="直接给出所有技术细节，让对方自己消化。", feedback="信息过载是学习的敌人。没有梯度的知识轰炸只会让人感到困惑和挫败。", is_preferred=False),
                            SocraticRoundOption(option_id=f"{section_id}_r2c", text="让对方自己搜索资料，我提供链接。", feedback="虽然自主学习很重要，但零散的参考资料缺乏结构。好的引导者应该帮助建立知识的框架。", is_preferred=False),
                        ],
                        expected_points=["好的解释应该从已知到未知逐步推进", "结构化比信息量更重要"],
                    ),
                    SocraticRound(
                        round_id=f"{section_id}_r3",
                        question=f"回顾你对前两个问题的思考，你觉得在{unit.title}中，'质量'是由哪些因素共同决定的？",
                        options=[
                            SocraticRoundOption(option_id=f"{section_id}_r3a", text="信息完整性、结构清晰度、受众匹配度三者缺一不可。", feedback="总结得非常到位！你已经抓住了核心——好的结果不是单一因素决定的，而是多个维度协同作用的产物。这也是本课程最想传达的洞察。", is_preferred=True),
                            SocraticRoundOption(option_id=f"{section_id}_r3b", text="只要有足够的计算资源就行。", feedback="计算资源是手段而非目的。资源再多，如果没有好的信息组织和明确的结构，产出也会令人失望。", is_preferred=False),
                            SocraticRoundOption(option_id=f"{section_id}_r3c", text="运气成分很大。", feedback="虽然不确定性存在，但通过系统性的方法可以大幅提升一致性。不要把不可控因素当作放弃努力的借口。", is_preferred=False),
                        ],
                        expected_points=["质量是多维度协同的结果", "系统性方法能提升一致性", "信息、结构、受众三个维度需要综合考虑"],
                    ),
                ],
            ),
            CalloutBlock(block_id=f"{section_id}_tip", variant="tip", content="对话教学目标：通过以上三轮追问，希望你已经发现——好的结果来自信息完整性、结构清晰度和受众匹配度的协同作用。这个洞察可以指导你的后续实践。"),
        ]

    elif mod == "scenario":
        blocks = [
            HeadingBlock(block_id=f"{section_id}_h", level=3, text=f"情景任务：{unit.title}"),
            ParagraphBlock(block_id=f"{section_id}_intro", text=f"在以下情景中，你将扮演一个需要运用{unit.title}知识的角色。每个任务都需要你做出决策，你的选择将影响最终的学习效果。"),
            ScenarioBlock(
                block_id=f"{section_id}_scenario",
                interaction_id=f"interaction_{section_id}",
                scenario_title=f"{unit.title}实战",
                background=f"你正在参与一个与{unit.title}相关的项目。你需要在多个环节做出决策，每个决策都会影响最终成果的质量。请根据你学到的知识做出最佳选择。",
                role=f"项目负责人（负责{unit.title}相关决策）",
                target_concepts=points[:3],
                purpose="choose_learning_path",
                feedback_policy=FeedbackPolicy(immediate_feedback=True, show_explanation_after_answer=True, feedback_tone="encouraging"),
                scenes=[
                    Scene(
                        scene_id=f"{section_id}_sc1",
                        task="明确需求和目标",
                        context=f"项目刚开始，你收到了一个与{unit.title}相关的任务请求。但这个请求非常模糊，只说了'帮我做一个东西'。你需要决定第一步怎么做。",
                        choices=[
                            SceneChoice(choice_id=f"{section_id}_sc1a", text="先和需求方沟通，明确受众、目标、格式和关键信息。", feedback="正确的选择！充分的前期沟通能避免后续返工。了解受众是谁、目标是什么、期望什么格式，这些信息决定了后续所有工作的方向。", is_preferred=True),
                            SceneChoice(choice_id=f"{section_id}_sc1b", text="马上开始工作，边做边调整。", feedback="这种方式可能导致大量返工。没有明确方向就开始，就像没有地图就出发——你可能会到达目的地，但更可能迷路。", is_preferred=False),
                            SceneChoice(choice_id=f"{section_id}_sc1c", text="等待对方给出更详细的说明再行动。", feedback="等待虽然比盲目行动好，但主动沟通、提出具体问题能更快推进项目。好的协作者会引导对方理清需求。", is_preferred=False),
                        ],
                    ),
                    Scene(
                        scene_id=f"{section_id}_sc2",
                        task="选择合适的方案",
                        context=f"需求已经明确：你需要为{unit.title}选择最合适的实施方案。有两个方案可选：方案 A 信息充足但较慢，方案 B 速度快但信息不够全面。",
                        choices=[
                            SceneChoice(choice_id=f"{section_id}_sc2a", text="选择方案 A，优先保证质量和准确性。", feedback="对于学习场景来说，质量和准确性通常比速度更重要。好的内容即使来得稍晚，也比差的内容更有价值。", is_preferred=True),
                            SceneChoice(choice_id=f"{section_id}_sc2b", text="选择方案 B，速度优先。", feedback="在时间压力下，速度的确有诱惑力。但如果信息不全面，可能导致后续产生误导或需要补充修正。", is_preferred=False),
                            SceneChoice(choice_id=f"{section_id}_sc2c", text="两个方案各取一部分，自己组合。", feedback="这种折中思路有创意，但增加了复杂度。在实际项目中，清晰的选择往往优于复杂的组合。", is_preferred=False),
                        ],
                    ),
                    Scene(
                        scene_id=f"{section_id}_sc3",
                        task="评估和优化结果",
                        context=f"方案实施后，你得到了初步结果。有些部分很好，有些部分需要改进。现在你需要决定如何优化。",
                        choices=[
                            SceneChoice(choice_id=f"{section_id}_sc3a", text="分析不足之处的根因，针对性地补充信息或调整结构。", feedback="优秀的做法！分析根因比表面修补更有效。找到问题的真正来源——是信息不足？结构不清？还是目标理解偏差？——然后对症下药。", is_preferred=True),
                            SceneChoice(choice_id=f"{section_id}_sc3b", text="全部推倒重来。", feedback="这会浪费已有成果。大部分情况下，局部优化比完全重来更高效、更可控。", is_preferred=False),
                            SceneChoice(choice_id=f"{section_id}_sc3c", text="不做修改，直接交付。", feedback="忽视已知的问题会降低最终质量。好的成果往往来自持续优化，而不是一次完成。", is_preferred=False),
                        ],
                    ),
                ],
            ),
            CalloutBlock(block_id=f"{section_id}_imp", variant="important", content="情景任务的核心启示：好的成果来自明确的目标、合适的方法和持续的优化。这三个环节缺一不可。"),
        ]

    elif mod == "practice":
        target_concepts = points[:3]
        fp = FeedbackPolicy(immediate_feedback=True, show_explanation_after_answer=True, feedback_tone="encouraging")
        blocks = [
            HeadingBlock(block_id=f"{section_id}_h", level=3, text=f"综合练习：检验你对{unit.title}的理解"),
            ParagraphBlock(block_id=f"{section_id}_intro", text="以下练习涵盖了本课程的核心知识点。请认真完成每道题，通过互动检验你的学习成果。"),
            # 单选题
            SingleChoiceBlock(
                block_id=f"{section_id}_q1", interaction_id=f"interaction_{section_id}_sc",
                question=f"关于{unit.title}，以下哪一项说法是正确的？",
                options=[
                    SingleChoiceOption(option_id=f"{section_id}_sc_a", text=f"{points[0] if len(points) > 0 else '核心概念'}是{unit.title}中最基础、最重要的要素。", is_correct=True, feedback="正确！你准确把握了核心概念的地位。"),
                    SingleChoiceOption(option_id=f"{section_id}_sc_b", text=f"在{unit.title}中，速度是唯一需要考虑的因素。", is_correct=False, feedback="不对。除了速度，质量、准确性、结构等多个维度同样重要。"),
                    SingleChoiceOption(option_id=f"{section_id}_sc_c", text=f"{unit.title}与信息质量无关，只取决于技术手段。", is_correct=False, feedback="不准确。信息质量和技术手段都是关键因素，二者缺一不可。"),
                    SingleChoiceOption(option_id=f"{section_id}_sc_d", text=f"只要完成{unit.title}就算成功，不需要关注过程和细节。", is_correct=False, feedback="这种看法忽视了过程的重要性。好的过程和关注细节才能产出好的结果。"),
                ],
                explanation=f"正确答案强调了核心概念的基础地位。在{unit.title}中，理解基础概念是正确实践的前提。",
                target_concepts=target_concepts, purpose="check_understanding", feedback_policy=fp,
            ),
            # 多选题
            MultipleChoiceBlock(
                block_id=f"{section_id}_q2", interaction_id=f"interaction_{section_id}_mc",
                question=f"要提高{unit.title}的质量，以下哪些做法是有效的？（多选）",
                options=[
                    MultipleChoiceOption(option_id=f"{section_id}_mc_a", text="提供充分、清晰的输入信息", is_correct=True, feedback="正确。充分的输入是高质量输出的基础。"),
                    MultipleChoiceOption(option_id=f"{section_id}_mc_b", text="明确目标和受众需求", is_correct=True, feedback="正确。明确目标和受众能确保结果的方向正确。"),
                    MultipleChoiceOption(option_id=f"{section_id}_mc_c", text="尽可能减少步骤以节省时间", is_correct=False, feedback="减少必要步骤可能损害质量。关键在于优化而非简单省略。"),
                    MultipleChoiceOption(option_id=f"{section_id}_mc_d", text="持续收集反馈并迭代改进", is_correct=True, feedback="正确。反馈驱动的迭代是持续提升质量的关键。"),
                ],
                explanation="有效提升质量的做法包括：提供充分的信息、明确目标受众、以及持续迭代改进。节省步骤不是目标，优化过程才是。",
                target_concepts=target_concepts, purpose="check_understanding", feedback_policy=fp,
            ),
            # 拖拽匹配
            DragMatchBlock(
                block_id=f"{section_id}_q3", interaction_id=f"interaction_{section_id}_dm",
                instruction="将左侧的概念拖到右侧对应的描述上：",
                items=[
                    DragMatchItem(item_id=f"{section_id}_dm_i1", text="信息准备" if len(points) < 1 else points[0], correct_target_id=f"{section_id}_dm_t1"),
                    DragMatchItem(item_id=f"{section_id}_dm_i2", text="过程处理" if len(points) < 2 else points[1], correct_target_id=f"{section_id}_dm_t2"),
                    DragMatchItem(item_id=f"{section_id}_dm_i3", text="结果评估" if len(points) < 3 else points[2], correct_target_id=f"{section_id}_dm_t3"),
                ],
                targets=[
                    DragMatchTarget(target_id=f"{section_id}_dm_t1", label="输入阶段——决定后续处理的起点", description="为整个过程提供原始材料和方向"),
                    DragMatchTarget(target_id=f"{section_id}_dm_t2", label="核心环节——将输入转化为输出", description="运用方法和工具进行加工处理"),
                    DragMatchTarget(target_id=f"{section_id}_dm_t3", label="检验阶段——判断输出是否达标", description="对照目标和标准进行核查"),
                ],
                explanation="信息准备→过程处理→结果评估构成了一个完整的闭环。每个阶段都有其不可替代的作用。",
                target_concepts=target_concepts, purpose="check_understanding", feedback_policy=fp,
            ),
            # 排序题
            SequenceBlock(
                block_id=f"{section_id}_q4", interaction_id=f"interaction_{section_id}_seq",
                instruction=f"将{unit.title}的关键步骤排为正确顺序：",
                items=[
                    SequenceItem(item_id=f"{section_id}_seq_1", text="明确目标和受众", correct_order=0),
                    SequenceItem(item_id=f"{section_id}_seq_2", text="准备和组织信息", correct_order=1),
                    SequenceItem(item_id=f"{section_id}_seq_3", text="执行核心处理", correct_order=2),
                    SequenceItem(item_id=f"{section_id}_seq_4", text="检验和优化结果", correct_order=3),
                ],
                explanation="正确的顺序是：先明确目标→再准备信息→然后执行处理→最后检验优化。这个顺序确保了每一步都有充分的依据。",
                target_concepts=target_concepts, purpose="check_understanding", feedback_policy=fp,
            ),
            # 翻卡复习
            FlashcardBlock(
                block_id=f"{section_id}_cards",
                cards=[
                    Flashcard(card_id=f"{section_id}_fc1", front=f"{unit.title}最重要的原则是什么？", back="信息充分、目标明确、持续优化——三个原则缺一不可。"),
                    Flashcard(card_id=f"{section_id}_fc2", front=f"{unit.title}中最常见的错误是什么？", back="信息不足、目标模糊、忽视反馈。这三者是导致结果不佳的主要原因。"),
                    Flashcard(card_id=f"{section_id}_fc3", front="如何判断结果的好坏？", back="对照最初的目标和受众需求进行检验。好结果应该准确、完整、有针对性。"),
                ],
            ),
        ]

    elif mod == "summary":
        blocks = [
            HeadingBlock(block_id=f"{section_id}_h", level=3, text="总结回顾"),
            SummaryBlock(block_id=f"{section_id}_summary", points=[
                f"核心概念：{points[0] if len(points) > 0 else '基础知识'}是理解整个体系的基础，需要牢固掌握。",
                f"完整流程：从输入到输出，每一步都有其价值。理解流程有助于在实际应用中做出正确决策。",
                f"案例对比：好的做法和差的做法之间的差异，往往体现在准备充分度和结构清晰度上。",
                f"实践检验：通过多种互动题型的练习，你已经具备了在实践中运用这些知识的能力。",
                f"持续改进：学习是一个迭代过程。遇到新的场景时，回到这些基本原则来指导你的决策。",
            ]),
            CalloutBlock(block_id=f"{section_id}_imp", variant="important", content="下一步建议：尝试将本课程学到的原则应用到你的实际场景中。实践是检验理解的唯一标准。如果遇到困惑，欢迎重新回顾相关模块。"),
        ]

    else:
        # Fallback for unknown module_type — generate a minimal concept-like section
        blocks = [
            HeadingBlock(block_id=f"{section_id}_h", level=2, text=unit.title),
            ParagraphBlock(block_id=f"{section_id}_p", text=core),
            SummaryBlock(block_id=f"{section_id}_summary", points=points),
        ]

    return InteractiveHtmlSectionSpec(
        section_id=section_id,
        title=unit.title,
        learning_goal=unit.goal,
        concepts=[],
        blocks=blocks,
        citations=[],
    )


def _infer_module_type(order: int, title: str) -> str:
    """Infer module_type from unit order when module_type is not explicitly set."""
    mapping = {
        0: "hero",
        1: "concept",
        2: "flow",
        3: "case",
        4: "socratic",
        5: "scenario",
        # practice and summary are determined dynamically below
    }
    if order in mapping:
        return mapping[order]
    # The last unit is always summary, the second-to-last is practice
    # We can't know the total here, so use order >= 6 as heuristic
    if order >= 7:
        return "summary"
    if order >= 6:
        return "practice"
    return "concept"


def build_interactive_html_unit_spec_fallback(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> InteractiveHtmlSectionSpec:
    """Stub fallback producing a valid teaching design spec (no HTML)."""
    from app.schemas.specs.interactive_html import InteractiveHtmlTeachingBlock, InteractiveHtmlInteractionSpec

    section_id = unit.id
    title = unit.title
    goal = unit.goal
    core = unit.core_message or unit.goal
    points = (unit.key_points or ["核心概念", "关键关系", "实践应用"])[:4]
    interaction_id = f"{section_id}_check"
    first_point = points[0] if points else "核心概念"

    return InteractiveHtmlSectionSpec(
        section_id=section_id,
        title=title,
        learning_goal=goal,
        narrative_goal=f"理解{title}的核心要点并形成清晰判断",
        teaching_flow=[
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_intro",
                block_type="intro",
                title=title,
                teaching_role="set_context",
                content_goal=core,
                must_cover=[core],
            ),
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_concepts",
                block_type="concept_explanation",
                title="关键概念线索",
                teaching_role="explain_core",
                content_goal="讲解本节核心概念及其相互关系",
                must_cover=points[:3],
            ),
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_check_block",
                block_type="single_choice",
                title="关键学习点诊断",
                teaching_role="diagnose_understanding",
                content_goal="诊断学习者对核心概念的理解程度",
                must_cover=[first_point],
                interaction_id=interaction_id,
            ),
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_reflection",
                block_type="reflection",
                title="学习目标收束",
                teaching_role="prompt_reflection",
                content_goal=goal,
                must_cover=[goal],
            ),
        ],
        interaction_specs=[
            InteractiveHtmlInteractionSpec(
                interaction_id=interaction_id,
                block_id=f"{section_id}_check_block",
                type="single_choice",
                event_type="single_choice_answered",
                target_concepts=[first_point],
                prompt="下面哪一项最能概括本节的关键学习点？",
                options=[
                    {"id": "a", "text": first_point},
                    {"id": "b", "text": "只记住页面样式"},
                ],
            )
        ],
        citations=[],
    )
