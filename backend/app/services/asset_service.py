from pathlib import Path
from typing import Protocol

from app.schemas.assets import AssetResponse
from app.services.storage_service import LocalStorageService, StorageService


class AssetService(Protocol):
    def get_asset(self, asset_id: str) -> AssetResponse | None:
        """Resolve asset metadata and access URL."""
        ...

    def get_file_path(self, asset_id: str) -> Path | None:
        """Resolve an asset file path."""
        ...


class LocalAssetService:
    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()

    def get_asset(self, asset_id: str) -> AssetResponse | None:
        record = self.storage_service.get_record(asset_id)
        if record is None:
            return None
        return AssetResponse(
            asset_id=record.asset_id,
            kind=record.kind,
            filename=record.filename,
            content_type=record.content_type,
            byte_size=record.byte_size,
            checksum_sha256=record.checksum_sha256,
            url=record.url,
            metadata=record.metadata,
        )

    def get_file_path(self, asset_id: str) -> Path | None:
        return self.storage_service.get_file_path(asset_id)
