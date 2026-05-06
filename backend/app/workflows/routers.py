from app.exporters.asset_exporter import AssetExporter
from app.exporters.base_exporter import Exporter
from app.exporters.pdf_exporter import PDFExporter
from app.exporters.slide_exporter import SlideExporter
from app.renderers.lecture_renderer import LectureRenderer
from app.renderers.slide_renderer import SlideRenderer
from app.schemas.base import ExportType, MvpContentType
from app.services.storage_service import StorageService


def get_renderer(content_type: MvpContentType) -> LectureRenderer | SlideRenderer:
    if content_type == "slide_deck":
        return SlideRenderer()
    return LectureRenderer()


def get_default_exporter(content_type: MvpContentType) -> PDFExporter | SlideExporter:
    if content_type == "slide_deck":
        return SlideExporter()
    return PDFExporter()


def get_exporter(export_type: ExportType, storage_service: StorageService | None = None) -> Exporter:
    if export_type == "pdf":
        return PDFExporter(storage_service=storage_service)
    if export_type == "slide_json":
        return SlideExporter(storage_service=storage_service)
    if export_type == "image_assets":
        return AssetExporter(storage_service=storage_service)
    raise ValueError(f"Unsupported export type: {export_type}")
