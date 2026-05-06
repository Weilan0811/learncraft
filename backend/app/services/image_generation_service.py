from typing import Protocol

from app.schemas.elements import ImageElement


class ImageGenerationService(Protocol):
    def generate_image(self, title: str, description: str, aspect_ratio: str = "16:9") -> ImageElement:
        """Generate and persist an image asset."""
        ...


class StubImageGenerationService:
    def generate_image(self, title: str, description: str, aspect_ratio: str = "16:9") -> ImageElement:
        prompt = f"Clean educational illustration, {description}, aspect ratio {aspect_ratio}"
        return ImageElement(
            id="img_stub",
            title=title,
            prompt=prompt,
            asset_url="/api/assets/img_stub",
            alt_text=title,
            metadata={"aspect_ratio": aspect_ratio, "stub": True},
        )
