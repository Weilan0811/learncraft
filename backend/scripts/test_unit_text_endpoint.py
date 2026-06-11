from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


DEFAULT_TASK_ID = "task_a24a102c6a85"


def configure_imports_and_database() -> None:
    script_path = Path(__file__).resolve()
    backend_root = script_path.parents[1]
    repo_root = script_path.parents[2]
    sys.path.insert(0, str(backend_root))
    database_path = repo_root / "storage" / "tasks.db"
    os.environ["CONTENT_GENERATOR_DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"


def repo_storage_root() -> Path:
    return Path(__file__).resolve().parents[2] / "storage"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export unit plain-text endpoint payloads for a task.")
    parser.add_argument("task_id", nargs="?", default=DEFAULT_TASK_ID, help="Task id to export, e.g. task_a24a102c6a85")
    return parser.parse_args(argv)


def export_unit_text_payloads(client, task_id: str, storage_root: Path) -> list[Path]:
    units_response = client.get(f"/api/content-generation/tasks/{task_id}/units")
    print(f"GET /tasks/{task_id}/units -> {units_response.status_code}")
    if units_response.status_code != 200:
        raise RuntimeError(units_response.text)

    units = units_response.json()["units"]
    if not units:
        raise RuntimeError(f"No units returned for task: {task_id}")

    task_dir = storage_root / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    written_files: list[Path] = []
    for unit in units:
        unit_id = unit["unit_id"]
        text_response = client.get(f"/api/content-generation/tasks/{task_id}/units/{unit_id}/text")
        print(f"GET /tasks/{task_id}/units/{unit_id}/text -> {text_response.status_code}")
        if text_response.status_code != 200:
            raise RuntimeError(text_response.text)

        payload = text_response.json()
        output_path = task_dir / f"{unit_id}.json"
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        written_files.append(output_path)
        print(
            f"saved: {output_path} "
            f"(full_text_length={len(payload['full_text'])}, chunk_count={len(payload['chunks'])})"
        )

    return written_files


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    configure_imports_and_database()

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    try:
        written_files = export_unit_text_payloads(client, args.task_id, repo_storage_root())
    except RuntimeError as exc:
        print(str(exc))
        return 1

    print(f"exported {len(written_files)} unit payloads under {written_files[0].parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
