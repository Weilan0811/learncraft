from app.schemas.specs import ElementRequest
from app.services.image_generation_service import get_image_generation_service
from app.workflows.nodes.helpers import fallback_image_element


def generate_image_element(state: dict[str, object]) -> dict[str, object]:
    request = ElementRequest.model_validate(state["element_request"])
    description = _build_image_description(request)
    try:
        aspect_ratio = str(request.constraints.get("aspect_ratio", "16:9"))
        generated = get_image_generation_service().generate_image(
            title=request.title,
            description=description,
            aspect_ratio=aspect_ratio,
        )
        element = generated.model_copy(
            update={
                "id": request.element_id,
                "source_unit_id": request.source_unit_id,
                "source_outline_unit_id": request.source_outline_unit_id,
                "source_chunk_ids": request.source_chunk_ids,
                "width": generated.metadata.get("width"),
                "height": generated.metadata.get("height"),
                "format": generated.metadata.get("format"),
                "model": generated.metadata.get("model"),
                "retry_count": int(generated.metadata.get("retry_count", 0)),
                "metadata": {
                    **generated.metadata,
                    "description": description,
                    "element_request_id": request.element_id,
                },
                "generation_info": {
                    "generator": "image_generation_service",
                    "provider": generated.metadata.get("provider", "stub"),
                    "model": generated.metadata.get("model", "stub"),
                    "prompt": generated.prompt,
                },
            }
        )
    except Exception as exc:
        element = fallback_image_element(request, str(exc), prompt=description)
    return {"current_unit_elements": [element]}


def _build_image_description(request: ElementRequest) -> str:
    parts = []

    if request.instruction:
        parts.append(request.instruction)
    elif request.purpose:
        parts.append(request.purpose)

    if request.context:
        context_info = []
        if "unit_title" in request.context:
            context_info.append(f"unit title: {request.context['unit_title']}")
        if "core_message" in request.context:
            context_info.append(f"core message: {request.context['core_message']}")
        if "key_points" in request.context and isinstance(request.context["key_points"], list):
            key_points = "; ".join(str(point) for point in request.context["key_points"][:4])
            if key_points:
                context_info.append(f"key points: {key_points}")
        if context_info:
            parts.append(" | ".join(context_info))

    style = request.constraints.get("style", "educational")
    parts.append(f"style: {style}")
    parts.append("Make the visual directly support the adjacent teaching text.")

    return ". ".join(str(part).strip() for part in parts if str(part).strip())


__all__ = ["generate_image_element"]
