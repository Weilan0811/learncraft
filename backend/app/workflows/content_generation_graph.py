from uuid import uuid4

from app.core.task import TaskStatus
from app.schemas.elements import ChartElement, ImageElement, MindmapElement, TextElement
from app.schemas.export import ExportRequest
from app.schemas.outline import Outline, OutlineSection
from app.schemas.request import ContentGenerationRequest
from app.schemas.specs import (
    ElementReferenceBlock,
    LectureSection,
    LectureSpec,
    SlideDeckSpec,
    SlideSpecElement,
    SlideSpecPage,
    TextBlock,
)
from app.schemas.state import ContentGenerationState
from app.services.image_generation_service import StubImageGenerationService
from app.services.rag_service import StubRAGService
from app.workflows.routers import get_exporter, get_renderer


def run_content_generation(
    request: ContentGenerationRequest,
    request_id: str | None = None,
) -> ContentGenerationState:
    """Run the generation workflow through stubbed nodes.

    TODO: Replace this sequential stub with a compiled LangGraph StateGraph once
    real async nodes, retries, and conditional routing are implemented.
    """
    state = ContentGenerationState(
        request_id=request_id or f"task_{uuid4().hex[:12]}",
        content_type=request.content_type,
        topic=request.topic,
        user_prompt=request.user_prompt,
        system_prompt=request.system_prompt,
        knowledge_base_ids=request.knowledge_base_ids,
        status=TaskStatus.running,
    )
    for node in (
        retrieve_context,
        plan_outline,
        generate_content_spec,
        generate_elements,
        validate_content,
        render_content,
        export_content,
    ):
        state = node(state, request)
    state.status = TaskStatus.completed
    return state


def retrieve_context(state: ContentGenerationState, request: ContentGenerationRequest) -> ContentGenerationState:
    # TODO(MVP-retriever): Support planning/generation/reviewer retrieval stages
    # and pass section_hint for secondary retrieval after outline creation.
    state.retrieved_chunks = StubRAGService().retrieve(request, stage="planning")
    return state


def plan_outline(state: ContentGenerationState, request: ContentGenerationRequest) -> ContentGenerationState:
    # TODO(MVP-planner): Replace placeholder outline with LLM-generated
    # lecture/slide outlines validated by Outline schema and citation coverage.
    state.outline = Outline(
        id=f"outline_{state.request_id}",
        content_type=request.content_type,
        title=request.topic,
        audience="待实现的目标受众",
        learning_objectives=[f"理解 {request.topic} 的核心概念"],
        sections=[
            OutlineSection(
                id="sec_stub",
                title=request.topic,
                goal="建立可扩展内容结构的占位大纲",
                key_points=["核心概念", "应用场景"],
                recommended_elements=["text", "image", "chart", "mindmap"],
                estimated_minutes=10,
                citations=[chunk.id for chunk in state.retrieved_chunks],
            )
        ],
        metadata={"stub": True},
    )
    return state


def generate_content_spec(state: ContentGenerationState, request: ContentGenerationRequest) -> ContentGenerationState:
    if state.outline is None:
        raise ValueError("Outline is required before content spec generation.")

    if request.content_type == "slide_deck":
        # TODO(MVP-slide-generator): Generate a multi-page SlideDeckSpec with
        # title/content/summary pages, visual strategy, layouts, and citations.
        state.content_spec = SlideDeckSpec(
            id=f"deck_{state.request_id}",
            title=state.outline.title,
            metadata={"language": request.generation_options.language, "stub": True},
            slides=[
                SlideSpecPage(
                    id="slide_stub",
                    title=state.outline.title,
                    core_message="这里是后续 Slide Generator 的接入点。",
                    layout="title-content-visual",
                    elements=[
                        SlideSpecElement(id="slide_text_stub", type="text", content="Slide 内容占位"),
                        SlideSpecElement(id="slide_image_stub", type="element_ref", element_id="img_stub"),
                    ],
                )
            ],
        )
        return state

    # TODO(MVP-lecture-generator): Generate full LectureSpec sections with
    # objectives, summaries, text blocks, required elements, and source citations.
    state.content_spec = LectureSpec(
        id=f"lecture_{state.request_id}",
        title=state.outline.title,
        metadata={"language": request.generation_options.language, "stub": True},
        objectives=state.outline.learning_objectives,
        sections=[
            LectureSection(
                id="sec_stub",
                title=state.outline.sections[0].title,
                summary="这里是后续 Lecture Spec Generator 的接入点。",
                blocks=[
                    TextBlock(
                        id="block_stub",
                        title="内容占位",
                        content="真实讲义正文将在 Generator 实现后填充。",
                        citations=[chunk.id for chunk in state.retrieved_chunks],
                    ),
                    ElementReferenceBlock(
                        id="block_image_stub",
                        title="图片占位",
                        element_id="img_stub",
                    ),
                ],
            )
        ],
    )
    return state


def generate_elements(state: ContentGenerationState, request: ContentGenerationRequest) -> ContentGenerationState:
    # TODO(MVP-elements): Fan out element generation for text/image/chart/
    # mindmap/table/quiz/citation, then merge generated assets by element id.
    image = StubImageGenerationService().generate_image(
        title=f"{request.topic} 示意图",
        description=f"{request.topic} 的教育类概念图",
    )
    elements = [
        TextElement(id="txt_stub", title="文本元素占位", content="后续由 Element Generator 生成。"),
        image,
        ChartElement(
            id="chart_stub",
            title="图表元素占位",
            chart_type="bar",
            description="后续转换为 ECharts option。",
            x_axis={"name": "类别", "data": ["A", "B"]},
            y_axis={"name": "数值"},
            series=[{"name": "示例", "data": [1, 2]}],
        ),
        MindmapElement(id="mindmap_stub", title="思维导图占位", markdown=f"# {request.topic}\n## 核心概念\n## 应用场景"),
    ]
    state.elements = elements
    return state


def validate_content(state: ContentGenerationState, request: ContentGenerationRequest) -> ContentGenerationState:
    # TODO(MVP-validator): Validate schema completeness, source citation
    # coverage, required element presence, and content quality before rendering.
    if state.content_spec is None:
        state.errors.append("content_spec is missing")
    if state.render_model is not None:
        state.errors.append("render_model should not be set before render_content")
    return state


def render_content(state: ContentGenerationState, request: ContentGenerationRequest) -> ContentGenerationState:
    # TODO(MVP-renderer): Route to typed content renderers and store render
    # snapshots for repeatable frontend preview and export.
    if state.content_spec is None:
        raise ValueError("Content spec is required before rendering.")
    renderer = get_renderer(request.content_type)
    state.render_model = renderer.render(state.content_spec, state.elements)
    return state


def export_content(state: ContentGenerationState, request: ContentGenerationRequest) -> ContentGenerationState:
    # TODO(MVP-export): Support multiple requested output_formats in one task
    # and defer long-running exports to async workers.
    if state.render_model is None:
        raise ValueError("Render model is required before exporting.")
    if request.content_type == "slide_deck":
        state.export_result = get_exporter("slide_json").export(
            state.request_id,
            state.render_model,
            ExportRequest(export_type="slide_json"),
        )
    elif "pdf" in request.output_formats:
        state.export_result = get_exporter("pdf").export(
            state.request_id,
            state.render_model,
            ExportRequest(export_type="pdf"),
        )
    return state
