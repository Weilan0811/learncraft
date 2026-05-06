from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel


class AssetExporter:
    def export(self, task_id: str, render_model: RenderModel, request: ExportRequest) -> ExportResult:
        return ExportResult(export_type="image_assets", file_url=f"/api/assets/export/{task_id}.zip", status="success")
