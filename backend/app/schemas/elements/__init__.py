from app.schemas.elements.common import BaseElement
from app.schemas.elements.visual import ChartElement, ImageElement, MindmapElement
from app.schemas.elements.learning import Citation, QuizElement, TableElement, TextElement

ContentElement = TextElement | ImageElement | ChartElement | MindmapElement | TableElement | QuizElement | Citation

__all__ = [
    "BaseElement",
    "TextElement",
    "ImageElement",
    "ChartElement",
    "MindmapElement",
    "TableElement",
    "QuizElement",
    "Citation",
    "ContentElement",
]
