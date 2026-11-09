from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect
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
        assert MigrationContext.configure(connection).get_current_revision() == "20260701_0007"
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
