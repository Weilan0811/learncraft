import json
import os
import re
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
    LectureSection,
    RequiredElementSpec,
    SlideSpecElement,
    SlideSpecPage,
    SUMMARY_TEXT_MAX_SENTENCES,
    TAKEAWAY_MAX_CN,
    TextBlock,
    TITLE_MAX_CN,
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
    role_map = {
        "body": "explanation",
        "bullet-list": "bullet_list",
        "example": "explanation",
        "comparison": "explanation",
        "callout": "takeaway",
        "note": "explanation",
        "caption": "explanation",
    }

    for i, element in enumerate(elements):
        if element.type != "text":
            continue
        role = str(element.metadata.get("role") or "")
        if role in role_map:
            new_metadata = dict(element.metadata)
            new_metadata["role"] = role_map[role]
            elements[i] = element.model_copy(update={"metadata": new_metadata})

    roles = {str(e.metadata.get("role") or "") for e in elements if e.type == "text"}

    if layout == "image_text":
        elements = _ensure_image_text_roles(elements, roles, spec, unit)
    elif layout == "visual_summary":
        elements = _ensure_visual_summary_roles(elements, roles, spec, unit)

    elements = _enforce_text_budget(elements, layout)

    return elements


def _ensure_image_text_roles(
    elements: list[SlideSpecElement],
    roles: set[str],
    spec: SlideSpecPage,
    unit: OutlineUnit,
) -> list[SlideSpecElement]:
    slide_id = spec.id
    extra_notes: list[str] = []

    if "title" not in roles:
        elements.insert(0, SlideSpecElement(
            id=f"{slide_id}_title", type="text", content=unit.title[:TITLE_MAX_CN], metadata={"role": "title"},
        ))

    if "explanation" not in roles:
        content = spec.core_message or unit.core_message
        elements.append(SlideSpecElement(
            id=f"{slide_id}_explanation", type="text", content=content, metadata={"role": "explanation"},
        ))

    if "bullet_list" not in roles:
        points = unit.key_points[:BULLET_LIST_MAX] if unit.key_points else ["核心概念", "关键关系"]
        bullet_content = "\n".join(f"• {p[:BULLET_MAX_CN]}" for p in points)
        elements.append(SlideSpecElement(
            id=f"{slide_id}_bullet_list", type="text", content=bullet_content, metadata={"role": "bullet_list"},
        ))

    if "takeaway" not in roles:
        takeaway = spec.core_message or unit.core_message
        elements.append(SlideSpecElement(
            id=f"{slide_id}_takeaway", type="text", content=takeaway[:TAKEAWAY_MAX_CN], metadata={"role": "takeaway"},
        ))

    visual_refs = [e for e in elements if e.type == "element_ref" and e.metadata.get("role") == "visual"]
    if not visual_refs:
        image_id = f"image_{spec.id}"
        elements.append(SlideSpecElement(
            id=f"{slide_id}_visual_ref", type="element_ref", element_id=image_id,
            metadata={"role": "visual", "placement": "primary"},
        ))

    return elements


def _ensure_visual_summary_roles(
    elements: list[SlideSpecElement],
    roles: set[str],
    spec: SlideSpecPage,
    unit: OutlineUnit,
) -> list[SlideSpecElement]:
    slide_id = spec.id

    bullet_elements = [e for e in elements if e.type == "text" and e.metadata.get("role") == "bullet_list"]
    if bullet_elements and "summary_text" not in roles:
        merged = "。".join(
            line.strip(" •-\t") for e in bullet_elements for line in (e.content or "").splitlines() if line.strip()
        )
        elements.append(SlideSpecElement(
            id=f"{slide_id}_summary_text", type="text", content=merged, metadata={"role": "summary_text"},
        ))
        for be in bullet_elements:
            elements.remove(be)

    if "title" not in roles:
        elements.insert(0, SlideSpecElement(
            id=f"{slide_id}_title", type="text", content=unit.title[:TITLE_MAX_CN], metadata={"role": "title"},
        ))

    if "summary_text" not in roles:
        content = spec.core_message or unit.core_message
        elements.append(SlideSpecElement(
            id=f"{slide_id}_summary_text", type="text", content=content, metadata={"role": "summary_text"},
        ))

    visual_refs = [e for e in elements if e.type == "element_ref" and e.metadata.get("role") == "visual"]
    if not visual_refs:
        image_id = f"image_{spec.id}"
        elements.append(SlideSpecElement(
            id=f"{slide_id}_visual_ref", type="element_ref", element_id=image_id,
            metadata={"role": "visual", "placement": "primary"},
        ))

    return elements


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
            content = _truncate_sentences(content, SUMMARY_TEXT_MAX_SENTENCES)
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
                f"Create a focused visual asset for a teaching slide about '{unit.title}'. "
                f"Use a realistic illustration, hand-drawn sketch, or clean educational illustration style. "
                f"The image should explain one concept or scenario. Keep information density low. "
                f"Use little or no text inside the image. "
                f"Do not create a mind-map, dense infographic, poster, full slide, title page, agenda page, or bullet-list layout."
            )
            style = "clean educational illustration, realistic diagram, hand-drawn sketch"
            aspect_ratio = "4:3"
        else:
            instruction = (
                f"Create a structured summary diagram for a teaching slide about '{unit.title}'. "
                f"Use a clear infographic, flowchart, framework diagram, or process diagram style. "
                f"The image should carry the main structural information of the slide. "
                f"Moderate text labels are allowed if they are readable. "
                f"Keep the hierarchy clear and visually organized. "
                f"Do not create a full PowerPoint slide screenshot or a decorative illustration without structure."
            )
            style = "infographic, flowchart, framework diagram, process diagram"
            aspect_ratio = "16:9"

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
    return os.path.join(prompts_dir, "lecture_spec.md")


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
        SlideSpecElement(id=f"{slide_id}_explanation", type="text", content=unit.core_message, metadata={"role": "explanation"}),
        SlideSpecElement(id=f"{slide_id}_bullet_list", type="text", content=bullet_content, metadata={"role": "bullet_list"}),
        SlideSpecElement(id=f"{slide_id}_takeaway", type="text", content=unit.core_message[:TAKEAWAY_MAX_CN], metadata={"role": "takeaway"}),
        SlideSpecElement(id=f"{slide_id}_visual_ref", type="element_ref", element_id=image_id, metadata={"role": "visual", "placement": "primary"}),
    ]

    required_elements = [
        RequiredElementSpec(
            element_id=image_id,
            type="image",
            title=f"{unit.title} illustration",
            purpose="Support the image_text slide with a low-density teaching visual.",
            instruction=(
                f"Create a focused visual asset for a teaching slide about '{unit.title}'. "
                f"Use a realistic illustration, hand-drawn sketch, or clean educational illustration style. "
                f"The image should explain one concept or scenario. Keep information density low. "
                f"Use little or no text inside the image. "
                f"Do not create a mind-map, dense infographic, poster, full slide, title page, agenda page, or bullet-list layout."
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
                f"Create a structured summary diagram for a teaching slide about '{unit.title}'. "
                f"Use a clear infographic, flowchart, framework diagram, or process diagram style. "
                f"The image should carry the main structural information of the slide. "
                f"Moderate text labels are allowed if they are readable. "
                f"Keep the hierarchy clear and visually organized. "
                f"Do not create a full PowerPoint slide screenshot or a decorative illustration without structure."
            ),
            style=str(options.get("image_style") or "infographic, flowchart, framework diagram"),
            aspect_ratio="16:9",
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
