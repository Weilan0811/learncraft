from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import Metadata, SchemaModel


class CitationRef(SchemaModel):
    chunk_id: str
    source_id: str | None = None
    title: str | None = None
    url: str | None = None
    note: str | None = None


class WechatOutlineSection(SchemaModel):
    section_id: str
    title: str
    core_question: str
    key_points: list[str] = Field(default_factory=list)
    evidence_refs: list[CitationRef] = Field(default_factory=list)
    suggested_visual: str | None = None


class WechatBriefOutline(SchemaModel):
    content_type: Literal["social_post"] = "social_post"
    platform: Literal["wechat"] = "wechat"
    subtype: Literal["wechat_article"] = "wechat_article"
    topic: str
    article_type: Literal[
        "concept_explanation",
        "engineering_practice",
        "project_story",
        "paper_or_report_review",
        "industry_observation",
        "product_or_tool_analysis",
        "news_analysis",
    ] = "concept_explanation"
    target_audience: str = "AI and software engineering readers"
    writing_angle: str
    core_question: str
    central_thesis: str
    reader_question_chain: list[str] = Field(default_factory=list)
    title_candidates: list[str] = Field(default_factory=list)
    recommended_template: Literal["deep-analysis", "industry-radar", "studio-brief"] = "deep-analysis"
    sections: list[WechatOutlineSection] = Field(min_length=3, max_length=7)
    image_strategy: str = "Cover plus one or two explanatory article images."
    risk_notes: list[str] = Field(default_factory=list)


class WechatMeta(SchemaModel):
    title: str = Field(max_length=32)
    digest: str = Field(max_length=128)
    subtitle: str | None = None
    author: str = "FutureLearning"
    date: str | None = None
    cover_image: dict[str, Any] | None = None
    thumb_media_id: str | None = None
    open_comment: int = 1

    @field_validator("title", "digest")
    @classmethod
    def text_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be empty")
        return value


class WechatImageRef(SchemaModel):
    slot_id: str | None = None
    url: str | None = None
    local_path: str | None = None
    caption: str = "Image"
    prompt: str | None = None


class WechatHeadline(SchemaModel):
    title: str
    body: list[str] = Field(min_length=1)
    source: str | None = None
    image: WechatImageRef | None = None
    citation_refs: list[CitationRef] = Field(default_factory=list)


class ParagraphBlock(SchemaModel):
    type: Literal["paragraph"] = "paragraph"
    text: str | list[str]
    citation_refs: list[CitationRef] = Field(default_factory=list)


class QuoteBlock(SchemaModel):
    type: Literal["quote"] = "quote"
    text: str
    attribution: str | None = None
    citation_refs: list[CitationRef] = Field(default_factory=list)


class TakeawaysBlock(SchemaModel):
    type: Literal["takeaways"] = "takeaways"
    title: str = "Key takeaways"
    items: list[str] = Field(min_length=2, max_length=6)
    citation_refs: list[CitationRef] = Field(default_factory=list)


class CardBlock(SchemaModel):
    type: Literal["card"] = "card"
    number: str | int | None = None
    title: str
    body: str | list[str]
    source: str | None = None
    style: Literal["highlight"] | None = None
    citation_refs: list[CitationRef] = Field(default_factory=list)


class OpinionBlock(SchemaModel):
    type: Literal["opinion"] = "opinion"
    number: str | int | None = None
    title: str
    body: str | list[str]
    source: str | None = None
    citation_refs: list[CitationRef] = Field(default_factory=list)


class ImageBlock(SchemaModel):
    type: Literal["image"] = "image"
    slot_id: str | None = None
    url: str | None = None
    local_path: str | None = None
    caption: str
    prompt: str | None = None


WechatBlock = ParagraphBlock | QuoteBlock | TakeawaysBlock | CardBlock | OpinionBlock | ImageBlock


class WechatSection(SchemaModel):
    section_id: str
    cn: str
    en: str = "SECTION"
    intro: str | None = None
    image: WechatImageRef | None = None
    blocks: list[WechatBlock] = Field(min_length=1)
    citation_refs: list[CitationRef] = Field(default_factory=list)


class WechatArticleDraft(SchemaModel):
    template: Literal["deep-analysis", "industry-radar", "studio-brief"] = "deep-analysis"
    meta: WechatMeta
    headline: WechatHeadline
    sections: list[WechatSection] = Field(min_length=3, max_length=7)
    conclusion: str | None = None
    cta: str | None = None
    estimated_word_count: int = Field(default=1600, ge=800, le=5000)
    writing_notes: list[str] = Field(default_factory=list)


class ImageSlotTarget(str):
    cover = "meta.cover_image"
    headline = "headline.image"
    section = "section.image"
    block = "block.image"


class ImageSlot(SchemaModel):
    slot_id: str
    target: Literal["meta.cover_image", "headline.image", "section.image", "block.image"]
    target_path: str
    required: bool = True
    aspect_ratio: Literal["2.35:1", "16:9", "4:3", "1:1"] = "16:9"
    caption: str
    visual_type: Literal[
        "cover",
        "concept_diagram",
        "workflow_diagram",
        "architecture_diagram",
        "timeline",
        "comparison",
        "editorial_illustration",
        "screenshot_like",
    ] = "concept_diagram"
    purpose: str
    context_summary: str
    prompt_en: str
    negative_prompt_en: str | None = "No cluttered small text, no random logos, no watermark."


class ImageSlotPlan(SchemaModel):
    image_slots: list[ImageSlot] = Field(min_length=1)


class ImageAsset(SchemaModel):
    slot_id: str
    status: Literal["planned", "generated", "uploaded", "failed"] = "planned"
    local_path: str | None = None
    public_url: str | None = None
    wechat_url: str | None = None
    media_id: str | None = None
    width: int | None = None
    height: int | None = None
    error_message: str | None = None


class SocialPostValidationIssue(SchemaModel):
    severity: Literal["error", "warning"]
    path: str
    message: str
    suggestion: str | None = None


class SocialPostValidationReport(SchemaModel):
    ok: bool
    issues: list[SocialPostValidationIssue] = Field(default_factory=list)


class SocialPostSpec(SchemaModel):
    id: str
    type: Literal["social_post"] = "social_post"
    version: str = "content.spec/v1"
    content_type: Literal["social_post"] = "social_post"
    platform: Literal["wechat"] = "wechat"
    subtype: Literal["wechat_article"] = "wechat_article"
    title: str
    metadata: Metadata = Field(default_factory=dict)
    outline: WechatBriefOutline
    draft: WechatArticleDraft
    image_slots: list[ImageSlot] = Field(default_factory=list)
    image_assets: list[ImageAsset] = Field(default_factory=list)
    article_json: dict[str, Any] | None = None
    validation_report: SocialPostValidationReport | None = None
