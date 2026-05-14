import json
import time
from collections.abc import Callable

from app.core.config import get_settings
from app.schemas.elements import ContentElement
from app.schemas.elements.audio import AudioFileElement
from app.schemas.render.podcast import PodcastAudioSegment, PodcastExportFile, PodcastRenderModel
from app.schemas.specs import PodcastSpec
from app.services.audio_assembler_service import AudioAssemblerService
from app.services.storage_service import LocalStorageService, StorageService
from app.services.tts_service import TTSService, get_tts_service


class PodcastRenderer:
    def __init__(
        self,
        tts_service: TTSService | None = None,
        storage_service: StorageService | None = None,
        audio_assembler: AudioAssemblerService | None = None,
        segment_max_retries: int | None = None,
        retry_delay_seconds: float | None = None,
        sleeper: Callable[[float], object] | None = None,
    ) -> None:
        settings = get_settings()
        self.tts_service = tts_service or get_tts_service()
        self.storage_service = storage_service or LocalStorageService()
        self.audio_assembler = audio_assembler or AudioAssemblerService()
        self.segment_max_retries = settings.podcast_segment_max_retries if segment_max_retries is None else segment_max_retries
        self.retry_delay_seconds = settings.podcast_segment_retry_delay_seconds if retry_delay_seconds is None else retry_delay_seconds
        self.sleeper = sleeper or time.sleep

    def render(self, spec: PodcastSpec, elements: list[ContentElement]) -> PodcastRenderModel:
        audio_segments: list[PodcastAudioSegment] = []
        audio_assets: list[AudioFileElement] = []
        warnings: list[str] = []

        for segment in spec.segments:
            asset_id = f"{spec.id}_{segment.order:03d}"
            retry_count = 0
            try:
                audio = self._synthesize_with_retries(text=segment.text, voice=segment.voice, asset_id=asset_id)
                retry_count = int(audio.metadata.get("retry_count", 0)) if audio.metadata else 0
                audio_assets.append(audio)
                audio_segments.append(
                    PodcastAudioSegment(
                        segment_id=segment.segment_id,
                        order=segment.order,
                        speaker=segment.speaker,
                        voice=segment.voice,
                        text=segment.text,
                        audio_url=audio.audio_url,
                        status="generated",
                        retry_count=retry_count,
                    )
                )
            except Exception as exc:
                audio_segments.append(
                    PodcastAudioSegment(
                        segment_id=segment.segment_id,
                        order=segment.order,
                        speaker=segment.speaker,
                        voice=segment.voice,
                        text=segment.text,
                        status="failed",
                        error_message=str(exc),
                        retry_count=self.segment_max_retries,
                    )
                )
                warnings.append(f"{segment.segment_id} TTS failed: {exc}")

        final_audio_url: str | None = None
        export_files: list[PodcastExportFile] = []
        if audio_segments and all(segment.status == "generated" for segment in audio_segments):
            try:
                final_record = self.audio_assembler.assemble(
                    asset_id=f"{spec.id}_final_audio",
                    title=spec.title,
                    audio_assets=audio_assets,
                    storage_service=self.storage_service,
                )
                if final_record is not None:
                    final_audio_url = final_record.url
                    export_files.append(PodcastExportFile(file_type="audio", url=final_record.url, label="Full audio"))
            except Exception as exc:
                warnings.append(f"final audio assembly failed: {exc}")

        manifest_record = self.storage_service.save_bytes(
            asset_id=f"{spec.id}_audio_manifest",
            filename=f"{spec.id}_audio_manifest.json",
            content=json.dumps(
                {
                    "title": spec.title,
                    "podcast_name": spec.podcast_name,
                    "podcast_tagline": spec.podcast_tagline,
                    "final_audio_url": final_audio_url,
                    "segments": [segment.model_dump(mode="json") for segment in audio_segments],
                },
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8"),
            content_type="application/json",
            kind="audio",
            metadata={"content_type": "podcast_script", "render_type": "audio_manifest"},
        )
        return PodcastRenderModel(
            title=spec.title,
            podcast_name=spec.podcast_name,
            podcast_tagline=spec.podcast_tagline,
            script_text=spec.raw_dialogue,
            segments=audio_segments,
            audio_assets=audio_assets,
            audio_manifest_url=manifest_record.url,
            final_audio_url=final_audio_url,
            export_files=[*export_files, PodcastExportFile(file_type="manifest", url=manifest_record.url, label="Audio manifest")],
            warnings=warnings,
        )

    def _synthesize_with_retries(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        last_error: Exception | None = None
        for attempt in range(self.segment_max_retries + 1):
            try:
                audio = self.tts_service.synthesize(text=text, voice=voice, asset_id=asset_id)
                metadata = dict(audio.metadata)
                metadata["retry_count"] = attempt
                return audio.model_copy(update={"metadata": metadata})
            except Exception as exc:
                last_error = exc
                if attempt >= self.segment_max_retries:
                    break
                if self.retry_delay_seconds > 0:
                    self.sleeper(self.retry_delay_seconds)
        raise last_error or RuntimeError("TTS synthesis failed.")
