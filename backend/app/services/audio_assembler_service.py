import re
import subprocess
import tempfile
import wave
from pathlib import Path

from app.core.config import get_settings
from app.schemas.assets import AssetRecord
from app.schemas.elements.audio import AudioFileElement
from app.services.storage_service import StorageService


class AudioAssemblyError(RuntimeError):
    """Raised when final podcast audio cannot be assembled."""


class AudioAssemblerService:
    """Concatenate podcast segments with ffmpeg.

    The ffmpeg executable comes from ``imageio-ffmpeg`` (bundled with the
    dependency) unless ``CONTENT_GENERATOR_FFMPEG_BINARY`` points at a system
    installation. Segments are decoded and re-encoded into one clean stream so
    per-segment MP3/WAV headers, VBR tags and mixed sample rates cannot corrupt
    playback or the reported duration.
    """

    def __init__(
        self,
        ffmpeg_binary: str | None = None,
        timeout_seconds: float = 300.0,
        output_format: str | None = None,
    ) -> None:
        self.ffmpeg_binary = ffmpeg_binary
        self.timeout_seconds = timeout_seconds
        self.output_format = output_format

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

        output_format = _normalize_output_format(self.output_format or get_settings().tts_output_format)
        ffmpeg = self._ffmpeg_executable()
        with tempfile.TemporaryDirectory(prefix="podcast_assembly_") as temp_dir:
            temp_path = Path(temp_dir)
            input_paths: list[Path] = []
            for index, asset in enumerate(ordered_assets, start=1):
                suffix = (asset.format or output_format).lstrip(".")
                path = temp_path / f"{index:03d}.{suffix}"
                path.write_bytes(storage_service.read_bytes(asset.id))
                input_paths.append(path)
            output_path = temp_path / f"final_audio.{output_format}"

            command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
            for path in input_paths:
                command.extend(["-i", str(path)])
            filter_inputs = "".join(f"[{index}:a]" for index in range(len(input_paths)))
            command.extend(
                [
                    "-filter_complex",
                    f"{filter_inputs}concat=n={len(input_paths)}:v=0:a=1[out]",
                    "-map",
                    "[out]",
                    "-ar",
                    "24000",
                    "-ac",
                    "1",
                ]
            )
            if output_format == "wav":
                command.extend(["-c:a", "pcm_s16le"])
            else:
                command.extend(["-c:a", "libmp3lame", "-b:a", "96k"])
            command.append(str(output_path))
            self._run(command)

            content = output_path.read_bytes()
            if not content:
                raise AudioAssemblyError("ffmpeg produced an empty audio file.")
            duration = _probe_duration(output_path, output_format, ffmpeg)

        return storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{asset_id}.{output_format}",
            content=content,
            content_type=_content_type(output_format),
            kind="audio",
            metadata={
                "content_type": "podcast_script",
                "render_type": "final_audio",
                "title": title,
                "assembly_mode": "ffmpeg_concat",
                "output_format": output_format,
                "duration_seconds": duration,
                "segment_count": len(ordered_assets),
                "source_asset_ids": [asset.id for asset in ordered_assets],
            },
        )

    def _ffmpeg_executable(self) -> str:
        configured = self.ffmpeg_binary or get_settings().ffmpeg_binary
        if configured:
            return configured
        try:
            import imageio_ffmpeg

            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception as exc:
            raise AudioAssemblyError(
                "找不到 ffmpeg。请安装 imageio-ffmpeg，或通过 CONTENT_GENERATOR_FFMPEG_BINARY 指定 ffmpeg 路径。"
            ) from exc

    def _run(self, command: list[str]) -> None:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise AudioAssemblyError(f"找不到 ffmpeg 可执行文件：{command[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise AudioAssemblyError(f"ffmpeg 音频合成超时（{self.timeout_seconds:.0f} 秒）。") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            if len(detail) > 600:
                detail = detail[-600:]
            raise AudioAssemblyError(f"ffmpeg 音频合成失败：{detail or '未知错误'}")


def _normalize_output_format(value: str) -> str:
    return "wav" if str(value).strip().lower() == "wav" else "mp3"


def _content_type(output_format: str) -> str:
    return "audio/wav" if output_format == "wav" else "audio/mpeg"


_DURATION_PATTERN = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def _probe_duration(path: Path, output_format: str, ffmpeg: str) -> float | None:
    if output_format == "wav":
        try:
            with wave.open(str(path), "rb") as audio:
                frame_rate = audio.getframerate()
                if frame_rate:
                    return round(audio.getnframes() / frame_rate, 3)
        except (wave.Error, OSError):
            return None
    try:
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-i", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = _DURATION_PATTERN.search(result.stderr or "")
    if match is None:
        return None
    hours, minutes, seconds = match.groups()
    return round(int(hours) * 3600 + int(minutes) * 60 + float(seconds), 3)


__all__ = ["AudioAssemblerService", "AudioAssemblyError"]
