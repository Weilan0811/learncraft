# Podcast 生成工作流设计

本文档描述第五阶段 `podcast_script` 内容类型的推荐设计。目标是在不扩大 lecture / slide unit-loop 主链路复杂度的前提下，复用第四阶段 `social_post` 已验证的 direct workflow，生成中文双人播客脚本，并通过阿里云百炼 `qwen3-tts-instruct-flash` 生成音频。

当前建议内部内容类型沿用已有 schema 预留值：

```text
content_type = podcast_script
```

前端展示名可以使用 `Podcast` 或 `播客`。如果后续希望内部枚举改成 `podcast`，需要同步迁移 `ContentType`、前端类型、schema export、历史任务兼容和 profile 注册；MVP 阶段不建议做这层重命名。

阿里云百炼 Qwen-TTS 文档确认 `qwen3-tts-instruct-flash` 属于 Qwen-TTS 系列，支持 OpenAI 兼容调用方式。本文设计固定双人音色映射：

| 角色 | 脚本标签 | TTS 音色 |
|---|---|---|
| 男声主持 | `Person1` | `Ethan` |
| 女声搭档 | `Person2` | `Cherry` |

参考文档：

- 阿里云百炼 Qwen-TTS: https://help.aliyun.com/zh/model-studio/qwen-tts/
- 播客脚本生成要求: `docs/output.txt`
- 当前阶段说明: `docs/done.md`
- direct workflow 样板: `backend/app/workflows/nodes/direct_content_node.py`
- 后端开发约定与说明：`backend\docs\development_notes.md`、 `backend\README.md`

---

## 一、目标与非目标

### 目标

本阶段交付一个可运行的播客生成闭环：

```text
用户请求 / 知识库内容
  -> 生成 PodcastSpec
  -> 校验 Person1 / Person2 对话脚本
  -> 调用 qwen3-tts-instruct-flash 分段生成音频
  -> 输出 PodcastRenderModel
  -> 前端预览脚本和音频
  -> 支持脚本和音频导出
```

播客内容必须符合 `docs/output.txt`：

- 只使用 `Person1` 和 `Person2` 作为说话人标识。
- 开场由 `Person1` 自然说出：“欢迎来到 {podcast_name} —— {podcast_tagline}。”
- 围绕输入内容展开，不编造无依据主题。
- 具备自然双人播客节奏。
- 至少出现一次温和、尊重的质疑、追问或保留意见。
- 适合 TTS 播放，句子不过长，允许有限通用 TTS 标签。
- 结尾由 `Person1` 自然收束并向听众道别。

### 非目标

本阶段不做以下能力：

- 不做播客剪辑器。
- 不做背景音乐、片头音乐、混音、降噪。
- 不做多主持人动态选角。
- 不做跨任务音频素材库。
- 不强制生成单个完整 mp3 文件。MVP 优先输出分段音频和播放清单；完整音频拼接可以作为 P1 增强。

---

## 二、推荐流程

`podcast_script` 建议和 `social_post` 一样走 direct workflow。

```text
normalize_request
  ↓
retrieve_for_planning
  ↓
route_generation_mode
  ↓
generate_direct_content
  ├─ build podcast prompt
  ├─ generate structured podcast draft
  ├─ parse Person1 / Person2 dialogue
  └─ build PodcastSpec
  ↓
validate_direct_content
  ├─ validate script tags
  ├─ validate opening / ending
  ├─ validate speaker turns
  ├─ validate TTS tags
  └─ validate factual grounding hints
  ↓
render_direct_content
  ├─ PodcastRenderer
  ├─ TTSService
  ├─ generate segment audio assets
  └─ build PodcastRenderModel
  ↓
finalize_task
  ↓
preview / export
```

不建议为 podcast 使用 unit-loop，原因是播客对话需要全局控制开场、节奏、观点递进、质疑点和结尾。如果逐段生成，容易出现上下文断裂、重复介绍和角色口吻漂移。

---

## 三、模块与文件

建议新增或修改以下文件。

```text
backend/app/content_types/
├── podcast.py
├── registry.py

backend/app/schemas/specs/
├── podcast.py
├── __init__.py

backend/app/schemas/render/
├── podcast.py
├── __init__.py

backend/app/schemas/elements/
├── audio.py
├── __init__.py

backend/app/generators/
├── podcast_generator.py

backend/app/validators/
├── podcast_validator.py
├── __init__.py

backend/app/renderers/
├── podcast_renderer.py

backend/app/services/
├── tts_service.py

backend/app/exporters/
├── audio_exporter.py
├── markdown_exporter.py

backend/app/prompts/generator/
├── podcast_script.md

backend/app/workflows/nodes/
├── direct_content_node.py

frontend/src/types/
├── podcast.ts
├── content.ts
├── export.ts

frontend/src/components/renderers/
├── PodcastRenderer/
│   └── index.tsx

frontend/src/components/generation/
├── ContentGenerationForm.tsx
├── ExportActions.tsx

frontend/src/pages/
├── ContentPreviewPage.tsx
```

同时更新：

```text
backend/scripts/export_json_schema.py
backend/docs/api.md
backend/README.md
```

---

## 四、ContentTypeProfile

新增 `backend/app/content_types/podcast.py`：

```python
from app.content_types.base import ContentTypeProfile, ElementPolicy
from app.renderers.podcast_renderer import PodcastRenderer
from app.schemas.render import PodcastRenderModel
from app.schemas.specs import PodcastSpec


def build_podcast_profile() -> ContentTypeProfile:
    return ContentTypeProfile(
        content_type="podcast_script",
        generation_mode="direct",
        unit_type="podcast",
        requires_outline=False,
        supports_unit_streaming=False,
        planner_prompt_name="",
        unit_spec_prompt_name="podcast_script.md",
        spec_schema=PodcastSpec,
        unit_spec_schema=PodcastSpec,
        render_model_schema=PodcastRenderModel,
        renderer_factory=PodcastRenderer,
        generator_name="podcast",
        element_policy=ElementPolicy(
            allowed_elements=("audio_script", "audio_file"),
            default_required_elements=("audio_script", "audio_file"),
            optional_elements=(),
        ),
        exporter_types=("markdown", "audio"),
    )
```

在 `backend/app/content_types/registry.py` 注册：

```python
"podcast_script": build_podcast_profile(),
```

`backend/app/schemas/base.py` 已经预留 `podcast_script`、`audio_script`、`audio_file`，本阶段只需要把 `ExportType` 扩展为包含 `audio`：

```python
ExportType = Literal["pdf", "slide_json", "image_assets", "pptx", "markdown", "html", "audio"]
```

---

## 五、Schema 设计

### 5.1 PodcastSpec

新增 `backend/app/schemas/specs/podcast.py`。

```python
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
    type: Literal["podcast_script"] = "podcast_script"
    content_type: Literal["podcast_script"] = "podcast_script"
    version: str = "content.spec/v1"

    title: str
    podcast_name: str
    podcast_tagline: str
    output_language: str = "zh-CN"
    roles_person1: str = "引导型主持人，负责推进结构、总结节点、照顾听众"
    roles_person2: str = "分析型搭档，负责提出洞察、追问、补充或温和挑战"
    conversation_style: str = "自然、专业、有节奏感的中文双人播客"
    dialogue_structure: str = "开场、主题展开、观点追问、关键 takeaway、自然结尾"
    engagement_techniques: list[str] = Field(
        default_factory=lambda: ["追问", "复述", "类比", "温和质疑", "阶段性总结"]
    )
    voice_config: PodcastVoiceConfig = Field(default_factory=PodcastVoiceConfig)
    raw_dialogue: str
    segments: list[PodcastSegmentSpec] = Field(default_factory=list)
    validation_report: PodcastValidationReport | None = None
```

设计要点：

- `raw_dialogue` 保留 `docs/output.txt` 要求的最终对话格式。
- `segments` 是后端解析后的结构化轮次，用于 TTS。
- `Person1` 永远映射 `Ethan`，`Person2` 永远映射 `Cherry`。
- `citation_refs` 初期可以只存 chunk id；后续如需更强溯源，再扩展为 CitationRef 对象。

### 5.2 Audio elements

新增 `backend/app/schemas/elements/audio.py`。

```python
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
```

更新 `backend/app/schemas/elements/__init__.py` 的 `ContentElement` union，把 `AudioScriptElement` 和 `AudioFileElement` 加进去。

### 5.3 PodcastRenderModel

新增 `backend/app/schemas/render/podcast.py`。

```python
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
```

更新 `backend/app/schemas/render/__init__.py` 的 `RenderModel` union，把 `PodcastRenderModel` 加进去。

---

## 六、Prompt 设计

新增 `backend/app/prompts/generator/podcast_script.md`，以 `docs/output.txt` 为基础改成模板。

建议输入变量：

```text
{user_request}
{generation_options}
{retrieved_chunks}
{podcast_name}
{podcast_tagline}
{output_language}
{roles_person1}
{roles_person2}
{conversation_style}
{dialogue_structure}
{engagement_techniques}
{input_texts}
```

推荐让 LLM 输出结构化 JSON，而不是直接输出裸对话。这样能继续复用 `BailianLLMService.generate_structured()` 和 schema repair 能力。

```md
你是中文播客脚本作者。

请根据输入内容生成一段适合文本转语音 TTS 播放的中文双人播客对话。

## 输入

用户请求：

{user_request}

生成选项：

{generation_options}

知识库检索内容：

{retrieved_chunks}

播客名称：

{podcast_name}

播客标语：

{podcast_tagline}

## 核心要求

- 对话必须围绕输入内容展开，不要偏题。
- 不要编造与输入无关的主题或事实。
- 只使用 Person1 和 Person2 作为说话人标识。
- Person1 是：{roles_person1}
- Person2 是：{roles_person2}
- 对话风格：{conversation_style}
- 对话流程：{dialogue_structure}
- 自然使用这些衔接方式：{engagement_techniques}
- 至少安排一次温和、尊重的质疑、补充、追问或保留意见。
- 句子适合朗读，避免过长、过密。
- 可以使用通用 TTS 标签：<break time="0.2s"/>、<prosody rate="slow">...</prosody>、<prosody pitch="+5%">...</prosody>、<prosody volume="soft">...</prosody>。
- 不要使用 Amazon 或 Alexa 专属标签。
- 不要使用 <emphasis> 标签。
- 不要使用 <say-as> 标签。

## raw_dialogue 格式要求

raw_dialogue 必须只包含如下格式的轮次：

<Person1>欢迎来到 {podcast_name} —— {podcast_tagline}。今天我们来聊一聊……</Person1>
<Person2>我很期待这个话题。这里面最值得注意的一点是……</Person2>

不要输出标题。
不要输出项目符号。
不要输出分析说明。
不要输出内部规划。
不要输出任何与播客正文无关的内容。

## 输出要求

只输出 JSON，不要输出 Markdown，不要解释。

JSON 必须符合 PodcastDialogueDraft schema：

{
  "title": "...",
  "podcast_name": "{podcast_name}",
  "podcast_tagline": "{podcast_tagline}",
  "output_language": "{output_language}",
  "raw_dialogue": "<Person1>...</Person1>\n<Person2>...</Person2>"
}
```

`docs/output.txt` 可以作为 prompt 内容的规范来源，但不建议运行时整段拼接所有说明，避免 prompt 过长。实现时应提炼关键规则，并通过 validator 补足约束。

---

## 七、PodcastGenerator

新增 `backend/app/generators/podcast_generator.py`。

核心流程：

```text
PodcastGenerator.generate(state)
  -> 判断 provider_mode
  -> real: 调用 LLM 生成 PodcastDialogueDraft
  -> stub: 生成本地 fallback 脚本
  -> parse raw_dialogue
  -> build PodcastSegmentSpec[]
  -> build PodcastSpec
```

real provider 失败时保持 social_post 的策略：

- 默认不静默 fallback。
- 只有 `generation_options.allow_fallback=true` 时才允许 fallback。
- fallback 产物在 metadata 记录 `generation_mode` 和 `fallback_reason`。

异常阶段建议命名：

```text
podcast_script_generation
podcast_dialogue_parse
```

解析规则：

```text
<Person1>...</Person1>
<Person2>...</Person2>
```

解析后映射：

```text
Person1 -> Ethan
Person2 -> Cherry
```

如果 raw_dialogue 中出现其他 speaker，直接进入 validation error。

---

## 八、PodcastValidator

新增 `backend/app/validators/podcast_validator.py`。

校验分为 pre-render 和 final-render。

### 8.1 Pre-render validation

在 TTS 前执行：

| 检查项 | 规则 |
|---|---|
| content_type | 必须是 `podcast_script` |
| raw_dialogue | 非空 |
| speaker tag | 只能包含 `Person1` 和 `Person2` |
| opening | 第一段 Person1 必须包含 `欢迎来到 {podcast_name} —— {podcast_tagline}。` |
| speaker coverage | Person1 / Person2 都必须出现 |
| turn count | 建议至少 6 轮 |
| turn length | 单轮不宜过长，超过阈值 warning |
| challenge | 至少出现一次追问、补充、保留或不同观点 |
| forbidden text | 不允许“我正在分析”“这张图片描述了”“以上就是总结”等机械说明 |
| forbidden tags | 不允许 `<emphasis>`、`<say-as>`、Amazon / Alexa 专属标签 |
| ssml closure | `<prosody>` 等标签必须闭合 |

### 8.2 Final-render validation

在 TTS 后执行：

| 检查项 | 规则 |
|---|---|
| segment audio | 每个 segment 都有对应状态 |
| required audio | 所有 required segment 的音频必须 generated |
| asset url | generated audio 必须有可下载 URL |
| voice mapping | Person1=Ethan，Person2=Cherry |
| manifest | audio manifest 可以被保存 |
| render model | `script_text` 和 `segments` 不为空 |

MVP 阶段如果单个非关键 segment TTS 失败，建议任务失败，而不是输出残缺播客。等前端支持局部重试后再放宽。

---

## 九、TTSService

新增 `backend/app/services/tts_service.py`。

服务接口：

```python
from typing import Protocol

from app.schemas.elements.audio import AudioFileElement


class TTSService(Protocol):
    def synthesize(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        ...
```

百炼实现建议：

```python
class BailianTTSService:
    def __init__(
        self,
        api_key: str,
        model: str = "qwen3-tts-instruct-flash",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout_seconds: float = 120.0,
        max_retries: int = 2,
        storage_service: StorageService | None = None,
        client: object | None = None,
    ) -> None:
        ...

    def synthesize(self, *, text: str, voice: str, asset_id: str) -> AudioFileElement:
        ...
```

配置项放入 `backend/app/core/config.py`：

```python
tts_provider: str = "bailian"
tts_model: str = "qwen3-tts-instruct-flash"
tts_person1_voice: str = "Ethan"
tts_person2_voice: str = "Cherry"
tts_output_format: str = "mp3"
```

实现要求：

- 沿用 `CONTENT_GENERATOR_BAILIAN_API_KEY`。
- 沿用现有 `request_timeout_seconds` / `max_retries` 风格。
- TTS 返回音频 bytes 后通过 `LocalStorageService.save_bytes()` 持久化。
- asset kind 可以先复用 `other`，如 `AssetKind` 需要更精确可新增 `audio`。
- metadata 记录 provider、model、voice、speaker、segment_id。
- TTS 请求失败应暴露具体 segment id、speaker、voice。

TTS 输入清洗：

- 去掉外层 `<Person1>` / `<Person2>` 标签。
- 保留允许的 `<break>` 和 `<prosody>`。
- 拒绝或清洗禁用标签。
- 避免把空白文本提交给付费接口。

---

## 十、PodcastRenderer

新增 `backend/app/renderers/podcast_renderer.py`。

核心职责：

```text
PodcastSpec
  -> AudioScriptElement[]
  -> TTSService.synthesize(...)
  -> AudioFileElement[]
  -> audio manifest JSON
  -> PodcastRenderModel
```

MVP 渲染策略：

1. 对每个 `PodcastSegmentSpec` 顺序调用 TTS。
2. 每个 segment 独立保存一个音频 asset。
3. 保存 `audio_manifest.json`，记录播放顺序、speaker、voice、text、audio_url。
4. `final_audio_url` 暂时为空。
5. 前端按 manifest / segments 顺序播放。

完整音频拼接作为 P1：

- 如果百炼能直接返回统一可拼接格式，可新增 `AudioAssemblerService`。
- 如果输出 mp3，不能简单拼接 bytes，应使用可靠音频处理库或外部工具。
- 当前 `pyproject.toml` 未引入音频处理依赖，因此 P0 不做拼接更稳。

---

## 十一、direct_content_node 改造

当前 `backend/app/workflows/nodes/direct_content_node.py` 对 `social_post` 写死了 generator、validator 和 renderer。接入 podcast 时建议顺手改成 registry 派发，避免继续堆分支。

建议新增轻量 router：

```python
def get_direct_generator(name: str):
    if name == "social_post":
        return SocialPostGenerator()
    if name == "podcast":
        return PodcastGenerator()
    raise ValueError(f"Unsupported direct generator: {name}")


def get_direct_validator(content_type: str):
    if content_type == "social_post":
        return SocialPostValidator()
    if content_type == "podcast_script":
        return PodcastValidator()
    raise ValueError(f"Unsupported direct validator: {content_type}")
```

`generate_direct_content`：

```text
profile = get_content_type_profile(state.content_type)
generator = get_direct_generator(profile.generator_name)
spec = generator.generate(state)
event type = direct_spec_ready
payload 根据 content_type 填充 title、segment_count 等摘要
```

`validate_direct_content`：

```text
validator = get_direct_validator(state.content_type)
report = validator.validate_pre_render(...)
```

`render_direct_content`：

```text
renderer = get_content_type_profile(state.content_type).renderer_factory()
render_model = renderer.render(state.content_spec, state.elements)
validator.validate_final_render(...)
```

这样 social_post 仍保持原行为，podcast 只新增 profile / generator / validator / renderer。

---

## 十二、事件流和 partial preview

复用现有 `stream_events` 和 `partial_render_model`。

建议新增事件 payload，但事件 type 可以先复用：

```text
direct_spec_ready
direct_render_ready
```

`direct_spec_ready` payload：

```json
{
  "title": "播客标题",
  "segment_count": 18,
  "voices": {
    "Person1": "Ethan",
    "Person2": "Cherry"
  }
}
```

`direct_render_ready` payload：

```json
{
  "title": "播客标题",
  "audio_segment_count": 18,
  "final_audio_url": null
}
```

如果希望前端在音频逐段生成时更早更新，可以在 P1 增加：

```text
audio_segment_ready
```

但这需要扩展 `TaskStreamEvent.type` union、schema export 和前端类型。P0 可以先让 render 完成后整体出现。

---

## 十三、导出设计

### 13.1 Markdown / script export

扩展 `backend/app/exporters/markdown_exporter.py`，支持 `PodcastRenderModel`：

```text
# {title}

{script_text}
```

导出类型仍用 `markdown`。

### 13.2 Audio export

新增 `backend/app/exporters/audio_exporter.py`，导出类型为 `audio`。

MVP 行为：

- 如果 `final_audio_url` 存在，直接返回完整音频。
- 如果不存在，保存或返回 `audio_manifest.json`。
- 后续可增强为 zip 打包所有分段音频。

为了避免 `audio` exporter 返回空，建议 renderer 阶段始终保存 manifest asset。

---

## 十四、前端设计

### 14.1 类型

更新 `frontend/src/types/content.ts`：

```ts
export type MvpContentType = "lecture" | "slide_deck" | "social_post" | "podcast_script";
export type ExportType = "pdf" | "slide_json" | "image_assets" | "pptx" | "markdown" | "html" | "audio";
```

新增 `frontend/src/types/podcast.ts`：

```ts
export interface PodcastAudioSegment {
  segment_id: string;
  order: number;
  speaker: "Person1" | "Person2";
  voice: "Ethan" | "Cherry";
  text: string;
  audio_url?: string | null;
  status: "pending" | "generated" | "failed";
  error_message?: string | null;
}

export interface PodcastRenderModel {
  render_type: "podcast_script";
  content_type: "podcast_script";
  title: string;
  podcast_name: string;
  podcast_tagline: string;
  script_text: string;
  segments: PodcastAudioSegment[];
  audio_manifest_url?: string | null;
  final_audio_url?: string | null;
  warnings: string[];
}
```

更新 `frontend/src/types/export.ts` 的 `RenderModel` union。

### 14.2 表单

`ContentGenerationForm.tsx` 新增 `Podcast` 选项：

```text
topic: "AI Agent 工作流的设计与实践"
prompt: "根据给定内容生成一段适合中文 TTS 播放的双人播客对话。"
systemPrompt: "内容准确、表达自然、节奏适合收听。"
```

generation options：

```text
language = zh-CN
style = chinese_podcast_dialogue
include_images = false
include_charts = false
include_mindmap = false
```

### 14.3 预览组件

新增 `frontend/src/components/renderers/PodcastRenderer/index.tsx`。

布局建议：

```text
标题区
  - podcast_name
  - podcast_tagline
  - voice mapping

播放器区
  - 如果 final_audio_url 存在，展示一个总播放器
  - 否则展示按 segment 顺序的分段播放器

脚本区
  - Person1 / Ethan
  - Person2 / Cherry
  - 保留自然段落和轮次
```

注意：

- 不需要做 landing page。
- 不需要解释“如何使用”。
- UI 应该是工作台式预览，不做营销 hero。
- 分段播放器可以先使用原生 `<audio controls>`。

---

## 十五、测试计划

新增测试：

```text
backend/tests/test_podcast_schema.py
backend/tests/test_podcast_prompts.py
backend/tests/test_podcast_validator.py
backend/tests/test_podcast_renderer.py
backend/tests/test_tts_service.py
```

扩展测试：

```text
backend/tests/test_content_type_profiles.py
backend/tests/test_api.py
backend/tests/test_assets.py
backend/tests/test_provider_services.py
```

重点用例：

| 测试 | 目标 |
|---|---|
| PodcastSpec enters ContentSpec union | schema union 可解析 |
| PodcastRenderModel enters RenderModel union | preview response 可解析 |
| podcast profile is registered | `podcast_script` direct mode 可路由 |
| prompt formats runtime variables | prompt 模板变量完整 |
| validator rejects unknown speaker | 禁止非 Person1 / Person2 |
| validator rejects forbidden TTS tags | 禁止 `<emphasis>` / `<say-as>` |
| validator requires opening phrase | 开场符合 `docs/output.txt` |
| validator requires voice mapping | Person1=Ethan, Person2=Cherry |
| tts service persists audio bytes | mock 响应能保存音频 asset |
| tts service uses qwen3 model | 请求模型为 `qwen3-tts-instruct-flash` |
| renderer creates manifest | render model 有分段音频和 manifest |
| API lifecycle | 任务创建、预览、导出跑通 |

建议验证命令：

```bash
uv run pytest backend/tests/test_podcast_schema.py backend/tests/test_podcast_validator.py backend/tests/test_tts_service.py -q
uv run pytest backend/tests/test_podcast_renderer.py backend/tests/test_content_type_profiles.py backend/tests/test_api.py -q
uv run python backend/scripts/export_json_schema.py
npm run build
```

---

## 十六、落地优先级

| 优先级 | 内容 | 目标 |
|---|---|---|
| P0 | schema / render model / element union | 后端能识别 podcast 数据结构 |
| P0 | profile 注册 | `podcast_script` 成为运行时支持内容类型 |
| P0 | prompt / generator / parser | 生成符合 `docs/output.txt` 的脚本 |
| P0 | validator | 在 TTS 前拦截格式和标签错误 |
| P0 | TTSService | 接入百炼 `qwen3-tts-instruct-flash`，固定 Ethan / Cherry |
| P0 | renderer | 输出脚本、分段音频和 manifest |
| P0 | direct_content_node 泛化 | social_post 和 podcast 共用 direct 节点 |
| P0 | API / schema export | 预览和任务响应可序列化 |
| P1 | frontend preview | 展示播客脚本和音频播放器 |
| P1 | markdown / audio export | 支持脚本和音频导出 |
| P1 | audio_segment_ready event | TTS 分段生成时前端可增量展示 |
| P2 | audio assembler | 生成单个完整音频文件 |
| P2 | segment retry | 单段 TTS 失败后可重试 |

---

## 十七、最小闭环

最小可交付闭环建议如下：

```text
用户提交 podcast_script
  -> retrieve_for_planning
  -> PodcastGenerator 生成 raw_dialogue
  -> PodcastValidator 校验 Person1 / Person2 格式
  -> PodcastRenderer 调 TTS 逐段生成音频
  -> 保存 audio_manifest.json
  -> 返回 PodcastRenderModel
  -> 前端展示脚本和分段 audio controls
  -> markdown 导出脚本
  -> audio 导出 manifest
```

这个闭环能证明三件事：

1. `direct workflow` 可以服务第二个非图文内容类型。
2. `ContentTypeProfile` 能承载 generator / validator / renderer 的进一步下沉。
3. 文本生成、TTS 生成、资产保存、预览和导出可以在同一任务生命周期里协作。

---

## 十八、风险与处理

| 风险 | 处理 |
|---|---|
| LLM 输出不符合 Person 标签 | 本地 parser + validator 拦截，必要时 repair |
| TTS 标签不兼容 | 只允许白名单标签，其他标签拒绝或清洗 |
| TTS 调用慢 | 分段生成，后续增加 `audio_segment_ready` 事件 |
| 单段 TTS 失败 | P0 任务失败并暴露 segment id；P1 增加重试 |
| 完整音频拼接不可靠 | P0 不拼接 mp3 bytes，只输出 manifest |
| direct node 分支膨胀 | 本阶段把 direct generator / validator / renderer 改为 registry 派发 |
| 真实 provider 失败被掩盖 | 沿用 social_post 策略，默认不静默 fallback |

---

## 十九、实施建议

建议下一步把本文档拆成实施计划，按 TDD 方式推进：

1. 先写 schema / profile 失败测试。
2. 实现 schema union 和 profile 注册。
3. 写 prompt / generator / parser 测试。
4. 实现 fallback generator 和 real generator。
5. 写 validator 测试。
6. 实现 TTS 白名单、voice mapping 和校验。
7. 写 TTSService mock 测试。
8. 实现百炼 TTS 调用和 asset 保存。
9. 写 renderer / API lifecycle 测试。
10. 实现 renderer、exporter、前端 preview。

完成 P0 后，`podcast_script` 应该能像 `social_post` 一样通过 direct workflow 创建任务、生成最终预览，并在任务记录中持久化 `content_spec`、`partial_render_model`、`render_model`、`stream_events` 和 debug artifacts。
