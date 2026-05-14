from app.schemas.elements.common import BaseElement
from app.schemas.elements.audio import AudioFileElement, AudioScriptElement
from app.schemas.elements.visual import ChartElement, ImageElement, MindmapElement
from app.schemas.elements.learning import Citation, QuizElement, TableElement, TextElement

ContentElement = TextElement | ImageElement | ChartElement | MindmapElement | TableElement | QuizElement | Citation | AudioScriptElement | AudioFileElement

__all__ = [
    "BaseElement",
    "AudioScriptElement",
    "AudioFileElement",
    "TextElement",
    "ImageElement",
    "ChartElement",
    "MindmapElement",
    "TableElement",
    "QuizElement",
    "Citation",
    "ContentElement",
]
