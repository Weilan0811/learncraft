from pathlib import Path
from uuid import uuid4

from app.services.storage_service import LocalStorageService


class FakeJsonResponse:
    content = b""
    headers = {"content-type": "application/json"}

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


class FakeAudioResponse:
    content = b"fake-wav-bytes"
    headers = {"content-type": "audio/wav"}

    def raise_for_status(self) -> None:
        return None


def test_bailian_tts_service_calls_dashscope_multimodal_generation_and_downloads_audio() -> None:
    from app.services.tts_service import BailianTTSService

    class FakeClient:
        def __init__(self) -> None:
            self.payloads: list[dict[str, object]] = []
            self.download_urls: list[str] = []

        def post(self, url: str, **kwargs: object) -> FakeJsonResponse:
            assert url == "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
            self.payloads.append(kwargs["json"])  # type: ignore[arg-type]
            return FakeJsonResponse({"output": {"audio": {"url": "https://example.test/audio.wav"}}})

        def get(self, url: str, **kwargs: object) -> FakeAudioResponse:
            self.download_urls.append(url)
            return FakeAudioResponse()

    client = FakeClient()
    storage = LocalStorageService(storage_root=Path("storage") / "test_tts_service" / uuid4().hex)
    service = BailianTTSService(api_key="sk-test", storage_service=storage, client=client, max_retries=0)

    audio = service.synthesize(text="欢迎来到未来学习电台。", voice="Ethan", asset_id="podcast_task_seg_001")

    assert client.payloads == [
        {
            "model": "qwen3-tts-instruct-flash",
            "input": {
                "text": "欢迎来到未来学习电台。",
                "voice": "Ethan",
                "language_type": "Chinese",
            },
        }
    ]
    assert client.download_urls == ["https://example.test/audio.wav"]
    assert audio.type == "audio_file"
    assert audio.voice == "Ethan"
    assert audio.audio_url.startswith("/api/assets/")
    assert audio.format == "wav"
    assert storage.read_bytes(audio.id) == b"fake-wav-bytes"
