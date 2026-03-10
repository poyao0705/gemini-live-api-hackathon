"""Application SQLModel models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GmailHistoryState(SQLModel, table=True):
    """Persist the latest processed Gmail historyId per account."""

    __tablename__ = "gmail_history_state"

    email_address: str = Field(primary_key=True, max_length=320)
    last_history_id: str = Field(index=True, max_length=64)
    last_sync_time: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    watch_expiration: str | None = Field(default=None, max_length=64)
    status: str = Field(default="active", max_length=64)
    reset_required: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )


class RecallFailureQueue(SQLModel, table=True):
    """Persist failed Recall bot automation actions for manual review or retry."""

    __tablename__ = "recall_failure_queue"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    status: str = Field(default="pending", index=True, max_length=32)
    action: str = Field(max_length=32)
    email_address: str | None = Field(default=None, index=True, max_length=320)
    title: str | None = Field(default=None, max_length=512)
    join_url: str = Field(index=True, max_length=2048)
    join_at: str | None = Field(default=None, max_length=64)
    bot_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    error_type: str = Field(max_length=128)
    error_message: str = Field(max_length=2048)
    metadata_json: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
