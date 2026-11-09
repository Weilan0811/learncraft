import json
from pathlib import Path

import pytest

from app.schemas.elements import AudioFileElement
from app.schemas.render.podcast import PodcastAudioSegment, PodcastRenderModel
from app.services.audio_assembler_service import AudioAssemblerService, AudioAssemblyError
from app.services.storage_service import LocalStorageService


def podcast_with_segment(storage: LocalStorageService) -> PodcastRenderModel:
    speech = Path(__file__).parent / "fixtures" / "podcast_speech.wav"
    record = storage.save_bytes(
        asset_id="podcast_segment_001", filename="speech.wav", content=speech.read_bytes(),
        content_type="audio/wav", kind="audio",
    )
    return PodcastRenderModel(
        title="音频恢复验证", podcast_name="音频验证", podcast_tagline="分段合成",
        script_text="", warnings=["final audio assembly failed: 找不到 ffmpeg"],
        segments=[PodcastAudioSegment(
            segment_id="segment_001", order=1, speaker="Person1", voice="Ethan",
            text="语音片段", audio_url=record.url, status="generated",
        )],
        audio_assets=[AudioFileElement(
            id=record.asset_id, title="语音片段", speaker="Person1", voice="Ethan",
            audio_url=record.url, order=1, format="wav",
        )],
    )


def test_recovery_assembles_real_audio_and_updates_manifest(tmp_path):
    storage = LocalStorageService(storage_root=tmp_path)
    model = podcast_with_segment(storage)
    recovered = AudioAssemblerService(output_format="wav").recover_podcast_audio(
        model, spec_id="podcast_recovery", storage_service=storage,
    )
    assert recovered.final_audio_url
    assert recovered.final_audio_duration_seconds == pytest.approx(1, abs=0.05)
    assert recovered.warnings == []
    manifest = json.loads(storage.read_bytes("podcast_recovery_audio_manifest"))
    assert manifest["final_audio_url"] == recovered.final_audio_url
    assert manifest["segments"] == [segment.model_dump(mode="json") for segment in model.segments]
    assert recovered.audio_assets == model.audio_assets
    assert model.final_audio_url is None


def test_recovery_can_repeat_after_correcting_ffmpeg_path(tmp_path):
    storage = LocalStorageService(storage_root=tmp_path)
    model = podcast_with_segment(storage)
    with pytest.raises(AudioAssemblyError, match="找不到 ffmpeg"):
        AudioAssemblerService(ffmpeg_binary=str(tmp_path / "missing_ffmpeg")).recover_podcast_audio(
            model, spec_id="podcast_recovery", storage_service=storage,
        )
    assert storage.get_record("podcast_recovery_final_audio") is None
    recovered = AudioAssemblerService(output_format="wav").recover_podcast_audio(
        model, spec_id="podcast_recovery", storage_service=storage,
    )
    assert recovered.final_audio_url


def test_recovery_requires_all_segments_before_assembling(tmp_path):
    storage = LocalStorageService(storage_root=tmp_path)
    model = podcast_with_segment(storage)
    model.segments[0].status = "failed"
    with pytest.raises(AudioAssemblyError, match="先重试失败的分段"):
        AudioAssemblerService().recover_podcast_audio(
            model, spec_id="podcast_recovery", storage_service=storage,
        )
    assert storage.get_record("podcast_recovery_final_audio") is None
