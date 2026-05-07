from app.schemas.elements import MindmapElement
from app.schemas.specs import ElementRequest


def generate_mindmap_element(state: dict[str, object]) -> dict[str, object]:
    request = ElementRequest.model_validate(state["element_request"])
    context = request.context
    key_points = context.get("key_points", [])
    if not isinstance(key_points, list) or not key_points:
        key_points = ["核心概念", "应用场景", "学习重点"]
    markdown = "\n".join([f"# {request.title}", *[f"## {point}" for point in key_points[:6]]])
    element = MindmapElement(
        id=request.element_id,
        title=request.title,
        markdown=markdown,
        source_unit_id=request.source_unit_id,
        source_outline_unit_id=request.source_outline_unit_id,
        source_chunk_ids=request.source_chunk_ids,
        metadata={"max_depth": 3, "format": "markmap_markdown", "fallback": True},
        render_hints={"renderer": "markmap", "export_as": ["svg", "png"]},
        generation_info={"generator": "mindmap_fallback"},
    )
    return {"current_unit_elements": [element]}


__all__ = ["generate_mindmap_element"]
