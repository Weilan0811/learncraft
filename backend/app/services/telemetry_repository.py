from sqlmodel import Session

from app.services.artifact_repository import ArtifactRepository


class TelemetryRepository:
    def __init__(self, session: Session) -> None:
        self.artifacts = ArtifactRepository(session)

    def append_metrics(self, task_id: str, metrics: list[dict[str, object]]) -> None:
        for metric in metrics:
            self.artifacts.append_metric(task_id, metric)
