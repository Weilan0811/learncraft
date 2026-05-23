from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel
from app.schemas.render.podcast import PodcastRenderModel
from app.services.storage_service import LocalStorageService, StorageService


class MarkdownExporter:
    export_type = "markdown"

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
        if isinstance(render_model, PodcastRenderModel):
            content = f"# {render_model.title}\n\n{render_model.script_text}\n"
            record = self.storage_service.save_bytes(
                asset_id=f"export_{task_id}_podcast_script",
                filename=f"{task_id}_podcast_script.md",
                content=content.encode("utf-8"),
                content_type="text/markdown; charset=utf-8",
                kind="markdown",
                metadata={"task_id": task_id, "render_type": render_model.render_type},
            )
            return ExportResult(
                export_type=request.export_type,
                file_url=record.url,
                status="success",
                metadata={"asset_id": record.asset_id, "render_type": render_model.render_type},
            )
        return ExportResult(export_type="markdown", file_url=f"/api/assets/export/{task_id}.md", status="success")
