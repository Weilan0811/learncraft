import base64
import json
from html import escape

from app.renderers.interactive_html_handout import InteractiveHtmlStaticHandoutRenderer
from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import LectureRenderModel, RenderModel
from app.schemas.render.interactive_html import InteractiveHtmlRenderModel
from app.schemas.render.social_post import SocialPostRenderModel
from app.schemas.specs import ContentSpec
from app.schemas.specs.interactive_html import InteractiveHtmlSpec
from app.services.learning_service import get_learning_service
from app.services.storage_service import LocalStorageService, StorageService


class HTMLExporter:
    export_type = "html"

    def __init__(self, storage_service: StorageService | None = None, learning_service: object | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()
        self.learning_service = learning_service

    def export(
        self,
        task_id: str,
        render_model: RenderModel,
        request: ExportRequest,
        asset_ids: list[str] | None = None,
        content_spec: ContentSpec | None = None,
    ) -> ExportResult:
        if isinstance(render_model, InteractiveHtmlRenderModel):
            return self._export_interactive_html_handout(task_id, render_model, request, content_spec)
        if isinstance(render_model, LectureRenderModel):
            return self._export_lecture_html(task_id, render_model, request)
        if not isinstance(render_model, SocialPostRenderModel):
            return ExportResult(
                export_type=request.export_type,
                file_url="",
                status="failed",
                metadata={"error": "html export is only supported for social_post", "task_id": task_id},
            )
        html_record = self.storage_service.save_bytes(
            asset_id=f"export_{task_id}_html",
            filename=f"{task_id}.html",
            content=render_model.html.encode("utf-8"),
            content_type="text/html; charset=utf-8",
            kind="html",
            metadata={"task_id": task_id, "render_type": render_model.render_type},
        )
        json_record = self.storage_service.save_bytes(
            asset_id=f"export_{task_id}_article_json",
            filename=f"{task_id}.json",
            content=json.dumps(render_model.article_json, ensure_ascii=False, indent=2).encode("utf-8"),
            content_type="application/json",
            kind="html",
            metadata={"task_id": task_id, "render_type": render_model.render_type, "paired_export": html_record.asset_id},
        )
        return ExportResult(
            export_type=request.export_type,
            file_url=html_record.url,
            status="success",
            metadata={"asset_id": html_record.asset_id, "article_json_asset_id": json_record.asset_id, "render_type": render_model.render_type},
        )

    def _export_interactive_html_handout(
        self,
        task_id: str,
        render_model: InteractiveHtmlRenderModel,
        request: ExportRequest,
        content_spec: ContentSpec | None,
    ) -> ExportResult:
        session_id = request.export_options.get("session_id")
        if not isinstance(session_id, str) or not session_id.strip():
            return ExportResult(
                export_type=request.export_type,
                file_url="",
                status="failed",
                metadata={"error": "interactive_html handout export requires session_id", "task_id": task_id},
            )
        if not isinstance(content_spec, InteractiveHtmlSpec):
            return ExportResult(
                export_type=request.export_type,
                file_url="",
                status="failed",
                metadata={"error": "interactive_html content_spec is required for handout export", "task_id": task_id},
            )

        learning_service = self.learning_service or get_learning_service()
        try:
            events = learning_service.list_events(render_model.lesson_id, session_id)
        except ValueError as exc:
            return ExportResult(
                export_type=request.export_type,
                file_url="",
                status="failed",
                metadata={"error": str(exc), "task_id": task_id, "session_id": session_id},
            )

        html = InteractiveHtmlStaticHandoutRenderer(storage_service=self.storage_service).render(
            content_spec,
            render_model,
            events,
            session_id=session_id,
        )
        html_record = self.storage_service.save_bytes(
            asset_id=f"export_{task_id}_offline_handout",
            filename=f"{task_id}-offline-handout.html",
            content=html.encode("utf-8"),
            content_type="text/html; charset=utf-8",
            kind="html",
            metadata={"task_id": task_id, "render_type": "offline_html_handout", "session_id": session_id},
        )
        return ExportResult(
            export_type=request.export_type,
            file_url=html_record.url,
            status="success",
            metadata={"asset_id": html_record.asset_id, "session_id": session_id, "render_type": "offline_html_handout"},
        )

    def _export_lecture_html(
        self,
        task_id: str,
        render_model: LectureRenderModel,
        request: ExportRequest,
    ) -> ExportResult:
        html = self._lecture_html(render_model)
        record = self.storage_service.save_bytes(
            asset_id=f"export_{task_id}_html",
            filename=f"{task_id}.html",
            content=html.encode("utf-8"),
            content_type="text/html; charset=utf-8",
            kind="html",
            metadata={"task_id": task_id, "render_type": render_model.render_type},
        )
        return ExportResult(
            export_type=request.export_type,
            file_url=record.url,
            status="success",
            metadata={
                "asset_id": record.asset_id,
                "render_type": render_model.render_type,
                "byte_size": record.byte_size,
            },
        )

    def _lecture_html(self, render_model: LectureRenderModel) -> str:
        citations: list[str] = []
        sections: list[str] = []
        for section in render_model.sections:
            blocks: list[str] = []
            for block in section.render_blocks:
                if block.type == "image":
                    src = self._image_data_uri(block.asset_url or "") or escape(block.asset_url or "")
                    caption = escape(block.title or block.id)
                    blocks.append(
                        f'<figure><img src="{src}" alt="{caption}">'
                        f"<figcaption>{caption}</figcaption></figure>"
                    )
                    continue
                title = f"<h3>{escape(block.title)}</h3>" if block.title else ""
                content = escape(block.content or "").replace("\n", "<br>")
                markers = self._citation_markers(block.metadata, citations)
                if block.type == "mindmap":
                    blocks.append(f"{title}<pre>{escape(block.content or '')}</pre>{markers}")
                elif content:
                    blocks.append(f"{title}<p>{content}{markers}</p>")
                elif title:
                    blocks.append(title)
            sections.append(f'<section><h2>{escape(section.title)}</h2>{"".join(blocks)}</section>')
        objectives = ""
        if render_model.objectives:
            items = "".join(f"<li>{escape(objective)}</li>" for objective in render_model.objectives)
            objectives = f"<section><h2>学习目标</h2><ul>{items}</ul></section>"
        references = ""
        if citations:
            items = "".join(f"<li><code>{escape(chunk_id)}</code></li>" for chunk_id in citations)
            references = f"<section><h2>引用</h2><ol>{items}</ol></section>"
        return (
            "<!DOCTYPE html>"
            '<html lang="zh-CN"><head><meta charset="utf-8">'
            f"<title>{escape(render_model.title)}</title>"
            "<style>"
            "body{margin:0;background:#f8fafc;color:#0f172a;font-family:'PingFang SC','Microsoft YaHei',sans-serif;line-height:1.8}"
            "main{max-width:840px;margin:0 auto;padding:48px 28px;background:#fff}"
            "h1{font-size:30px;margin:0 0 28px}h2{font-size:22px;margin:36px 0 14px;border-left:4px solid #2563eb;padding-left:12px}"
            "h3{font-size:17px;margin:22px 0 8px;color:#1d4ed8}p{margin:0 0 14px}"
            "figure{margin:20px 0;text-align:center}img{max-width:100%;border-radius:12px;box-shadow:0 12px 30px rgba(15,23,42,.14)}"
            "figcaption{font-size:13px;color:#64748b;margin-top:8px}"
            "pre{background:#f1f5f9;padding:14px;border-radius:10px;overflow:auto;font-size:13px}"
            "ol,ul{padding-left:24px}code{background:#f1f5f9;padding:2px 6px;border-radius:6px;font-size:13px}"
            "@media print{body{background:#fff}main{box-shadow:none;padding:0}}"
            "</style></head><body><main>"
            f"<h1>{escape(render_model.title)}</h1>{objectives}{''.join(sections)}{references}"
            "</main></body></html>"
        )

    def _image_data_uri(self, asset_url: str) -> str | None:
        marker = "/api/assets/"
        if marker not in asset_url:
            return None
        asset_id = asset_url.split(marker, 1)[1].split("/", 1)[0]
        record = self.storage_service.get_record(asset_id)
        if record is None:
            return None
        try:
            encoded = base64.b64encode(self.storage_service.read_bytes(asset_id)).decode("ascii")
        except Exception:
            return None
        return f"data:{record.content_type};base64,{encoded}"

    @staticmethod
    def _citation_markers(metadata: dict[str, object], citations: list[str]) -> str:
        values = metadata.get("citations")
        if not isinstance(values, list):
            return ""
        markers: list[str] = []
        for chunk_id in values:
            value = str(chunk_id)
            if value not in citations:
                citations.append(value)
            markers.append(f"<sup>[{citations.index(value) + 1}]</sup>")
        return "".join(markers)
