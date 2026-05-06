from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.schemas.assets import AssetResponse
from app.services.asset_service import LocalAssetService


router = APIRouter()
asset_service = LocalAssetService()


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str) -> AssetResponse:
    asset = asset_service.get_asset(asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.get("/{asset_id}/download")
def download_asset(asset_id: str) -> FileResponse:
    asset = asset_service.get_asset(asset_id)
    file_path = asset_service.get_file_path(asset_id)
    if asset is None or file_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return FileResponse(path=file_path, media_type=asset.content_type, filename=asset.filename)
