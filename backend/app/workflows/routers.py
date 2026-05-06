from app.exporters.pdf_exporter import PDFExporter
from app.exporters.slide_exporter import SlideExporter
from app.renderers.lecture_renderer import LectureRenderer
from app.renderers.slide_renderer import SlideRenderer
from app.schemas.base import MvpContentType


def get_renderer(content_type: MvpContentType) -> LectureRenderer | SlideRenderer:
    if content_type == "slide_deck":
        return SlideRenderer()
    return LectureRenderer()


def get_default_exporter(content_type: MvpContentType) -> PDFExporter | SlideExporter:
    if content_type == "slide_deck":
        return SlideExporter()
    return PDFExporter()
