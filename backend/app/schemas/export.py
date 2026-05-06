from typing import Literal

from pydantic import Field

from app.schemas.base import ExportType, SchemaModel


class ExportRequest(SchemaModel):
    export_type: ExportType
    export_options: dict[str, object] = Field(default_factory=dict)


class ExportFile(SchemaModel):
    type: ExportType
    url: str


class ExportResult(SchemaModel):
    export_type: ExportType
    file_url: str
    status: Literal["success", "failed"] = "success"
    metadata: dict[str, object] = Field(default_factory=dict)
