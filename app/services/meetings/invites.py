"""Persistence helpers for meeting invite emails."""

from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import desc
from sqlmodel import select

from app.db.models.meeting import MeetingInvite, utc_now
from app.db.session import async_session_factory

if TYPE_CHECKING:
    from app.services.gmail.history import GmailMessageSummary


def _parse_join_at(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value)


class MeetingInviteStore:
    """Store meeting invite emails extracted from Gmail."""

    async def upsert_from_message(
        self,
        email_address: str,
        message: "GmailMessageSummary",
    ) -> dict[str, Any] | None:
        details = message.meeting_details
        if not details:
            return None

        async with async_session_factory() as session:
            record = await session.get(MeetingInvite, message.id)
            if record is None:
                record = MeetingInvite(
                    gmail_message_id=message.id,
                    email_address=email_address,
                    meeting_status=details.get("event_status", "confirmed"),
                    email_event_type=details.get("email_event_type", "created"),
                )

            record.email_address = email_address
            record.gmail_thread_id = message.thread_id
            record.gmail_history_id = message.history_id
            record.sender = message.sender
            record.recipient = message.recipient
            record.subject = message.subject
            record.message_date = message.date
            record.snippet = message.snippet
            record.body_text = message.body_text
            record.title = details.get("title")
            record.calendar_event_id = details.get("calendar_event_id")
            record.join_url = details.get("join_url")
            record.join_at = _parse_join_at(details.get("join_at"))
            record.meeting_status = details.get("event_status", "confirmed")
            record.email_event_type = details.get("email_event_type", "created")
            record.is_canceled = bool(details.get("is_canceled", False))
            record.meeting_details_json = details
            record.updated_at = utc_now()

            session.add(record)
            await session.commit()
            await session.refresh(record)
            return self._to_dict(record)

    async def list_invites(
        self,
        *,
        email_address: str | None = None,
        meeting_status: str | None = None,
    ) -> list[dict[str, Any]]:
        async with async_session_factory() as session:
            statement = select(MeetingInvite).order_by(desc(MeetingInvite.updated_at))
            if email_address:
                statement = statement.where(MeetingInvite.email_address == email_address)
            if meeting_status:
                statement = statement.where(MeetingInvite.meeting_status == meeting_status)

            result = await session.exec(statement)
            return [self._to_dict(item) for item in result.all()]

    @staticmethod
    def _to_dict(record: MeetingInvite) -> dict[str, Any]:
        payload = record.model_dump(mode="json")
        payload["created_at"] = record.created_at.isoformat()
        payload["updated_at"] = record.updated_at.isoformat()
        if record.join_at is not None:
            if record.join_at.tzinfo is None and record.meeting_details_json.get("join_at"):
                payload["join_at"] = str(record.meeting_details_json["join_at"])
            else:
                payload["join_at"] = record.join_at.isoformat()
        return payload


meeting_invite_store = MeetingInviteStore()