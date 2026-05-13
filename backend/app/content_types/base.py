from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from app.schemas.base import ContentType, ExportType, SchemaModel


@dataclass(frozen=True)
class ElementPolicy:
    allowed_elements: tuple[str, ...] = ("image", "mindmap")
    default_required_elements: tuple[str, ...] = ("image",)
    optional_elements: tuple[str, ...] = ("mindmap",)


@dataclass(frozen=True)
class ContentTypeProfile:
    content_type: ContentType
    generation_mode: Literal["unit_loop", "direct"]
    unit_type: str
    requires_outline: bool
    supports_unit_streaming: bool
    planner_prompt_name: str
    unit_spec_prompt_name: str
    spec_schema: type[SchemaModel]
    unit_spec_schema: type[SchemaModel]
    render_model_schema: type[SchemaModel]
    renderer_factory: Callable[[], Any]
    generator_name: str
    element_policy: ElementPolicy = field(default_factory=ElementPolicy)
    exporter_types: tuple[ExportType, ...] = ("pdf",)
