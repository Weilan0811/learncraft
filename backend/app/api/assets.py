from fastapi import APIRouter

from app.services.asset_service import StubAssetService


router = APIRouter()
asset_service = StubAssetService()


@router.get("/{asset_id}")
def get_asset(asset_id: str) -> dict[str, object]:
    return asset_service.get_asset(asset_id)
