import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.core.config import get_settings


class WorkflowDebugArtifacts:
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        self.output_dir = Path(get_settings().debug_root) / task_id
        self.steps_dir = self.output_dir / "steps"
        self.trace: list[dict[str, Any]] = []

    def write_step(self, node: str, output: object) -> str:
        step = {"step": len(self.trace) + 1, "node": node, "output": _jsonable(output)}
        self.trace.append(step)
        path = self.steps_dir / f"{step['step']:02d}_{node}.json"
        _write_json(path, step)
        _write_json(self.output_dir / "trace.json", self.trace)
        return str(path)

    def write_state_artifacts(self, state: dict[str, object]) -> None:
        _write_json(self.output_dir / "final_state.json", state)
        if state.get("content_spec") is not None:
            _write_json(self.output_dir / "content_spec.json", state["content_spec"])
        if state.get("render_model") is not None:
            _write_json(self.output_dir / "render_model.json", state["render_model"])
        if state.get("elements") is not None:
            _write_json(self.output_dir / "elements.json", state["elements"])
        _write_json(self.output_dir / "generated_assets.json", {"asset_ids": state.get("asset_ids", [])})


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(value), ensure_ascii=False, indent=2), encoding="utf-8")


def _jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value
