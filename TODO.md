# TODO 汇总

本文档汇总当前代码中根据 `docs/PRD.md` MVP 要求与 `docs/introduction.md` 预留接口补充的 TODO 项。行号会随代码变更漂移，以下位置以当前版本为准。

## 后端 API 与配置

| 状态 | 优先级 | 位置 | TODO 内容 |
|---|---|---|---|
| [x] | MVP-assets | `backend/app/api/assets.py:12` | Local 资源元数据、下载 URL 和 not-found 处理已实现；OSS/S3 与签名 URL 后续扩展。 |
| [ ] | MVP-task | `backend/app/api/content_generation.py:15` | 将同步内存任务执行替换为异步任务执行，使 queued/running/completed 反映真实进度。 |
| [ ] | MVP-task | `backend/app/api/content_generation.py:22` | 查询任务时返回节点级进度，例如 retrieving、planning、generating、rendering。 |
| [ ] | MVP-preview | `backend/app/api/content_generation.py:32` | 预览接口读取持久化 render_model 快照，支持进程重启后的重复访问和后续编辑/再生成。 |
| [x] | MVP-export | `backend/app/api/content_generation.py:42` | 根据 export_type 路由到 Local PDF/Slide JSON/资源包 exporter，并返回可下载存储 URL。 |
| [x] | MVP-config | `backend/app/core/config.py:10` | 已增加文本、图片、embedding provider/model 配置，支持 APIMart、百炼、Qdrant 与本地存储关键参数；对象存储和异步任务队列后续扩展。 |

## 后端 Schema

| 状态 | 优先级 | 位置 | TODO 内容 |
|---|---|---|---|
| [ ] | schema-extension | `backend/app/schemas/base.py:16` | 启用非 MVP 内容类型时，同步新增 Spec、Renderer、导出格式映射、前端类型和 workflow route。 |
| [ ] | export-extension | `backend/app/schemas/base.py:37` | 生产环境中仅允许已有具体 exporter 实现的导出格式。 |
| [ ] | MVP-options | `backend/app/schemas/request.py:13` | 增加受众、时长/slide 数、图片风格、引用策略、PDF 选项、Slide 主题选项。 |
| [ ] | MVP-request | `backend/app/schemas/request.py:24` | 按 content_type 校验 generation options，例如 lecture 时长、slide_deck 页数和主题配置。 |
| [x] | MVP-image | `backend/app/schemas/elements.py:26` | ImageElement 已增加 width、height、format、model、retry_count、source_unit_id、source_outline_unit_id、source_chunk_ids 与 generation_info；真实 provider 参数细化后续随生成器接入完善。 |
| [ ] | P1-mindmap | `backend/app/schemas/elements.py:44` | 为思维导图记录生成后的 SVG/PNG asset URL，供 PDF 和 Slide 嵌入。 |
| [ ] | MVP-pdf | `backend/app/schemas/render.py:29` | 将 printable_model dict 替换为 typed print/PDF model，覆盖目录、页边距、页眉和引用。 |
| [ ] | MVP-slide-render | `backend/app/schemas/render.py:36` | 将 Slide page dict 替换为 scene-content-kit 官方 page schema。 |
| [-] | MVP-lecture | `backend/app/schemas/specs.py:43` | LectureSection 已增加 outline_unit_id、learning_goal、source_chunk_ids 与分节 required_elements；LectureSpec 级总结、引用和可编辑版本元数据待补。 |
| [-] | MVP-slide | `backend/app/schemas/specs.py:70` | SlideSpecPage 已增加 outline_unit_id、speaker_notes、source_chunk_ids 与 required_elements；deck theme、slide count 与 asset dependency 声明待补。 |
| [ ] | content-types | `backend/app/schemas/specs.py:75` | 启用 social_post、podcast_script、video_script、project_task、quiz_pack、learning_path 时扩展 ContentSpec union。 |
| [-] | MVP-observability | `backend/app/schemas/state.py:36` | 工作流状态已增加 current_node、progress、unit_results、element_status、workflow_errors 等结构；node timings、完整 retry records 与 API 暴露待补。 |

## 后端 Services

| 状态 | 优先级 | 位置 | TODO 内容 |
|---|---|---|---|
| [x] | MVP-assets | `backend/app/services/asset_service.py:12` | 查询 Local 资源记录，为图片、PDF、Slide JSON 和资源包返回公开下载 URL。 |
| [ ] | P1-citations | `backend/app/services/citation_service.py:7` | 引用去重，保留 page/section 元数据，并格式化为讲义、PDF、Slide 视图可用结构。 |
| [x] | MVP-image | `backend/app/services/image_generation_service.py:14` | 已实现 APIMart GPT-Image-2 默认图片 provider、百炼图片 provider、任务轮询、图片下载落盘和 metadata 记录；workflow 接入后续完成。 |
| [x] | MVP-llm | `backend/app/services/llm_service.py:20` | 已实现百炼兼容 OpenAI 结构化输出调用、重试、超时、token usage 记录和 schema repair；workflow 接入后续完成。 |
| [x] | MVP-retriever | `backend/app/services/rag_service.py:15` | 已实现百炼 embedding 与 `langchain_qdrant` 检索 service，支持单知识库、去重、排序、字符限制和来源 metadata；知识库构建与 workflow 二次检索后续完成。 |
| [x] | MVP-storage | `backend/app/services/storage_service.py:12` | 将 bytes 保存到 local storage，并返回前端可消费 URL；OSS/S3-compatible storage 后续扩展。 |
| [ ] | MVP-task | `backend/app/services/task_service.py:13` | 将任务持久化到数据库，并通过 BackgroundTasks/Celery/Arq 派发 workflow。 |
| [ ] | MVP-preview | `backend/app/services/task_service.py:38` | 从持久化 render snapshot 加载 preview，保证服务重启后任务结果可访问。 |
| [x] | MVP-export | `backend/app/services/task_service.py:44` | 根据 stored render_model 调用对应 exporter，并持久化导出文件资源。 |

## 后端 Workflow

| 状态 | 优先级 | 位置 | TODO 内容 |
|---|---|---|---|
| [x] | MVP-workflow | `backend/app/workflows/content_generation_graph.py:14` | 已替换为已编译的 LangGraph StateGraph；`run_content_generation` 保持同步入口并调用 compiled graph。 |
| [-] | MVP-retriever | `backend/app/workflows/nodes/retriever_node.py` | 已支持 planning/generation 两阶段检索，并在 unit 阶段传入 section_hint；reviewer 阶段待真实评审链路接入。 |
| [ ] | MVP-planner | `backend/app/workflows/nodes/planner_node.py` | 下一步：接入 LLM 生成 lecture/slide outline，并通过 Outline schema、引用覆盖和 repair prompt 校验。 |
| [-] | MVP-slide-generator | `backend/app/generators/unit_spec_generators.py` | 已生成 SlideSpecPage、视觉布局、speaker notes、required image/mindmap 与引用来源；多页标题/内容/总结结构和 LLM 生成待补。 |
| [-] | MVP-lecture-generator | `backend/app/generators/unit_spec_generators.py` | 已生成 LectureSection、目标、摘要、文本块、required image/mindmap 与来源引用；完整 LLM 正文、总结和引用策略待补。 |
| [x] | MVP-elements | `backend/app/workflows/nodes/element_flow_node.py` | 已使用 LangGraph Send 并行分发 image/mindmap worker，并在同一 element flow 模块内按 element id 合并全局资产。 |
| [-] | MVP-validator | `backend/app/workflows/nodes/validator_node.py` | 已校验 outline/unit spec/content spec 闭合与 required element 存在；引用覆盖质量、内容质量和 repair 路径待补。 |
| [-] | MVP-renderer | `backend/app/workflows/nodes/renderer_node.py` | 已按 content_type 路由 typed renderer；render snapshot 持久化与预览/导出复用待任务持久化后补齐。 |
| [x] | workflow-structure | `backend/app/workflows/nodes/` | workflow 节点已从 graph 文件拆分到 focused node modules；已移除旧兼容壳文件，并将元素 fan-out/fan-in 合并到 `element_flow_node.py`、unit loop 合并到 `unit_loop_node.py`。 |
| [ ] | MVP-export | `backend/app/services/task_service.py:40` | 将长耗时导出交给异步 worker，并按 export_type 追踪导出状态、重试和下载 URL。 |
| [ ] | content-router | `backend/app/workflows/routers.py:9` | 内容类型增加后，用 mapping 或 plugin-style registry 注册 renderer。 |
| [x] | export-router | `backend/app/workflows/routers.py:23` | 按显式 export_type 路由 exporter。 |

## 后端 Renderers 与 Exporters

| 状态 | 优先级 | 位置 | TODO 内容 |
|---|---|---|---|
| [ ] | MVP-lecture-renderer | `backend/app/renderers/lecture_renderer.py:8` | 渲染标题、目标、目录、章节、总结、引用、阅读模式和打印模式。 |
| [ ] | MVP-slide-renderer | `backend/app/renderers/slide_renderer.py:8` | 将 SlideDeckSpec 转换为完整 scene-content-kit JSON，支持图片、表格、主题和布局。 |
| [x] | MVP-assets | `backend/app/exporters/asset_exporter.py:7` | 打包生成图片资源，用于下载；思维导图导出资源后续接入。 |
| [ ] | P2-markdown | `backend/app/exporters/markdown_exporter.py:7` | 将讲义、脚本和未来内容 spec 转换为 Markdown，并保留引用与资产链接。 |
| [-] | MVP-pdf | `backend/app/exporters/pdf_exporter.py:7` | 将 LectureRenderModel.printable_model 渲染为 PDF，包含图片、思维导图和引用。 |
| [-] | MVP-slide-export | `backend/app/exporters/slide_exporter.py:7` | 序列化 scene-content-kit pages 为 Slide JSON，并预留 PPTX exporter 路径。 |

## 前端 API、状态与页面

| 状态 | 优先级 | 位置 | TODO 内容 |
|---|---|---|---|
| [ ] | MVP-assets | `frontend/src/api/assetApi.ts:6` | 增加签名下载 URL、图片预览元数据、PDF 下载、Slide JSON 下载和资源包导出 helper。 |
| [ ] | MVP-api | `frontend/src/api/contentGenerationApi.ts:9` | 增加鉴权 header、统一错误归一化、request tracing、任务轮询、取消和重试接口。 |
| [ ] | MVP-form | `frontend/src/components/generation/ContentGenerationForm.tsx:9` | 扩展生成表单，支持受众、难度、slide count/duration、图片风格、PDF 选项、Slide 主题。 |
| [ ] | MVP-export | `frontend/src/components/generation/ExportActions.tsx:4` | 支持多导出格式、禁用原因、下载进度、失败重试和文件元数据。 |
| [ ] | MVP-progress | `frontend/src/components/generation/GenerationProgress.tsx:4` | 展示 workflow 节点进度：检索、规划、spec 生成、元素生成、校验、渲染。 |
| [ ] | MVP-preview | `frontend/src/pages/ContentPreviewPage.tsx:6` | 增加可编辑预览模式和章节级再生成入口。 |
| [ ] | MVP-task-history | `frontend/src/pages/TaskHistoryPage.tsx:8` | 加载持久化任务历史，支持按 content_type/status 过滤和重新打开预览/导出结果。 |
| [ ] | MVP-task | `frontend/src/stores/contentGenerationStore.ts:24` | 后端异步化后，启动轮询或订阅 SSE/WebSocket 进度。 |
| [ ] | MVP-export | `frontend/src/stores/contentGenerationStore.ts:36` | 将长耗时导出任务与内容生成任务分开追踪，并暴露重试/下载状态。 |

## 前端 Renderers、Elements 与 Utils

| 状态 | 优先级 | 位置 | TODO 内容 |
|---|---|---|---|
| [ ] | P1-citations | `frontend/src/components/elements/CitationList.tsx:6` | 渲染来源标题、页码/章节、URL 和引用编号。 |
| [ ] | MVP-image | `frontend/src/components/elements/ImageElement.tsx:8` | 加载真实图片 URL，展示 loading/error，占位图、点击放大和 alt_text。 |
| [ ] | P1-mindmap | `frontend/src/components/elements/MindmapElement.tsx:7` | 使用 Markmap 渲染 Markdown，并暴露 SVG/PNG 导出给打印和 Slide 嵌入。 |
| [ ] | MVP-lecture-renderer | `frontend/src/components/renderers/LectureRenderer/index.tsx:10` | 增加目录、引用、阅读模式、打印模式和 mindmap block 支持。 |
| [ ] | MVP-slide-renderer | `frontend/src/components/renderers/SlideRenderer/SlideDeckPreview.tsx:10` | 用 scene-content-kit SceneRenderer 替换 JSON 预览，增加缩放、缩略图和资源渲染。 |
| [ ] | schema-sync | `frontend/src/types/content.ts:10` | 后续从后端 JSON Schema/OpenAPI 自动生成前端类型，避免手写漂移。 |
| [ ] | MVP-options | `frontend/src/types/content.ts:33` | 与后端新增生成配置字段保持同步。 |
| [ ] | schema-sync | `frontend/src/types/elements.ts:36` | 添加 citation 以及未来 audio/video element union。 |
| [ ] | MVP-task | `frontend/src/types/export.ts:19` | 增加 progress、current_node、timestamps 和结构化错误详情。 |
| [ ] | MVP-export | `frontend/src/utils/export.ts:2` | 集中管理导出 label、扩展名、MIME type 和下载文件名生成。 |
| [ ] | P1-mindmap | `frontend/src/utils/markmap.ts:2` | 清洗生成 Markdown 并规范标题层级后再传给 Markmap。 |

## 暂缓设计

| 状态 | 优先级 | 位置 | TODO 内容 |
|---|---|---|---|
| [ ] | deferred-chart | `backend/app/schemas/elements.py:37` | 设计图表元素 schema、数据来源、图表类型和静态导出契约。 |
| [ ] | deferred-chart | `frontend/src/components/elements/ChartElement.tsx:6` | 设计 ChartElement、ECharts 渲染适配和响应式交互。 |
| [ ] | deferred-chart | `frontend/src/utils/chartSpecToEchartsOption.ts:4` | 设计 chart spec 到 ECharts option 的转换规则。 |
| [ ] | deferred-table | `backend/app/schemas/elements.py:50` | 设计表格元素 schema、数据来源、渲染和导出契约。 |
| [ ] | deferred-quiz | `backend/app/schemas/elements.py:57` | 设计测验生成 schema、题型、交互渲染和作答反馈。 |

## 优先级说明

- `MVP-*`：与当前 PRD MVP/P0 范围直接相关，建议优先实现。
- `P1-*`：PRD P1 能力，通常依赖 MVP 数据流稳定后接入。
- `P2-*`：后续扩展能力。
- `schema-*`、`content-*`、`export-*`：横向扩展与契约治理任务。

## 接真实 LLM 前的下一步

1. `backend/app/workflows/nodes/planner_node.py`：将确定性 outline stub 替换为 `get_llm_service().generate_structured(...)`，输出 `Outline`，失败时走 repair/fail 路径。
2. `backend/app/generators/unit_spec_generators.py`：拆出 lecture 与 slide 的 LLM prompt/generator，分别生成 `LectureSection` 与 `SlideSpecPage`，保留当前 deterministic fallback。
3. `backend/app/workflows/nodes/validator_node.py`：补引用覆盖校验、LLM 输出质量校验与 repair 节点，避免坏 schema 直接进入 renderer。
4. `backend/app/schemas/request.py`：补 audience、duration/slide_count、image_style、citation_policy、slide_theme 等 generation options，并按 content_type 校验。
5. `backend/app/services/task_service.py`：在真实 LLM/图片耗时变长后，将同步内存任务迁移到异步执行与持久化进度。
