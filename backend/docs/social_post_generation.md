# Social Post / WeChat Article 生成说明

本文档描述 `social_post` 内容类型的当前实现。当前 `social_post` 只实现微信公众号文章，即：

```text
content_type = social_post
platform = wechat
subtype = wechat_article
```

## 1. 模块定位

`social_post` 生成链路用于将用户请求和知识库检索结果转成一篇适合微信公众号发布的技术型文章，并输出：

- `SocialPostSpec`
- WeChat article JSON
- HTML 预览
- 图片资源
- HTML 导出文件

当前实现采用 direct workflow，一次性生成文章 spec，不走 lecture / slide 的 unit-loop 流程。

## 2. 生成流程

```text
用户请求
  ↓
知识库检索 retrieve_for_planning
  ↓
generate_direct_content
  ├─ brief outline
  ├─ article draft
  ├─ image slot plan
  └─ image assets
  ↓
validate_direct_content
  ├─ pre-assets validation
  ├─ to_wechat_claw_article
  └─ final validation
  ↓
render_direct_content
  ├─ SocialPostRenderer
  ├─ WechatClawRenderer
  ├─ HTML
  └─ article JSON
  ↓
finalize_task
  ↓
POST /api/content-generation/tasks/{task_id}/export
  ↓
HTMLExporter
```

## 3. 相关文件

| 类型 | 路径 |
|---|---|
| 内容类型 profile | `app/content_types/social_post.py` |
| workflow 节点 | `app/workflows/nodes/direct_content_node.py` |
| generator | `app/generators/social_post_generator.py` |
| schema | `app/schemas/specs/social_post.py` |
| renderer | `app/renderers/social_post_renderer.py` |
| validator | `app/validators/social_post_validator.py` |
| HTML renderer 适配 | `app/services/wechat_claw_renderer.py` |
| HTML exporter | `app/exporters/html_exporter.py` |
| outline prompt | `app/prompts/planner/social_post_outline.md` |
| draft prompt | `app/prompts/generator/social_post_draft.md` |
| image prompt | `app/prompts/generator/social_post_image.md` |
| review prompt | `app/prompts/reviewer/social_post_review.md` |

## 4. ContentTypeProfile

`social_post` profile 当前配置：

| 字段 | 值 |
|---|---|
| `content_type` | `social_post` |
| `generation_mode` | `direct` |
| `unit_type` | `article` |
| `requires_outline` | `False` |
| `planner_prompt_name` | `social_post_outline.md` |
| `unit_spec_prompt_name` | `social_post_draft.md` |
| `spec_schema` | `SocialPostSpec` |
| `unit_spec_schema` | `SocialPostSpec` |
| `render_model_schema` | `SocialPostRenderModel` |
| `renderer_factory` | `SocialPostRenderer` |
| `generator_name` | `social_post` |
| `allowed_elements` | `image` |
| `exporter_types` | `html`, `image_assets` |

## 5. Schema 结构

### 5.1 SocialPostSpec

`SocialPostSpec` 是 social_post 的最终内容规格。

核心字段：

| 字段 | 说明 |
|---|---|
| `id` | spec ID。 |
| `type` | 固定为 `social_post`。 |
| `version` | 当前为 `content.spec/v1`。 |
| `platform` | 固定为 `wechat`。 |
| `subtype` | 固定为 `wechat_article`。 |
| `title` | 文章标题。 |
| `metadata` | 生成元数据。 |
| `outline` | `WechatBriefOutline`。 |
| `draft` | `WechatArticleDraft`。 |
| `image_slots` | 图片位规划。 |
| `image_assets` | 生成后的图片资源。 |
| `article_json` | 适配 wechat-claw renderer 的文章 JSON。 |
| `validation_report` | 本地校验结果。 |

### 5.2 WechatBriefOutline

用于约束文章的立意和结构。

关键字段：

| 字段 | 说明 |
|---|---|
| `topic` | 文章主题。 |
| `article_type` | 文章类型，例如概念解释、工程实践、论文解读、行业观察等。 |
| `target_audience` | 目标读者。 |
| `writing_angle` | 写作切入角度。 |
| `core_question` | 文章回答的核心问题。 |
| `central_thesis` | 中心论点。 |
| `reader_question_chain` | 读者问题链。 |
| `title_candidates` | 标题候选。 |
| `recommended_template` | `deep-analysis` / `industry-radar` / `studio-brief`。 |
| `sections` | 3-7 个文章段落规划。 |
| `image_strategy` | 配图策略。 |
| `risk_notes` | 风险提示。 |

### 5.3 WechatArticleDraft

用于承载可渲染文章草稿。

关键字段：

| 字段 | 说明 |
|---|---|
| `template` | 文章模板。 |
| `meta` | 标题、摘要、作者、封面图等。 |
| `headline` | 开头导语。 |
| `sections` | 正文段落。 |
| `conclusion` | 结尾总结。 |
| `cta` | 可选行动引导。 |
| `estimated_word_count` | 预计字数。 |
| `writing_notes` | 写作说明。 |

### 5.4 ImageSlot / ImageAsset

`ImageSlot` 描述文章需要什么图，`ImageAsset` 描述生成结果。

`ImageSlot` 关键字段：

| 字段 | 说明 |
|---|---|
| `slot_id` | 图片位 ID。 |
| `target` | 图片目标位置。 |
| `target_path` | 绑定到 article JSON 的路径。 |
| `required` | 是否必需。 |
| `aspect_ratio` | 图片比例。 |
| `caption` | 图片标题或说明。 |
| `visual_type` | 封面图、概念图、流程图、架构图、时间线等。 |
| `purpose` | 图片承担的表达目的。 |
| `context_summary` | 图片生成上下文。 |
| `prompt_en` | 英文图片生成 prompt。 |
| `negative_prompt_en` | 负向提示词。 |

`ImageAsset` 关键字段：

| 字段 | 说明 |
|---|---|
| `slot_id` | 对应图片位。 |
| `status` | `planned` / `generated` / `uploaded` / `failed`。 |
| `local_path` | 本地资源路径或 URL。 |
| `public_url` | 后端可访问 URL。 |
| `wechat_url` | 微信图床 URL，当前预留。 |
| `media_id` | 微信素材 ID，当前预留。 |
| `width` / `height` | 图片尺寸。 |
| `error_message` | 失败信息。 |

## 6. Prompt 分工

### 6.1 social_post_outline.md

目标：生成简要 outline。

输入：

- 用户请求
- generation options
- retrieved chunks

输出：

- `WechatBriefOutline`

要求：

- 明确文章类型和写作角度。
- 给出核心问题、中心论点和读者问题链。
- 规划 3-7 个正文 section。
- 每个 section 需要绑定 evidence refs。
- 给出标题候选和配图策略。

### 6.2 social_post_draft.md

目标：根据 outline 生成微信公众号文章草稿。

输入：

- 用户请求
- generation options
- retrieved chunks
- outline JSON

输出：

- `WechatArticleDraft`

要求：

- 文章风格贴近知识技术型公众号推文。
- 开头提出明确问题或判断。
- 正文按 section 展开，每节有清晰观点和证据。
- 避免空泛口号，优先使用可解释、可落地的技术表达。
- 标题和摘要满足微信限制。

### 6.3 social_post_image.md

目标：根据文章草稿规划图片位。

输入：

- 用户请求
- generation options
- draft JSON

输出：

- `ImageSlotPlan`

要求：

- 至少规划一张封面或头图。
- 根据文章内容选择概念图、流程图、架构图、时间线或编辑插画。
- 图片 prompt 使用英文。
- 避免小字堆叠、复杂思维导图、随机 logo 和水印。

## 7. 图片生成策略

`SocialPostGenerator._generate_image_assets(...)` 根据 `image_slots` 逐个调用图片服务。

当前规则：

1. `generation_options.include_images=false` 时不生成图片。
2. 每个 `ImageSlot` 转换为一次图片生成调用。
3. 图片生成结果保存为本地 asset，并写入 `ImageAsset.public_url`。
4. 必需图片失败时记录 failed asset，并停止后续必需图片链路。
5. stub 模式下生成本地 SVG 占位图，便于本地闭环测试。

## 8. 渲染与导出

### 8.1 Article JSON 转换

`to_wechat_claw_article(spec)` 会将 `SocialPostSpec` 转为 wechat-claw renderer 可消费的 article JSON：

1. 复制 `draft.template`、`draft.meta`、`draft.headline`、`draft.sections`、`draft.conclusion`、`draft.cta`。
2. 根据 `image_slots` 和 `image_assets` 绑定图片。
3. 移除内部字段，例如 `section_id`、`citation_refs`、`writing_notes`、`estimated_word_count`。

### 8.2 SocialPostRenderer

`SocialPostRenderer` 调用 `WechatClawRenderer` 输出 `SocialPostRenderModel`。

`SocialPostRenderModel` 包含：

| 字段 | 说明 |
|---|---|
| `render_type` | 固定为 `social_post`。 |
| `platform` | 固定为 `wechat`。 |
| `subtype` | 固定为 `wechat_article`。 |
| `title` | 文章标题。 |
| `digest` | 文章摘要。 |
| `template` | 使用的模板。 |
| `html` | 文章 HTML。 |
| `article_json` | 渲染输入 JSON。 |
| `preview_assets` | 预览图片资源。 |
| `export_files` | 渲染或导出文件。 |
| `warnings` | 图片缺失等警告。 |

### 8.3 HTMLExporter

`HTMLExporter` 只支持 `SocialPostRenderModel`。

导出时会保存：

- `{task_id}.html`
- `{task_id}.json`

返回结果中的 `file_url` 指向 HTML 文件下载地址，`metadata.article_json_asset_id` 指向 article JSON asset。

## 9. Validator 职责

`SocialPostValidator` 负责校验：

1. `SocialPostSpec` 结构完整。
2. outline、draft、image_slots、image_assets 之间能对应。
3. 文章 section 数量、block 数量、标题、摘要满足 schema 约束。
4. 引用信息能够追溯到检索 chunk。
5. 必需图片缺失时给出 error 或 warning。
6. HTML 和 article JSON 生成后再次执行 final validation。

## 10. 当前边界

- 当前只支持微信公众号文章。
- 当前没有实现微信素材上传，`wechat_url` 和 `media_id` 仍是预留字段。
- 当前 HTML 渲染使用本地 wechat-claw renderer 适配层。
- 当前图片生成以本地 asset URL 绑定到文章 JSON。
- 当前不支持多平台 social post 复用同一 spec。

## 11. 后续开发建议

1. 将 wechat-claw renderer 的模板能力整理成稳定的本地服务接口。
2. 增加文章 HTML 的视觉检查和结构检查。
3. 增加微信素材上传服务，回填 `wechat_url`、`media_id`、`thumb_media_id`。
4. 将 `social_post_review.md` 接入 LLM reviewer 或 repair 流程。
5. 增加 `article_type` 到 prompt 和模板选择的显式映射。
6. 增加封面图、正文图的尺寸和安全区域约束。
7. 增加导出 zip，包含 HTML、article JSON、图片和 manifest。
