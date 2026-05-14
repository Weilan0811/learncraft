# Content Generation Refactor Progress

本文档基于 `docs/improve.md` 和当前工作区改动，记录已经完成的重构内容与后续待办事项。

## 已完成内容

### 第一阶段：生成底座解耦

已完成“通用生成内核 + Content Type Profile”底座改造。

- 将后端 schema 边界从 `MvpContentType` 扩展为更开放的 `ContentType`。
- 新增 `backend/app/content_types/`：
  - `base.py`
  - `registry.py`
  - `lecture.py`
  - `slide_deck.py`
  - `__init__.py`
- 当前注册并支持的 profile：
  - `lecture`
  - `slide_deck`
- 将 lecture / slide_deck 的 unit 类型、prompt 名称、spec schema、render schema、renderer factory、generator 名称等信息放入 profile。
- 将 planner、unit generator、assembler、renderer router 中的部分内容类型判断收敛到 profile registry。
- 保持现有 lecture / slide_deck 业务能力不变。

### 第一阶段补充：目录结构重组

已进行受控目录重组，便于后续人工审查和维护。

- 将原 `backend/app/schemas/specs.py` 拆分为：
  - `backend/app/schemas/specs/common.py`
  - `backend/app/schemas/specs/lecture.py`
  - `backend/app/schemas/specs/slide.py`
  - `backend/app/schemas/specs/__init__.py`
- 将原 `backend/app/schemas/render.py` 拆分为：
  - `backend/app/schemas/render/lecture.py`
  - `backend/app/schemas/render/slide.py`
  - `backend/app/schemas/render/__init__.py`
- 将原 `backend/app/schemas/elements.py` 拆分为：
  - `backend/app/schemas/elements/common.py`
  - `backend/app/schemas/elements/visual.py`
  - `backend/app/schemas/elements/learning.py`
  - `backend/app/schemas/elements/__init__.py`
- 通过 package `__init__.py` 保持原有导入方式兼容，例如 `from app.schemas.specs import LectureSpec`。

### 第一阶段补充：生成日志增强

已完善生成过程日志，方便后续维护排查。

- 新增结构化 workflow log entry。
- `ContentGenerationState.logs` 改为结构化日志列表。
- 生成过程会记录任务开始、节点完成、任务完成、任务失败等事件。
- 日志会持久化到数据库任务记录。
- 同时写入任务级 JSONL 文件：
  - `storage/logs/content-generation/{task_id}.log`
- 新增数据库迁移：
  - `backend/alembic/versions/20260511_0002_add_task_logs.py`

### 第二阶段：unit 级 render

已完成 unit 级渲染主链路。

- 新增 workflow 节点：
  - `backend/app/workflows/nodes/unit_renderer_node.py`
  - `backend/app/workflows/nodes/publish_event_node.py`
- workflow unit loop 已从：

```text
validate_unit -> merge_unit_result
```

调整为：

```text
validate_unit -> render_unit -> publish_unit_render -> merge_unit_result
```

- `LectureRenderer` 已支持：
  - `render_unit(...)`
  - `assemble(...)`
  - 原 `render(...)` 兼容保留
- `SlideRenderer` 已支持：
  - `render_unit(...)`
  - `assemble(...)`
  - 原 `render(...)` 兼容保留
- 每个 lecture section / slide page 完成后可生成独立 render fragment。

### 第三阶段：partial preview 与任务持久化

已完成部分结果持久化和轮询式流式接口。

- `ContentGenerationState` 新增：
  - `render_units`
  - `partial_render_model`
  - `stream_events`
- 新增 schema：
  - `RenderUnitSnapshot`
  - `TaskStreamEvent`
- `ContentGenerationTask` 新增持久化字段：
  - `outline`
  - `unit_results`
  - `render_units`
  - `partial_render_model`
  - `stream_events`
- 新增数据库迁移：
  - `backend/alembic/versions/20260511_0003_add_streaming_snapshots.py`
- `SQLModelTaskRepository.save_state()` 会保存 outline、unit results、render units、partial preview 和 stream events。
- 新增 API：
  - `GET /api/content-generation/tasks/{task_id}/events`
  - `GET /api/content-generation/tasks/{task_id}/preview/partial`
  - `GET /api/content-generation/tasks/{task_id}/units`
  - `GET /api/content-generation/tasks/{task_id}/units/{unit_id}/preview`
- `backend/scripts/export_json_schema.py` 已加入新增 response schema 导出。

### 前端流式展示

已完成前端对 partial preview 的基础展示支持。

- `frontend/src/api/contentGenerationApi.ts` 新增：
  - `getContentGenerationEvents`
  - `getContentGenerationPartialPreview`
  - `getContentGenerationUnits`
- `frontend/src/types/export.ts` 新增：
  - `PartialPreviewResponse`
  - `TaskStreamEvent`
  - `RenderUnitSnapshot`
  - `TaskEventsResponse`
  - `TaskUnitsResponse`
- `frontend/src/stores/contentGenerationStore.ts` 在任务轮询过程中同步拉取：
  - stream events
  - render units
  - partial preview
- `frontend/src/pages/ContentPreviewPage.tsx` 优先展示 partial preview，任务完成后展示 final preview。
- `frontend/src/components/generation/GenerationProgress.tsx` 增加已渲染 unit 数和最新事件展示。
- `frontend/src/components/generation/ExportActions.tsx` 调整为任务完成后才允许导出。

### 第四阶段：接入 social_post

已完成 `social_post` 内容类型接入，用于验证 direct workflow。

- 新增 social post 规格 schema：
  - `WechatBriefOutline`
  - `WechatArticleDraft`
  - `ImageSlotPlan`
  - `SocialPostSpec`
  - `SocialPostValidationReport`
- 新增 social post render schema：
  - `SocialPostRenderModel`
  - `SocialPostPreviewAsset`
  - `SocialPostExportFile`
- 新增 `SocialPostProfile`，并注册到 content type registry。
- 新增 direct path workflow：

```text
retrieve_for_planning
  -> route_generation_mode
  -> generate_direct_content
  -> validate_direct_content
  -> render_direct_content
  -> finalize_task
```

- `social_post` 已从 outline + unit loop 中独立出来，走单篇文章 direct workflow。
- 新增 `SocialPostGenerator`：
  - real provider 模式下按 outline、draft、image slot plan 三步结构化生成。
  - stub 模式下生成可用于本地开发和测试的 fallback 文章。
  - 对缺失的 `citation_refs` 做规范化补齐。
  - 将微信封面推荐比例 `2.35:1` 映射为当前图片 provider 支持的 `21:9` 生成比例。
- 新增 `SocialPostValidator`：
  - 校验标题、摘要、section 数量、section 引用、图片 slot、图片 asset 绑定。
  - final validation 不再重复合并 pre validation issue，避免前端重复展示同一错误。
- 新增 `SocialPostRenderer`：
  - 将内部 `SocialPostSpec` 转换为 wechat-claw article JSON。
  - 渲染微信公众号 HTML 预览。
  - 回填 cover、headline、section 图片。
  - 输出 HTML 和 article JSON 文件。
- 新增 HTML exporter 对 `social_post` 的支持。
- 新增 image assets exporter 对任务图片资产的打包支持。
- 前端已支持 `social_post` 任务创建、轮询、HTML preview 和导出入口。

### 第四阶段补充：social_post 真实生成可观测性

已针对 social post direct workflow 增强失败定位能力。

- real provider 模式下，LLM 生成失败不再静默 fallback。
- LLM 生成失败会暴露具体阶段：
  - `social_post_outline_generation`
  - `social_post_draft_generation`
  - `social_post_image_plan_generation`
- 如果需要 fallback，必须通过 `generation_options.allow_fallback=true` 显式允许。
- fallback 产物会在 metadata 中记录：
  - `generation_mode`
  - `fallback_reason`
- 新增 workflow debug artifact 输出：
  - `storage/debug_workflow/{task_id}/trace.json`
  - `storage/debug_workflow/{task_id}/steps/*.json`
  - `storage/debug_workflow/{task_id}/final_state.json`
  - `storage/debug_workflow/{task_id}/content_spec.json`
  - `storage/debug_workflow/{task_id}/render_model.json`
  - `storage/debug_workflow/{task_id}/elements.json`
  - `storage/debug_workflow/{task_id}/generated_assets.json`
- 普通任务日志会记录对应 step artifact 路径，便于从 JSONL 日志跳转到完整中间产物。
- KB 检索为空或异常时会记录 `workflow_errors`，包含 query 摘要、状态、chunk 数和错误信息。
- LLM schema repair 失败时会在错误信息中包含 schema 名和 validation errors。

### 第四阶段当前边界：微信发布暂缓

当前 social post 已支持本地预览和导出，但尚未接入微信公众号发布链路。

- 本地预览使用 `/api/assets/{asset_id}/download` 图片地址。
- wechat-claw 会提示：
  - `meta.thumb_media_id is missing`
  - content image URL does not look like WeChat CDN
- 这些提示属于发布前 warning，不影响本地 HTML preview。
- 暂不处理微信素材上传、`thumb_media_id` 回填和正文图片 CDN URL 回填。

## 已验证内容

已运行以下验证：

```bash
uv run pytest backend/tests/test_workflow_logs.py backend/tests/test_social_post_prompts.py::test_social_post_real_mode_llm_failure_is_not_silent_fallback backend/tests/test_social_post_prompts.py::test_social_post_real_mode_generator_uses_structured_prompt_sequence backend/tests/test_social_post_prompts.py::test_social_post_real_mode_normalizes_missing_citations_and_provider_cover_ratio -q
```

结果：

```text
6 passed, 1 warning
```

```bash
uv run pytest backend/tests/test_workflow_logs.py backend/tests/test_social_post_validator.py backend/tests/test_social_post_renderer.py backend/tests/test_api.py::test_social_post_task_lifecycle_exposes_html_preview_and_export -q
```

结果：

```text
11 passed, 1 warning
```

```bash
uv run pytest backend/tests/test_social_post_prompts.py -q
```

结果：

```text
4 passed, 1 failed
```

失败项为既有 prompt 文案测试：`test_social_post_prompts_embed_wechat_writing_standards` 要求 prompt 文件包含 `docs/general.md` 字样，当前 prompt 文件未包含该文本。

## 待办事项

### 第五阶段：接入 podcast

播客仍未接入。

- 建议确认内容类型命名：`podcast` 还是沿用 `podcast_script`。
- 新增 `PodcastSpec`
- 新增 `PodcastSegmentSpec`
- 新增 `PodcastRenderModel`
- 新增 `AudioScriptElement`
- 新增 `AudioFileElement`
- 新增 `TTSService`
- 新增 `PodcastProfile`
- 新增 `PodcastGenerator`
- 新增 `PodcastValidator`
- 新增 `PodcastRenderer`
- 新增 workflow 节点：
  - `tts_node.py`
  - `audio_assembler_node.py`
- 支持文本脚本片段流式输出，再支持音频片段输出。

### 第六阶段：强化教材和 PPT

教材增强待办：

- 增加 `InteractiveElement`
- 增加 quiz / reflection / drag_sort / fill_blank / case_analysis / code_exercise 等交互类型。
- 扩展 lecture block 类型，支持可交互 block。
- 更新 lecture profile 的 element policy。
- 前端增加交互式 block 渲染组件。

PPT 增强待办：

- 新增 `SlideSpecValidator`
- 新增 `SlideLayoutValidator`
- 新增 `SlideRenderValidator`
- 支持 slide spec repair。
- 支持布局 downgrade / fallback。
- 在每页生成后立即做页面级质量校验。
- 前端补充页级错误状态展示。

### Workflow kernel 继续解耦

当前主图已支持 unit path 和 direct path。后续应继续推进：

- 将 generator / validator / renderer strategy 进一步放入 profile。
- 将 lecture / slide_deck 的剩余分支继续向 profile 或 strategy 下沉。
- 为未来 `podcast`、`video_script` 避免继续污染主图。

### 事件流能力增强

当前前端采用轮询 JSON 接口，尚未实现 SSE / WebSocket。

- 可新增 `GET /tasks/{task_id}/events/stream`。
- 支持按 `last_event_id` 增量拉取 events。
- 增加事件去重和事件序号。
- 前端 store 可从全量轮询改为增量拉取或 SSE。
- 支持任务失败时实时显示失败节点、错误详情和恢复建议。

### 日志与可观测性增强

当前已有结构化日志和 debug artifact，但还可继续增强：

- 记录每个节点耗时。
- 记录 LLM prompt 摘要、模型名、token usage。
- 记录元素生成重试次数和 fallback 原因。
- 增加日志下载接口。
- 增加 task detail 页面中的日志查看面板。
- 前端增加 debug artifact 链接或结构化日志查看入口。

### 微信发布链路

social post 当前只做到本地预览和导出，发布功能暂缓。

- 接入微信素材上传。
- cover 上传后回填 `meta.thumb_media_id`。
- headline / section 图片上传后回填微信 CDN URL。
- 增加 publish-ready validation。
- 增加发布前检查和发布失败日志。

### 数据库与迁移

已新增 logs 和 streaming snapshots 迁移，但还需要生产级确认。

- 在 MySQL 环境验证 `20260511_0002_add_task_logs.py`。
- 在 MySQL 环境验证 `20260511_0003_add_streaming_snapshots.py`。
- 评估 JSON 字段大小和索引策略。
- 对历史任务数据补默认值。

### 前端体验待办

- 当前 partial preview 是轮询式更新，后续可以优化为增量事件驱动。
- 增加“正在生成第 N 页 / 第 N 节”的更清晰状态。
- 对 slide / lecture 增加 unit 列表导航。
- 对失败 unit 增加错误提示和重试入口。
- 对 partial preview 和 final preview 增加明显状态标识。
- 解决当前部分中文文案存在乱码的问题。

### 测试待办

- 修复 `test_social_post_prompts_embed_wechat_writing_standards` 与当前 prompt 文案之间的不一致。
- 为前端 store 增加测试框架和单元测试。
- 为 partial preview UI 增加组件测试。
- 为 API 增加 events 增量查询测试。
- 为数据库迁移增加 MySQL 集成验证。
- 增加真实 provider 模式下的慢任务流式输出测试。
- 增加真实 social post provider 生成的慢任务回归测试。

## 当前注意事项

- 当前 social post 预览阶段仍会出现微信发布相关 warning，原因是尚未上传图片到微信素材库。
- 当前 real provider 模式下默认不再静默 fallback；如需保留 fallback，需显式传入 `generation_options.allow_fallback=true`。
- 当前 debug artifact 会写入 `storage/debug_workflow/{task_id}`，需要评估长期存储清理策略。
