import json
from pathlib import Path

from app.core.config import get_settings
from app.schemas.state import TaskStreamEvent


class TaskEventStore:
    def __init__(self, log_root: str | Path | None = None) -> None:
        self.directory = Path(log_root or get_settings().log_root) / "content-generation"

    def get_events(self, task_id: str) -> list[TaskStreamEvent]:
        path = self.directory / f"{task_id}.events.json"
        if not path.exists():
            return []
        return [TaskStreamEvent.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]

    def save_events(self, task_id: str, events: list[TaskStreamEvent]) -> None:
        if not events:
            return
        existing = {event.event_id: event for event in self.get_events(task_id)}
        existing.update({event.event_id: event for event in events})
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{task_id}.events.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps([event.model_dump(mode="json") for event in existing.values()], ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(path)
