from typing import Literal

from pydantic import Field

from app.schemas.base import Metadata, SchemaModel


AssetKind = Literal["image", "pdf", "slide_json", "image_assets", "html", "audio", "markdown"]


class AssetRecord(SchemaModel):
    asset_id: str
    kind: AssetKind
    filename: str
    content_type: str
    byte_size: int
    checksum_sha256: str
    storage_path: str
    created_at: str
    url: str
    metadata: Metadata = Field(default_factory=dict)


class AssetResponse(SchemaModel):
    asset_id: str
    kind: AssetKind
    filename: str
    content_type: str
    byte_size: int
    checksum_sha256: str
    url: str
    metadata: Metadata = Field(default_factory=dict)
