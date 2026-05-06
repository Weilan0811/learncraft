from typing import Protocol


class AssetService(Protocol):
    def get_asset(self, asset_id: str) -> dict[str, object]:
        """Resolve asset metadata or access URL."""
        ...


class StubAssetService:
    def get_asset(self, asset_id: str) -> dict[str, object]:
        return {
            "asset_id": asset_id,
            "status": "available",
            "url": f"/api/assets/{asset_id}",
            "metadata": {"stub": True},
        }
