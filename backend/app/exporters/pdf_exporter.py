from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel


class PDFExporter:
    def export(self, task_id: str, render_model: RenderModel, request: ExportRequest) -> ExportResult:
        return ExportResult(
            export_type="pdf",
            file_url=f"/api/assets/export/{task_id}.pdf",
            status="success",
            metadata={"stub": True, "render_type": getattr(render_model, "render_type", None)},
        )
