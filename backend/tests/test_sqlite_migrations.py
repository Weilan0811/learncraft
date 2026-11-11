from datetime import datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import MetaData, Table, inspect, select
from sqlmodel import SQLModel, create_engine

from app.schemas.request import ContentGenerationRequest
from app.services.task_repository import SQLModelTaskRepository


def migration_config(connection) -> Config:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    config.attributes["connection"] = connection
    return config


def assert_current_schema(repository: SQLModelTaskRepository) -> None:
    with repository.engine.begin() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == "20260702_0008"
        command.upgrade(migration_config(connection), "head")
        assert "status" in {
            column["name"] for column in inspect(connection).get_columns("content_generation_asset")
        }


def test_new_sqlite_database_records_revision_and_can_upgrade_again(tmp_path):
    repository = SQLModelTaskRepository(database_url=f"sqlite:///{tmp_path / 'new.db'}")
    try:
        assert_current_schema(repository)
    finally:
        repository.engine.dispose()


def test_startup_upgrades_versioned_sqlite_without_losing_tasks(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'versioned.db'}"
    engine = create_engine(database_url)
    with engine.begin() as connection:
        command.upgrade(migration_config(connection), "20260630_0006")
    engine.dispose()
    repository = SQLModelTaskRepository(database_url=database_url, create_tables=False)
    task = repository.create_task(ContentGenerationRequest(
        content_type="lecture", topic="数据库升级", user_prompt="验证任务记录在升级后保留",
    ))
    repository.engine.dispose()
    repository = SQLModelTaskRepository(database_url=database_url)
    try:
        assert repository.get_task(task.task_id).topic == "数据库升级"
        assert_current_schema(repository)
    finally:
        repository.engine.dispose()


def test_startup_adopts_database_created_without_migration_version(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'unversioned.db'}"
    engine = create_engine(database_url)
    SQLModel.metadata.create_all(engine)
    engine.dispose()
    repository = SQLModelTaskRepository(database_url=database_url)
    try:
        assert_current_schema(repository)
    finally:
        repository.engine.dispose()


def test_upgrade_accepts_fields_already_added_by_previous_startup(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'already_added.db'}"
    engine = create_engine(database_url)
    SQLModel.metadata.create_all(engine)
    with engine.begin() as connection:
        command.stamp(migration_config(connection), "20260630_0006")
    engine.dispose()
    repository = SQLModelTaskRepository(database_url=database_url)
    try:
        assert_current_schema(repository)
    finally:
        repository.engine.dispose()


@pytest.mark.parametrize("has_updated_at", [False, True])
def test_upgrade_preserves_existing_assets_and_fills_missing_times(tmp_path, has_updated_at):
    database_url = f"sqlite:///{tmp_path / 'assets.db'}"
    engine = create_engine(database_url)
    with engine.begin() as connection:
        command.upgrade(migration_config(connection), "20260630_0006")
        if has_updated_at:
            connection.exec_driver_sql("ALTER TABLE content_generation_asset ADD COLUMN updated_at DATETIME")
    repository = SQLModelTaskRepository(database_url=database_url, create_tables=False)
    task = repository.create_task(ContentGenerationRequest(
        content_type="podcast_script", topic="资源时间迁移", user_prompt="保留已有音频资源",
    ))
    repository.engine.dispose()
    created_at = datetime(2026, 11, 8, 10, 0)
    updated_at = datetime(2026, 11, 8, 11, 0)
    speech = Path(__file__).parent / "fixtures" / "podcast_speech.wav"
    with engine.begin() as connection:
        assets = Table("content_generation_asset", MetaData(), autoload_with=connection)
        for index in range(2):
            values = {
                "asset_id": f"speech_{index}", "task_id": task.task_id,
                "asset_type": "audio", "uri": str(speech),
                "mime_type": "audio/wav", "created_at": created_at,
            }
            if has_updated_at:
                values["updated_at"] = updated_at if index else None
            connection.execute(assets.insert().values(**values))
    engine.dispose()

    repository = SQLModelTaskRepository(database_url=database_url)
    try:
        assert_current_schema(repository)
        with repository.engine.begin() as connection:
            assets = Table("content_generation_asset", MetaData(), autoload_with=connection)
            rows = connection.execute(select(assets).order_by(assets.c.asset_id)).mappings().all()
            assert len(rows) == 2
            assert all(row["uri"] == str(speech) and row["created_at"] == created_at for row in rows)
            assert all(row["status"] == "generated" and row["retry_count"] == 0 for row in rows)
            assert rows[0]["updated_at"] == created_at
            assert rows[1]["updated_at"] == (updated_at if has_updated_at else created_at)
            column = next(column for column in inspect(connection).get_columns(assets.name) if column["name"] == "updated_at")
            assert not column["nullable"]
            assert column["default"] is not None
            connection.execute(assets.insert().values(
                asset_id="speech_after_upgrade", task_id=task.task_id,
                asset_type="audio", uri=str(speech), created_at=created_at,
            ))
            assert connection.execute(select(assets.c.updated_at).where(
                assets.c.asset_id == "speech_after_upgrade",
            )).scalar_one() is not None
    finally:
        repository.engine.dispose()
