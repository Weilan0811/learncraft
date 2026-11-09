from sqlmodel import Session, select

from app.core.asset import AssetStatus
from app.core.task import TaskStatus
from app.models.content_generation_asset import ContentGenerationAsset
from app.models.content_generation_task import ContentGenerationTask
from app.services.asset_repository import AssetRepository
from app.services.task_repository import SQLModelTaskRepository, now_utc


INTERRUPTED_REASON = "服务重启，任务执行被中断；已生成的内容仍然保留。"
RETRY_INTERRUPTED_REASON = "服务重启，资源重试被中断。"


def recover_interrupted_tasks(
    repository: SQLModelTaskRepository,
    *,
    reason: str = INTERRUPTED_REASON,
) -> dict[str, int]:
    """Mark leftover running work as interrupted after a single-process restart.

    Only enable this when the backend runs as one process: with several workers
    each worker would wrongly interrupt tasks that another worker is still
    executing.
    """
    with Session(repository.engine) as session:
        tasks = list(
            session.exec(
                select(ContentGenerationTask).where(
                    ContentGenerationTask.status.in_(
                        [TaskStatus.queued.value, TaskStatus.running.value]
                    )
                )
            ).all()
        )
        for task in tasks:
            progress = dict(task.progress or {})
            progress.update(
                {
                    "stage": TaskStatus.interrupted.value,
                    "display_stage": TaskStatus.interrupted.value,
                    "current_stage": TaskStatus.interrupted.value,
                    "interrupted_reason": reason,
                }
            )
            task.progress = progress
            task.status = TaskStatus.interrupted.value
            task.error_message = reason
            task.updated_at = now_utc()
            session.add(task)

        retrying_assets = list(
            session.exec(
                select(ContentGenerationAsset).where(
                    ContentGenerationAsset.status == AssetStatus.retrying.value
                )
            ).all()
        )
        affected_task_ids: set[str] = set()
        for asset in retrying_assets:
            asset.status = AssetStatus.failed.value
            asset.error_message = RETRY_INTERRUPTED_REASON
            asset.updated_at = now_utc()
            session.add(asset)
            affected_task_ids.add(asset.task_id)

        asset_repository = AssetRepository(session)
        for task_id in affected_task_ids:
            task = session.get(ContentGenerationTask, task_id)
            if task is None:
                continue
            progress = dict(task.progress or {})
            progress["resource_summary"] = asset_repository.summary(task_id)
            task.progress = progress
            task.updated_at = now_utc()
            session.add(task)

        session.commit()
        return {"interrupted_tasks": len(tasks), "reset_assets": len(retrying_assets)}


__all__ = ["INTERRUPTED_REASON", "recover_interrupted_tasks"]
