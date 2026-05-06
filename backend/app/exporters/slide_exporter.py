from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel


class SlideExporter:
    def export(self, task_id: str, render_model: RenderModel, request: ExportRequest) -> ExportResult:
        return ExportResult(
            export_type="slide_json",
            file_url=f"/api/assets/export/{task_id}.json",
            status="success",
            metadata={"stub": True, "render_type": getattr(render_model, "render_type", None)},
        )
