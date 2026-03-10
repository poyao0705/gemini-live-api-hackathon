"""Persistence helpers for meeting invite emails."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import re
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


def _derive_meeting_status(details: dict[str, Any]) -> str:
    """Map email event details to a user-facing meeting status."""
    if details.get("is_canceled") or details.get("email_event_type") == "canceled":
        return "canceled"
    return "scheduled"


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _coerce_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _sort_key(item: dict[str, Any]) -> datetime:
    join_at = _coerce_utc(_parse_datetime(item.get("join_at")))
    updated_at = _coerce_utc(_parse_datetime(item.get("updated_at")))
    created_at = _coerce_utc(_parse_datetime(item.get("created_at")))
    return join_at or updated_at or created_at or datetime.min.replace(tzinfo=timezone.utc)


def _calendar_month(items: list[dict[str, Any]], now: datetime) -> tuple[int, int]:
    for item in items:
        join_at = _parse_datetime(item.get("join_at"))
        if join_at is not None:
            return join_at.year, join_at.month
    return now.year, now.month


_TIME_ONLY_FORMATS = ("%I:%M%p", "%I%p")


def _infer_meeting_end(item: dict[str, Any], join_at: datetime) -> datetime:
    details = item.get("meeting_details_json") or {}
    date_time_text = details.get("date_time_text")
    if not date_time_text or not isinstance(date_time_text, str):
        return join_at + timedelta(hours=1)

    parts = re.split(r"\s*[–-]\s*", date_time_text.replace("⋅", " "), maxsplit=1)
    if len(parts) != 2:
        return join_at + timedelta(hours=1)

    end_text = re.sub(r"\s+", " ", parts[1]).strip()
    for fmt in _TIME_ONLY_FORMATS:
        try:
            parsed_end = datetime.strptime(end_text, fmt)
            end_at = join_at.replace(
                hour=parsed_end.hour,
                minute=parsed_end.minute,
                second=0,
                microsecond=0,
            )
            if end_at <= join_at:
                return join_at + timedelta(hours=1)
            return end_at
        except ValueError:
            continue

    return join_at + timedelta(hours=1)


def build_dashboard_payload(
    items: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Split invite data into past-meeting and upcoming-event dashboard sections."""

    current_time = _coerce_utc(now or datetime.now(timezone.utc))
    past_meetings: list[dict[str, Any]] = []
    upcoming_events: list[dict[str, Any]] = []

    for item in items:
        join_at = _coerce_utc(_parse_datetime(item.get("join_at")))
        if join_at is None:
            continue

        end_at = _coerce_utc(_infer_meeting_end(item, join_at)) or (join_at + timedelta(hours=1))
        is_ongoing = join_at <= current_time < end_at

        normalized_item = {
            **item,
            "sort_at": join_at.isoformat(),
            "has_time": True,
            "end_at": end_at.isoformat(),
            "is_ongoing": is_ongoing,
            "is_future": join_at > current_time,
            "is_past": end_at <= current_time,
        }
        if join_at > current_time:
            upcoming_events.append(normalized_item)
        else:
            past_meetings.append(normalized_item)

    upcoming_events.sort(key=_sort_key)
    past_meetings.sort(key=_sort_key, reverse=True)

    grouped_upcoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in upcoming_events:
        join_at = _parse_datetime(item.get("join_at"))
        if join_at is None:
            continue
        grouped_upcoming[join_at.date().isoformat()].append(item)

    calendar_year, calendar_month = _calendar_month(upcoming_events, current_time)

    return {
        "generated_at": current_time.isoformat(),
        "calendar_month": calendar_month,
        "calendar_year": calendar_year,
        "past_meetings": past_meetings,
        "upcoming_events": upcoming_events,
        "upcoming_by_date": dict(grouped_upcoming),
        "counts": {
            "past_meetings": len(past_meetings),
            "upcoming_events": len(upcoming_events),
            "canceled": sum(1 for item in items if item.get("meeting_status") == "canceled"),
        },
    }


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

        calendar_event_id = details.get("calendar_event_id")

        async with async_session_factory() as session:
            # Look up the existing row using the most stable identifier available,
            # so that update/cancel emails mutate the same row instead of
            # creating duplicates.
            #
            # Priority:
            # 1. calendar_event_id  – present on invite/update emails (most reliable)
            # 2. gmail_thread_id    – Google sends all emails for one calendar event
            #                         in the same thread, works for cancellations too
            # 3. gmail_message_id   – fall back to exact message match (new row)
            record: MeetingInvite | None = None
            if calendar_event_id:
                result = await session.exec(
                    select(MeetingInvite).where(
                        MeetingInvite.calendar_event_id == calendar_event_id
                    )
                )
                record = result.first()
            # Fallback: match on join_url — cancellation emails keep the same
            # Meet link even when the calendar URL (with eid=) is absent.
            join_url = details.get("join_url")
            if record is None and join_url:
                result = await session.exec(
                    select(MeetingInvite).where(
                        MeetingInvite.email_address == email_address,
                        MeetingInvite.join_url == join_url,
                    )
                )
                record = result.first()
            if record is None:
                record = await session.get(MeetingInvite, message.id)
            if record is None:
                record = MeetingInvite(
                    gmail_message_id=message.id,
                    email_address=email_address,
                    meeting_status=_derive_meeting_status(details),
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
            record.meeting_status = _derive_meeting_status(details)
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

    async def get_dashboard_payload(
        self,
        *,
        email_address: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        items = await self.list_invites(email_address=email_address)
        return build_dashboard_payload(items, now=now)

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