from typing import Protocol

from app.schemas.elements import ContentElement
from app.schemas.render import RenderModel
from app.schemas.specs import ContentSpec


class Renderer(Protocol):
    def render(self, spec: ContentSpec, elements: list[ContentElement]) -> RenderModel:
        """Convert a content spec and generated elements into a frontend render model."""
        ...
