from html import escape
from typing import Protocol

from app.schemas.elements import ImageElement
from app.services.storage_service import LocalStorageService, StorageService


class ImageGenerationService(Protocol):
    def generate_image(self, title: str, description: str, aspect_ratio: str = "16:9") -> ImageElement:
        """Generate and persist an image asset."""
        ...


class StubImageGenerationService:
    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()

    def generate_image(self, title: str, description: str, aspect_ratio: str = "16:9") -> ImageElement:
        prompt = f"Clean educational illustration, {description}, aspect ratio {aspect_ratio}"
        svg = self._placeholder_svg(title=title, description=description)
        record = self.storage_service.save_bytes(
            asset_id="img_stub",
            filename="img_stub.svg",
            content=svg.encode("utf-8"),
            content_type="image/svg+xml",
            kind="image",
            metadata={
                "aspect_ratio": aspect_ratio,
                "prompt": prompt,
                "provider": "stub",
                "width": 1280,
                "height": 720,
                "format": "svg",
            },
        )
        return ImageElement(
            id=record.asset_id,
            title=title,
            prompt=prompt,
            asset_url=record.url,
            alt_text=title,
            metadata=record.metadata,
        )

    @staticmethod
    def _placeholder_svg(title: str, description: str) -> str:
        safe_title = escape(title)
        safe_description = escape(description)
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">'
            '<rect width="1280" height="720" fill="#f8fafc"/>'
            '<rect x="80" y="80" width="1120" height="560" rx="28" fill="#dbeafe" stroke="#2563eb" stroke-width="8"/>'
            f'<text x="120" y="220" font-family="Arial, sans-serif" font-size="56" font-weight="700" fill="#111827">{safe_title}</text>'
            f'<text x="120" y="320" font-family="Arial, sans-serif" font-size="34" fill="#1f2937">{safe_description}</text>'
            '<circle cx="1060" cy="500" r="74" fill="#0f766e" opacity="0.9"/>'
            '<circle cx="960" cy="505" r="44" fill="#2563eb" opacity="0.9"/>'
            '<circle cx="1130" cy="510" r="38" fill="#f59e0b" opacity="0.9"/>'
            "</svg>"
        )
