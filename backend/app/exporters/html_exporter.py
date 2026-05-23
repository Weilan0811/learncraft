import json

from app.renderers.interactive_html_handout import InteractiveHtmlStaticHandoutRenderer
from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel
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
