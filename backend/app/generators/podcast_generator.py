import json
import os
import re
from html import escape, unescape
from typing import cast

from app.core.config import get_settings
from app.schemas.specs import PodcastDialogueDraft, PodcastSegmentSpec, PodcastSpec
from app.schemas.state import ContentGenerationState
from app.services.llm_service import get_llm_service


TURN_RE = re.compile(r"<\s*(Person1|Person2)\s*>(.*?)<\s*/\s*\1\s*>", re.DOTALL)
PLAIN_TURN_RE = re.compile(r"^\s*(Person1|Person2)\s*[:：]\s*(.+?)\s*$")


class PodcastGenerationError(RuntimeError):
    def __init__(self, stage: str, original: Exception) -> None:
        super().__init__(f"{stage} failed: {original}")
        self.stage = stage
        self.original = original


class PodcastGenerator:
    def generate(self, state: ContentGenerationState) -> PodcastSpec:
        settings = get_settings()
        if settings.provider_mode != "stub":
            try:
                spec = self._generate_with_llm(state)
            except Exception as exc:
                if not bool((state.normalized_request or {}).get("allow_fallback", False)):
                    raise
                spec = self._generate_fallback(state).model_copy(
                    update={"metadata": {"generation_mode": "fallback", "fallback_reason": str(exc)}}
                )
        else:
            spec = self._generate_fallback(state).model_copy(update={"metadata": {"generation_mode": "stub_fallback"}})
        return spec

    def _generate_with_llm(self, state: ContentGenerationState) -> PodcastSpec:
        llm_service = get_llm_service()
        try:
            draft = cast(PodcastDialogueDraft, llm_service.generate_structured(self._prompt(state), PodcastDialogueDraft))
        except Exception as exc:
            raise PodcastGenerationError("podcast_script_generation", exc) from exc
        try:
            raw_dialogue = normalize_dialogue(draft.raw_dialogue)
            raw_dialogue = ensure_opening_phrase(raw_dialogue, podcast_name=draft.podcast_name, podcast_tagline=draft.podcast_tagline)
            segments = parse_dialogue_segments(raw_dialogue)
        except Exception as exc:
            raise PodcastGenerationError("podcast_dialogue_parse", exc) from exc
        return PodcastSpec(
            id=f"podcast_{state.request_id}",
            title=draft.title,
            podcast_name=draft.podcast_name,
            podcast_tagline=draft.podcast_tagline,
            output_language=draft.output_language,
            raw_dialogue=raw_dialogue,
            segments=segments,
            metadata={"language": draft.output_language, "generation_mode": "llm"},
        )

    def _generate_fallback(self, state: ContentGenerationState) -> PodcastSpec:
        topic = state.topic.strip() or "播客话题"
        podcast_name = str((state.normalized_request or {}).get("podcast_name") or "未来学习电台")
        podcast_tagline = str((state.normalized_request or {}).get("podcast_tagline") or "把复杂问题讲清楚")
        output_language = str((state.normalized_request or {}).get("language") or "zh-CN")
        dialogue = "\n".join(
            [
                f"<Person1>欢迎来到 {podcast_name} —— {podcast_tagline}。今天我们来聊一聊{topic}。</Person1>",
                "<Person2>我很期待这个话题。这里面最值得注意的一点是，它适合用一个完整的对话来讲清楚。</Person2>",
                "<Person1>对，从内容生成工作流来看，播客不像讲义或幻灯片那样天然分成很多教学单元。</Person1>",
                "<Person2>我想稍微补充一点，如果输入内容很多，脚本仍然要保持取舍，不能把所有材料都塞进去。</Person2>",
                "<Person1>这个提醒很重要。更稳的做法是先生成完整脚本，再把 Person1 和 Person2 的轮次拆出来做 TTS。</Person1>",
                "<Person2>这样 Person1 可以负责推进结构，Person2 负责分析、追问和补充，听感会更自然。</Person2>",
                f"<Person1>所以这期的 takeaway 是：围绕{topic}，direct workflow 能保留播客的整体节奏，也方便后续生成音频。感谢收听，我们下期再见。</Person1>",
            ]
        )
        return PodcastSpec(
            id=f"podcast_{state.request_id}",
            title=f"{topic}播客",
            podcast_name=podcast_name,
            podcast_tagline=podcast_tagline,
            output_language=output_language,
            raw_dialogue=dialogue,
            segments=parse_dialogue_segments(dialogue),
        )

    @staticmethod
    def _prompt(state: ContentGenerationState) -> str:
        path = os.path.join(os.path.dirname(__file__), "..", "prompts", "generator", "podcast_script.md")
        template = open(path, "r", encoding="utf-8").read()
        chunks = state.planning_chunks or state.retrieved_chunks
        input_texts = "\n\n".join([state.user_prompt, *[chunk.content for chunk in chunks]])
        data = {
            "user_request": json.dumps(state.raw_request or {}, ensure_ascii=False, indent=2),
            "generation_options": json.dumps(state.normalized_request or {}, ensure_ascii=False, indent=2),
            "retrieved_chunks": json.dumps([chunk.model_dump(mode="json") for chunk in chunks], ensure_ascii=False, indent=2),
            "podcast_name": "未来学习电台",
            "podcast_tagline": "把复杂问题讲清楚",
            "output_language": (state.normalized_request or {}).get("language", "zh-CN"),
            "roles_person1": "引导型主持人，负责推进结构、总结节点、照顾听众",
            "roles_person2": "分析型搭档，负责提出洞察、追问、补充或温和挑战",
            "conversation_style": (state.normalized_request or {}).get("style", "自然、专业、有节奏感的中文双人播客"),
            "dialogue_structure": "开场、主题展开、观点追问、关键 takeaway、自然结尾",
            "engagement_techniques": "追问、复述、类比、温和质疑、阶段性总结",
            "input_texts": input_texts,
        }
        return template.format(**data)


def parse_dialogue_segments(raw_dialogue: str) -> list[PodcastSegmentSpec]:
    segments: list[PodcastSegmentSpec] = []
    normalized = normalize_dialogue(raw_dialogue)
    for index, (speaker, body) in enumerate(TURN_RE.findall(normalized), 1):
        voice = "Ethan" if speaker == "Person1" else "Cherry"
        text = re.sub(r"<[^>]+>", "", body).strip()
        segments.append(
            PodcastSegmentSpec(
                segment_id=f"seg-{index:03d}",
                order=index,
                speaker=speaker,  # type: ignore[arg-type]
                voice=voice,  # type: ignore[arg-type]
                text=text,
                ssml_text=body.strip(),
            )
        )
    if not segments:
        raise ValueError("No Person1/Person2 dialogue turns found.")
    return segments


def normalize_dialogue(raw_dialogue: str) -> str:
    value = unescape(raw_dialogue).strip()
    if TURN_RE.search(value):
        turns = [
            f"<{speaker}>{body.strip()}</{speaker}>"
            for speaker, body in TURN_RE.findall(value)
        ]
        return "\n".join(turns)

    turns: list[str] = []
    for line in value.splitlines():
        match = PLAIN_TURN_RE.match(line)
        if not match:
            continue
        speaker, text = match.groups()
        turns.append(f"<{speaker}>{escape(text.strip(), quote=False)}</{speaker}>")
    if turns:
        return "\n".join(turns)
    return value


def ensure_opening_phrase(raw_dialogue: str, *, podcast_name: str, podcast_tagline: str) -> str:
    normalized = normalize_dialogue(raw_dialogue)
    turns = TURN_RE.findall(normalized)
    if not turns or turns[0][0] != "Person1":
        return normalized

    first_body = turns[0][1].strip()
    canonical = f"欢迎来到 {podcast_name} —— {podcast_tagline}。"
    if first_body.startswith(canonical):
        return normalized

    end_index = _opening_variant_end(first_body, podcast_name=podcast_name, podcast_tagline=podcast_tagline)
    if end_index is None:
        return normalized

    repaired_body = canonical + first_body[end_index:].lstrip()
    return TURN_RE.sub(lambda match: f"<Person1>{repaired_body}</Person1>", normalized, count=1)


def _opening_variant_end(value: str, *, podcast_name: str, podcast_tagline: str) -> int | None:
    target = f"欢迎来到{podcast_name}{podcast_tagline}"
    matched = 0
    last_index = 0
    for index, char in enumerate(value):
        if char in {" ", "\t", "\n", "\r", "，", ",", "。", ".", "！", "!", "？", "?", "；", ";", "：", ":", "、", "—", "-"}:
            continue
        if matched >= len(target) or char != target[matched]:
            return None
        matched += 1
        last_index = index + 1
        if matched == len(target):
            break
    if matched != len(target):
        return None
    while last_index < len(value) and value[last_index] in {" ", "\t", "\n", "\r", "，", ",", "。", ".", "！", "!", "？", "?", "；", ";", "：", ":", "、", "—", "-"}:
        last_index += 1
    return last_index
