"""Persistence helpers for failed Recall bot automation actions."""

from __future__ import annotations

from typing import Any

from sqlalchemy import desc
from sqlmodel import select

from app.db.models.meeting import RecallFailureQueue, utc_now
from app.db.session import async_session_factory


class RecallFailureQueueStore:
    """Store and manage Recall bot automation failures."""

    async def enqueue(
        self,
        *,
        action: str,
        join_url: str,
        error: Exception,
        email_address: str | None = None,
        title: str | None = None,
        join_at: str | None = None,
        bot_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with async_session_factory() as session:
            record = RecallFailureQueue(
                action=action,
                email_address=email_address,
                title=title,
                join_url=join_url,
                join_at=join_at,
                bot_ids=bot_ids or [],
                error_type=type(error).__name__,
                error_message=str(error),
                metadata_json=self._sanitize_metadata(metadata),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return self._to_dict(record)

    async def list_items(self, *, status: str | None = None) -> list[dict[str, Any]]:
        async with async_session_factory() as session:
            statement = select(RecallFailureQueue).order_by(desc(RecallFailureQueue.created_at))
            if status:
                statement = statement.where(RecallFailureQueue.status == status)

            result = await session.exec(statement)
            return [self._to_dict(item) for item in result.all()]

    async def resolve(self, queue_id: str) -> dict[str, Any] | None:
        async with async_session_factory() as session:
            record = await session.get(RecallFailureQueue, queue_id)
            if record is None:
                return None

            record.status = "resolved"
            record.updated_at = utc_now()
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return self._to_dict(record)

    @staticmethod
    def _sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, str | int | float | bool | None]:
        if not metadata:
            return {}

        sanitized: dict[str, str | int | float | bool | None] = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        return sanitized

    @staticmethod
    def _to_dict(record: RecallFailureQueue) -> dict[str, Any]:
        payload = record.model_dump(mode="json")
        payload["created_at"] = record.created_at.isoformat()
        payload["updated_at"] = record.updated_at.isoformat()
        return payload


recall_failure_queue_store = RecallFailureQueueStore()