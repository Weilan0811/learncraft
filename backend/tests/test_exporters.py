from io import BytesIO
import zipfile

from PIL import Image
from pypdf import PdfReader

from app.exporters.asset_exporter import AssetExporter
from app.exporters.html_exporter import HTMLExporter
from app.exporters.markdown_exporter import MarkdownExporter
from app.exporters.pdf_exporter import PDFExporter
from app.schemas.export import ExportRequest
from app.schemas.render import (
    KitImageElement,
    KitSlidePage,
    KitTheme,
    LectureRenderModel,
    LectureRenderSection,
    PodcastRenderModel,
    RenderBlock,
    SlidePageModel,
    SlideRenderModel,
)
from app.schemas.request import ContentGenerationRequest
from app.schemas.state import ContentGenerationState
from app.services.storage_service import LocalStorageService
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_service import PersistentTaskService


def build_lecture_model(storage: LocalStorageService) -> LectureRenderModel:
    buffer = BytesIO()
    Image.new("RGB", (320, 180), (37, 99, 235)).save(buffer, "PNG")
    image = storage.save_bytes(
        asset_id="img_export",
        filename="img_export.png",
        content=buffer.getvalue(),
        content_type="image/png",
        kind="image",
    )
    return LectureRenderModel(
        title="AI Agent 的记忆机制",
        objectives=["理解短期记忆", "理解长期记忆"],
        sections=[
            LectureRenderSection(
                id="unit_001",
                title="为什么需要记忆",
                render_blocks=[
                    RenderBlock(
                        id="block_text",
                        type="text",
                        title="核心问题",
                        content="第一段正文。\n第二段正文。",
                        metadata={"citations": ["chunk_alpha"]},
                    ),
                    RenderBlock(
                        id="img_export",
                        type="image",
                        title="对比示意图",
                        asset_url=image.url,
                    ),
                ],
            )
        ],
    )


def test_pdf_export_produces_chinese_document_with_image(tmp_path) -> None:
    storage = LocalStorageService(storage_root=tmp_path)
    model = build_lecture_model(storage)

    result = PDFExporter(storage_service=storage).export(
        "task_export", model, ExportRequest(export_type="pdf")
    )

    assert result.status == "success"
    content = storage.read_bytes("export_task_export_pdf")
    assert content.startswith(b"%PDF-")
    assert len(content) > 2000
    assert result.metadata["image_count"] == 1
    assert result.metadata["section_count"] == 1
    assert result.metadata["page_count"] >= 1
    extracted = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
    assert "AI Agent 的记忆机制" in extracted
    assert "第一段正文" in extracted
    assert "chunk_alpha" in extracted


def test_markdown_export_covers_lecture_text_images_and_citations(tmp_path) -> None:
    storage = LocalStorageService(storage_root=tmp_path)
    model = build_lecture_model(storage)

    result = MarkdownExporter(storage_service=storage).export(
        "task_export", model, ExportRequest(export_type="markdown")
    )

    assert result.status == "success"
    markdown = storage.read_bytes("export_task_export_markdown").decode("utf-8")
    assert "# AI Agent 的记忆机制" in markdown
    assert "## 学习目标" in markdown
    assert "## 为什么需要记忆" in markdown
    assert "第一段正文" in markdown
    assert "![对比示意图](/api/assets/img_export/download)" in markdown
    assert "[1]" in markdown
    assert "1. `chunk_alpha`" in markdown


def test_html_export_embeds_images_and_citations(tmp_path) -> None:
    storage = LocalStorageService(storage_root=tmp_path)
    model = build_lecture_model(storage)

    result = HTMLExporter(storage_service=storage).export(
        "task_export", model, ExportRequest(export_type="html")
    )

    assert result.status == "success"
    html = storage.read_bytes("export_task_export_html").decode("utf-8")
    assert "AI Agent 的记忆机制" in html
    assert "<h2>为什么需要记忆</h2>" in html
    assert "data:image/png;base64," in html
    assert "<h2>引用</h2>" in html
    assert "chunk_alpha" in html


def test_exporters_reject_unsupported_render_models(tmp_path) -> None:
    storage = LocalStorageService(storage_root=tmp_path)
    slide_model = SlideRenderModel(title="幻灯片", pages=[])

    pdf_result = PDFExporter(storage_service=storage).export(
        "task_slide", slide_model, ExportRequest(export_type="pdf")
    )
    markdown_result = MarkdownExporter(storage_service=storage).export(
        "task_slide", slide_model, ExportRequest(export_type="markdown")
    )
    html_result = HTMLExporter(storage_service=storage).export(
        "task_slide", slide_model, ExportRequest(export_type="html")
    )

    assert pdf_result.status == "failed"
    assert markdown_result.status == "failed"
    assert html_result.status == "failed"
    assert pdf_result.file_url == ""
    assert "error" in pdf_result.metadata


def test_asset_export_collects_slide_deck_images(tmp_path) -> None:
    storage = LocalStorageService(storage_root=tmp_path)
    buffer = BytesIO()
    Image.new("RGB", (160, 90), (16, 185, 129)).save(buffer, "PNG")
    image = storage.save_bytes(
        asset_id="img_slide",
        filename="img_slide.png",
        content=buffer.getvalue(),
        content_type="image/png",
        kind="image",
    )
    model = SlideRenderModel(
        title="幻灯片",
        pages=[
            SlidePageModel(
                page=KitSlidePage(
                    id="page_1",
                    title="第一页",
                    width=960,
                    height=540,
                    theme=KitTheme(
                        backgroundColor="#FFFFFF",
                        themeColors=["#0B4F7A"],
                        fontColor="#111827",
                        fontName="Arial",
                    ),
                    elements=[
                        KitImageElement(
                            id="img_slide",
                            left=0,
                            top=0,
                            width=320,
                            height=180,
                            rotate=0,
                            src=image.url,
                        )
                    ],
                )
            )
        ],
    )

    result = AssetExporter(storage_service=storage).export(
        "task_slide", model, ExportRequest(export_type="image_assets")
    )

    assert result.status == "success"
    assert result.metadata["asset_count"] == 1
    with zipfile.ZipFile(BytesIO(storage.read_bytes("export_task_slide_image_assets"))) as archive:
        names = archive.namelist()
    assert "assets/img_slide.png" in names
    assert "manifest.json" in names


def test_export_records_only_successful_files_and_dedupes(tmp_path, monkeypatch) -> None:
    storage = LocalStorageService(storage_root=tmp_path)
    monkeypatch.setattr("app.exporters.pdf_exporter.LocalStorageService", lambda: storage)
    repository = SQLModelTaskRepository(
        database_url=f"sqlite:///{tmp_path / 'exports.db'}",
        echo=False,
        create_tables=True,
    )
    service = PersistentTaskService(repository=repository)
    lecture = service.create_task(
        ContentGenerationRequest(content_type="lecture", topic="Exports", user_prompt="Generate")
    )
    lecture_model = LectureRenderModel(
        title="Exports",
        sections=[LectureRenderSection(id="unit_001", title="Section", render_blocks=[])],
    )
    repository.save_state(
        lecture.task_id,
        ContentGenerationState(
            request_id=lecture.task_id,
            content_type="lecture",
            topic="Exports",
            user_prompt="Generate",
            render_model=lecture_model,
            status="completed",
            progress={"stage": "completed", "percent": 100},
        ),
    )

    first = service.export_task(lecture.task_id, ExportRequest(export_type="pdf"))
    second = service.export_task(lecture.task_id, ExportRequest(export_type="pdf"))
    rejected = service.export_task(lecture.task_id, ExportRequest(export_type="pptx"))

    assert first is not None and first.status == "success"
    assert second is not None and second.status == "success"
    assert rejected is not None and rejected.status == "failed"
    task = repository.get_task(lecture.task_id)
    assert task is not None
    assert task.progress["export_files"] == [
        {"type": "pdf", "url": first.file_url},
    ]

    podcast = service.create_task(
        ContentGenerationRequest(content_type="podcast_script", topic="No audio", user_prompt="Generate")
    )
    repository.save_state(
        podcast.task_id,
        ContentGenerationState(
            request_id=podcast.task_id,
            content_type="podcast_script",
            topic="No audio",
            user_prompt="Generate",
            render_model=PodcastRenderModel(
                title="No audio",
                podcast_name="Podcast",
                podcast_tagline="Tagline",
                script_text="Person1: hello",
            ),
            status="completed",
            progress={"stage": "completed", "percent": 100},
        ),
    )

    audio = service.export_task(podcast.task_id, ExportRequest(export_type="audio"))

    assert audio is not None and audio.status == "failed"
    podcast_task = repository.get_task(podcast.task_id)
    assert podcast_task is not None
    assert "export_files" not in podcast_task.progress
