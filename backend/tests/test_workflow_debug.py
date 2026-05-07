import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.task import TaskStatus
from app.schemas.request import ContentGenerationRequest
from app.schemas.state import ContentGenerationState
from app.workflows.content_generation_graph import build_content_generation_graph


def test_lecture(monkeypatch: pytest.MonkeyPatch) -> None:
    request = ContentGenerationRequest(
        content_type="lecture",
        topic="人工智能基础",
        user_prompt="生成一份适合初学者阅读的课程讲义",
        knowledge_base_ids=["default"],
        generation_options={
            "language": "zh-CN",
            "difficulty": "introductory",
            "include_images": True,
            "include_mindmap": True,
        },
    )

    final_state = _run_debug_workflow(request, "debug_lecture", monkeypatch)

    assert final_state.status == "completed"
    assert final_state.content_spec is not None
    assert final_state.render_model is not None
    assert final_state.elements


def test_slides(monkeypatch: pytest.MonkeyPatch) -> None:
    request = ContentGenerationRequest(
        content_type="slide_deck",
        topic="人工智能基础",
        user_prompt="生成一份适合课堂导入的 slides",
        knowledge_base_ids=["default"],
        generation_options={
            "language": "zh-CN",
            "difficulty": "introductory",
            "include_images": True,
            "include_mindmap": True,
        },
    )

    final_state = _run_debug_workflow(request, "debug_slides", monkeypatch)

    assert final_state.status == "completed"
    assert final_state.content_spec is not None
    assert final_state.render_model is not None
    assert final_state.elements


def _run_debug_workflow(
    request: ContentGenerationRequest,
    request_prefix: str,
    monkeypatch: pytest.MonkeyPatch,
) -> ContentGenerationState:
    request_id = f"{request_prefix}_{uuid4().hex[:8]}"
    output_dir = Path("storage") / "debug_workflow" / request_id
    steps_dir = output_dir / "steps"
    assets_dir = output_dir / "assets"
    steps_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("CONTENT_GENERATOR_STORAGE_ROOT", str(assets_dir))
    get_settings.cache_clear()
    settings = get_settings()
    if settings.provider_mode != "real":
        pytest.skip("Workflow debug tests require CONTENT_GENERATOR_PROVIDER_MODE=real.")

    state = ContentGenerationState(
        request_id=request_id,
        content_type=request.content_type,
        topic=request.topic,
        user_prompt=request.user_prompt,
        system_prompt=request.system_prompt,
        knowledge_base_ids=request.knowledge_base_ids,
        raw_request=request.model_dump(mode="json"),
        status=TaskStatus.running,
    )

    graph = build_content_generation_graph()
    trace: list[dict[str, Any]] = []
    last_values: dict[str, Any] | None = None

    try:
        for event_type, payload in graph.stream(state, stream_mode=["updates", "values"]):
            if event_type == "values":
                last_values = payload
                continue
            if event_type != "updates":
                continue
            for node_name, node_output in payload.items():
                step_number = len(trace) + 1
                step = {
                    "step": step_number,
                    "node": node_name,
                    "output": _jsonable(node_output),
                }
                trace.append(step)
                print(f"\n[workflow-debug] step {step_number:02d}: {node_name}")
                print(json.dumps(step["output"], ensure_ascii=False, indent=2))
                _write_json(steps_dir / f"{step_number:02d}_{node_name}.json", step)
    finally:
        _write_json(output_dir / "trace.json", trace)
        _write_generated_assets(output_dir, assets_dir)
        get_settings.cache_clear()

    if last_values is None:
        raise AssertionError(f"Workflow did not emit a final state. Partial trace: {output_dir}")

    final_state = ContentGenerationState.model_validate(last_values)
    _write_json(output_dir / "final_state.json", final_state)
    _write_json(output_dir / "content_spec.json", final_state.content_spec)
    _write_json(output_dir / "render_model.json", final_state.render_model)
    _write_json(output_dir / "elements.json", final_state.elements)
    _write_generated_assets(output_dir, assets_dir)

    print(f"\n[workflow-debug] output_dir: {output_dir.resolve()}")
    return final_state


def _write_generated_assets(output_dir: Path, assets_dir: Path) -> None:
    manifest_path = assets_dir / "manifest.json"
    payload: dict[str, Any]
    if manifest_path.exists():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["manifest_path"] = str(manifest_path)
    else:
        payload = {"assets": {}, "manifest_path": str(manifest_path), "missing": True}
    _write_json(output_dir / "generated_assets.json", payload)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(value), ensure_ascii=False, indent=2), encoding="utf-8")


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value
