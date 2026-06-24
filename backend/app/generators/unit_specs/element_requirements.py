from app.schemas.outline import OutlineUnit
from app.schemas.specs import RequiredElementSpec


def image_spec_for_unit(
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


def mindmap_spec_for_unit(
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
