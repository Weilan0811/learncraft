from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


DEFAULT_TASK_ID = "task_3e9c42218469"


def configure_imports_and_database() -> None:
    script_path = Path(__file__).resolve()
    backend_root = script_path.parents[1]
    repo_root = script_path.parents[2]
    sys.path.insert(0, str(backend_root))
    database_path = repo_root / "storage" / "tasks.db"
    os.environ["CONTENT_GENERATOR_DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export references endpoint payloads for a content generation task.")
    parser.add_argument("task_id", nargs="?", default=DEFAULT_TASK_ID, help=f"Task id to export. Default: {DEFAULT_TASK_ID}")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory. Defaults to backend/scripts/<task_id>_references.",
    )
    return parser.parse_args(argv)


def get_json(client: Any, path: str) -> dict[str, Any]:
    response = client.get(path)
    print(f"GET {path} -> {response.status_code}")
    payload: dict[str, Any]
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw_text": response.text}
    return {
        "path": path,
        "status_code": response.status_code,
        "payload": payload,
    }


def export_references_payloads(client: Any, task_id: str, output_dir: Path) -> list[Path]:
    units_result = get_json(client, f"/api/content-generation/tasks/{task_id}/units")
    if units_result["status_code"] != 200:
        raise RuntimeError(json.dumps(units_result, ensure_ascii=False, indent=2))

    units = units_result["payload"].get("units", [])
    if not isinstance(units, list) or not units:
        raise RuntimeError(f"No units returned for task: {task_id}")

    output_dir.mkdir(parents=True, exist_ok=True)
    written_files: list[Path] = []

    task_references = get_json(client, f"/api/content-generation/tasks/{task_id}/references")
    task_output_path = output_dir / f"{task_id}_references.json"
    task_output_path.write_text(json.dumps(task_references["payload"], ensure_ascii=False, indent=2), encoding="utf-8")
    written_files.append(task_output_path)
    print(f"saved: {task_output_path}")

    for unit in units:
        unit_id = unit.get("unit_id") if isinstance(unit, dict) else None
        if not isinstance(unit_id, str) or not unit_id:
            continue
        unit_references = get_json(client, f"/api/content-generation/tasks/{task_id}/units/{unit_id}/references")
        unit_output_path = output_dir / f"{task_id}_{unit_id}_references.json"
        unit_output_path.write_text(json.dumps(unit_references["payload"], ensure_ascii=False, indent=2), encoding="utf-8")
        written_files.append(unit_output_path)
        print(f"saved: {unit_output_path}")

    return written_files


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args(argv)
    configure_imports_and_database()

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    try:
        script_dir = Path(__file__).resolve().parent
        output_dir = Path(args.output_dir) if args.output_dir else script_dir / f"{args.task_id}_references"
        written_files = export_references_payloads(client, args.task_id, output_dir)
    except RuntimeError as exc:
        print(str(exc))
        return 1

    print(f"exported {len(written_files)} references payload files under {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
