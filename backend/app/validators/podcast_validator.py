import re

from app.schemas.render.podcast import PodcastRenderModel
from app.schemas.specs.podcast import PodcastSpec, PodcastValidationIssue, PodcastValidationReport


SPEAKER_TAG_RE = re.compile(r"<(/?)([A-Za-z0-9_:-]+)(?:\s[^>]*)?>")
TURN_RE = re.compile(r"<(Person1|Person2)>(.*?)</\1>", re.DOTALL)
FORBIDDEN_TTS_TAGS = {"emphasis", "say-as", "amazon:emotion", "amazon:domain", "amazon:effect", "alexa:emotion"}
ALLOWED_TTS_TAGS = {"Person1", "Person2", "break", "prosody"}
CHALLENGE_HINTS = ("补充", "追问", "保留", "不同看法", "质疑", "提醒", "稍微")


class PodcastValidator:
    def validate_pre_render(self, spec: PodcastSpec) -> PodcastValidationReport:
        issues: list[PodcastValidationIssue] = []
        if spec.content_type != "podcast_script":
            issues.append(_error("content_type", "content_type must be podcast_script."))
        if not spec.raw_dialogue.strip():
            issues.append(_error("raw_dialogue", "raw_dialogue cannot be empty."))

        xml_like_tags = [tag for _, tag in SPEAKER_TAG_RE.findall(spec.raw_dialogue)]
        speaker_tags = [tag for tag in xml_like_tags if tag.startswith("Person") or tag in {"Host", "Speaker", "主持人", "嘉宾"}]
        if any(tag not in {"Person1", "Person2"} for tag in speaker_tags):
            issues.append(_error("raw_dialogue", "Only Person1 and Person2 speaker tags are allowed."))

        for tag in xml_like_tags:
            tag_name = tag.lower()
            if tag_name in FORBIDDEN_TTS_TAGS:
                issues.append(_error("raw_dialogue", f"Forbidden TTS tag: {tag}."))
            elif tag not in ALLOWED_TTS_TAGS and tag_name not in FORBIDDEN_TTS_TAGS:
                issues.append(_error("raw_dialogue", f"Unsupported TTS tag: {tag}."))

        turns = TURN_RE.findall(spec.raw_dialogue)
        if turns:
            first_speaker, first_text = turns[0]
            if first_speaker != "Person1" or not _has_opening_phrase(
                _plain_text(first_text),
                podcast_name=spec.podcast_name,
                podcast_tagline=spec.podcast_tagline,
            ):
                issues.append(_error("raw_dialogue", "Podcast opening phrase is required in the first Person1 turn."))
        else:
            issues.append(_error("raw_dialogue", "At least one Person1 or Person2 turn is required."))

        speakers = {speaker for speaker, _ in turns}
        if speakers != {"Person1", "Person2"}:
            issues.append(_error("raw_dialogue", "Both Person1 and Person2 must speak."))
        if len(turns) < 6:
            issues.append(_error("raw_dialogue", "Podcast dialogue must contain at least 6 turns."))
        if not any(hint in text for _, text in turns for hint in CHALLENGE_HINTS):
            issues.append(_error("raw_dialogue", "Podcast dialogue must include at least one respectful challenge, follow-up, or reservation."))

        for segment in spec.segments:
            expected_voice = "Ethan" if segment.speaker == "Person1" else "Cherry"
            if segment.voice != expected_voice:
                issues.append(_error(f"segments[{segment.order}].voice", f"{segment.speaker} must use voice {expected_voice}."))
            if len(segment.text) > 500:
                issues.append(_warning(f"segments[{segment.order}].text", "Segment text is long for TTS playback."))

        return PodcastValidationReport(ok=not any(issue.severity == "error" for issue in issues), issues=issues)

    def validate_final_render(self, render_model: PodcastRenderModel) -> PodcastValidationReport:
        issues: list[PodcastValidationIssue] = []
        if not render_model.script_text.strip():
            issues.append(_error("script_text", "script_text cannot be empty."))
        if not render_model.segments:
            issues.append(_error("segments", "render model must include audio segments."))
        for segment in render_model.segments:
            if segment.status != "generated" or not segment.audio_url:
                issues.append(_error(f"segments[{segment.order}]", f"Audio segment {segment.segment_id} was not generated."))
            expected_voice = "Ethan" if segment.speaker == "Person1" else "Cherry"
            if segment.voice != expected_voice:
                issues.append(_error(f"segments[{segment.order}].voice", f"{segment.speaker} must use voice {expected_voice}."))
        if not render_model.audio_manifest_url:
            issues.append(_error("audio_manifest_url", "audio manifest is required."))
        if not render_model.final_audio_url:
            issues.append(_error("final_audio_url", "final audio is required."))
        return PodcastValidationReport(ok=not any(issue.severity == "error" for issue in issues), issues=issues)


def _plain_text(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def _has_opening_phrase(value: str, *, podcast_name: str, podcast_tagline: str) -> bool:
    return _normalize_opening_text(value).startswith(_normalize_opening_text(f"欢迎来到{podcast_name}{podcast_tagline}"))


def _normalize_opening_text(value: str) -> str:
    return re.sub(r"[\s，,。.!！？?；;：:、—-]+", "", value)


def _error(path: str, message: str) -> PodcastValidationIssue:
    return PodcastValidationIssue(severity="error", path=path, message=message)


def _warning(path: str, message: str) -> PodcastValidationIssue:
    return PodcastValidationIssue(severity="warning", path=path, message=message)
