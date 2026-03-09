"""Alembic environment configuration."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import Any

from alembic import context as alembic_context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from app.core.config import settings
from app.db import models as app_models  # noqa: F401 — import for SQLModel metadata registration


alembic_ctx: Any = alembic_context
config = getattr(alembic_ctx, "config")
config.set_main_option("sqlalchemy.url", settings.database_url)

MODELS_MODULE = app_models

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live database connection."""

    getattr(alembic_ctx, "configure")(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with getattr(alembic_ctx, "begin_transaction")():
        getattr(alembic_ctx, "run_migrations")()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""

    asyncio.run(run_async_migrations())


async def run_async_migrations() -> None:
    """Run migrations with an async database connection."""

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection: Any) -> None:
    """Configure Alembic and run migrations on a synchronous connection facade."""

    getattr(alembic_ctx, "configure")(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with getattr(alembic_ctx, "begin_transaction")():
        getattr(alembic_ctx, "run_migrations")()


if getattr(alembic_ctx, "is_offline_mode")():
    run_migrations_offline()
else:
    run_migrations_online()