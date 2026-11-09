import json
import zipfile
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.export import ExportRequest
from app.schemas.render import LectureRenderModel, SlidePageModel, SlideRenderModel
from app.services.storage_service import LocalStorageService
from app.workflows.routers import get_exporter


client = TestClient(app)


def wait_for_completed_task(task_id: str) -> None:
    response = client.get(f"/api/content-generation/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def storage_test_root() -> Path:
    root = Path("storage") / "test_assets" / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_local_storage_saves_bytes_and_manifest_record() -> None:
    storage_root = storage_test_root()
    storage = LocalStorageService(storage_root=storage_root, public_base_url="/api/assets")

    record = storage.save_bytes(
        asset_id="asset_one",
        filename="one.txt",
        content=b"hello asset",
        content_type="text/plain",
        kind="image_assets",
        metadata={"source": "test"},
    )

    assert record.url == "/api/assets/asset_one/download"
    assert record.byte_size == 11
    assert record.metadata == {"source": "test"}
    assert (storage_root / "files" / "asset_one.txt").read_bytes() == b"hello asset"

    manifest = json.loads((storage_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["assets"]["asset_one"]["filename"] == "one.txt"
    assert manifest["assets"]["asset_one"]["content_type"] == "text/plain"


def test_local_storage_preserves_distinct_manifest_records() -> None:
    storage_root = storage_test_root()
    storage = LocalStorageService(storage_root=storage_root, public_base_url="/api/assets")

    storage.save_bytes("asset_one", "one.txt", b"one", "text/plain", "image_assets")
    storage.save_bytes("asset_two", "two.txt", b"two", "text/plain", "image_assets")

    manifest = json.loads((storage_root / "manifest.json").read_text(encoding="utf-8"))
    assert sorted(manifest["assets"]) == ["asset_one", "asset_two"]


def test_local_storage_preserves_manifest_records_across_concurrent_instances() -> None:
    storage_root = storage_test_root()

    def save_asset(index: int) -> str:
        asset_id = f"asset_{index}"
        LocalStorageService(storage_root=storage_root, public_base_url="/api/assets").save_bytes(
            asset_id,
            f"{asset_id}.txt",
            f"content {index}".encode("utf-8"),
            "text/plain",
            "image",
        )
        return asset_id

    with ThreadPoolExecutor(max_workers=4) as executor:
        asset_ids = list(executor.map(save_asset, range(8)))

    verifier = LocalStorageService(storage_root=storage_root, public_base_url="/api/assets")
    assert [verifier.get_record(asset_id).asset_id for asset_id in asset_ids] == asset_ids


def test_unknown_asset_returns_404() -> None:
    response = client.get("/api/assets/does-not-exist")

    assert response.status_code == 404


def test_content_generation_persists_downloadable_image_asset() -> None:
    create_response = client.post(
        "/api/content-generation/tasks",
        json={
            "content_type": "lecture",
            "topic": "人工智能基础导论",
            "user_prompt": "生成一份讲义",
        },
    )

    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]
    wait_for_completed_task(task_id)
    preview_response = client.get(f"/api/content-generation/tasks/{task_id}/preview")
    blocks = preview_response.json()["render_model"]["sections"][0]["render_blocks"]
    image_block = next(block for block in blocks if block["type"] == "image")

    asset_id = image_block["asset_url"].split("/api/assets/", 1)[1].split("/", 1)[0]
    asset_response = client.get(f"/api/assets/{asset_id}")
    assert asset_response.status_code == 200
    asset = asset_response.json()
    assert image_block["asset_url"] == asset["url"]
    assert asset["asset_id"] != "img_stub"
    assert asset["kind"] == "image"
    assert asset["content_type"] == "image/svg+xml"

    download_response = client.get(asset["url"])
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in download_response.content


def test_pdf_export_persists_real_downloadable_asset() -> None:
    create_response = client.post(
        "/api/content-generation/tasks",
        json={
            "content_type": "lecture",
            "topic": "人工智能基础导论",
            "user_prompt": "生成一份讲义",
        },
    )
    task_id = create_response.json()["task_id"]
    wait_for_completed_task(task_id)

    export_response = client.post(f"/api/content-generation/tasks/{task_id}/export", json={"export_type": "pdf"})

    assert export_response.status_code == 200
    exported = export_response.json()
    assert exported["file_url"].startswith("/api/assets/")
    assert exported["file_url"].endswith("/download")

    download_response = client.get(exported["file_url"])
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("application/pdf")
    assert download_response.content.startswith(b"%PDF-")


def test_slide_json_export_persists_valid_json_asset() -> None:
    create_response = client.post(
        "/api/content-generation/tasks",
        json={
            "content_type": "slide_deck",
            "topic": "人工智能基础导论",
            "user_prompt": "生成一份 Slide",
        },
    )
    task_id = create_response.json()["task_id"]
    wait_for_completed_task(task_id)

    export_response = client.post(
        f"/api/content-generation/tasks/{task_id}/export",
        json={"export_type": "slide_json"},
    )

    assert export_response.status_code == 200
    download_response = client.get(export_response.json()["file_url"])
    payload = download_response.json()
    assert payload["render_type"] == "slide_deck"
    assert payload["pages"][0]["version"] == "scenekit.slide/v1"


def test_image_assets_export_writes_zip_manifest() -> None:
    create_response = client.post(
        "/api/content-generation/tasks",
        json={
            "content_type": "lecture",
            "topic": "人工智能基础导论",
            "user_prompt": "生成一份讲义",
        },
    )
    task_id = create_response.json()["task_id"]
    wait_for_completed_task(task_id)

    export_response = client.post(
        f"/api/content-generation/tasks/{task_id}/export",
        json={"export_type": "image_assets"},
    )

    assert export_response.status_code == 200
    zip_asset = client.get(export_response.json()["file_url"])
    assert zip_asset.status_code == 200
    with zipfile.ZipFile(BytesIO(zip_asset.content)) as archive:
        assert "manifest.json" in archive.namelist()
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    assert manifest["assets"][0]["asset_id"].startswith("image_")


def test_get_exporter_routes_by_explicit_export_type() -> None:
    assert get_exporter("pdf").export_type == "pdf"
    assert get_exporter("slide_json").export_type == "slide_json"
    assert get_exporter("image_assets").export_type == "image_assets"


def test_exporters_persist_expected_formats() -> None:
    storage = LocalStorageService(storage_root=storage_test_root(), public_base_url="/api/assets")
    lecture_model = LectureRenderModel(title="Title")
    slide_model = SlideRenderModel(
        title="Deck",
        pages=[
            SlidePageModel(
                page={
                    "id": "slide-1",
                    "title": "Slide 1",
                    "width": 960,
                    "height": 540,
                    "theme": {
                        "backgroundColor": "#FFFFFF",
                        "themeColors": ["#2563eb"],
                        "fontColor": "#111827",
                        "fontName": "Arial",
                    },
                    "elements": [],
                }
            )
        ],
    )

    pdf = get_exporter("pdf", storage_service=storage).export("task_pdf", lecture_model, ExportRequest(export_type="pdf"))
    slide = get_exporter("slide_json", storage_service=storage).export(
        "task_slide",
        slide_model,
        ExportRequest(export_type="slide_json"),
    )

    assert storage.read_bytes(pdf.metadata["asset_id"]).startswith(b"%PDF-")
    assert json.loads(storage.read_bytes(slide.metadata["asset_id"]).decode("utf-8"))["title"] == "Deck"
