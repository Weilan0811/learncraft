import wave
from io import BytesIO

from app.schemas.assets import AssetRecord
from app.schemas.elements.audio import AudioFileElement
from app.services.storage_service import StorageService


class AudioAssemblyError(RuntimeError):
    """Raised when final podcast audio cannot be assembled."""


class AudioAssemblerService:
    def assemble(
        self,
        *,
        asset_id: str,
        title: str,
        audio_assets: list[AudioFileElement],
        storage_service: StorageService,
    ) -> AssetRecord | None:
        ordered_assets = sorted(audio_assets, key=lambda asset: asset.order)
        if not ordered_assets:
            return None

        if all(asset.format == "wav" for asset in ordered_assets):
            content = self._assemble_wav(ordered_assets, storage_service)
            output_format = "wav"
            content_type = "audio/wav"
            assembly_mode = "wav_concat"
        else:
            content = b"".join(storage_service.read_bytes(asset.id) for asset in ordered_assets)
            output_format = ordered_assets[0].format or "mp3"
            content_type = _content_type(output_format)
            assembly_mode = "byte_concat"

        return storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{asset_id}.{output_format}",
            content=content,
            content_type=content_type,
            kind="audio",
            metadata={
                "content_type": "podcast_script",
                "render_type": "final_audio",
                "title": title,
                "assembly_mode": assembly_mode,
                "source_asset_ids": [asset.id for asset in ordered_assets],
            },
        )

    def _assemble_wav(self, audio_assets: list[AudioFileElement], storage_service: StorageService) -> bytes:
        params = None
        frames: list[bytes] = []
        for asset in audio_assets:
            with wave.open(BytesIO(storage_service.read_bytes(asset.id)), "rb") as audio:
                current_params = audio.getparams()
                comparable_params = current_params[:3]
                if params is None:
                    params = current_params
                    expected_comparable = comparable_params
                elif comparable_params != expected_comparable:
                    raise AudioAssemblyError("WAV segments must have matching channels, sample width, and frame rate.")
                frames.append(audio.readframes(audio.getnframes()))
        if params is None:
            raise AudioAssemblyError("No WAV segments to assemble.")

        output = BytesIO()
        with wave.open(output, "wb") as combined:
            combined.setparams(params)
            combined.writeframes(b"".join(frames))
        return output.getvalue()


def _content_type(output_format: str) -> str:
    if output_format == "wav":
        return "audio/wav"
    return "audio/mpeg"
