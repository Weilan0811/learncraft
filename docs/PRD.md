# 内容生成 Agent 开发文档

## 1. 文档定位

本文档用于指导“内容生成 Agent”模块的正式开发。模块目标是基于系统 Prompt、用户 Prompt 与外部知识库内容，生成可渲染、可导出、可扩展的多模态内容资源。

当前 MVP 重点支持：

1. 讲义生成
2. Slide 生成
3. 图片生成
4. 图表生成
5. 思维导图生成
6. PDF 导出
7. Slide 导出或预览

模块整体采用统一生成流程：

```text
content_request
  -> outline
  -> content_spec
  -> elements
  -> renderer
```

其中：

- `outline`：内容大纲，由 Planner 生成。
- `content_spec`：面向具体内容类型的结构化内容描述，例如 `lecture_spec`、`slide_deck_spec`。
- `elements`：生成内容所需的多模态元素，例如文本、图片、图表、思维导图、表格、引用、音频脚本等。
- `renderer`：将结构化内容渲染为前端可展示内容。

导出流程由前端导出指令触发，基于已生成的预览数据与资源生成 PDF、Slide 文件、图片、Markdown 等格式，并返回可下载 URL。

后续可扩展支持：

1. 推文生成
2. 播客脚本生成
3. 视频脚本生成
4. 项目任务书生成
5. 课程页面生成
6. 测验包生成
7. 个性化学习路径生成

---

## 2. 总体技术栈

### 2.1 后端技术栈

| 层级 | 技术选型 | 说明 |
|---|---|---|
| Web API | Python + FastAPI | 提供内容生成、任务查询、导出、资源访问接口 |
| Agent / Workflow 编排 | LangGraph | 编排 Retriever、Planner、Generator、Renderer 等生成节点 |
| 数据模型 | Pydantic v2 | 定义请求、Outline、Spec、Element、Export Result 等结构 |
| RAG 检索 | 自研 Retriever / 可扩展 LlamaIndex、Haystack | MVP 可先接入简单向量检索与关键词检索 |
| LLM 调用 | 统一 LLM Service | 封装模型调用、结构化输出、重试、日志 |
| 图片生成 | Image Generation Service | MVP 必须实现，支持生成图片资源并返回可访问 URL |
| 图表生成 | chart_spec -> ECharts | 后端生成 `chart_spec`，前端使用 ECharts 渲染 |
| 思维导图生成 | Markdown Outline -> Markmap | 后端生成 Markdown 大纲，前端使用 Markmap 渲染 |
| PDF 渲染 | 自研 PDF Renderer | 生成讲义 PDF 所需的渲染模型或 HTML |
| Slide 渲染 | scene-content-kit | 使用已有 slide-only renderer 渲染静态 Slide JSON |
| 文件存储 | Local / OSS / S3-compatible Storage | 存储图片、导出文件、生成结果 |
| 任务执行 | FastAPI BackgroundTasks / Celery / Arq | MVP 可先使用简单异步任务，后续接入任务队列 |

### 2.2 前端技术栈

| 层级 | 技术选型 | 说明 |
|---|---|---|
| 前端框架 | React 19 + Vite + TypeScript | 内容预览与交互展示 |
| 状态管理 | Zustand / React Context | 管理生成任务、预览状态、导出状态 |
| 请求库 | Fetch / Axios | 调用后端生成与导出接口 |
| Markdown 渲染 | react-markdown / MDX 可选 | 渲染正文内容与 Markdown 片段 |
| 图表渲染 | ECharts / echarts-for-react | 渲染 `chart_spec` |
| 思维导图渲染 | Markmap | 渲染 Markdown 大纲 |
| Slide 渲染 | scene-content-kit | 渲染 `slide_deck_spec` 中的 Slide 页面 |
| 讲义渲染 | 自研 LectureRenderer | 渲染 `lecture_spec` 与多模态 elements |
| PDF 预览 | 浏览器预览 / 后端生成 PDF URL | 展示 PDF 导出结果 |

---

## 3. 核心生成流程

### 3.1 标准生成流程

```text
用户输入
  -> Content Request
  -> Retriever 获取知识上下文
  -> Planner 生成 Outline
  -> Generator 生成 content_spec
  -> Generator 生成 SectionElement / ContentElement
  -> Validator 校验结构与内容
  -> Renderer 生成前端可渲染模型
```

预览生成完成后，前端通过导出接口提交导出指令，后端基于任务的渲染快照执行目标格式导出。

### 3.2 内容类型扩展机制

内容生成 Agent 使用 `content_type` 区分目标内容类型。

MVP 支持：

```text
lecture
slide_deck
```

后续扩展：

```text
social_post
podcast_script
video_script
project_task
quiz_pack
learning_path
```

不同内容类型共享以下流程：

```text
outline -> xxx_spec -> elements -> renderer
```

不同内容类型拥有独立 Spec：

| content_type | Spec 名称 | Renderer | 可用导出格式 |
|---|---|---|---|
| lecture | `LectureSpec` | `LectureRenderer` | `pdf` |
| slide_deck | `SlideDeckSpec` | `SlideRenderer` | `slide_json`、`pptx` |
| social_post | `SocialPostSpec` | `SocialPostRenderer` | `markdown`、`image_assets` |
| podcast_script | `PodcastSpec` | `PodcastRenderer` | `markdown`、`audio` |
| video_script | `VideoScriptSpec` | `VideoScriptRenderer` | `markdown`、`html` |

---

## 4. 后端项目结构

```text
backend/
  app/
    main.py
    api/
      content_generation.py
      export.py
      assets.py
    core/
      config.py
      logging.py
      exceptions.py
      task.py
    schemas/
      request.py
      outline.py
      base.py
      lecture_spec.py
      slide_spec.py
      elements.py
      chart_spec.py
      mindmap_spec.py
      image_spec.py
      export.py
      task.py
    workflows/
      content_generation_graph.py
      states.py
      routers.py
      nodes/
        retriever_node.py
        planner_node.py
        generator_node.py
        element_generator_node.py
        validator_node.py
        renderer_node.py
        exporter_node.py
    services/
      llm_service.py
      rag_service.py
      image_generation_service.py
      asset_service.py
      storage_service.py
      citation_service.py
      task_service.py
    renderers/
      base_renderer.py
      lecture_renderer.py
      slide_renderer.py
      social_post_renderer.py
      podcast_renderer.py
    exporters/
      base_exporter.py
      pdf_exporter.py
      slide_exporter.py
      markdown_exporter.py
      asset_exporter.py
    prompts/
      planner/
        lecture_outline.md
        slide_outline.md
      generator/
        lecture_spec.md
        slide_deck_spec.md
        section_elements.md
      reviewer/
        content_review.md
    tests/
      test_planner.py
      test_generator.py
      test_renderer.py
      test_exporter.py
```

---

## 5. 后端模块开发需求

# 5.1 Retriever

## 5.1.1 模块目标

Retriever 负责根据用户请求、系统约束与内容生成阶段，从知识库中检索相关知识片段，并提供给 Planner 与 Generator 使用。

## 5.1.2 输入

```json
{
  "request_id": "req_001",
  "content_type": "lecture",
  "topic": "人工智能基础导论",
  "user_prompt": "为本科一年级学生生成一份讲义",
  "system_prompt": "内容需准确、结构清晰，适合教学使用",
  "knowledge_base_ids": ["kb_ai_basic"],
  "retrieval_stage": "planning",
  "section_hint": null
}
```

## 5.1.3 输出

```json
{
  "chunks": [
    {
      "id": "chunk_001",
      "source_id": "doc_001",
      "source_title": "人工智能基础教材",
      "content": "人工智能是研究如何使机器表现出智能行为的技术领域……",
      "score": 0.89,
      "metadata": {
        "page": 3,
        "section": "第一章"
      }
    }
  ]
}
```

## 5.1.4 功能需求

1. 支持按主题检索知识库内容。
2. 支持按大纲章节二次检索。
3. 支持返回来源信息。
4. 支持检索结果去重。
5. 支持检索结果按相关性排序。
6. 支持控制返回片段数量与最大 token 数。
7. 支持为 Planner、Generator、Reviewer 提供不同阶段的检索上下文。

## 5.1.5 MVP 要求

1. 支持单知识库检索。
2. 支持关键词检索或向量检索中的至少一种。
3. 返回 chunk 内容与来源信息。
4. 支持基于章节标题进行二次检索。

---

# 5.2 Planner

## 5.2.1 模块目标

Planner 负责生成内容大纲 `outline`。`outline` 是后续生成 `xxx_spec` 的核心规划结果。

## 5.2.2 输入

```json
{
  "content_type": "lecture",
  "topic": "人工智能基础导论",
  "audience": "本科一年级学生",
  "user_prompt": "生成一份适合课堂学习的多模态讲义",
  "system_prompt": "结构完整、知识准确、适合教学",
  "retrieved_chunks": []
}
```

## 5.2.3 输出：通用 Outline

```json
{
  "id": "outline_001",
  "content_type": "lecture",
  "title": "人工智能基础导论",
  "audience": "本科一年级学生",
  "learning_objectives": [
    "理解人工智能的基本概念",
    "区分人工智能、机器学习与深度学习",
    "了解人工智能在教育中的应用"
  ],
  "sections": [
    {
      "id": "sec_001",
      "title": "什么是人工智能",
      "goal": "理解人工智能的定义、边界与典型应用",
      "key_points": ["定义", "发展背景", "应用场景"],
      "recommended_elements": ["text", "image", "mindmap", "quiz"],
      "estimated_minutes": 15
    }
  ]
}
```

## 5.2.4 功能需求

1. 根据 `content_type` 生成对应内容大纲。
2. 生成内容标题、目标受众、学习目标或传播目标。
3. 生成分节结构。
4. 为每个分节生成核心知识点。
5. 为每个分节推荐所需多模态元素。
6. 生成内容难度、学习时长或阅读时长等元数据。
7. 保留知识来源引用关系。

## 5.2.5 不同内容类型的大纲差异

### Lecture Outline

重点字段：

```text
learning_objectives
sections
key_points
recommended_elements
estimated_minutes
assessment_points
```

### Slide Outline

重点字段：

```text
slide_count
slide_titles
core_message_per_slide
visual_strategy
recommended_elements
```

### Social Post Outline

重点字段：

```text
hook
main_points
post_structure
visual_need
platform_style
```

### Podcast Outline

重点字段：

```text
episode_title
opening
segments
host_script_points
transition_points
closing
```

## 5.2.6 MVP 要求

1. 支持 `lecture` 大纲生成。
2. 支持 `slide_deck` 大纲生成。
3. 输出必须通过 Pydantic Schema 校验。
4. 每个 section 必须包含推荐元素类型。
5. 每个 section 必须保留检索上下文引用。

---

# 5.3 Generator

## 5.3.1 模块目标

Generator 负责基于 `outline` 和知识库上下文生成结构化内容 Spec，并进一步生成所需多模态 elements。

Generator 分为两层：

```text
Spec Generator
Element Generator
```

其中：

- `Spec Generator` 生成目标内容类型的结构化内容，例如 `LectureSpec`、`SlideDeckSpec`。
- `Element Generator` 生成图片、图表、思维导图、表格、测验、引用等元素。

---

## 5.3.2 Spec Generator

### 输入

```json
{
  "content_type": "lecture",
  "outline": {},
  "retrieved_chunks": [],
  "generation_config": {
    "language": "zh-CN",
    "style": "educational",
    "difficulty": "introductory"
  }
}
```

### 输出示例：LectureSpec

```json
{
  "id": "lecture_001",
  "type": "lecture",
  "title": "人工智能基础导论",
  "metadata": {
    "audience": "本科一年级学生",
    "difficulty": "introductory",
    "language": "zh-CN"
  },
  "objectives": [
    "理解人工智能的基本概念"
  ],
  "sections": [
    {
      "id": "sec_001",
      "title": "什么是人工智能",
      "summary": "本节介绍人工智能的定义、边界与应用。",
      "blocks": [
        {
          "id": "block_001",
          "type": "text",
          "title": "概念解释",
          "content": "人工智能是研究如何使机器表现出智能行为的技术领域。",
          "citations": ["chunk_001"]
        }
      ]
    }
  ]
}
```

### 输出示例：SlideDeckSpec

```json
{
  "id": "deck_001",
  "type": "slide_deck",
  "title": "人工智能基础导论",
  "slides": [
    {
      "id": "slide_001",
      "title": "什么是人工智能",
      "core_message": "人工智能的核心是让机器表现出智能行为。",
      "layout": "title-content-visual",
      "elements": [
        {
          "id": "el_text_001",
          "type": "text",
          "content": "人工智能是研究如何使机器表现出智能行为的技术领域。"
        }
      ]
    }
  ]
}
```

### 功能需求

1. 按 `content_type` 生成对应 Spec。
2. Spec 必须引用 Outline 中的 section 或 slide 规划。
3. Spec 必须保留引用来源。
4. Spec 必须声明所需 elements。
5. Spec 必须通过 Pydantic Schema 校验。
6. Spec 支持版本字段。
7. Spec 支持后续编辑与重新生成。

---

## 5.3.3 Element Generator

### 模块目标

Element Generator 负责生成目标内容所需的多模态元素。

MVP 必须支持：

```text
text
image
chart
mindmap
table
quiz
citation
```

后续支持：

```text
audio_script
audio_file
video_script
interactive_task
project_task
```

---

## 5.3.4 图片生成 Element

### 开发级别

图片生成为 MVP 必做功能。

### 输入

```json
{
  "element_type": "image",
  "content_type": "lecture",
  "section_id": "sec_001",
  "title": "人工智能应用场景示意图",
  "image_intent": "concept_illustration",
  "description": "展示人工智能在教育、医疗、交通、金融中的典型应用",
  "style": "clean educational illustration",
  "aspect_ratio": "16:9"
}
```

### 输出

```json
{
  "id": "img_001",
  "type": "image",
  "title": "人工智能应用场景示意图",
  "prompt": "A clean educational illustration showing AI applications in education, healthcare, transportation and finance, minimal style, white background",
  "asset_url": "https://assets.example.com/img_001.png",
  "alt_text": "人工智能应用场景示意图",
  "metadata": {
    "width": 1280,
    "height": 720,
    "format": "png"
  }
}
```

### 功能需求

1. 支持根据 section 内容生成图片需求。
2. 支持生成图片 prompt。
3. 支持调用图片生成服务生成图片。
4. 支持保存图片资源。
5. 支持返回图片 URL。
6. 支持生成 `alt_text`。
7. 支持记录图片生成参数。
8. 支持图片生成失败后的重试。
9. 支持图片资源进入 LectureRenderer 与 SlideRenderer。

### MVP 验收标准

1. 每个讲义或 Slide Deck 至少支持生成 1 张图片。
2. 图片元素必须包含 `prompt`、`asset_url`、`alt_text`。
3. 前端可展示图片。
4. PDF 导出可包含图片。
5. Slide 渲染可包含图片。

---

## 5.3.5 图表生成 Element

### 技术路线

```text
chart_spec -> ECharts
```

### 输入

```json
{
  "element_type": "chart",
  "title": "不同学习方式效果对比",
  "chart_intent": "comparison",
  "data_source": "generated_from_context",
  "section_context": "比较视频学习、阅读学习、项目学习三种学习方式"
}
```

### 输出：ChartSpec

```json
{
  "id": "chart_001",
  "type": "chart",
  "chart_type": "bar",
  "title": "不同学习方式效果对比",
  "description": "比较三种学习方式的平均测验成绩",
  "x_axis": {
    "name": "学习方式",
    "data": ["视频学习", "阅读学习", "项目学习"]
  },
  "y_axis": {
    "name": "平均成绩"
  },
  "series": [
    {
      "name": "平均成绩",
      "data": [75, 82, 91]
    }
  ]
}
```

### 功能需求

1. 支持生成 `chart_spec`。
2. 支持柱状图、折线图、饼图。
3. 支持图表标题、说明、坐标轴、数据序列。
4. 支持前端转换为 ECharts option。
5. 支持 PDF 导出时转为静态图片或 SVG。
6. 支持 Slide 渲染时转为图片元素。

---

## 5.3.6 思维导图 Element

### 技术路线

```text
Markdown 大纲 -> Markmap
```

### 输出

```json
{
  "id": "mindmap_001",
  "type": "mindmap",
  "title": "人工智能基础知识结构",
  "markdown": "# 人工智能基础\n## 基本概念\n### 人工智能\n### 机器学习\n### 深度学习\n## 应用场景\n### 教育\n### 医疗\n### 金融"
}
```

### 功能需求

1. 支持根据章节内容生成 Markdown 大纲。
2. 支持前端 Markmap 渲染。
3. 支持导出时转为 SVG 或 PNG。
4. 支持嵌入 LectureRenderer。
5. 支持嵌入 SlideRenderer，嵌入前转换为图片元素。

---

# 5.4 Renderer

## 5.4.1 模块目标

Renderer 负责将 `content_spec` 与 elements 转换为前端可渲染的数据模型。

Renderer 按内容类型拆分：

```text
LectureRenderer
SlideRenderer
SocialPostRenderer
PodcastRenderer
```

---

## 5.4.2 LectureRenderer

### 模块目标

LectureRenderer 负责渲染 `LectureSpec`，生成前端讲义页面与 PDF 导出所需结构。

### 输入

```json
{
  "type": "lecture",
  "lecture_spec": {},
  "elements": []
}
```

### 输出

```json
{
  "render_type": "lecture_page",
  "title": "人工智能基础导论",
  "sections": [
    {
      "id": "sec_001",
      "title": "什么是人工智能",
      "render_blocks": [
        {
          "type": "text",
          "content": "人工智能是……"
        },
        {
          "type": "image",
          "asset_url": "https://assets.example.com/img_001.png"
        }
      ]
    }
  ]
}
```

### 功能需求

1. 支持渲染讲义标题、学习目标、目录、章节、总结、引用。
2. 支持渲染文本、图片、图表、思维导图、表格、测验。
3. 支持交互式阅读模式。
4. 支持打印模式。
5. 支持生成 PDF 导出所需 `printable_model`。

---

## 5.4.3 SlideRenderer

### 模块目标

SlideRenderer 负责将 `SlideDeckSpec` 转换为 slide renderer 可消费的静态 Slide JSON。

### 已有渲染器

项目使用 `scene-content-kit` 作为 Slide 渲染器。该 renderer 用于渲染静态 Slide 页面，支持 `text`、`image`、`shape`、`line`、`table` 等元素。复杂图表、SmartArt、复杂自由图形在 v1 阶段以图片形式进入 slide JSON。

### Slide JSON 输出示例

```json
{
  "version": "scenekit.slide/v1",
  "page": {
    "id": "slide-001",
    "title": "PPT Page 1",
    "width": 960,
    "height": 540,
    "background": {
      "type": "solid",
      "color": "#ffffff"
    },
    "theme": {
      "backgroundColor": "#ffffff",
      "themeColors": ["#2563eb", "#0f766e"],
      "fontColor": "#111827",
      "fontName": "Arial"
    },
    "elements": [
      {
        "id": "title-1",
        "type": "text",
        "left": 48,
        "top": 40,
        "width": 600,
        "height": 80,
        "rotate": 0,
        "content": "<p>人工智能基础导论</p>",
        "defaultFontName": "Arial",
        "defaultColor": "#111827",
        "fontSize": 36,
        "bold": true
      }
    ]
  }
}
```

### 功能需求

1. 支持将 `SlideDeckSpec` 转换为 `scenekit.slide/v1` JSON。
2. 支持生成多页 slide deck。
3. 支持 text、image、shape、line、table 元素。
4. 支持将 chart、mindmap 转换为图片后嵌入。
5. 支持主题、背景、字体、颜色配置。
6. 支持调用前端 `SceneRenderer` 预览。

---

# 5.5 Exporter

## 5.5.1 模块目标

Exporter 负责将渲染结果导出为目标格式。

Exporter 由导出接口按需调用，输入为 `task_id`、`export_type`、导出选项以及任务已持久化的 `render_model`、`content_spec`、资源引用。导出完成后返回可下载 URL，并更新任务的 `export_files`。

MVP 支持：

```text
PDF
Slide JSON
图片资源
```

后续支持：

```text
PPTX
Markdown
HTML
Audio
Video Script
Social Image
```

---

## 5.5.2 PDFExporter

### 输入

```json
{
  "export_type": "pdf",
  "content_type": "lecture",
  "printable_model": {},
  "export_options": {
    "page_size": "A4",
    "margin": "normal",
    "include_references": true
  }
}
```

### 输出

```json
{
  "export_type": "pdf",
  "file_url": "https://assets.example.com/export/lecture_001.pdf",
  "status": "success"
}
```

### 功能需求

1. 支持将讲义导出为 PDF。
2. 支持图片、图表、思维导图进入 PDF。
3. 支持目录、页眉页脚、页码。
4. 支持参考资料输出。
5. 支持导出失败重试。
6. 支持返回可下载 URL。

---

## 5.5.3 SlideExporter

### 输入

```json
{
  "export_type": "slide_json",
  "content_type": "slide_deck",
  "slide_pages": []
}
```

### 输出

```json
{
  "export_type": "slide_json",
  "file_url": "https://assets.example.com/export/deck_001.json",
  "status": "success"
}
```

### 功能需求

1. 支持导出 Slide JSON。
2. 支持前端预览 Slide Deck。
3. 支持后续扩展 PPTX 导出。
4. 支持图片资源与 Slide JSON 的引用关系。

---

## 6. LangGraph 工作流设计

### 6.1 State 定义

```python
from typing import Literal, Optional
from pydantic import BaseModel

ContentType = Literal[
    "lecture",
    "slide_deck",
    "social_post",
    "podcast_script",
    "video_script"
]

class ContentGenerationState(BaseModel):
    request_id: str
    content_type: ContentType
    topic: str
    user_prompt: str
    system_prompt: Optional[str] = None
    knowledge_base_ids: list[str] = []

    retrieved_chunks: list[dict] = []
    outline: Optional[dict] = None
    content_spec: Optional[dict] = None
    elements: list[dict] = []
    render_model: Optional[dict] = None

    errors: list[str] = []
    status: str = "pending"
```

### 6.2 Graph 节点

```text
START
  -> retrieve_context
  -> plan_outline
  -> generate_content_spec
  -> generate_elements
  -> validate_content
  -> render_content
  -> END
```

### 6.3 条件分支

根据 `content_type` 选择不同 Spec Generator 与 Renderer：

```text
content_type = lecture
  -> LectureSpecGenerator
  -> LectureRenderer

content_type = slide_deck
  -> SlideDeckSpecGenerator
  -> SlideRenderer

content_type = social_post
  -> SocialPostSpecGenerator
  -> SocialPostRenderer
```

导出路径根据 `export_type` 选择 Exporter：

```text
export_type = pdf
  -> PDFExporter

export_type = slide_json
  -> SlideExporter

export_type = image_assets
  -> AssetExporter
```

### 6.4 并行元素生成

`generate_elements` 节点支持按元素类型并行生成：

```text
text_element_generator
image_element_generator
chart_element_generator
mindmap_element_generator
table_element_generator
quiz_element_generator
```

---

## 7. API 设计

### 7.1 创建内容生成任务

```http
POST /api/content-generation/tasks
```

### 请求体

```json
{
  "content_type": "lecture",
  "topic": "人工智能基础导论",
  "user_prompt": "生成一份适合本科一年级学生学习的多模态讲义",
  "system_prompt": "内容准确、结构清晰、适合教学",
  "knowledge_base_ids": ["kb_ai_basic"],
  "generation_options": {
    "language": "zh-CN",
    "difficulty": "introductory",
    "include_images": true,
    "include_charts": true,
    "include_mindmap": true
  }
}
```

### 响应体

```json
{
  "task_id": "task_001",
  "status": "queued"
}
```

---

### 7.2 查询任务状态

```http
GET /api/content-generation/tasks/{task_id}
```

### 响应体

```json
{
  "task_id": "task_001",
  "status": "completed",
  "content_type": "lecture",
  "preview_url": "/preview/lecture/task_001",
  "export_files": []
}
```

`export_files` 在导出接口成功返回后更新。

---

### 7.3 获取预览数据

```http
GET /api/content-generation/tasks/{task_id}/preview
```

### 响应体

```json
{
  "content_type": "lecture",
  "render_model": {}
}
```

---

### 7.4 导出内容

```http
POST /api/content-generation/tasks/{task_id}/export
```

### 请求体

```json
{
  "export_type": "pdf"
}
```

### 响应体

```json
{
  "export_type": "pdf",
  "file_url": "https://assets.example.com/export/lecture_001.pdf",
  "status": "success"
}
```

---

## 8. 前端项目结构

```text
frontend/
  src/
    main.tsx
    App.tsx
    api/
      contentGenerationApi.ts
      assetApi.ts
    types/
      content.ts
      outline.ts
      lecture.ts
      slide.ts
      elements.ts
      export.ts
    pages/
      ContentGenerationPage.tsx
      ContentPreviewPage.tsx
      TaskHistoryPage.tsx
    components/
      generation/
        ContentGenerationForm.tsx
        GenerationProgress.tsx
        ExportActions.tsx
      renderers/
        LectureRenderer/
          index.tsx
          LectureSection.tsx
          blocks/
            TextBlock.tsx
            ImageBlock.tsx
            ChartBlock.tsx
            MindmapBlock.tsx
            TableBlock.tsx
            QuizBlock.tsx
        SlideRenderer/
          index.tsx
          SlideDeckPreview.tsx
      elements/
        ChartElement.tsx
        MindmapElement.tsx
        ImageElement.tsx
        CitationList.tsx
    stores/
      contentGenerationStore.ts
    utils/
      chartSpecToEchartsOption.ts
      markmap.ts
      export.ts
```

---

## 9. 前端开发需求

# 9.1 内容生成页面

## 功能需求

1. 支持选择 `content_type`。
2. 支持输入主题。
3. 支持输入用户 Prompt。
4. 支持选择知识库。
5. 支持选择生成配置。
6. 支持提交生成任务。
7. 支持展示任务进度。

---

# 9.2 LectureRenderer

## 功能需求

1. 渲染讲义标题、学习目标、目录。
2. 渲染章节内容。
3. 渲染文本块。
4. 渲染图片块。
5. 渲染图表块。
6. 渲染思维导图块。
7. 渲染表格块。
8. 渲染测验块。
9. 渲染引用列表。
10. 支持阅读模式。
11. 支持打印模式。
12. 支持调用导出 PDF。

---

# 9.3 SlideRenderer

## 功能需求

1. 接收 `slide_deck` 渲染模型。
2. 调用 `scene-content-kit` 渲染 Slide 页面。
3. 支持多页 Slide 预览。
4. 支持上一页、下一页切换。
5. 支持缩放预览。
6. 支持导出 Slide JSON。

---

# 9.4 ChartElement

## 功能需求

1. 接收 `chart_spec`。
2. 将 `chart_spec` 转换为 ECharts option。
3. 使用 ECharts 渲染图表。
4. 支持响应式布局。
5. 支持导出为图片，供 PDF 与 Slide 使用。

---

# 9.5 MindmapElement

## 功能需求

1. 接收 Markdown 大纲。
2. 使用 Markmap 渲染思维导图。
3. 支持展开与折叠。
4. 支持导出为 SVG 或 PNG。
5. 支持在讲义和 Slide 中复用。

---

# 9.6 ImageElement

## 功能需求

1. 接收图片 URL。
2. 展示图片标题与 `alt_text`。
3. 支持加载状态。
4. 支持失败占位图。
5. 支持点击放大预览。
6. 支持 PDF 与 Slide 渲染。

---

## 10. MVP 范围

### 10.1 后端 MVP

1. FastAPI 项目初始化。
2. LangGraph 主工作流实现。
3. `ContentGenerationState` 实现。
4. Retriever 实现。
5. Planner 实现。
6. Lecture Spec Generator 实现。
7. Slide Deck Spec Generator 实现。
8. Element Generator 实现。
9. 图片生成服务实现。
10. Chart Spec 生成实现。
11. Mindmap Markdown 生成实现。
12. Lecture Renderer 数据模型实现。
13. Slide Renderer 适配实现。
14. PDF Exporter 实现。
15. Slide JSON Exporter 实现。

### 10.2 前端 MVP

1. 内容生成表单。
2. 任务状态展示。
3. LectureRenderer。
4. SlideRenderer。
5. ChartElement。
6. MindmapElement。
7. ImageElement。
8. PDF 导出入口。
9. Slide JSON 预览入口。

### 10.3 内容能力 MVP

1. 讲义生成。
2. Slide Deck 生成。
3. 图片生成。
4. 图表生成。
5. 思维导图生成。
6. 表格生成。
7. 测验生成。
8. 引用来源展示。

---

## 11. 验收标准

### 11.1 通用验收标准

1. 用户可创建内容生成任务。
2. 系统可根据知识库生成 outline。
3. 系统可根据 outline 生成对应内容类型的 Spec。
4. 系统可生成多模态 elements。
5. 系统可完成前端预览。
6. 系统可完成目标格式导出。
7. 所有核心数据结构通过 Pydantic 校验。
8. 生成结果保留来源引用。
9. 任务失败时返回错误信息。
10. 任务结果可重复访问。

### 11.2 Lecture 验收标准

1. 生成完整讲义结构。
2. 讲义包含标题、学习目标、章节、正文、总结、引用。
3. 讲义包含至少 1 张生成图片。
4. 讲义支持图表展示。
5. 讲义支持思维导图展示。
6. 讲义支持 PDF 导出。

### 11.3 Slide Deck 验收标准

1. 生成多页 Slide Deck。
2. Slide Deck 包含标题页、内容页、总结页。
3. Slide 页面可通过 `scene-content-kit` 渲染。
4. Slide Deck 包含至少 1 张生成图片。
5. 图表和思维导图可作为图片元素进入 Slide。
6. Slide JSON 可导出。

### 11.4 图片生成验收标准

1. 图片生成服务可被 Element Generator 调用。
2. 图片生成结果包含 `prompt`、`asset_url`、`alt_text`。
3. 图片可在前端展示。
4. 图片可进入 PDF。
5. 图片可进入 Slide。

---

## 12. 开发优先级

### P0

1. 后端 FastAPI 基础结构。
2. LangGraph 工作流。
3. Pydantic Schemas。
4. Retriever。
5. Planner。
6. LectureSpec Generator。
7. SlideDeckSpec Generator。
8. 图片生成服务。
9. Element Generator。
10. 前端 LectureRenderer。
11. 前端 SlideRenderer。
12. PDF 导出。

### P1

1. Chart Spec 生成与 ECharts 渲染。
2. Mindmap Markdown 生成与 Markmap 渲染。
3. 表格生成。
4. 测验生成。
5. 引用展示。
6. Slide JSON 导出。

### P2

1. PPTX 导出。
2. 推文生成。
3. 播客脚本生成。
4. 音频生成。
5. 视频脚本生成。
6. 用户编辑与二次生成。
7. 版本管理。

---

## 13. 开发约定

1. 所有 LLM 输出必须经过结构化 Schema 校验。
2. 所有内容类型必须遵循 `outline -> xxx_spec -> elements -> renderer` 生成流程。
3. 所有 Spec 必须包含 `id`、`type`、`version`、`metadata`。
4. 所有元素必须包含 `id`、`type`、`title`。
5. 图片元素必须包含 `prompt`、`asset_url`、`alt_text`。
6. 图表元素必须包含 `chart_spec`。
7. 思维导图元素必须包含 Markdown 大纲。
8. Renderer 按内容类型拆分。
9. Exporter 按导出格式拆分，并由导出接口按需调用。
10. Lecture 与 Slide 使用独立 Spec、Renderer，并声明支持的导出格式。
11. 后续新增内容类型时新增对应 Spec、Renderer 与导出格式映射。
