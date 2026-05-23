from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel
from app.schemas.render.podcast import PodcastRenderModel
from app.services.storage_service import StorageService


class AudioExporter:
    export_type = "audio"

    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service

    def export(
        self,
        task_id: str,
        render_model: RenderModel,
        request: ExportRequest,
        asset_ids: list[str] | None = None,
        content_spec: object | None = None,
    ) -> ExportResult:
        if not isinstance(render_model, PodcastRenderModel):
            return ExportResult(
                export_type=request.export_type,
                file_url="",
                status="failed",
                metadata={"error": "audio export is only supported for podcast_script", "task_id": task_id},
            )
        file_url = render_model.final_audio_url or render_model.audio_manifest_url or ""
        return ExportResult(
            export_type=request.export_type,
            file_url=file_url,
            status="success" if file_url else "failed",
            metadata={
                "task_id": task_id,
                "render_type": render_model.render_type,
                "mode": "final_audio" if render_model.final_audio_url else "manifest",
            },
        )
