from functools import lru_cache
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as ReportLabImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import LectureRenderModel, RenderModel
from app.services.storage_service import LocalStorageService, StorageService


_FONT_CANDIDATES: tuple[tuple[str, str, int | None], ...] = (
    ("MicrosoftYaHei", "C:/Windows/Fonts/msyh.ttc", 0),
    ("SimHei", "C:/Windows/Fonts/simhei.ttf", None),
    ("SimSun", "C:/Windows/Fonts/simsun.ttc", 0),
    ("NotoSansCJK", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
    ("WenQuanYiZenHei", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
)


@lru_cache(maxsize=1)
def _cjk_font_name() -> str:
    for name, path, subfont_index in _FONT_CANDIDATES:
        if not Path(path).exists():
            continue
        try:
            font = (
                TTFont(name, path, subfontIndex=subfont_index)
                if subfont_index is not None
                else TTFont(name, path)
            )
            pdfmetrics.registerFont(font)
            return name
        except Exception:
            continue
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    return "STSong-Light"


class PDFExporter:
    export_type = "pdf"

    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()

    def export(
        self,
        task_id: str,
        render_model: RenderModel,
        request: ExportRequest,
        asset_ids: list[str] | None = None,
        content_spec: object | None = None,
    ) -> ExportResult:
        if not isinstance(render_model, LectureRenderModel):
            return ExportResult(
                export_type=request.export_type,
                file_url="",
                status="failed",
                metadata={"task_id": task_id, "error": "PDF 导出当前支持讲义（lecture）。"},
            )
        try:
            content, stats = self._build_pdf(render_model)
        except Exception as exc:
            return ExportResult(
                export_type=request.export_type,
                file_url="",
                status="failed",
                metadata={"task_id": task_id, "error": f"PDF 生成失败：{exc}"},
            )
        asset_id = f"export_{task_id}_pdf"
        record = self.storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{task_id}.pdf",
            content=content,
            content_type="application/pdf",
            kind="pdf",
            metadata={"task_id": task_id, "render_type": render_model.render_type, **stats},
        )
        return ExportResult(
            export_type=request.export_type,
            file_url=record.url,
            status="success",
            metadata={
                "asset_id": record.asset_id,
                "render_type": render_model.render_type,
                "byte_size": record.byte_size,
                **stats,
            },
        )

    def _build_pdf(self, render_model: LectureRenderModel) -> tuple[bytes, dict[str, object]]:
        font_name = _cjk_font_name()
        styles = self._styles(font_name)
        story = [
            Paragraph(escape(render_model.title or "讲义"), styles["title"]),
            Spacer(1, 6),
        ]
        if render_model.objectives:
            story.append(Paragraph("学习目标", styles["heading"]))
            for objective in render_model.objectives:
                story.append(Paragraph(f"• {escape(objective)}", styles["body"]))

        citation_order: list[str] = []
        image_count = 0
        for section in render_model.sections:
            story.append(Paragraph(escape(section.title), styles["heading"]))
            for block in section.render_blocks:
                if block.type == "image":
                    flowable, embedded = self._image_flowable(block, styles)
                    if embedded:
                        image_count += 1
                    story.append(flowable)
                    story.append(Spacer(1, 6))
                    continue
                if block.title:
                    story.append(Paragraph(escape(block.title), styles["subheading"]))
                content = block.content or ""
                if block.type == "mindmap":
                    story.append(Paragraph(escape(content).replace("\n", "<br/>"), styles["code"]))
                elif content:
                    markers = self._citation_markers(block.metadata, citation_order)
                    story.append(Paragraph(f"{escape(content)}{markers}", styles["body"]))
                story.append(Spacer(1, 4))

        if citation_order:
            story.append(Paragraph("引用", styles["heading"]))
            for index, chunk_id in enumerate(citation_order, start=1):
                story.append(Paragraph(f"[{index}] {escape(chunk_id)}", styles["small"]))

        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=render_model.title,
            author="Content Generator Agent",
        )
        document.build(
            story,
            onFirstPage=lambda canvas, doc: _draw_footer(canvas, doc, font_name),
            onLaterPages=lambda canvas, doc: _draw_footer(canvas, doc, font_name),
        )
        return buffer.getvalue(), {
            "page_count": document.page,
            "section_count": len(render_model.sections),
            "image_count": image_count,
            "citation_count": len(citation_order),
        }

    @staticmethod
    def _styles(font_name: str) -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "CJKTitle",
                parent=base["Title"],
                fontName=font_name,
                fontSize=22,
                leading=30,
                spaceAfter=10,
            ),
            "heading": ParagraphStyle(
                "CJKHeading",
                parent=base["Heading2"],
                fontName=font_name,
                fontSize=15,
                leading=22,
                spaceBefore=14,
                spaceAfter=8,
                textColor=colors.HexColor("#0f172a"),
            ),
            "subheading": ParagraphStyle(
                "CJKSubheading",
                parent=base["Heading3"],
                fontName=font_name,
                fontSize=12,
                leading=18,
                spaceBefore=6,
                spaceAfter=4,
                textColor=colors.HexColor("#1d4ed8"),
            ),
            "body": ParagraphStyle(
                "CJKBody",
                parent=base["BodyText"],
                fontName=font_name,
                fontSize=11,
                leading=18,
                spaceAfter=6,
            ),
            "small": ParagraphStyle(
                "CJKSmall",
                parent=base["BodyText"],
                fontName=font_name,
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#475569"),
            ),
            "code": ParagraphStyle(
                "CJKCode",
                parent=base["BodyText"],
                fontName=font_name,
                fontSize=9,
                leading=14,
                backColor=colors.HexColor("#f1f5f9"),
                borderPadding=6,
                spaceAfter=6,
            ),
        }

    def _image_flowable(self, block, styles) -> tuple[object, bool]:
        asset_url = getattr(block, "asset_url", None) or ""
        path = self._local_path(asset_url)
        if path is None or path.suffix.lower() == ".svg":
            return Paragraph(f"[图片不可用：{escape(block.title or block.id)}]", styles["small"]), False
        try:
            reader = ImageReader(str(path))
            width, height = reader.getSize()
            max_width = 160 * mm
            max_height = 95 * mm
            scale = min(max_width / width, max_height / height, 1.0)
            image = ReportLabImage(str(path), width=width * scale, height=height * scale)
        except Exception:
            return Paragraph(f"[图片读取失败：{escape(block.title or block.id)}]", styles["small"]), False
        if block.title:
            return KeepTogether([image, Spacer(1, 3), Paragraph(escape(block.title), styles["small"])]), True
        return image, True

    def _local_path(self, asset_url: str) -> Path | None:
        marker = "/api/assets/"
        if marker not in asset_url:
            return None
        asset_id = asset_url.split(marker, 1)[1].split("/", 1)[0]
        return self.storage_service.get_file_path(asset_id)

    @staticmethod
    def _citation_markers(metadata: dict[str, object], citation_order: list[str]) -> str:
        citations = metadata.get("citations")
        if not isinstance(citations, list):
            return ""
        markers: list[str] = []
        for chunk_id in citations:
            value = str(chunk_id)
            if value not in citation_order:
                citation_order.append(value)
            markers.append(f"<super>[{citation_order.index(value) + 1}]</super>")
        return "".join(markers)


def _draw_footer(canvas, document, font_name: str) -> None:
    canvas.saveState()
    canvas.setFont(font_name, 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"第 {document.page} 页")
    canvas.restoreState()
