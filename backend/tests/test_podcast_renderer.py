import wave
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from app.renderers.podcast_renderer import PodcastRenderer
from app.schemas.elements.audio import AudioFileElement
from app.schemas.specs.podcast import PodcastSegmentSpec, PodcastSpec
from app.services.storage_service import LocalStorageService


class FakeTTSService:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def synthesize(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        self.texts.append(text)
        speaker = "Person1" if voice == "Ethan" else "Person2"
        order = int(asset_id.rsplit("_", 1)[1])
        return AudioFileElement(
            id=asset_id,
            speaker=speaker,
            voice=voice,
            audio_url=f"/api/assets/{asset_id}/download",
            order=order,
            title=f"{speaker} audio",
            metadata={"text": text},
        )


class FlakyTTSService:
    def __init__(self, storage: LocalStorageService) -> None:
        self.storage = storage
        self.calls_by_asset: dict[str, int] = {}

    def synthesize(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        self.calls_by_asset[asset_id] = self.calls_by_asset.get(asset_id, 0) + 1
        if asset_id.endswith("_001") and self.calls_by_asset[asset_id] == 1:
            raise RuntimeError("temporary TTS failure")
        speaker = "Person1" if voice == "Ethan" else "Person2"
        order = int(asset_id.rsplit("_", 1)[1])
        record = self.storage.save_bytes(
            asset_id=asset_id,
            filename=f"{asset_id}.wav",
            content=_wav_bytes(),
            content_type="audio/wav",
            kind="audio",
            metadata={"text": text},
        )
        return AudioFileElement(
            id=record.asset_id,
            speaker=speaker,
            voice=voice,
            audio_url=record.url,
            order=order,
            title=f"{speaker} audio",
            format="wav",
            byte_size=record.byte_size,
        )


def test_podcast_renderer_creates_audio_segments_and_manifest() -> None:
    spec = PodcastSpec(
        id="podcast_task_123",
        title="Direct workflow podcast",
        podcast_name="未来学习电台",
        podcast_tagline="把复杂问题讲清楚",
        raw_dialogue="<Person1>欢迎来到 未来学习电台 —— 把复杂问题讲清楚。</Person1>\n<Person2>我很期待。</Person2>",
        segments=[
            PodcastSegmentSpec(segment_id="seg-001", order=1, speaker="Person1", voice="Ethan", text="欢迎来到 未来学习电台 —— 把复杂问题讲清楚。"),
            PodcastSegmentSpec(segment_id="seg-002", order=2, speaker="Person2", voice="Cherry", text="我很期待。"),
        ],
    )

    render_model = PodcastRenderer(tts_service=FakeTTSService()).render(spec, [])

    assert render_model.render_type == "podcast_script"
    assert [segment.status for segment in render_model.segments] == ["generated", "generated"]
    assert [segment.voice for segment in render_model.segments] == ["Ethan", "Cherry"]
    assert len(render_model.audio_assets) == 2
    assert render_model.audio_manifest_url


def test_podcast_renderer_sends_plain_text_to_tts() -> None:
    spec = PodcastSpec(
        id="podcast_task_456",
        title="Direct workflow podcast",
        podcast_name="未来学习电台",
        podcast_tagline="把复杂问题讲清楚",
        raw_dialogue="<Person1>欢迎<break time=\"0.2s\"/>回来。</Person1>",
        segments=[
            PodcastSegmentSpec(
                segment_id="seg-001",
                order=1,
                speaker="Person1",
                voice="Ethan",
                text="欢迎回来。",
                ssml_text='欢迎<break time="0.2s"/>回来。',
            ),
        ],
    )
    tts_service = FakeTTSService()

    PodcastRenderer(tts_service=tts_service).render(spec, [])

    assert tts_service.texts == ["欢迎回来。"]


def test_podcast_renderer_retries_failed_segment_and_records_final_audio() -> None:
    storage = LocalStorageService(storage_root=Path("storage") / "test_podcast_renderer" / uuid4().hex)
    tts_service = FlakyTTSService(storage)
    spec = PodcastSpec(
        id="podcast_task_789",
        title="Direct workflow podcast",
        podcast_name="未来学习电台",
        podcast_tagline="把复杂问题讲清楚",
        raw_dialogue="<Person1>欢迎来到 未来学习电台 —— 把复杂问题讲清楚。</Person1>\n<Person2>我很期待。</Person2>",
        segments=[
            PodcastSegmentSpec(segment_id="seg-001", order=1, speaker="Person1", voice="Ethan", text="欢迎来到 未来学习电台 —— 把复杂问题讲清楚。"),
            PodcastSegmentSpec(segment_id="seg-002", order=2, speaker="Person2", voice="Cherry", text="我很期待。"),
        ],
    )

    render_model = PodcastRenderer(
        tts_service=tts_service,
        storage_service=storage,
        segment_max_retries=1,
        retry_delay_seconds=0,
    ).render(spec, [])

    assert tts_service.calls_by_asset["podcast_task_789_001"] == 2
    assert [segment.status for segment in render_model.segments] == ["generated", "generated"]
    assert render_model.segments[0].retry_count == 1
    assert render_model.final_audio_url
    assert any(file.file_type == "audio" and file.url == render_model.final_audio_url for file in render_model.export_files)
    assert storage.read_bytes("podcast_task_789_final_audio").startswith(b"RIFF")


def test_podcast_renderer_waits_before_retrying_failed_segment() -> None:
    storage = LocalStorageService(storage_root=Path("storage") / "test_podcast_renderer" / uuid4().hex)
    waits: list[float] = []

    renderer = PodcastRenderer(
        tts_service=FlakyTTSService(storage),
        storage_service=storage,
        segment_max_retries=1,
        retry_delay_seconds=10.0,
        sleeper=waits.append,
    )

    renderer._synthesize_with_retries(text="欢迎回来。", voice="Ethan", asset_id="podcast_task_999_001")

    assert waits == [10.0]


def _wav_bytes() -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 80)
    return buffer.getvalue()
