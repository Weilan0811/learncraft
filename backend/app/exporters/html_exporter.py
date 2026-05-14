import json

from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel
from app.schemas.render.social_post import SocialPostRenderModel
from app.services.storage_service import LocalStorageService, StorageService


class HTMLExporter:
    export_type = "html"

    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()

    def export(
        self,
        task_id: str,
        render_model: RenderModel,
        request: ExportRequest,
        asset_ids: list[str] | None = None,
    ) -> ExportResult:
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
