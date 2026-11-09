from io import BytesIO
from pathlib import Path
import subprocess
import wave

import imageio_ffmpeg

from app.schemas.elements.audio import AudioFileElement
from app.services.audio_assembler_service import AudioAssemblerService
from app.services.storage_service import LocalStorageService


def wav_bytes(duration_seconds: float, sample_rate: int = 16000) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(b"\x00\x00" * int(sample_rate * duration_seconds))
    return buffer.getvalue()


def mp3_bytes(wav_content: bytes, tmp_path: Path) -> bytes:
    wav_path = tmp_path / "source.wav"
    mp3_path = tmp_path / "source.mp3"
    wav_path.write_bytes(wav_content)
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(wav_path),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "96k",
            str(mp3_path),
        ],
        check=True,
        capture_output=True,
    )
    return mp3_path.read_bytes()


def test_assembles_wav_segments_into_single_wav_with_duration(tmp_path) -> None:
    storage = LocalStorageService(storage_root=tmp_path)
    first = storage.save_bytes(
        asset_id="seg_001",
        filename="seg_001.wav",
        content=wav_bytes(0.4, 16000),
        content_type="audio/wav",
        kind="audio",
    )
    second = storage.save_bytes(
        asset_id="seg_002",
        filename="seg_002.wav",
        content=wav_bytes(0.6, 24000),
        content_type="audio/wav",
        kind="audio",
    )
    assets = [
        AudioFileElement(
            id=first.asset_id,
            title="first",
            speaker="Person1",
            voice="Ethan",
            audio_url=first.url,
            format="wav",
            order=1,
        ),
        AudioFileElement(
            id=second.asset_id,
            title="second",
            speaker="Person2",
            voice="Cherry",
            audio_url=second.url,
            format="wav",
            order=2,
        ),
    ]

    record = AudioAssemblerService(output_format="wav").assemble(
        asset_id="podcast_final",
        title="测试播客",
        audio_assets=assets,
        storage_service=storage,
    )

    assert record is not None
    content = storage.read_bytes("podcast_final")
    assert content.startswith(b"RIFF")
    assert record.metadata["assembly_mode"] == "ffmpeg_concat"
    assert record.metadata["output_format"] == "wav"
    assert record.metadata["source_asset_ids"] == ["seg_001", "seg_002"]
    duration = record.metadata["duration_seconds"]
    assert isinstance(duration, float)
    assert 0.9 <= duration <= 1.1
    with wave.open(BytesIO(content), "rb") as audio:
        measured = audio.getnframes() / audio.getframerate()
    assert abs(measured - duration) < 0.05


def test_assembles_mixed_wav_and_mp3_segments_into_mp3(tmp_path) -> None:
    storage = LocalStorageService(storage_root=tmp_path)
    wav_record = storage.save_bytes(
        asset_id="seg_wav",
        filename="seg_wav.wav",
        content=wav_bytes(0.5, 16000),
        content_type="audio/wav",
        kind="audio",
    )
    mp3_record = storage.save_bytes(
        asset_id="seg_mp3",
        filename="seg_mp3.mp3",
        content=mp3_bytes(wav_bytes(0.5, 16000), tmp_path),
        content_type="audio/mpeg",
        kind="audio",
    )
    assets = [
        AudioFileElement(
            id=wav_record.asset_id,
            title="wav",
            speaker="Person1",
            voice="Ethan",
            audio_url=wav_record.url,
            format="wav",
            order=1,
        ),
        AudioFileElement(
            id=mp3_record.asset_id,
            title="mp3",
            speaker="Person2",
            voice="Cherry",
            audio_url=mp3_record.url,
            format="mp3",
            order=2,
        ),
    ]

    record = AudioAssemblerService(output_format="mp3").assemble(
        asset_id="podcast_mixed",
        title="混合格式",
        audio_assets=assets,
        storage_service=storage,
    )

    assert record is not None
    content = storage.read_bytes("podcast_mixed")
    assert content.startswith(b"ID3") or content[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"}
    assert record.metadata["output_format"] == "mp3"
    duration = record.metadata["duration_seconds"]
    assert isinstance(duration, float)
    assert 0.9 <= duration <= 1.2


def test_assembly_requires_readable_segments(tmp_path) -> None:
    storage = LocalStorageService(storage_root=tmp_path)
    record = storage.save_bytes(
        asset_id="not_audio",
        filename="not_audio.mp3",
        content=b"stub text that is not audio",
        content_type="audio/mpeg",
        kind="audio",
    )
    asset = AudioFileElement(
        id=record.asset_id,
        title="broken",
        speaker="Person1",
        voice="Ethan",
        audio_url=record.url,
        format="mp3",
        order=1,
    )

    try:
        AudioAssemblerService().assemble(
            asset_id="podcast_broken",
            title="broken",
            audio_assets=[asset],
            storage_service=storage,
        )
    except Exception as exc:
        assert "ffmpeg" in str(exc)
    else:
        raise AssertionError("invalid audio bytes must fail assembly")
