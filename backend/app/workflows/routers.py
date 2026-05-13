from app.exporters.asset_exporter import AssetExporter
from app.exporters.base_exporter import Exporter
from app.exporters.html_exporter import HTMLExporter
from app.exporters.pdf_exporter import PDFExporter
from app.exporters.slide_exporter import SlideExporter
from app.content_types.registry import get_content_type_profile
from app.renderers.lecture_renderer import LectureRenderer
from app.renderers.slide_renderer import SlideRenderer
from app.renderers.social_post_renderer import SocialPostRenderer
from app.schemas.base import ContentType, ExportType
from app.services.storage_service import StorageService


def get_renderer(content_type: ContentType) -> LectureRenderer | SlideRenderer | SocialPostRenderer:
    return get_content_type_profile(content_type).renderer_factory()


def get_default_exporter(content_type: ContentType) -> PDFExporter | SlideExporter:
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
    if export_type == "html":
        return HTMLExporter(storage_service=storage_service)
    raise ValueError(f"Unsupported export type: {export_type}")
