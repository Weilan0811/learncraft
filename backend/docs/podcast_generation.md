# Podcast 生成说明

本文档描述 `podcast_script` 内容类型的当前实现。当前 `podcast_script` 用于生成中文双人播客脚本和音频，即：

```text
content_type = podcast_script
speaker = Person1 / Person2
voice = Ethan / Cherry
```

## 1. 模块定位

`podcast_script` 生成链路用于将用户请求和知识库检索结果转成一段适合 TTS 播放的中文双人播客，并输出：

- `PodcastSpec`
- 结构化对话轮次
- 分段音频
- audio manifest
- 完整音频
- Markdown 脚本导出
- Audio 导出文件

当前实现采用 direct workflow，一次性生成完整播客 spec，不走 lecture / slide 的 unit-loop 流程。

## 2. 生成流程

```text
用户请求
  ↓
知识库检索 retrieve_for_planning
  ↓
generate_direct_content
  ├─ PodcastGenerator
  ├─ PodcastDialogueDraft
  ├─ raw_dialogue normalize
  └─ dialogue segments
  ↓
validate_direct_content
  ├─ speaker tag validation
  ├─ opening validation
  ├─ turn / challenge validation
  └─ voice mapping validation
  ↓
render_direct_content
  ├─ PodcastRenderer
  ├─ TTSService
  ├─ audio_segment_ready events
  ├─ AudioAssemblerService
  ├─ audio_manifest.json
  └─ final audio
  ↓
finalize_task
  ↓
POST /api/content-generation/tasks/{task_id}/export
  ↓
MarkdownExporter / AudioExporter
```

## 3. 相关文件

| 类型 | 路径 |
|---|---|
| 内容类型 profile | `app/content_types/podcast.py` |
| workflow 节点 | `app/workflows/nodes/direct_content_node.py` |
| generator | `app/generators/podcast_generator.py` |
| schema | `app/schemas/specs/podcast.py` |
| render schema | `app/schemas/render/podcast.py` |
| audio element schema | `app/schemas/elements/audio.py` |
| renderer | `app/renderers/podcast_renderer.py` |
| validator | `app/validators/podcast_validator.py` |
| TTS service | `app/services/tts_service.py` |
| audio assembler | `app/services/audio_assembler_service.py` |
| audio exporter | `app/exporters/audio_exporter.py` |
| prompt | `app/prompts/generator/podcast_script.md` |

## 4. ContentTypeProfile

`podcast_script` profile 当前配置：

| 字段 | 值 |
|---|---|
| `content_type` | `podcast_script` |
| `generation_mode` | `direct` |
| `unit_type` | `podcast` |
| `requires_outline` | `False` |
| `unit_spec_prompt_name` | `podcast_script.md` |
| `spec_schema` | `PodcastSpec` |
| `unit_spec_schema` | `PodcastSpec` |
| `render_model_schema` | `PodcastRenderModel` |
| `renderer_factory` | `PodcastRenderer` |
| `generator_name` | `podcast` |
| `allowed_elements` | `audio_script`, `audio_file` |
| `exporter_types` | `markdown`, `audio` |

## 5. Schema 结构

### 5.1 PodcastSpec

`PodcastSpec` 是播客的最终内容规格。

核心字段：

| 字段 | 说明 |
|---|---|
| `id` | spec ID。 |
| `type` | 固定为 `podcast_script`。 |
| `content_type` | 固定为 `podcast_script`。 |
| `title` | 播客标题。 |
| `podcast_name` | 播客名称，默认用于开场。 |
| `podcast_tagline` | 播客标语，默认用于开场。 |
| `voice_config` | `Person1` / `Person2` 音色映射。 |
| `raw_dialogue` | 原始对话脚本，保留 speaker tag。 |
| `segments` | 解析后的 TTS 分段。 |
| `validation_report` | 本地校验结果。 |

### 5.2 PodcastSegmentSpec

`PodcastSegmentSpec` 是单个说话轮次。

| 字段 | 说明 |
|---|---|
| `segment_id` | 分段 ID，例如 `seg-001`。 |
| `order` | 播放顺序。 |
| `speaker` | `Person1` 或 `Person2`。 |
| `voice` | `Ethan` 或 `Cherry`。 |
| `text` | 清洗后的 TTS 文本。 |
| `ssml_text` | 原始带 TTS 标签文本。 |
| `citation_refs` | 引用 chunk ID。 |

### 5.3 PodcastRenderModel

`PodcastRenderModel` 是前端预览和导出的核心模型。

| 字段 | 说明 |
|---|---|
| `render_type` | 固定为 `podcast_script`。 |
| `title` | 播客标题。 |
| `script_text` | 完整脚本。 |
| `segments` | 分段音频状态。 |
| `audio_assets` | 保存后的音频 asset。 |
| `audio_manifest_url` | manifest 下载 URL。 |
| `final_audio_url` | 完整音频下载 URL。 |
| `warnings` | 渲染警告。 |

## 6. Prompt 与解析

`podcast_script.md` 输出 `PodcastDialogueDraft` JSON。核心约束：

- 只使用 `Person1` 和 `Person2`。
- 第一段由 `Person1` 开场。
- 对话必须围绕输入内容展开。
- 至少包含一次温和质疑、追问、补充或保留意见。
- 句子适合朗读。
- 禁止 Amazon / Alexa 专属 TTS 标签。

`PodcastGenerator` 会在生成后做确定性解析和规范化：

- 支持 `<Person1>...</Person1>` / `<Person2>...</Person2>`。
- 支持 HTML escaped speaker tag。
- 支持 `Person1:` / `Person2：` 行式格式。
- 规范化开场为 `欢迎来到 {podcast_name} —— {podcast_tagline}。`。
- 将 `Person1` 映射为 `Ethan`，`Person2` 映射为 `Cherry`。

## 7. TTS 与音频生成

当前 TTS 配置：

| 角色 | speaker | voice |
|---|---|---|
| 男声主持 | `Person1` | `Ethan` |
| 女声搭档 | `Person2` | `Cherry` |

real provider 模式下：

- 文本生成使用当前配置的文本服务，可选择百炼或 DeepSeek；语音生成单独使用百炼。
- TTS 使用 DashScope 多模态生成接口。
- `BailianTTSService` 先请求 `qwen3-tts-flash` 获取音频 URL，再下载音频 bytes。
- 音频 bytes 通过 `LocalStorageService.save_bytes(...)` 保存为 `audio` asset。
- `PodcastRenderer` 只把清洗后的 `segment.text` 传入 TTS，避免把不兼容标签直接送入语音接口。

相关环境变量：

| 环境变量 | 默认值 |
|---|---|
| `CONTENT_GENERATOR_TTS_PROVIDER` | `bailian` |
| `CONTENT_GENERATOR_TTS_MODEL` | `qwen3-tts-flash` |
| `CONTENT_GENERATOR_TTS_PERSON1_VOICE` | `Ethan` |
| `CONTENT_GENERATOR_TTS_PERSON2_VOICE` | `Cherry` |
| `CONTENT_GENERATOR_TTS_OUTPUT_FORMAT` | `mp3` |
| `CONTENT_GENERATOR_BAILIAN_TTS_BASE_URL` | `https://dashscope.aliyuncs.com` |
| `CONTENT_GENERATOR_PODCAST_SEGMENT_MAX_RETRIES` | `1` |
| `CONTENT_GENERATOR_PODCAST_SEGMENT_RETRY_DELAY_SECONDS` | `10` |

## 8. 重试与完整音频

`PodcastRenderer` 以有限并发生成语音分段，并按原稿顺序整理结果。并发数由 `CONTENT_GENERATOR_TTS_GENERATION_CONCURRENCY` 控制，默认 4。

- 单段失败后按 `CONTENT_GENERATOR_PODCAST_SEGMENT_MAX_RETRIES` 重试。
- 每次 retry 前等待 `CONTENT_GENERATOR_PODCAST_SEGMENT_RETRY_DELAY_SECONDS` 秒。
- segment 成功后会记录 `retry_count`。
- 每个成功分段会触发 `audio_segment_ready` 事件。

所有分段生成成功后，`AudioAssemblerService` 生成完整音频：

- 使用 ffmpeg 按原稿顺序解码并重新编码分段，统一为 24 kHz 单声道。
- 根据输出配置生成 WAV 或 MP3；默认使用 `imageio-ffmpeg` 附带的程序，也可以通过 `CONTENT_GENERATOR_FFMPEG_BINARY` 指定路径。合成失败时保留分段并报告错误。
- 完整音频写入 `final_audio_url`。
- `audio_manifest.json` 始终保存，记录分段状态和完整音频 URL。

## 9. 导出

当前支持：

| export_type | 行为 |
|---|---|
| `markdown` | 导出播客脚本。 |
| `audio` | 优先返回完整音频；完整音频不存在时回退 audio manifest。 |

## 10. 测试

常用测试：

```bash
pytest tests/test_tts_service.py tests/test_podcast_renderer.py tests/test_podcast_schema.py tests/test_podcast_validator.py tests/test_podcast_api.py tests/test_podcast_prompts.py tests/test_podcast_parser.py -q
```

覆盖重点：

1. `PodcastSpec` 和 `PodcastRenderModel` 进入 union。
2. profile 注册和 direct routing。
3. prompt 模板变量完整。
4. 对话解析、开场规范化和 voice mapping。
5. pre-render / final-render validation。
6. 百炼 TTS payload、音频下载和 asset 保存。
7. segment retry、retry delay 和完整音频生成。
8. API lifecycle、preview、events 和 export。
