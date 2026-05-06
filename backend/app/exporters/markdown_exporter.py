from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel


class MarkdownExporter:
    def export(self, task_id: str, render_model: RenderModel, request: ExportRequest) -> ExportResult:
        return ExportResult(export_type="markdown", file_url=f"/api/assets/export/{task_id}.md", status="success")
