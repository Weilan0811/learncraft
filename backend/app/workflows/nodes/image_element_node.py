from app.schemas.specs import ElementRequest
from app.workflows.nodes.helpers import fallback_image_element
from app.services.image_generation_service import get_image_generation_service


def generate_image_element(state: dict[str, object]) -> dict[str, object]:
    request = ElementRequest.model_validate(state["element_request"])
    try:
        aspect_ratio = str(request.constraints.get("aspect_ratio", "16:9"))
        generated = get_image_generation_service().generate_image(
            title=request.title,
            description=request.instruction or request.purpose,
            aspect_ratio=aspect_ratio,
            asset_id=request.element_id,
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
                "generation_info": {
                    "generator": "image_generation_service",
                    "provider": generated.metadata.get("provider", "stub"),
                    "model": generated.metadata.get("model", "stub"),
                },
            }
        )
    except Exception as exc:
        element = fallback_image_element(request, str(exc))
    return {"current_unit_elements": [element]}


__all__ = ["generate_image_element"]
