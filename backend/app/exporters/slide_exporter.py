import json

from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel
from app.services.storage_service import LocalStorageService, StorageService


class SlideExporter:
    export_type = "slide_json"

    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()

    def export(
        self,
        task_id: str,
        render_model: RenderModel,
        request: ExportRequest,
        asset_ids: list[str] | None = None,
    ) -> ExportResult:
        payload = render_model.model_dump(mode="json")
        content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        asset_id = f"export_{task_id}_slide_json"
        record = self.storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{task_id}.json",
            content=content,
            content_type="application/json",
            kind="slide_json",
            metadata={"task_id": task_id, "render_type": getattr(render_model, "render_type", None)},
        )
        return ExportResult(
            export_type=request.export_type,
            file_url=record.url,
            status="success",
            metadata={"asset_id": record.asset_id, "render_type": getattr(render_model, "render_type", None)},
        )
