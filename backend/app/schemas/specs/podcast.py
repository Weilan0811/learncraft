from typing import Literal

from pydantic import Field

from app.schemas.base import SchemaModel, VersionedSchema


class PodcastVoiceConfig(SchemaModel):
    person1_voice: Literal["Ethan"] = "Ethan"
    person2_voice: Literal["Cherry"] = "Cherry"
    model: str = "qwen3-tts-instruct-flash"


class PodcastSegmentSpec(SchemaModel):
    segment_id: str
    order: int
    speaker: Literal["Person1", "Person2"]
    voice: Literal["Ethan", "Cherry"]
    text: str = Field(min_length=1)
    ssml_text: str | None = None
    citation_refs: list[str] = Field(default_factory=list)


class PodcastValidationIssue(SchemaModel):
    severity: Literal["error", "warning"]
    path: str
    message: str
    suggestion: str | None = None


class PodcastValidationReport(SchemaModel):
    ok: bool
    issues: list[PodcastValidationIssue] = Field(default_factory=list)


class PodcastDialogueDraft(SchemaModel):
    title: str
    podcast_name: str
    podcast_tagline: str
    output_language: str = "zh-CN"
    raw_dialogue: str


class PodcastSpec(VersionedSchema):
    id: str
    version: str = "content.spec/v1"
    type: Literal["podcast_script"] = "podcast_script"
    content_type: Literal["podcast_script"] = "podcast_script"
    title: str
    podcast_name: str
    podcast_tagline: str
    output_language: str = "zh-CN"
    roles_person1: str = "引导型主持人，负责推进结构、总结节点、照顾听众"
    roles_person2: str = "分析型搭档，负责提出洞察、追问、补充或温和挑战"
    conversation_style: str = "自然、专业、有节奏感的中文双人播客"
    dialogue_structure: str = "开场、主题展开、观点追问、关键 takeaway、自然结尾"
    engagement_techniques: list[str] = Field(default_factory=lambda: ["追问", "复述", "类比", "温和质疑", "阶段性总结"])
    voice_config: PodcastVoiceConfig = Field(default_factory=PodcastVoiceConfig)
    raw_dialogue: str
    segments: list[PodcastSegmentSpec] = Field(default_factory=list)
    validation_report: PodcastValidationReport | None = None
