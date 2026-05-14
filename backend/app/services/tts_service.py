import time
from typing import Protocol

import httpx

from app.core.config import Settings, get_settings
from app.schemas.elements.audio import AudioFileElement
from app.services.storage_service import LocalStorageService, StorageService


class TTSGenerationError(RuntimeError):
    """Raised when TTS generation fails."""


class TTSService(Protocol):
    def synthesize(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        ...


class StubTTSService:
    def __init__(self, storage_service: StorageService | None = None, output_format: str = "mp3") -> None:
        self.storage_service = storage_service or LocalStorageService()
        self.output_format = output_format

    def synthesize(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        if not text.strip():
            raise TTSGenerationError("TTS text is empty.")
        payload = f"stub audio\nvoice={voice}\n{text}".encode("utf-8")
        record = self.storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{asset_id}.{self.output_format}",
            content=payload,
            content_type=_content_type(self.output_format),
            kind="audio",
            metadata={"provider": "stub", "voice": voice, "format": self.output_format},
        )
        return AudioFileElement(
            id=record.asset_id,
            title=f"{voice} audio",
            speaker="Person1" if voice == "Ethan" else "Person2",
            voice=voice,  # type: ignore[arg-type]
            audio_url=record.url,
            format=self.output_format,
            byte_size=record.byte_size,
            order=_order_from_asset_id(asset_id),
            metadata={"provider": "stub", "voice": voice},
        )


class BailianTTSService:
    def __init__(
        self,
        api_key: str,
        model: str = "qwen3-tts-instruct-flash",
        base_url: str = "https://dashscope.aliyuncs.com",
        timeout_seconds: float = 120.0,
        max_retries: int = 2,
        output_format: str = "mp3",
        storage_service: StorageService | None = None,
        client: object | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Bailian API key is required for real TTS calls.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.output_format = output_format
        self.storage_service = storage_service or LocalStorageService()
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def synthesize(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        clean_text = text.strip()
        if not clean_text:
            raise TTSGenerationError("TTS text is empty.")
        payload = {
            "model": self.model,
            "input": {
                "text": clean_text,
                "voice": voice,
                "language_type": "Chinese",
            },
        }
        response = self._post_with_retries(
            f"{self.base_url}/api/v1/services/aigc/multimodal-generation/generation",
            payload,
        )
        audio_url = self._extract_audio_url(response)
        audio_response = self._get_with_retries(audio_url)
        content = getattr(audio_response, "content", b"")
        content_type = str(
            getattr(audio_response, "headers", {}).get("content-type", _content_type(self.output_format))
        ).split(";", 1)[0]
        output_format = _format_from_content_type(content_type, fallback=self.output_format, url=audio_url)
        if not isinstance(content, bytes) or not content:
            raise TTSGenerationError("TTS response did not include audio bytes.")
        record = self.storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{asset_id}.{output_format}",
            content=content,
            content_type=content_type,
            kind="audio",
            metadata={"provider": "bailian", "model": self.model, "voice": voice, "format": output_format},
        )
        return AudioFileElement(
            id=record.asset_id,
            title=f"{voice} audio",
            speaker="Person1" if voice == "Ethan" else "Person2",
            voice=voice,  # type: ignore[arg-type]
            audio_url=record.url,
            format=output_format,
            byte_size=record.byte_size,
            order=_order_from_asset_id(asset_id),
            metadata={"provider": "bailian", "model": self.model, "voice": voice},
        )

    def _post_with_retries(self, url: str, payload: dict[str, object]) -> object:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post(url, json=payload, headers=self._headers(), timeout=self.timeout_seconds)
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(min(2**attempt, 5))
        raise TTSGenerationError(f"TTS request failed after retries: {last_error}") from last_error

    def _get_with_retries(self, url: str) -> object:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.get(url, timeout=self.timeout_seconds)
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(min(2**attempt, 5))
        raise TTSGenerationError(f"TTS audio download failed after retries: {last_error}") from last_error

    def _extract_audio_url(self, response: object) -> str:
        try:
            data = response.json()  # type: ignore[attr-defined]
        except Exception as exc:
            raise TTSGenerationError(f"TTS response was not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise TTSGenerationError("TTS response JSON was not an object.")
        output = data.get("output")
        if not isinstance(output, dict):
            raise TTSGenerationError("TTS response did not include output.")
        audio = output.get("audio")
        if isinstance(audio, dict) and isinstance(audio.get("url"), str):
            return audio["url"]
        if isinstance(output.get("audio_url"), str):
            return output["audio_url"]
        if isinstance(output.get("url"), str):
            return output["url"]
        audios = output.get("audios")
        if isinstance(audios, list) and audios and isinstance(audios[0], dict) and isinstance(audios[0].get("url"), str):
            return audios[0]["url"]
        raise TTSGenerationError("TTS response did not include an audio URL.")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}


def get_tts_service(settings: Settings | None = None) -> TTSService:
    settings = settings or get_settings()
    if settings.provider_mode == "stub":
        return StubTTSService(output_format=settings.tts_output_format)
    if settings.tts_provider != "bailian":
        raise ValueError(f"Unsupported TTS provider: {settings.tts_provider}")
    return BailianTTSService(
        api_key=settings.bailian_api_key or "",
        model=settings.tts_model,
        base_url=settings.bailian_tts_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        max_retries=settings.max_retries,
        output_format=settings.tts_output_format,
    )


def _content_type(output_format: str) -> str:
    if output_format == "wav":
        return "audio/wav"
    return "audio/mpeg"


def _format_from_content_type(content_type: str, *, fallback: str, url: str = "") -> str:
    normalized = content_type.lower()
    if "wav" in normalized:
        return "wav"
    if "mpeg" in normalized or "mp3" in normalized:
        return "mp3"
    suffix = url.rsplit("?", 1)[0].rsplit(".", 1)[-1].lower()
    if suffix in {"mp3", "wav"}:
        return suffix
    return fallback


def _order_from_asset_id(asset_id: str) -> int:
    try:
        return int(asset_id.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        return 0
