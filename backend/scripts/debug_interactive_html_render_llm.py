"""
Replay the interactive_html render-stage LLM call for one workflow debug task.

Default target: task_428771b383fd.

Examples:
  uv run python backend/scripts/debug_interactive_html_render_llm.py --dry-run
  uv run python backend/scripts/debug_interactive_html_render_llm.py --call-api --timeout 180 --max-retries 0
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings
from app.renderers.interactive_html_explanation_composer import (
    ExplanationHtmlComposer,
    InteractiveHtmlExplanationRender,
    INTERACTION_BLOCK_TYPES,
)
from app.schemas.specs.interactive_html import InteractiveHtmlSectionSpec
from app.schemas.specs.interactive_html_style import DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE
from app.services.llm_service import BailianLLMService


DEFAULT_TASK_ID = "task_428771b383fd"


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay interactive_html render LLM call from workflow debug state.")
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID, help=f"Workflow debug task id. Default: {DEFAULT_TASK_ID}")
    parser.add_argument("--debug-root", default=str(REPO_ROOT / "storage" / "debug_workflow"))
    parser.add_argument("--output-dir", default=str(REPO_ROOT / "storage" / "debug_llm_replay"))
    parser.add_argument("--timeout", type=float, default=None, help="Override request timeout seconds.")
    parser.add_argument("--max-retries", type=int, default=None, help="Override max retries.")
    parser.add_argument("--call-api", action="store_true", help="Actually call the configured Bailian/OpenAI-compatible API.")
    parser.add_argument("--dry-run", action="store_true", help="Only build and save prompt/payload; do not call API.")
    args = parser.parse_args()

    if args.dry_run and args.call_api:
        raise SystemExit("Choose only one of --dry-run or --call-api.")

    settings = get_settings()
    state = _load_final_state(Path(args.debug_root), args.task_id)
    section_spec = InteractiveHtmlSectionSpec.model_validate(state["current_unit_spec"])
    style_scope_id = f"ih-scope-{section_spec.section_id}"
    retrieval_context = _current_retrieval_context(state)
    explanation_spec = _build_explanation_only_spec(section_spec)

    prompt = ExplanationHtmlComposer()._build_render_prompt(
        section_spec=explanation_spec,
        style_guide=DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE,
        style_scope_id=style_scope_id,
        retrieval_context=retrieval_context,
    )
    schema = InteractiveHtmlExplanationRender.model_json_schema()
    payload = _build_chat_payload(settings.text_model, prompt, schema)

    output_dir = Path(args.output_dir) / args.task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "render_prompt.txt").write_text(prompt, encoding="utf-8")
    (output_dir / "render_schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "request_payload.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "explanation_unit_spec.json").write_text(
        explanation_spec.model_dump_json(indent=2),
        encoding="utf-8",
    )

    summary = {
        "task_id": args.task_id,
        "unit_id": state.get("current_unit_id"),
        "section_id": section_spec.section_id,
        "model": settings.text_model,
        "base_url": settings.bailian_base_url,
        "timeout_seconds": args.timeout if args.timeout is not None else settings.request_timeout_seconds,
        "max_retries": args.max_retries if args.max_retries is not None else settings.max_retries,
        "api_key_present": bool(settings.bailian_api_key),
        "retrieval_chunks": len(retrieval_context),
        "retrieval_chars": sum(len(str(chunk.get("content") or "")) for chunk in retrieval_context),
        "teaching_blocks_original": len(section_spec.teaching_flow),
        "teaching_blocks_sent_to_render_llm": len(explanation_spec.teaching_flow),
        "interaction_specs": len(section_spec.interaction_specs),
        "prompt_chars": len(prompt),
        "schema_chars": len(json.dumps(schema, ensure_ascii=False)),
        "payload_chars": len(json.dumps(payload, ensure_ascii=False)),
        "output_dir": str(output_dir),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if not args.call_api:
        print("\nDry run complete. Add --call-api to send this payload to the configured API.")
        return

    service = BailianLLMService(
        api_key=settings.bailian_api_key or "",
        model=settings.text_model,
        base_url=settings.bailian_base_url,
        timeout_seconds=args.timeout if args.timeout is not None else settings.request_timeout_seconds,
        max_retries=args.max_retries if args.max_retries is not None else settings.max_retries,
    )

    started = time.perf_counter()
    try:
        rendered = service.generate_structured(prompt=prompt, schema=InteractiveHtmlExplanationRender)
    except Exception as exc:
        elapsed = time.perf_counter() - started
        failure = {
            "ok": False,
            "elapsed_seconds": round(elapsed, 3),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        (output_dir / "result_failure.json").write_text(json.dumps(failure, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(failure, ensure_ascii=False, indent=2))
        raise SystemExit(1) from exc

    elapsed = time.perf_counter() - started
    result = {
        "ok": True,
        "elapsed_seconds": round(elapsed, 3),
        "usage": service.last_usage,
        "rendered": rendered.model_dump(mode="json"),
    }
    (output_dir / "result_success.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "elapsed_seconds": round(elapsed, 3),
        "usage": service.last_usage,
        "result_path": str(output_dir / "result_success.json"),
    }, ensure_ascii=False, indent=2))


def _load_final_state(debug_root: Path, task_id: str) -> dict[str, Any]:
    path = debug_root / task_id / "final_state.json"
    if not path.exists():
        raise SystemExit(f"final_state.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _current_retrieval_context(state: dict[str, Any]) -> list[dict[str, Any]]:
    current = state.get("current_unit_context")
    if current:
        return current
    unit_id = state.get("current_unit_id")
    context_map = state.get("unit_context_map") or {}
    return list(context_map.get(unit_id) or [])


def _build_explanation_only_spec(section_spec: InteractiveHtmlSectionSpec) -> InteractiveHtmlSectionSpec:
    interaction_block_ids = {spec.block_id for spec in section_spec.interaction_specs}
    return section_spec.model_copy(
        update={
            "teaching_flow": [
                block for block in section_spec.teaching_flow
                if block.block_type not in INTERACTION_BLOCK_TYPES
                and block.block_id not in interaction_block_ids
            ],
            "interaction_specs": [],
        }
    )


def _build_chat_payload(model: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You generate strictly valid JSON for backend services. "
                    "Return JSON only, with no Markdown fences or commentary."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{prompt}\n\n"
                    "The response must validate against this JSON Schema:\n"
                    f"{json.dumps(schema, ensure_ascii=False)}"
                ),
            },
        ],
        "response_format": {"type": "json_object"},
    }


if __name__ == "__main__":
    main()
