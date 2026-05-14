from typing import Literal

from app.schemas.elements.common import BaseElement


class AudioScriptElement(BaseElement):
    type: Literal["audio_script"] = "audio_script"
    speaker: Literal["Person1", "Person2"]
    voice: Literal["Ethan", "Cherry"]
    text: str
    ssml_text: str | None = None
    order: int


class AudioFileElement(BaseElement):
    type: Literal["audio_file"] = "audio_file"
    speaker: Literal["Person1", "Person2"]
    voice: Literal["Ethan", "Cherry"]
    audio_url: str
    format: str = "mp3"
    duration_seconds: float | None = None
    byte_size: int | None = None
    order: int
