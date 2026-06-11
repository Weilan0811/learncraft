import importlib.util
import json
from pathlib import Path


def load_script_module():
    script_path = Path(__file__).parents[1] / "scripts" / "test_unit_text_endpoint.py"
    spec = importlib.util.spec_from_file_location("test_unit_text_endpoint", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self) -> dict:
        return self._payload


class FakeClient:
    def get(self, path: str) -> FakeResponse:
        if path == "/api/content-generation/tasks/task_test/units":
            return FakeResponse(
                200,
                {
                    "task_id": "task_test",
                    "units": [
                        {"unit_id": "unit-01"},
                        {"unit_id": "unit-02"},
                    ],
                },
            )
        if path == "/api/content-generation/tasks/task_test/units/unit-01/text":
            return FakeResponse(200, {"task_id": "task_test", "unit_id": "unit-01", "full_text": "One", "chunks": []})
        if path == "/api/content-generation/tasks/task_test/units/unit-02/text":
            return FakeResponse(200, {"task_id": "task_test", "unit_id": "unit-02", "full_text": "Two", "chunks": []})
        return FakeResponse(404, {"detail": "not found"})


def test_script_saves_each_unit_text_payload_under_task_folder(tmp_path: Path) -> None:
    module = load_script_module()

    result = module.export_unit_text_payloads(FakeClient(), "task_test", tmp_path)

    task_dir = tmp_path / "task_test"
    assert result == [task_dir / "unit-01.json", task_dir / "unit-02.json"]
    assert json.loads((task_dir / "unit-01.json").read_text(encoding="utf-8"))["full_text"] == "One"
    assert json.loads((task_dir / "unit-02.json").read_text(encoding="utf-8"))["full_text"] == "Two"
