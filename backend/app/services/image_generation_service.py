import base64
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
        layout: str = "image_text",
    ) -> ImageElement:
        """Generate and persist an image asset."""
        ...


class StubImageGenerationService:
    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()
        self.last_retry_count = 0
        self.last_metadata: dict[str, object] = {"provider": "stub"}

    def generate_image(
        self,
        title: str,
        description: str,
        aspect_ratio: str = "16:9",
        asset_id: str | None = None,
        layout: str = "image_text",
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
        self.last_retry_count = 0
        self.last_metadata = dict(record.metadata)
        return ImageElement(
            id=record.asset_id,
            title=title,
            prompt=prompt,
            asset_url=record.url,
            alt_text=title,
            metadata=record.metadata,
            width=record.metadata.get("width"),
            height=record.metadata.get("height"),
            format="svg",
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
        self.last_retry_count = 0
        self.last_metadata: dict[str, object] = {"provider": "apimart", "model": model}

    def generate_image(
        self,
        title: str,
        description: str,
        aspect_ratio: str = "16:9",
        asset_id: str | None = None,
        layout: str = "image_text",
    ) -> ImageElement:
        if not description.strip():
            raise APIMartImageGenerationError(f"Image prompt is empty for title: {title}")
        prompt = self._build_prompt(description=description, aspect_ratio=aspect_ratio, layout=layout)
        data = self._submit_generation_request(prompt=prompt, aspect_ratio=aspect_ratio)
        response_mode = "task"
        task_id = self._extract_task_id(data)
        direct_image = self._extract_direct_image(data)
        remote_url = ""
        if direct_image is not None:
            response_mode, payload, content_type = direct_image
            if response_mode == "url":
                remote_url = payload.decode("utf-8")
                content, content_type = self._download_image(remote_url)
            else:
                content = payload
        else:
            if task_id is None:
                raise APIMartImageGenerationError("APIMart response did not include task_id or image data.")
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
                "response_mode": response_mode,
                "retry_count": 0,
                "format": file_format,
                **self._dimensions_for_aspect_ratio(aspect_ratio),
            },
        )
        self.last_metadata = dict(record.metadata)
        return ImageElement(
            id=record.asset_id,
            title=title,
            prompt=prompt,
            asset_url=record.url,
            alt_text=title,
            metadata=record.metadata,
            width=record.metadata.get("width"),
            height=record.metadata.get("height"),
            format=file_format,
            model=self.model,
        )

    def _submit_generation_request(self, prompt: str, aspect_ratio: str) -> dict[str, object]:
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
        if not isinstance(data, dict):
            raise APIMartImageGenerationError("APIMart response was not a JSON object.")
        return data

    def _submit_task(self, prompt: str, aspect_ratio: str) -> str:
        data = self._submit_generation_request(prompt=prompt, aspect_ratio=aspect_ratio)
        task_id = self._extract_task_id(data)
        if task_id is None:
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
    def _build_prompt(description: str, aspect_ratio: str, layout: str = "image_text") -> str:
        if layout == "visual_summary":
            return (
                "Create a wide landscape summary diagram asset for the upper area of a teaching slide, not a full slide. "
                "Use a clear framework diagram, flowchart, process diagram, or structured summary diagram. "
                "The diagram should fit a wide horizontal canvas. "
                "Keep the main content inside a centered safe area with generous margins. "
                "Use 3-5 major nodes and at most 2 hierarchy levels. "
                "Use large readable labels with at most one short line per node. "
                "No outer title, no top banner, no footer, no bottom explanation bar, no slide border. "
                "Avoid numbered large cards, dense arrows, dense small text, poster layout, and full PowerPoint slide screenshot. "
                f"Description: {description}. Aspect ratio {aspect_ratio}."
            )
        return (
            "Create a low-density teaching illustration asset for a slide, not a full slide. "
            "The image will appear in a medium-sized right-side panel. "
            "Show one clear scene, object, metaphor, or simple action. "
            "Use realistic illustration, hand-drawn sketch, or clean educational illustration style. "
            "No title bar, no header, no footer, no slide border, no lecture card layout. "
            "No infographic. No flowchart. No architecture diagram. No mind map. "
            "No dense arrows. No multiple panels. No small text. "
            "Use at most 1-3 short labels only if necessary. "
            "The image must remain readable in a compact slide image area. "
            f"Description: {description}. Aspect ratio {aspect_ratio}."
        )

    @staticmethod
    def _extract_task_id(data: dict[str, object]) -> str | None:
        task_id = data.get("task_id")
        if isinstance(task_id, str):
            return task_id
        nested = data.get("data", {})
        if isinstance(nested, dict) and isinstance(nested.get("task_id"), str):
            return nested["task_id"]
        if isinstance(nested, list):
            for item in nested:
                if isinstance(item, dict) and isinstance(item.get("task_id"), str):
                    return item["task_id"]
        return None

    @staticmethod
    def _extract_direct_image(data: dict[str, object]) -> tuple[str, bytes, str] | None:
        entries = data.get("data", [])
        if isinstance(entries, dict):
            entries = [entries]
        if not isinstance(entries, list) or not entries or not isinstance(entries[0], dict):
            return None
        first = entries[0]
        b64_json = first.get("b64_json")
        if isinstance(b64_json, str) and b64_json.strip():
            return ("b64_json", base64.b64decode(b64_json), "image/png")
        url = first.get("url")
        if isinstance(url, str) and url.strip():
            return ("url", url.encode("utf-8"), "text/uri-list")
        return None

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
        if aspect_ratio == "21:9":
            return {"width": 1344, "height": 576}
        return {"width": 1024, "height": 576}


class BailianImageGenerationService:
    """DashScope native text-to-image via the async two-phase task API.

    NOTE: DashScope's OpenAI-compatible layer (/compatible-mode/v1) does NOT expose
    /images/generations for image models — that path returns 404 (verified 2026-11-07,
    regardless of model name, while /chat/completions works with the same key).
    Text-to-image must use the native API:
      1) POST /services/aigc/text2image/image-synthesis with X-DashScope-Async: enable
      2) poll GET /tasks/{task_id} until SUCCEEDED
      3) download output.results[0].url
    """

    NATIVE_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "wan2.2-t2i-flash",
        base_url: str | None = None,
        storage_service: StorageService | None = None,
        client: object | None = None,
        timeout_seconds: float = 60.0,
        poll_interval_seconds: float = 2.0,
        poll_timeout_seconds: float = 180.0,
    ) -> None:
        if not api_key:
            raise ValueError("Bailian API key is required for real image generation.")
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or self.NATIVE_DEFAULT_BASE_URL).rstrip("/")
        self.storage_service = storage_service or LocalStorageService()
        self.client = client or httpx.Client(timeout=timeout_seconds)
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.poll_timeout_seconds = poll_timeout_seconds
        self.last_retry_count = 0
        self.last_metadata: dict[str, object] = {"provider": "bailian", "model": model}

    def generate_image(
        self,
        title: str,
        description: str,
        aspect_ratio: str = "16:9",
        asset_id: str | None = None,
        layout: str = "image_text",
    ) -> ImageElement:
        prompt = f"Clean educational illustration, {description}, aspect ratio {aspect_ratio}"
        # wan2.2 free-tier concurrency is low; a 429 here is a throttle, not an error.
        submit_response = None
        for attempt in range(3):
            submit_response = self.client.post(
                f"{self.base_url}/services/aigc/text2image/image-synthesis",
                json={
                    "model": self.model,
                    "input": {"prompt": prompt},
                    "parameters": {"size": self._size_for_aspect_ratio(aspect_ratio), "n": 1},
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-DashScope-Async": "enable",
                },
                timeout=self.timeout_seconds,
            )
            if submit_response.status_code != 429:
                break
            time.sleep(15.0 * (attempt + 1))
        submit_response.raise_for_status()
        submit_data = submit_response.json()
        output = submit_data.get("output") if isinstance(submit_data, dict) else None
        task_id = output.get("task_id") if isinstance(output, dict) else None
        if not task_id:
            raise ImageGenerationError("Bailian image task submission did not return a task_id.")
        image_url = self._poll_task_url(str(task_id))
        image_response = self.client.get(image_url, timeout=self.timeout_seconds)
        image_response.raise_for_status()
        content_type = image_response.headers.get("content-type", "image/png").split(";")[0]
        file_format = APIMartImageGenerationService._format_from_content_type(content_type, image_url)
        resolved_asset_id = asset_id or f"img_{uuid4().hex[:12]}"
        record = self.storage_service.save_bytes(
            asset_id=resolved_asset_id,
            filename=f"{resolved_asset_id}.{file_format}",
            content=image_response.content,
            content_type=content_type,
            kind="image",
            metadata={
                "provider": "bailian",
                "model": self.model,
                "aspect_ratio": aspect_ratio,
                "size": self._size_for_aspect_ratio(aspect_ratio),
                "prompt": prompt,
                "retry_count": 0,
                "format": file_format,
                **APIMartImageGenerationService._dimensions_for_aspect_ratio(aspect_ratio),
            },
        )
        self.last_retry_count = 0
        self.last_metadata = dict(record.metadata)
        return ImageElement(
            id=record.asset_id,
            title=title,
            prompt=prompt,
            asset_url=record.url,
            alt_text=title,
            metadata=record.metadata,
        )

    def _poll_task_url(self, task_id: str) -> str:
        deadline = time.monotonic() + self.poll_timeout_seconds
        last_status = None
        while time.monotonic() < deadline:
            response = self.client.get(
                f"{self.base_url}/tasks/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            output = payload.get("output") if isinstance(payload, dict) else None
            status = output.get("task_status") if isinstance(output, dict) else None
            last_status = status
            if status == "SUCCEEDED":
                results = output.get("results") or []
                url = results[0].get("url") if results and isinstance(results[0], dict) else None
                if not url:
                    raise ImageGenerationError("Bailian image task succeeded without an image URL.")
                return str(url)
            if status in {"FAILED", "UNKNOWN", "CANCELED"}:
                message = output.get("message") or output.get("code") if isinstance(output, dict) else None
                raise ImageGenerationError(f"Bailian image task {task_id} ended with status {status}: {message or ''}")
            time.sleep(self.poll_interval_seconds)
        raise ImageGenerationError(f"Bailian image task timed out after {self.poll_timeout_seconds}s (last status: {last_status}): {task_id}")

    @staticmethod
    def _size_for_aspect_ratio(aspect_ratio: str) -> str:
        # DashScope native API uses "width*height" strings and requires both
        # dimensions within 512-1440 ("Either width or height should be between
        # 512 and 1440"). All mapped sizes stay inside that window; wide covers
        # keep the target ratio as closely as the window allows.
        mapping = {
            "1:1": "1024*1024",
            "9:16": "810*1440",
            "16:9": "1440*810",
            "21:9": "1440*618",
        }
        return mapping.get(aspect_ratio, "1440*810")


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
            storage_service=storage_service,
            timeout_seconds=settings.request_timeout_seconds,
            poll_interval_seconds=settings.apimart_image_poll_interval_seconds,
            poll_timeout_seconds=settings.apimart_image_poll_timeout_seconds,
        )
    raise ValueError(f"Unsupported image provider: {settings.image_provider}")
