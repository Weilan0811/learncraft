import math
import struct
import time
import wave
from io import BytesIO
from typing import Protocol

import httpx

from app.core.config import Settings, get_settings
from app.core.provider_config import ensure_capability
from app.schemas.elements.audio import AudioFileElement
from app.services.storage_service import LocalStorageService, StorageService


class TTSGenerationError(RuntimeError):
    """Raised when TTS generation fails."""


class TTSService(Protocol):
    last_retry_count: int

    def synthesize(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        ...


class StubTTSService:
    """Development placeholder that writes a real, playable WAV tone.

    It deliberately ignores ``output_format``: without an encoder the stub cannot
    produce MP3, and a text payload named ``.mp3`` is not a valid audio file.
    """

    def __init__(self, storage_service: StorageService | None = None, output_format: str = "mp3") -> None:
        self.storage_service = storage_service or LocalStorageService()
        self.output_format = output_format
        self.last_retry_count = 0
        self.last_metadata: dict[str, object] = {"provider": "stub", "format": "wav"}

    def synthesize(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        clean_text = text.strip()
        if not clean_text:
            raise TTSGenerationError("TTS text is empty.")
        duration = max(0.4, min(2.0, len(clean_text) / 12))
        record = self.storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{asset_id}.wav",
            content=_stub_wav(duration),
            content_type="audio/wav",
            kind="audio",
            metadata={
                "provider": "stub",
                "voice": voice,
                "format": "wav",
                "duration_seconds": round(duration, 3),
            },
        )
        self.last_retry_count = 0
        self.last_metadata = dict(record.metadata)
        return AudioFileElement(
            id=record.asset_id,
            title=f"{voice} audio",
            speaker="Person1" if voice == "Ethan" else "Person2",
            voice=voice,  # type: ignore[arg-type]
            audio_url=record.url,
            format="wav",
            byte_size=record.byte_size,
            order=_order_from_asset_id(asset_id),
            metadata={"provider": "stub", "voice": voice},
        )


def _stub_wav(duration_seconds: float, sample_rate: int = 16000) -> bytes:
    frame_count = max(1, int(sample_rate * duration_seconds))
    frames = bytearray()
    for index in range(frame_count):
        value = int(1200 * math.sin(2 * math.pi * 220 * index / sample_rate))
        frames.extend(struct.pack("<h", value))
    buffer = BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(bytes(frames))
    return buffer.getvalue()


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
        self.last_retry_count = 0
        self.last_metadata: dict[str, object] = {"provider": "bailian", "model": model}

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
        self.last_metadata = dict(record.metadata)
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
        self.last_retry_count = 0
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post(url, json=payload, headers=self._headers(), timeout=self.timeout_seconds)
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                self.last_retry_count += 1
                time.sleep(_retry_delay(exc, attempt))
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
                self.last_retry_count += 1
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
    ensure_capability(settings, "tts")
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


def _retry_delay(exc: Exception, attempt: int) -> float:
    response = getattr(exc, "response", None)
    if response is not None and getattr(response, "status_code", None) == 429:
        retry_after = getattr(response, "headers", {}).get("retry-after")
        try:
            if retry_after is not None:
                return max(1.0, float(retry_after))
        except (TypeError, ValueError):
            pass
        return min(5.0 * (attempt + 1), 20.0)
    return min(2**attempt, 5)


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
