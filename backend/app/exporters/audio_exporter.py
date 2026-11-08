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
        if not render_model.final_audio_url:
            return ExportResult(
                export_type=request.export_type,
                file_url="",
                status="failed",
                metadata={
                    "task_id": task_id,
                    "render_type": render_model.render_type,
                    "error": "完整音频尚未合成，请先处理失败的分段或音频合成警告后重试。",
                },
            )
        return ExportResult(
            export_type=request.export_type,
            file_url=render_model.final_audio_url,
            status="success",
            metadata={
                "task_id": task_id,
                "render_type": render_model.render_type,
                "mode": "final_audio",
                "duration_seconds": render_model.final_audio_duration_seconds,
            },
        )
