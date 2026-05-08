from html import escape
import time
from pathlib import Path
from typing import Protocol
from uuid import uuid4

import httpx

from app.core.config import Settings, get_settings
from app.schemas.elements import ImageElement
from app.services.storage_service import LocalStorageService, StorageService


class ImageGenerationError(RuntimeError):
    """Raised when an image provider cannot produce a usable local asset."""


class APIMartImageGenerationError(ImageGenerationError):
    """Raised when APIMart image generation fails."""


class ImageGenerationService(Protocol):
    def generate_image(
        self,
        title: str,
        description: str,
        aspect_ratio: str = "16:9",
        asset_id: str | None = None,
    ) -> ImageElement:
        """Generate and persist an image asset."""
        ...


class StubImageGenerationService:
    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()

    def generate_image(
        self,
        title: str,
        description: str,
        aspect_ratio: str = "16:9",
        asset_id: str | None = None,
    ) -> ImageElement:
        prompt = f"Clean educational illustration, {description}, aspect ratio {aspect_ratio}"
        svg = self._placeholder_svg(title=title, description=description)
        stored_asset_id = asset_id or f"img_{uuid4().hex[:12]}"
        record = self.storage_service.save_bytes(
            asset_id=stored_asset_id,
            filename=f"{stored_asset_id}.svg",
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


class APIMartImageGenerationService:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-image-2",
        base_url: str = "https://api.apimart.ai/v1",
        resolution: str = "1k",
        storage_service: StorageService | None = None,
        client: object | None = None,
        timeout_seconds: float = 60.0,
        poll_interval_seconds: float = 2.0,
        poll_timeout_seconds: float = 180.0,
    ) -> None:
        if not api_key:
            raise ValueError("APIMart API key is required for real image generation.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.resolution = resolution
        self.storage_service = storage_service or LocalStorageService()
        self.client = client or httpx.Client(timeout=timeout_seconds)
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.poll_timeout_seconds = poll_timeout_seconds

    def generate_image(
        self,
        title: str,
        description: str,
        aspect_ratio: str = "16:9",
        asset_id: str | None = None,
    ) -> ImageElement:
        prompt = self._build_prompt(description=description, aspect_ratio=aspect_ratio)
        task_id = self._submit_task(prompt=prompt, aspect_ratio=aspect_ratio)
        remote_url = self._wait_for_image_url(task_id)
        content, content_type = self._download_image(remote_url)
        file_format = self._format_from_content_type(content_type, remote_url)
        asset_id = asset_id or f"img_{uuid4().hex[:12]}"
        record = self.storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{asset_id}.{file_format}",
            content=content,
            content_type=content_type,
            kind="image",
            metadata={
                "provider": "apimart",
                "model": self.model,
                "resolution": self.resolution,
                "aspect_ratio": aspect_ratio,
                "size": aspect_ratio,
                "prompt": prompt,
                "task_id": task_id,
                "retry_count": 0,
                "format": file_format,
                **self._dimensions_for_aspect_ratio(aspect_ratio),
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

    def _submit_task(self, prompt: str, aspect_ratio: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": aspect_ratio,
            "resolution": self.resolution,
        }
        response = self.client.post(
            f"{self.base_url}/images/generations",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        task_id = data.get("task_id")
        if not isinstance(task_id, str):
            nested = data.get("data", {}) if isinstance(data, dict) else {}
            task_id = nested.get("task_id") if isinstance(nested, dict) else None
        if not isinstance(task_id, str):
            raise APIMartImageGenerationError("APIMart response did not include task_id.")
        return task_id

    def _wait_for_image_url(self, task_id: str) -> str:
        deadline = time.monotonic() + self.poll_timeout_seconds
        while time.monotonic() <= deadline:
            response = self.client.get(
                f"{self.base_url}/tasks/{task_id}",
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            status_payload = data.get("data", data) if isinstance(data, dict) else {}
            status = status_payload.get("status") if isinstance(status_payload, dict) else None
            if status == "completed":
                return self._extract_image_url(status_payload)
            if status == "failed":
                error = status_payload.get("error", {}) if isinstance(status_payload, dict) else {}
                message = error.get("message") if isinstance(error, dict) else None
                raise APIMartImageGenerationError(str(message or "APIMart image task failed."))
            if self.poll_interval_seconds > 0:
                time.sleep(self.poll_interval_seconds)
            else:
                break
        raise APIMartImageGenerationError(f"APIMart image task timed out: {task_id}")

    def _download_image(self, url: str) -> tuple[bytes, str]:
        response = self.client.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "image/png").split(";")[0]
        return response.content, content_type

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _build_prompt(description: str, aspect_ratio: str) -> str:
        return f"Clean educational illustration, {description}, aspect ratio {aspect_ratio}"

    @staticmethod
    def _extract_image_url(payload: dict[str, object]) -> str:
        result = payload.get("result", {})
        images = result.get("images", []) if isinstance(result, dict) else []
        if images and isinstance(images[0], dict):
            urls = images[0].get("url")
            if isinstance(urls, list) and urls and isinstance(urls[0], str):
                return urls[0]
            if isinstance(urls, str):
                return urls
        raise APIMartImageGenerationError("APIMart completed task did not include an image URL.")

    @staticmethod
    def _format_from_content_type(content_type: str, remote_url: str) -> str:
        if content_type == "image/jpeg":
            return "jpg"
        if content_type.startswith("image/"):
            return content_type.removeprefix("image/").replace("svg+xml", "svg")
        suffix = Path(remote_url).suffix.lower().lstrip(".")
        return suffix or "png"

    @staticmethod
    def _dimensions_for_aspect_ratio(aspect_ratio: str) -> dict[str, int]:
        if aspect_ratio == "1:1":
            return {"width": 1024, "height": 1024}
        if aspect_ratio == "9:16":
            return {"width": 576, "height": 1024}
        return {"width": 1024, "height": 576}


class BailianImageGenerationService:
    def __init__(
        self,
        api_key: str,
        model: str = "qwen-image-2.0",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        storage_service: StorageService | None = None,
        client: object | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("Bailian API key is required for real image generation.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.storage_service = storage_service or LocalStorageService()
        self.client = client or httpx.Client(timeout=timeout_seconds)
        self.timeout_seconds = timeout_seconds

    def generate_image(
        self,
        title: str,
        description: str,
        aspect_ratio: str = "16:9",
        asset_id: str | None = None,
    ) -> ImageElement:
        prompt = f"Clean educational illustration, {description}, aspect ratio {aspect_ratio}"
        response = self.client.post(
            f"{self.base_url}/images/generations",
            json={"model": self.model, "prompt": prompt, "n": 1, "size": aspect_ratio},
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        image_url = self._extract_image_url(data)
        image_response = self.client.get(image_url, timeout=self.timeout_seconds)
        image_response.raise_for_status()
        content_type = image_response.headers.get("content-type", "image/png").split(";")[0]
        file_format = APIMartImageGenerationService._format_from_content_type(content_type, image_url)
        asset_id = asset_id or f"img_{uuid4().hex[:12]}"
        record = self.storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{asset_id}.{file_format}",
            content=image_response.content,
            content_type=content_type,
            kind="image",
            metadata={
                "provider": "bailian",
                "model": self.model,
                "aspect_ratio": aspect_ratio,
                "prompt": prompt,
                "retry_count": 0,
                "format": file_format,
                **APIMartImageGenerationService._dimensions_for_aspect_ratio(aspect_ratio),
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
    def _extract_image_url(data: dict[str, object]) -> str:
        output = data.get("output", {})
        results = output.get("results", []) if isinstance(output, dict) else []
        if results and isinstance(results[0], dict) and isinstance(results[0].get("url"), str):
            return results[0]["url"]
        choices = data.get("data", [])
        if choices and isinstance(choices, list) and isinstance(choices[0], dict) and isinstance(choices[0].get("url"), str):
            return choices[0]["url"]
        raise ImageGenerationError("Bailian image response did not include an image URL.")


def get_image_generation_service(settings: Settings | None = None, storage_service: StorageService | None = None) -> ImageGenerationService:
    settings = settings or get_settings()
    if settings.provider_mode == "stub":
        return StubImageGenerationService(storage_service=storage_service)
    if settings.image_provider == "apimart":
        return APIMartImageGenerationService(
            api_key=settings.apimart_api_key or "",
            model=settings.image_model,
            base_url=settings.apimart_base_url,
            resolution=settings.image_resolution,
            storage_service=storage_service,
            timeout_seconds=settings.request_timeout_seconds,
            poll_interval_seconds=settings.apimart_image_poll_interval_seconds,
            poll_timeout_seconds=settings.apimart_image_poll_timeout_seconds,
        )
    if settings.image_provider == "bailian":
        return BailianImageGenerationService(
            api_key=settings.bailian_api_key or "",
            model=settings.image_model,
            base_url=settings.bailian_base_url,
            storage_service=storage_service,
            timeout_seconds=settings.request_timeout_seconds,
        )
    raise ValueError(f"Unsupported image provider: {settings.image_provider}")
