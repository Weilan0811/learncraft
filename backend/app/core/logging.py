import logging
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from app.core.config import get_settings


LogLevel = Literal["debug", "info", "warning", "error"]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def task_log_file_path(task_id: str) -> Path:
    return Path(get_settings().log_root) / "content-generation" / f"{task_id}.log"


def build_workflow_log_entry(
    *,
    task_id: str,
    content_type: str,
    event: str,
    message: str,
    level: LogLevel = "info",
    node: str | None = None,
    unit_id: str | None = None,
    detail: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": level,
        "event": event,
        "message": message,
        "task_id": task_id,
        "content_type": content_type,
        "node": node,
        "unit_id": unit_id,
        "detail": detail or {},
    }


def write_task_log_entry(entry: dict[str, object]) -> None:
    task_id = str(entry["task_id"])
    path = task_log_file_path(task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, default=str))
        handle.write("\n")


def append_workflow_log(
    logs: list[dict[str, object]],
    *,
    task_id: str,
    content_type: str,
    event: str,
    message: str,
    level: LogLevel = "info",
    node: str | None = None,
    unit_id: str | None = None,
    detail: dict[str, object] | None = None,
    write_file: bool = True,
) -> list[dict[str, object]]:
    entry = build_workflow_log_entry(
        task_id=task_id,
        content_type=content_type,
        event=event,
        message=message,
        level=level,
        node=node,
        unit_id=unit_id,
        detail=detail,
    )
    if write_file:
        write_task_log_entry(entry)
    return [*logs, entry]
