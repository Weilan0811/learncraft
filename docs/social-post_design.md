依据当前 `done.md`，第四阶段本来就计划新增 `SocialPostSpec / SocialPostRenderModel / SocialPostProfile / SocialPostGenerator / SocialPostValidator / SocialPostRenderer`，并走 direct path workflow；现阶段把 `social_post` 固定为 `wechat` 子类型，刚好适合作为 direct workflow 的第一条验证链路。
`wechat-claw-skill` 本身提供结构化 JSON 到公众号 HTML 的渲染、校验、配图规划、草稿创建和发布链路，并提供 `render_article.py`、`validate_article.py`、`plan_images.py`、`run_pipeline.py` 等核心脚本，所以你们后端只需要把内部 schema 稳定映射到它的 article JSON 即可。(skill见backend/skills/wechat-claw-skill)

---

# 一、推荐最终流程

```text
用户请求
  ↓
normalize_request
  ↓
retrieve_for_planning
  ↓
generate_wechat_brief_outline
  ↓
generate_wechat_article_draft
  ↓
plan_wechat_image_slots
  ↓
pre_validate_social_post
  ↓
generate_image_assets
  ↓
bind_image_assets_to_article
  ↓
validate_social_post
  ↓
render_social_post_html
  ↓
finalize
  ↓
HTML preview / export
```

`pre-validator` 检查的是文章结构、标题长度、摘要长度、章节数量、配图槽位数量、chunk 引用覆盖率；`final-validator` 再检查图片资产是否回填、HTML 是否能渲染、是否仍有未解析占位符、导出文件是否完整。

---

# 二、模块与文件建议

```text
backend/app/content_types/
├── social_post.py

backend/app/schemas/specs/
├── social_post.py

backend/app/schemas/render/
├── social_post.py

backend/app/generators/
├── social_post_generator.py

backend/app/validators/
├── social_post_validator.py

backend/app/renderers/
├── social_post_renderer.py

backend/app/services/
├── wechat_claw_renderer.py
├── social_image_service.py

backend/app/workflows/nodes/
├── social_post_outline_node.py
├── social_post_draft_node.py
├── social_post_image_plan_node.py
├── social_post_prevalidate_node.py
├── social_post_image_node.py
├── social_post_bind_assets_node.py
├── social_post_validate_node.py
├── social_post_render_node.py

backend/app/prompts/social_post/wechat/
├── outline.md
├── draft.md
├── image_slots.md
├── repair.md
```

`wechat-claw` 支持的模板包括 `daily-intelligence`、`weekly-financial`、`deep-analysis`、`industry-radar`、`product-release`、`breaking-watch`、`studio-brief`、`neo-brutalism`；对你们的知识技术型推文，MVP 建议只开放 `deep-analysis`、`industry-radar`、`studio-brief` 三种，降低模板不匹配概率。

---

# 三、核心 schema 设计

建议内部 schema 分成四层：

```text
WechatBriefOutline
WechatArticleDraft
ImageSlot / ImageAsset
SocialPostSpec
SocialPostRenderModel
```

其中 `WechatArticleDraft` 尽量贴近 `wechat-claw` 的 article JSON，减少渲染适配成本。`wechat-claw` 的最小 article JSON 包含 `template`、`meta`、`headline`、`sections`，正文 block 支持 `card`、`opinion`、`week-ahead`、`image`、`quote`、`takeaways`、`paragraph` 等类型。([GitHub][2])

```python
# backend/app/schemas/specs/social_post.py

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class SocialPostPlatform(str, Enum):
    wechat = "wechat"


class SocialPostSubtype(str, Enum):
    wechat_article = "wechat_article"


class WechatTemplate(str, Enum):
    deep_analysis = "deep-analysis"
    industry_radar = "industry-radar"
    studio_brief = "studio-brief"
    daily_intelligence = "daily-intelligence"
    product_release = "product-release"
    breaking_watch = "breaking-watch"
    neo_brutalism = "neo-brutalism"


class ArticleType(str, Enum):
    concept_explanation = "concept_explanation"
    engineering_practice = "engineering_practice"
    project_story = "project_story"
    paper_or_report_review = "paper_or_report_review"
    industry_observation = "industry_observation"
    product_or_tool_analysis = "product_or_tool_analysis"
    news_analysis = "news_analysis"


class CitationRef(BaseModel):
    chunk_id: str = Field(..., description="检索 chunk 的稳定 ID")
    source_id: Optional[str] = Field(default=None, description="知识库文档或外部来源 ID")
    title: Optional[str] = Field(default=None, description="来源标题")
    url: Optional[str] = Field(default=None, description="来源 URL，如有")
    note: Optional[str] = Field(default=None, description="该来源支撑了什么判断")


class WechatOutlineSection(BaseModel):
    section_id: str = Field(..., description="稳定章节 ID，例如 sec-01")
    title: str = Field(..., description="章节中文标题")
    core_question: str = Field(..., description="本节回答的问题")
    key_points: list[str] = Field(default_factory=list)
    evidence_refs: list[CitationRef] = Field(default_factory=list)
    suggested_visual: Optional[str] = Field(
        default=None,
        description="该节是否适合配图，例如 架构图 / 流程图 / 时间线 / 对比图",
    )


class WechatBriefOutline(BaseModel):
    content_type: Literal["social_post"] = "social_post"
    platform: Literal["wechat"] = "wechat"
    subtype: Literal["wechat_article"] = "wechat_article"

    topic: str
    article_type: ArticleType
    target_audience: str = Field(
        default="对 AI、软件工程或知识技术内容感兴趣的公众号读者"
    )
    writing_angle: str = Field(..., description="文章切入角度")
    core_question: str = Field(..., description="全文核心问题")
    central_thesis: str = Field(..., description="全文主判断")
    reader_question_chain: list[str] = Field(
        default_factory=list,
        description="读者会依次产生的问题，驱动文章结构",
    )
    title_candidates: list[str] = Field(default_factory=list)
    recommended_template: WechatTemplate = WechatTemplate.deep_analysis
    sections: list[WechatOutlineSection] = Field(min_length=3, max_length=7)
    image_strategy: str = Field(
        default="封面图 + 1-3 张正文解释型配图，优先结构图、流程图、对比图、时间线图"
    )
    risk_notes: list[str] = Field(default_factory=list)


class WechatMeta(BaseModel):
    title: str = Field(..., max_length=32)
    digest: str = Field(..., max_length=128)
    subtitle: Optional[str] = None
    author: str = "未来学习中心"
    date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    cover_image: Optional[dict[str, Any]] = None
    thumb_media_id: Optional[str] = None
    open_comment: int = 1

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("meta.title cannot be empty")
        return value

    @field_validator("digest")
    @classmethod
    def digest_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("meta.digest cannot be empty")
        return value


class WechatImageRef(BaseModel):
    slot_id: Optional[str] = None
    url: Optional[str] = None
    local_path: Optional[str] = None
    caption: str = "配图"
    prompt: Optional[str] = None


class WechatHeadline(BaseModel):
    title: str
    body: list[str] = Field(min_length=1)
    source: Optional[str] = None
    image: Optional[WechatImageRef] = None
    citation_refs: list[CitationRef] = Field(default_factory=list)


class ParagraphBlock(BaseModel):
    type: Literal["paragraph"] = "paragraph"
    text: Union[str, list[str]]
    citation_refs: list[CitationRef] = Field(default_factory=list)


class QuoteBlock(BaseModel):
    type: Literal["quote"] = "quote"
    text: str
    attribution: Optional[str] = None
    citation_refs: list[CitationRef] = Field(default_factory=list)


class TakeawaysBlock(BaseModel):
    type: Literal["takeaways"] = "takeaways"
    title: str = "核心要点"
    items: list[str] = Field(min_length=2, max_length=6)
    citation_refs: list[CitationRef] = Field(default_factory=list)


class CardBlock(BaseModel):
    type: Literal["card"] = "card"
    number: Optional[Union[str, int]] = None
    title: str
    body: Union[str, list[str]]
    source: Optional[str] = None
    style: Optional[Literal["highlight"]] = None
    citation_refs: list[CitationRef] = Field(default_factory=list)


class OpinionBlock(BaseModel):
    type: Literal["opinion"] = "opinion"
    number: Optional[Union[str, int]] = None
    title: str
    body: Union[str, list[str]]
    source: Optional[str] = None
    citation_refs: list[CitationRef] = Field(default_factory=list)


class ImageBlock(BaseModel):
    type: Literal["image"] = "image"
    slot_id: Optional[str] = None
    url: Optional[str] = None
    local_path: Optional[str] = None
    caption: str
    prompt: Optional[str] = None


WechatBlock = Union[
    ParagraphBlock,
    QuoteBlock,
    TakeawaysBlock,
    CardBlock,
    OpinionBlock,
    ImageBlock,
]


class WechatSection(BaseModel):
    section_id: str
    cn: str = Field(..., description="中文小标题")
    en: str = Field(default="SECTION", description="模板展示用英文标题")
    intro: Optional[str] = None
    image: Optional[WechatImageRef] = None
    blocks: list[WechatBlock] = Field(min_length=1)
    citation_refs: list[CitationRef] = Field(default_factory=list)


class WechatArticleDraft(BaseModel):
    template: WechatTemplate = WechatTemplate.deep_analysis
    meta: WechatMeta
    headline: WechatHeadline
    sections: list[WechatSection] = Field(min_length=3, max_length=7)
    conclusion: Optional[str] = None
    cta: Optional[str] = None

    estimated_word_count: int = Field(default=2200, ge=800, le=5000)
    writing_notes: list[str] = Field(default_factory=list)


class ImageSlotTarget(str, Enum):
    cover = "meta.cover_image"
    headline = "headline.image"
    section = "section.image"
    block = "block.image"


class ImageAspectRatio(str, Enum):
    wechat_cover = "2.35:1"
    wide = "16:9"
    standard = "4:3"
    square = "1:1"


class ImageSlot(BaseModel):
    slot_id: str = Field(..., description="cover / headline / img-01 / img-02")
    target: ImageSlotTarget
    target_path: str = Field(
        ...,
        description="回填路径，例如 meta.cover_image、headline.image、sections[1].image",
    )
    required: bool = True
    aspect_ratio: ImageAspectRatio
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
    ]
    purpose: str = Field(..., description="这张图帮助读者理解什么")
    context_summary: str = Field(..., description="配图所在段落或章节的上下文")
    prompt_en: str = Field(..., description="英文图像生成提示词")
    negative_prompt_en: Optional[str] = Field(
        default="No cluttered small text, no unreadable UI, no random logos, no low quality, no watermark."
    )


class ImageAssetStatus(str, Enum):
    planned = "planned"
    generated = "generated"
    uploaded = "uploaded"
    failed = "failed"


class ImageAsset(BaseModel):
    slot_id: str
    status: ImageAssetStatus = ImageAssetStatus.planned
    local_path: Optional[str] = None
    public_url: Optional[str] = None
    wechat_url: Optional[str] = None
    media_id: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    error_message: Optional[str] = None


class SocialPostValidationIssue(BaseModel):
    severity: Literal["error", "warning"]
    path: str
    message: str
    suggestion: Optional[str] = None


class SocialPostValidationReport(BaseModel):
    ok: bool
    issues: list[SocialPostValidationIssue] = Field(default_factory=list)


class SocialPostSpec(BaseModel):
    content_type: Literal["social_post"] = "social_post"
    platform: SocialPostPlatform = SocialPostPlatform.wechat
    subtype: SocialPostSubtype = SocialPostSubtype.wechat_article

    outline: WechatBriefOutline
    draft: WechatArticleDraft
    image_slots: list[ImageSlot] = Field(default_factory=list)
    image_assets: list[ImageAsset] = Field(default_factory=list)

    article_json: Optional[dict[str, Any]] = Field(
        default=None,
        description="绑定图片后生成的 wechat-claw 兼容 article JSON",
    )
    validation_report: Optional[SocialPostValidationReport] = None
```

---

# 四、RenderModel schema

```python
# backend/app/schemas/render/social_post.py

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SocialPostExportFile(BaseModel):
    file_type: Literal["html", "json", "markdown", "image", "zip"]
    path: str
    url: Optional[str] = None
    label: Optional[str] = None


class SocialPostPreviewAsset(BaseModel):
    slot_id: str
    caption: str
    local_path: Optional[str] = None
    public_url: Optional[str] = None
    wechat_url: Optional[str] = None


class SocialPostRenderModel(BaseModel):
    content_type: Literal["social_post"] = "social_post"
    platform: Literal["wechat"] = "wechat"
    subtype: Literal["wechat_article"] = "wechat_article"

    title: str
    digest: str
    template: str

    html: str = Field(..., description="可直接用于预览的公众号 HTML")
    article_json: dict[str, Any] = Field(..., description="wechat-claw 兼容 article JSON")

    preview_assets: list[SocialPostPreviewAsset] = Field(default_factory=list)
    export_files: list[SocialPostExportFile] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)
```

---

# 五、Prompt 1：生成 brief outline

`wechat.md` 里已经把知识技术型推文定位为 AI、技术趋势、论文/报告解读、工具实践、知识库文章等，并强调讲清楚问题、搭出结构、给出判断；`general.md` 也要求技术自媒体文章使用问题链推进，避免目录式展开。 prompt大致组织如下：

```md
你是一个公众号知识技术型推文策划助手。

你的任务是：根据用户请求和知识库检索结果，生成一份 brief outline，用于后续撰写微信公众号文章。

## 输入

用户请求：

{{ user_request }}

生成选项：

{{ generation_options }}

知识库检索结果：

{{ retrieved_chunks }}

每条 chunk 通常包含：
- chunk_id
- source_id
- title
- url
- text
- metadata

## 写作定位

这是一篇微信公众号文章，目标读者愿意阅读有深度、有结构、有判断的长文。

文章需要兼顾三件事：

1. 讲清楚问题：读者要知道文章讨论的对象、背景、痛点或变化是什么。
2. 搭出结构：用问题链、流程拆解、案例对比、技术框架、时间线等方式组织内容。
3. 给出判断：文章要有明确的分析结论、实践启发或趋势判断，避免只堆资料。

整体语气应接近技术博主的个人分享：自然、稳健、有解释过程。读者有一定基础，但未必对该话题有系统认知。

## 结构要求

请根据内容属性选择文章类型：

- concept_explanation：概念解释类
- engineering_practice：工程实践类
- project_story：项目经验/项目复盘类
- paper_or_report_review：论文或报告解读类
- industry_observation：行业观察类
- product_or_tool_analysis：产品或工具分析类
- news_analysis：新闻事件分析类

outline 必须体现“问题链”：

- 读者第一个想知道什么
- 第二个问题是什么
- 理解之后自然会追问什么
- 最后应收束到什么判断

## 标题要求

输出 3-5 个标题候选。

标题应清楚表达文章对象、问题或收益。标题可以有观点和张力，但不能夸张、焦虑化或标题党。

标题建议控制在 20-28 个汉字，硬性上限 32 个汉字。

## 章节要求

生成 3-7 个章节，每个章节必须包含：

- section_id
- title
- core_question
- key_points
- evidence_refs
- suggested_visual

每个章节至少绑定 1 个 evidence_ref。只能引用输入中真实存在的 chunk_id，不能编造来源。

## 配图策略

给出 image_strategy。

知识技术型推文优先使用：

- 结构图
- 流程图
- 架构图
- 时间线图
- 对比图
- 概念图
- 工具截图风格示意图

避免纯装饰性插图过多。

## 输出要求

只输出 JSON，不要输出 Markdown，不要解释。

JSON 必须符合 WechatBriefOutline schema：

{
  "content_type": "social_post",
  "platform": "wechat",
  "subtype": "wechat_article",
  "topic": "...",
  "article_type": "concept_explanation | engineering_practice | project_story | paper_or_report_review | industry_observation | product_or_tool_analysis | news_analysis",
  "target_audience": "...",
  "writing_angle": "...",
  "core_question": "...",
  "central_thesis": "...",
  "reader_question_chain": ["...", "..."],
  "title_candidates": ["...", "..."],
  "recommended_template": "deep-analysis | industry-radar | studio-brief",
  "sections": [
    {
      "section_id": "sec-01",
      "title": "...",
      "core_question": "...",
      "key_points": ["...", "..."],
      "evidence_refs": [
        {
          "chunk_id": "...",
          "source_id": "...",
          "title": "...",
          "url": "...",
          "note": "..."
        }
      ],
      "suggested_visual": "..."
    }
  ],
  "image_strategy": "...",
  "risk_notes": ["..."]
}
```

---

# 六、Prompt 2：生成公众号 Draft

```md
你是一个知识技术型公众号文章写作者。

你的任务是：根据 brief outline、用户请求和知识库检索结果，生成一篇微信公众号文章 Draft。

## 输入

用户请求：

{{ user_request }}

brief outline：

{{ outline_json }}

知识库检索结果：

{{ retrieved_chunks }}

生成选项：

{{ generation_options }}

## 文章目标

文章要让读者读完后感觉：

- 这个问题被讲清楚了；
- 文章有结构，不是资料堆砌；
- 能获得一个明确判断、实践启发或后续思考方向。

文章适合 AI、软件工程、知识库、Agent、工具实践、论文/报告解读、行业观察等知识技术型主题，但不要把风格固定成论文摘要或产品文档。

## 行文风格

请遵守以下要求：

1. 写成技术博主的个人分享，不要写成教材、PRD、百科词条或营销稿。
2. 语气自然、稳健、口语化，但不要使用网络段子、表情包和夸张口号。
3. 用问题链驱动行文。每个章节回答一个自然产生的问题。
4. 重要观点要给出解释过程，不能只给结论。
5. 技术概念第一次出现时，用一句通俗解释帮助读者进入。
6. 可以使用“其实”“说白了”“你可能会想”等自然表达，但不要过度。
7. 保留必要技术细节，例如输入输出、模块关系、流程、约束、评估方式。
8. 减少不必要的中英文括注，避免外包翻译感。
9. 不要使用以下模板化句式：
   - 以上就是关于 X 的完整梳理
   - 希望这篇文章能帮你建立起更系统的认知
   - 总的来说
   - 综上所述
   - 本文将从以下几个方面介绍

## 篇幅要求

- 推荐 1500-3000 字。
- 深度解读类可扩展到 3000-4500 字。
- 每段 3-5 行，不要写成每行一个短句。
- 章节数量遵循 outline，通常为 3-7 节。

## 标题与摘要

- meta.title：建议 20-28 个汉字，硬性上限 32 个汉字。
- meta.digest：必须小于等于 128 个汉字。
- 标题必须和正文内容一致，不得标题党。

## 输出结构

输出 WechatArticleDraft JSON。

注意：正文不是 Markdown 文章，而是后续可映射到 wechat-claw 的结构化 article JSON。

允许的 block 类型：

- paragraph：普通段落
- quote：引用块或核心观点卡片
- takeaways：要点清单
- card：信息卡片，适合新闻、案例、阶段、方法
- opinion：编辑观点卡片
- image：图片块，由后续 ImageSlot 和 ImageAsset 回填

知识技术型长文优先使用：

- paragraph
- quote
- takeaways
- card

只有在确实需要展示图片位置时才使用 image block。常规正文配图优先挂在 section.image。

## 事实与引用要求

1. 每个章节必须包含 citation_refs。
2. 每个关键事实、数据、论文、报告、产品功能、开源项目信息，都必须能追溯到输入 chunk。
3. 只能引用输入中存在的 chunk_id，不能编造 chunk_id。
4. 如果材料不足，请在 writing_notes 中说明缺口，并采用谨慎表述。

## 图片占位提示

Draft 阶段可以在 section.image 留空。不要生成最终图片 URL。

如某节明显需要配图，可以在 section intro 或 writing_notes 中说明视觉建议，但具体 ImageSlot 由下一个 prompt 生成。

## 输出要求

只输出 JSON，不要输出 Markdown，不要解释。

JSON 必须符合 WechatArticleDraft schema：

{
  "template": "deep-analysis | industry-radar | studio-brief",
  "meta": {
    "title": "...",
    "digest": "...",
    "subtitle": "...",
    "author": "未来学习中心",
    "date": "YYYY-MM-DD"
  },
  "headline": {
    "title": "...",
    "body": ["...", "..."],
    "source": "...",
    "citation_refs": [
      {
        "chunk_id": "...",
        "source_id": "...",
        "title": "...",
        "url": "...",
        "note": "..."
      }
    ]
  },
  "sections": [
    {
      "section_id": "sec-01",
      "cn": "...",
      "en": "SECTION",
      "intro": "...",
      "blocks": [
        {
          "type": "paragraph",
          "text": "..."
        },
        {
          "type": "quote",
          "text": "...",
          "attribution": "..."
        },
        {
          "type": "takeaways",
          "title": "这一节真正重要的是",
          "items": ["...", "..."]
        },
        {
          "type": "card",
          "number": "01",
          "title": "...",
          "body": ["...", "..."],
          "source": "..."
        }
      ],
      "citation_refs": [
        {
          "chunk_id": "...",
          "source_id": "...",
          "title": "...",
          "url": "...",
          "note": "..."
        }
      ]
    }
  ],
  "conclusion": "...",
  "cta": "...",
  "estimated_word_count": 2200,
  "writing_notes": ["..."]
}
```

---

# 七、Prompt 3：生成 ImageSlot

生图核心思路是从文章配图占位符出发，结合占位符语义、前后文、风格指南和用户要求生成英文图像提示词；封面图强调主题象征和宽幅构图，正文配图强调与段落内容强相关，优先信息可视化、流程图、对比图等辅助理解的形式。

```md
你是公众号知识技术型文章的配图策划助手。

你的任务是：根据文章 Draft 和 brief outline，规划封面图与正文配图的 ImageSlot。

## 输入

brief outline：

{{ outline_json }}

文章 Draft：

{{ draft_json }}

用户临时配图要求：

{{ image_preferences }}

## 配图目标

配图必须帮助读者理解文章，而不是装饰页面。

知识技术型推文优先使用：

1. 结构图：展示框架、模块关系、系统架构。
2. 流程图：展示算法流程、工作流、使用步骤。
3. 时间线图：展示技术演进、产品迭代、事件脉络。
4. 对比图：展示不同方法、方案或阶段差异。
5. 概念图：用抽象视觉解释一个核心概念。
6. 工具截图风格示意图：展示产品或系统使用场景。

## 数量要求

必须生成：

- 1 个 cover slot

建议生成：

- 1 个 headline slot
- 1-3 个正文 section slot

总数一般为 2-5 个。

如果文章较短，可以只生成 cover + headline + 1 个正文图。

## 封面图要求

- slot_id 固定为 "cover"
- target 固定为 "meta.cover_image"
- target_path 固定为 "meta.cover_image"
- aspect_ratio 使用 "2.35:1"
- 视觉要能体现文章主题
- 可以有少量文字空间，但 prompt 不要强依赖模型生成可读文字
- 避免复杂小字、密集界面和随机 logo

## 正文图要求

正文图需要挂载到具体位置：

- headline.image
- sections[0].image
- sections[1].image
- sections[2].image
- 或某个 image block

每个 ImageSlot 必须说明：

- 这张图服务于哪一节
- 它帮助读者理解什么
- 适合什么视觉形式
- 英文 prompt

## 英文 prompt 写法

每条 prompt_en 必须包含：

- subject：画面主体
- context：文章中的技术或知识语境
- visual form：结构图 / 流程图 / 概念图 / 时间线 / 编辑插图
- style：专业、清晰、公众号科技文章风格
- composition：宽幅或标准比例构图
- constraints：避免小字、避免水印、避免随机 logo

封面图可以偏编辑视觉；正文图优先清晰解释。

## 输出要求

只输出 JSON 数组，不要输出 Markdown，不要解释。

每个对象必须符合 ImageSlot schema：

[
  {
    "slot_id": "cover",
    "target": "meta.cover_image",
    "target_path": "meta.cover_image",
    "required": true,
    "aspect_ratio": "2.35:1",
    "caption": "...",
    "visual_type": "cover",
    "purpose": "...",
    "context_summary": "...",
    "prompt_en": "...",
    "negative_prompt_en": "No cluttered small text, no unreadable UI, no random logos, no low quality, no watermark."
  },
  {
    "slot_id": "headline",
    "target": "headline.image",
    "target_path": "headline.image",
    "required": true,
    "aspect_ratio": "16:9",
    "caption": "...",
    "visual_type": "concept_diagram | workflow_diagram | architecture_diagram | timeline | comparison | editorial_illustration | screenshot_like",
    "purpose": "...",
    "context_summary": "...",
    "prompt_en": "...",
    "negative_prompt_en": "No cluttered small text, no unreadable UI, no random logos, no low quality, no watermark."
  }
]
```

---

# 八、Prompt 4：Review

```md
你是结构化公众号文章 JSON 修复助手。

你的任务是：根据 validation errors 修复 social_post / wechat JSON。

## 输入

原始 JSON：

{{ invalid_json }}

校验错误：

{{ validation_errors }}

可用 chunk 列表：

{{ retrieved_chunks }}

目标 schema：

{{ target_schema_name }}

## 修复原则

1. 只修复结构、字段、长度、引用、格式问题。
2. 保留原文章主旨、事实内容、章节顺序和写作风格。
3. 不新增无法从 chunk 支撑的事实。
4. 不编造 chunk_id。
5. 如果标题超过 32 字，压缩标题但保留核心对象和判断。
6. 如果 digest 超过 128 字，压缩摘要。
7. 如果某个章节没有 citation_refs，从最相关的已有 chunk 中补充。
8. 如果图片槽位 target_path 无效，改为合法路径。
9. 如果正文 block 类型不被支持，改为 paragraph、quote、takeaways 或 card。
10. 如果 HTML 渲染发现未解析占位符，删除或替换相关占位符内容。

## 输出要求

只输出修复后的 JSON，不要输出 Markdown，不要解释。
```

---

# 九、Validator 规则

建议拆成两类 validator。

## 1. Pre-validator

在图片生成前执行：

```text
validate_outline
validate_draft_schema
validate_wechat_constraints
validate_citation_coverage
validate_image_slots
validate_article_adapter
```

具体规则：

| 检查项            | 规则                                                        |
| -------------- | --------------------------------------------------------- |
| content_type   | 必须是 `social_post`                                         |
| platform       | MVP 只允许 `wechat`                                          |
| subtype        | MVP 只允许 `wechat_article`                                  |
| template       | MVP 推荐只允许 `deep-analysis / industry-radar / studio-brief` |
| meta.title     | 非空，硬性 ≤ 32 字，推荐 ≤ 28 字                                    |
| meta.digest    | 非空，硬性 ≤ 128 字                                             |
| headline.body  | 至少 1 段                                                    |
| sections       | 3-7 个                                                     |
| section.blocks | 每节至少 1 个 block                                            |
| citation_refs  | 每节至少 1 个有效 chunk                                          |
| image_slots    | 至少 cover，建议 2-5 个                                         |
| slot_id        | 不重复                                                       |
| target_path    | 必须可映射到 draft                                              |
| prompt_en      | 非空                                                        |
| aspect_ratio   | cover 用 2.35:1，正文用 16:9 或 4:3                             |

## 2. Final-validator

在图片生成与绑定后执行：

```text
validate_image_assets
validate_bound_article_json
validate_wechat_claw_article
validate_rendered_html
```

具体规则：

| 检查项                     | 规则                                |
| ----------------------- | --------------------------------- |
| required image slot     | 必须有对应 ImageAsset                  |
| local_path / public_url | 预览至少有一个可用                         |
| article_json            | 必须可被 wechat-claw 渲染               |
| image binding           | cover/headline/section 图片路径已回填    |
| unresolved placeholder  | HTML 中不能残留 `{{...}}`              |
| html size               | 小于 1MB                            |
| export file             | html/json 至少各有一个                  |
| warnings                | 非微信 CDN 图片可 warning，不阻断本地 preview |

`wechat-claw` 的校验逻辑会检查模板是否存在、标题和摘要长度、headline、sections、block title、未解析占位符和 HTML 大小等，后端 final-validator 可以先做内部校验，再调用它的 `validate_article.py` 兜底。([GitHub][3])

---

# 十、HTML renderer 接入方案

建议新增一个薄封装服务：

```python
# backend/app/services/wechat_claw_renderer.py

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from app.schemas.render.social_post import SocialPostRenderModel, SocialPostExportFile


class WechatClawRenderer:
    def __init__(self, skill_root: Path, storage_root: Path):
        self.skill_root = skill_root
        self.storage_root = storage_root

    def render(
        self,
        *,
        task_id: str,
        article_json: dict[str, Any],
        check: bool = True,
    ) -> SocialPostRenderModel:
        work_dir = self.storage_root / "content-generation" / task_id / "wechat"
        work_dir.mkdir(parents=True, exist_ok=True)

        article_path = work_dir / "article.json"
        html_path = work_dir / "article.html"

        article_path.write_text(
            json.dumps(article_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        cmd = [
            "python3",
            str(self.skill_root / "scripts" / "render_article.py"),
            str(article_path),
            "-o",
            str(html_path),
        ]
        if check:
            cmd.append("--check")

        result = subprocess.run(
            cmd,
            cwd=str(self.skill_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        warnings: list[str] = []
        if result.returncode != 0:
            raise RuntimeError(
                f"wechat-claw render failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )

        if result.stderr.strip():
            warnings.extend(result.stderr.strip().splitlines())

        html = html_path.read_text(encoding="utf-8")

        meta = article_json.get("meta") or {}

        return SocialPostRenderModel(
            title=str(meta.get("title") or ""),
            digest=str(meta.get("digest") or ""),
            template=str(article_json.get("template") or ""),
            html=html,
            article_json=article_json,
            export_files=[
                SocialPostExportFile(file_type="json", path=str(article_path), label="Article JSON"),
                SocialPostExportFile(file_type="html", path=str(html_path), label="HTML"),
            ],
            warnings=warnings,
        )
```

MVP 先用 subprocess 最稳，因为 `wechat-claw` 当前就是脚本入口；等链路稳定后，再把 `scripts/article_lib.py` 的 `render_article()` / `validate_article()` 作为内部库 import。仓库文档也明确推荐用 `render_article.py article.json -o build/article.html --check` 进行 HTML 渲染和校验。([GitHub][4])

---

# 十一、Article JSON 适配规则

内部的 `WechatArticleDraft` 可以含有 `citation_refs`、`section_id`、`slot_id` 等字段；传给 `wechat-claw` 前要清理成它支持的结构。

```python
def to_wechat_claw_article(spec: SocialPostSpec) -> dict[str, Any]:
    draft = spec.draft.model_dump(mode="json")
    assets_by_slot = {asset.slot_id: asset for asset in spec.image_assets}

    article = {
        "template": draft["template"],
        "meta": draft["meta"],
        "headline": draft["headline"],
        "sections": draft["sections"],
        "conclusion": draft.get("conclusion"),
        "cta": draft.get("cta"),
    }

    bind_images(article, spec.image_slots, assets_by_slot)
    strip_internal_fields(article)

    return article


def strip_internal_fields(obj):
    if isinstance(obj, dict):
        for key in ["section_id", "citation_refs", "slot_id", "writing_notes"]:
            obj.pop(key, None)
        for value in obj.values():
            strip_internal_fields(value)
    elif isinstance(obj, list):
        for item in obj:
            strip_internal_fields(item)


def bind_images(article, image_slots, assets_by_slot):
    for slot in image_slots:
        asset = assets_by_slot.get(slot.slot_id)
        if not asset:
            continue

        image_payload = {
            "slot_id": slot.slot_id,
            "url": asset.wechat_url or asset.public_url or asset.local_path,
            "local_path": asset.local_path,
            "caption": slot.caption,
            "prompt": slot.prompt_en,
        }

        if slot.target_path == "meta.cover_image":
            article.setdefault("meta", {})["cover_image"] = image_payload
            if asset.media_id:
                article["meta"]["thumb_media_id"] = asset.media_id

        elif slot.target_path == "headline.image":
            article.setdefault("headline", {})["image"] = image_payload

        elif slot.target_path.startswith("sections[") and slot.target_path.endswith("].image"):
            index = int(slot.target_path.split("[", 1)[1].split("]", 1)[0])
            article["sections"][index]["image"] = image_payload
```

---

# 十二、Workflow 节点状态与进度

建议 social_post 先走 direct path，不进入 lecture/slide 的 unit loop。

```text
normalize_request                 5%
retrieve_for_planning             15%
generate_wechat_brief_outline     25%
generate_wechat_article_draft     45%
plan_wechat_image_slots           55%
pre_validate_social_post          60%
generate_image_assets             75%
bind_image_assets                 82%
validate_social_post              88%
render_social_post_html           95%
completed                         100%
```

`done.md` 已经完成了任务日志、partial preview、stream events、render units、partial_render_model 等持久化字段，所以 social_post 可以复用现有轮询式事件接口；在 Draft 完成时先发布一次文本预览，在 HTML render 完成后再更新 final preview。

---

# 十三、SocialPostProfile 建议

```python
# backend/app/content_types/social_post.py

from app.content_types.base import ContentTypeProfile
from app.schemas.specs.social_post import SocialPostSpec
from app.schemas.render.social_post import SocialPostRenderModel
from app.generators.social_post_generator import SocialPostGenerator
from app.validators.social_post_validator import SocialPostValidator
from app.renderers.social_post_renderer import SocialPostRenderer


SocialPostProfile = ContentTypeProfile(
    content_type="social_post",
    display_name="社交媒体推文",
    generation_mode="direct",
    supported_subtypes=["wechat_article"],
    default_subtype="wechat_article",
    spec_schema=SocialPostSpec,
    render_schema=SocialPostRenderModel,
    generator_factory=SocialPostGenerator,
    validator_factory=SocialPostValidator,
    renderer_factory=SocialPostRenderer,
    prompt_namespace="social_post/wechat",
    supports_partial_preview=True,
    supports_export=True,
)
```

如果你们当前 `ContentTypeProfile` 还没有 `generation_mode` 字段，就在第四阶段同步加上：

```python
generation_mode: Literal["unit_loop", "direct"]
```

然后在 workflow 中新增：

```text
route_generation_mode
  ├── unit_loop: lecture / slide_deck
  └── direct: social_post
```

---

# 十四、前端 preview 建议

前端新增一个 `SocialPostPreviewRenderer`：

```text
frontend/src/components/preview/SocialPostPreviewRenderer.tsx
```

渲染策略：

```tsx
export function SocialPostPreviewRenderer({ renderModel }) {
  return (
    <div className="mx-auto max-w-[430px] bg-white shadow rounded-xl overflow-hidden">
      <iframe
        title={renderModel.title}
        srcDoc={renderModel.html}
        className="w-full min-h-[720px] border-0"
      />
    </div>
  )
}
```

展示上建议模拟手机宽度，因为公众号文章主要在手机端阅读。导出按钮仍沿用现有 `ExportActions`，只要 `SocialPostRenderModel.export_files` 提供 HTML 和 JSON 即可。

---

# 十五、测试清单

## 后端单测

```text
tests/test_social_post_schema.py
tests/test_social_post_outline_prompt.py
tests/test_social_post_validator.py
tests/test_wechat_article_adapter.py
tests/test_wechat_claw_renderer.py
tests/test_social_post_workflow.py
```

重点测：

```text
1. outline schema 可解析
2. draft schema 可解析
3. 每个 section 都有 citation_refs
4. image_slots 至少包含 cover
5. target_path 能正确回填
6. article_json 能被 wechat-claw validate
7. html 文件能生成
8. partial preview 能保存
9. final preview 能保存
10. provider 失败时能进入 repair 或 fail
```

## 手动验证命令

```bash
uv run pytest backend/tests/test_social_post_schema.py -q
uv run pytest backend/tests/test_social_post_validator.py -q
uv run pytest backend/tests/test_wechat_article_adapter.py -q
uv run pytest backend/tests/test_social_post_workflow.py -q -s
uv run python backend/scripts/export_json_schema.py
npm run build
```

---

# 十六、落地优先级

建议按这个顺序开发：

| 优先级 | 内容                                       | 目标                                |
| --- | ---------------------------------------- | --------------------------------- |
| P0  | schema + profile + route_generation_mode | 让 `social_post` 成为合法 content_type |
| P0  | outline / draft / image_slots prompts    | 跑通结构化生成                           |
| P0  | pre-validator + repair                   | 保证生成结果可修                          |
| P0  | article adapter + wechat-claw render     | 跑通 HTML preview                   |
| P0  | image asset generation + binding         | 形成完整图文结果                          |
| P1  | final-validator                          | 保证导出质量                            |
| P1  | frontend SocialPostPreviewRenderer       | 前端可预览                             |
| P2  | 微信上传 / 草稿箱 / 发布                          | 后续接真实公众号能力                        |

最小闭环可以先做到：

```text
用户请求
  -> 检索
  -> outline
  -> draft
  -> image slots
  -> 使用占位图片或本地生成图片
  -> article_json
  -> wechat-claw HTML
  -> 前端 preview
```

这样第四阶段就能证明三件事：`direct workflow` 能跑通、`social_post/wechat` 的 schema 边界清楚、外部 skill 的 HTML 渲染能力能稳定接入。

[1]: https://github.com/th3ee9ine/wechat-claw-skill "GitHub - th3ee9ine/wechat-claw-skill: 一键爆款微信公众号文章发布。微信公众号技能库，整合多种公众号能力，便于快速调用。 · GitHub"
[2]: https://raw.githubusercontent.com/th3ee9ine/wechat-claw-skill/master/docs/README.zh.md "raw.githubusercontent.com"
[3]: https://raw.githubusercontent.com/th3ee9ine/wechat-claw-skill/master/scripts/article_lib.py "raw.githubusercontent.com"
[4]: https://raw.githubusercontent.com/th3ee9ine/wechat-claw-skill/master/SKILL.md "raw.githubusercontent.com"
