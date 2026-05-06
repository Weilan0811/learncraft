import json
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.export import ExportRequest
from app.schemas.render import LectureRenderModel, SlidePageModel, SlideRenderModel
from app.services.storage_service import LocalStorageService
from app.workflows.routers import get_exporter


client = TestClient(app)


def test_local_storage_saves_bytes_and_manifest_record(tmp_path: Path) -> None:
    storage = LocalStorageService(storage_root=tmp_path, public_base_url="/api/assets")

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
    assert (tmp_path / "files" / "asset_one.txt").read_bytes() == b"hello asset"

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["assets"]["asset_one"]["filename"] == "one.txt"
    assert manifest["assets"]["asset_one"]["content_type"] == "text/plain"


def test_local_storage_preserves_distinct_manifest_records(tmp_path: Path) -> None:
    storage = LocalStorageService(storage_root=tmp_path, public_base_url="/api/assets")

    storage.save_bytes("asset_one", "one.txt", b"one", "text/plain", "image_assets")
    storage.save_bytes("asset_two", "two.txt", b"two", "text/plain", "image_assets")

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert sorted(manifest["assets"]) == ["asset_one", "asset_two"]


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
            "output_formats": ["preview"],
            "generation_options": {"include_images": True},
        },
    )

    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]
    preview_response = client.get(f"/api/content-generation/tasks/{task_id}/preview")
    blocks = preview_response.json()["render_model"]["sections"][0]["render_blocks"]
    image_block = next(block for block in blocks if block["type"] == "image")

    asset_response = client.get("/api/assets/img_stub")
    assert asset_response.status_code == 200
    asset = asset_response.json()
    assert image_block["asset_url"] == asset["url"]
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
            "output_formats": ["preview"],
        },
    )
    task_id = create_response.json()["task_id"]

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
            "output_formats": ["preview"],
        },
    )
    task_id = create_response.json()["task_id"]

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
            "output_formats": ["preview"],
            "generation_options": {"include_images": True},
        },
    )
    task_id = create_response.json()["task_id"]

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
    assert manifest["assets"][0]["asset_id"] == "img_stub"


def test_get_exporter_routes_by_explicit_export_type() -> None:
    assert get_exporter("pdf").export_type == "pdf"
    assert get_exporter("slide_json").export_type == "slide_json"
    assert get_exporter("image_assets").export_type == "image_assets"


def test_exporters_persist_expected_formats(tmp_path: Path) -> None:
    storage = LocalStorageService(storage_root=tmp_path, public_base_url="/api/assets")
    lecture_model = LectureRenderModel(title="Title")
    slide_model = SlideRenderModel(
        title="Deck",
        pages=[SlidePageModel(page={"id": "slide-1", "elements": []})],
    )

    pdf = get_exporter("pdf", storage_service=storage).export("task_pdf", lecture_model, ExportRequest(export_type="pdf"))
    slide = get_exporter("slide_json", storage_service=storage).export(
        "task_slide",
        slide_model,
        ExportRequest(export_type="slide_json"),
    )

    assert storage.read_bytes(pdf.metadata["asset_id"]).startswith(b"%PDF-")
    assert json.loads(storage.read_bytes(slide.metadata["asset_id"]).decode("utf-8"))["title"] == "Deck"
