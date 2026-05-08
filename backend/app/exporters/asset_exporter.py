import json
import zipfile
from io import BytesIO

from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel
from app.services.storage_service import LocalStorageService, StorageService


class AssetExporter:
    export_type = "image_assets"

    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()

    def export(
        self,
        task_id: str,
        render_model: RenderModel,
        request: ExportRequest,
        asset_ids: list[str] | None = None,
    ) -> ExportResult:
        asset_ids = sorted(set([*(asset_ids or []), *self._collect_asset_ids(render_model)]))
        manifest_assets: list[dict[str, object]] = []
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for asset_id in asset_ids:
                record = self.storage_service.get_record(asset_id)
                if record is None:
                    continue
                archive_name = f"assets/{record.filename}"
                archive.writestr(archive_name, self.storage_service.read_bytes(asset_id))
                manifest_assets.append(
                    {
                        "asset_id": record.asset_id,
                        "filename": record.filename,
                        "content_type": record.content_type,
                        "path": archive_name,
                        "metadata": record.metadata,
                    }
                )
            archive.writestr(
                "manifest.json",
                json.dumps({"task_id": task_id, "assets": manifest_assets}, ensure_ascii=False, indent=2),
            )

        asset_id = f"export_{task_id}_image_assets"
        record = self.storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{task_id}-assets.zip",
            content=buffer.getvalue(),
            content_type="application/zip",
            kind="image_assets",
            metadata={"task_id": task_id, "asset_count": len(manifest_assets)},
        )
        return ExportResult(
            export_type=request.export_type,
            file_url=record.url,
            status="success",
            metadata={"asset_id": record.asset_id, "asset_count": len(manifest_assets)},
        )

    @staticmethod
    def _collect_asset_ids(render_model: RenderModel) -> list[str]:
        urls: list[str] = []
        if getattr(render_model, "render_type", None) == "lecture_page":
            for section in getattr(render_model, "sections", []):
                for block in section.render_blocks:
                    if block.type == "image" and block.asset_url:
                        urls.append(block.asset_url)
        elif getattr(render_model, "render_type", None) == "slide_deck":
            for page in getattr(render_model, "pages", []):
                for element in page.page.get("elements", []):
                    if isinstance(element, dict) and element.get("type") == "image" and isinstance(element.get("src"), str):
                        urls.append(element["src"])
        return [asset_id for asset_id in (AssetExporter._asset_id_from_url(url) for url in urls) if asset_id]

    @staticmethod
    def _asset_id_from_url(url: str) -> str | None:
        marker = "/api/assets/"
        if marker not in url:
            return None
        remainder = url.split(marker, 1)[1]
        return remainder.split("/", 1)[0] or None
