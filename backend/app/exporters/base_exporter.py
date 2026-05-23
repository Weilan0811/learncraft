from typing import Protocol

from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel
from app.schemas.specs import ContentSpec


class Exporter(Protocol):
    def export(
        self,
        task_id: str,
        render_model: RenderModel,
        request: ExportRequest,
        asset_ids: list[str] | None = None,
        content_spec: ContentSpec | None = None,
    ) -> ExportResult:
        """Export rendered content to a target format."""
        ...
