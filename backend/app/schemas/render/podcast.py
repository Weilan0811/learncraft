from typing import Literal

from pydantic import Field

from app.schemas.base import SchemaModel
from app.schemas.elements.audio import AudioFileElement


class PodcastAudioSegment(SchemaModel):
    segment_id: str
    order: int
    speaker: Literal["Person1", "Person2"]
    voice: Literal["Ethan", "Cherry"]
    text: str
    audio_url: str | None = None
    status: Literal["pending", "generated", "failed"] = "pending"
    error_message: str | None = None
    retry_count: int = 0


class PodcastExportFile(SchemaModel):
    file_type: Literal["script", "manifest", "audio", "zip"]
    path: str | None = None
    url: str | None = None
    label: str | None = None


class PodcastRenderModel(SchemaModel):
    render_type: Literal["podcast_script"] = "podcast_script"
    content_type: Literal["podcast_script"] = "podcast_script"
    title: str
    podcast_name: str
    podcast_tagline: str
    script_text: str
    segments: list[PodcastAudioSegment] = Field(default_factory=list)
    audio_assets: list[AudioFileElement] = Field(default_factory=list)
    audio_manifest_url: str | None = None
    final_audio_url: str | None = None
    export_files: list[PodcastExportFile] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
