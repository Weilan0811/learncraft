from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import ensure_sqlite_parent_directory, get_settings
from app import models


config = context.config

if config.config_file_name is not None and config.file_config.has_section("formatters"):
    fileConfig(config.config_file_name)

if config.attributes.get("connection") is None:
    config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL)
    ensure_sqlite_parent_directory(config.get_main_option("sqlalchemy.url"))
target_metadata = SQLModel.metadata


def render_item(type_, obj, autogen_context):
    if type_ == "type" and obj.__class__.__module__ == "sqlmodel.sql.sqltypes":
        if obj.__class__.__name__ == "AutoString":
            length = getattr(obj, "length", None)
            if length is not None:
                return f"sa.String(length={length})"
            return "sa.String()"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        context.configure(connection=connection, target_metadata=target_metadata, render_item=render_item)
        with context.begin_transaction():
            context.run_migrations()
        return
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_item=render_item)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
