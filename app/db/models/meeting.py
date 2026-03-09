"""Application SQLModel models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime
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
