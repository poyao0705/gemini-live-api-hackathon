"""Gmail history processing utilities for Pub/Sub push notifications."""

from __future__ import annotations

import asyncio
import base64
import binascii
import html
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, unquote, urlparse
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from googleapiclient.errors import HttpError
from sqlmodel import select

from app.core.config import settings
from app.db.session import async_session_factory
from app.integrations.google.client import get_gmail_service
from app.db.models.meeting import GmailHistoryState, utc_now
from app.services.meetings.invites import meeting_invite_store


logger = logging.getLogger(__name__)


class InvalidPubSubPayloadError(ValueError):
    """Raised when the Pub/Sub payload is not valid Gmail push JSON."""


class HistoryIdExpiredError(RuntimeError):
    """Raised when Gmail no longer has history for the stored historyId."""


def _coerce_history_id(value: str | int | None) -> str | None:
    if value is None:
        return None
    return str(value)


def decode_pubsub_message(data: str) -> dict[str, Any]:
    """Decode the base64 Pub/Sub envelope into a Gmail push payload."""

    try:
        decoded_bytes = base64.b64decode(data)
        payload = json.loads(decoded_bytes)
    except (binascii.Error, json.JSONDecodeError) as exc:
        raise InvalidPubSubPayloadError("Invalid Pub/Sub message payload") from exc

    if not isinstance(payload, dict):
        raise InvalidPubSubPayloadError("Pub/Sub payload must decode to a JSON object")

    return payload


@dataclass(slots=True)
class GmailMessageSummary:
    """Minimal message fields useful for downstream processing."""

    id: str
    thread_id: str | None
    history_id: str | None
    label_ids: list[str]
    snippet: str
    subject: str | None
    sender: str | None
    recipient: str | None
    date: str | None
    body_text: str
    meeting_details: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CALENDAR_SECTION_HEADERS = {
    "location",
    "organizer",
    "guests",
}

AGENDA_SECTION_HEADERS = {
    "agenda",
    "topics",
    "discussion items",
    "discussion points",
    "items to discuss",
    "meeting agenda",
}

NON_TITLE_LINES = {
    "this event has been updated",
    "this event has been canceled.",
}

SUBJECT_EVENT_TYPES = {
    "Invitation": "created",
    "Updated invitation": "updated",
    "Canceled event": "canceled",
}


@dataclass(slots=True)
class MeetingDetails:
    title: str | None
    calendar_event_id: str | None
    email_event_type: str
    event_status: str
    is_canceled: bool
    date_time_text: str | None
    join_at: str | None
    timezone: str | None
    location: str | None
    join_url: str | None
    meeting_id: str | None
    passcode: str | None
    organizer: str | None
    guests: list[str]
    agenda: list[str]
    agenda_confidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_section_label(value: str) -> str:
    normalized = value.strip().lower()
    normalized = normalized.rstrip(":")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _is_calendar_section_header(value: str) -> bool:
    return _normalize_section_label(value) in CALENDAR_SECTION_HEADERS


def _is_agenda_header(value: str) -> bool:
    normalized = _normalize_section_label(value)
    if normalized in AGENDA_SECTION_HEADERS:
        return True

    return bool(
        re.fullmatch(r"(?:the\s+)?agenda(?:\s+of\s+this\s+meeting)?(?:\s+is)?", normalized)
    )


def _extract_subject_parts(subject: str | None) -> tuple[str | None, str | None, str | None]:
    if not subject:
        return None, None, None

    for prefix, event_type in SUBJECT_EVENT_TYPES.items():
        token = f"{prefix}:"
        if not subject.startswith(token):
            continue

        remainder = subject[len(token) :].strip()
        if " @ " not in remainder:
            return event_type, remainder or None, None

        title, schedule = remainder.split(" @ ", 1)
        return event_type, title.strip() or None, schedule.strip() or None

    return None, None, None


def _parse_datetime_with_formats(value: str, formats: tuple[str, ...]) -> datetime | None:
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _extract_calendar_timezone_id(body_text: str) -> str | None:
    for raw_url in re.findall(r"https?://\S+", body_text):
        candidate = raw_url.rstrip(").,;]")
        parsed = urlparse(candidate)
        if parsed.netloc != "calendar.google.com":
            continue

        timezone_id = parse_qs(parsed.query).get("ctz", [None])[0]
        if timezone_id:
            return unquote(timezone_id)

    return None


def _extract_calendar_event_id(body_text: str) -> str | None:
    for raw_url in re.findall(r"https?://\S+", body_text):
        candidate = raw_url.rstrip(").,;]")
        parsed = urlparse(candidate)
        if parsed.netloc != "calendar.google.com":
            continue

        event_id = parse_qs(parsed.query).get("eid", [None])[0]
        if event_id:
            return event_id

    return None


def _extract_join_at_from_body(date_time_text: str | None, body_text: str) -> str | None:
    if not date_time_text:
        return None

    timezone_id = _extract_calendar_timezone_id(body_text)
    if not timezone_id:
        return None

    start_text = re.split(r"\s*[–-]\s*", date_time_text.replace("⋅", " "), maxsplit=1)[0]
    start_text = re.sub(r"\s+", " ", start_text).strip()
    start_at = _parse_datetime_with_formats(
        start_text,
        (
            "%A %b %d, %Y %I:%M%p",
            "%A %b %d, %Y %I%p",
            "%a %b %d, %Y %I:%M%p",
            "%a %b %d, %Y %I%p",
        ),
    )
    if start_at is None:
        return None

    try:
        return start_at.replace(tzinfo=ZoneInfo(timezone_id)).isoformat()
    except ZoneInfoNotFoundError:
        return None


def _extract_join_at_from_subject(subject: str | None) -> str | None:
    _, _, schedule = _extract_subject_parts(subject)
    if not schedule:
        return None

    timezone_match = re.search(r"\((GMT[+-]\d{1,2}(?::\d{2})?)\)", schedule)
    if not timezone_match:
        return None

    schedule_text = schedule[: timezone_match.start()].strip()
    start_text = re.split(r"\s*[–-]\s*", schedule_text, maxsplit=1)[0].strip()
    start_at = _parse_datetime_with_formats(
        start_text,
        (
            "%A %b %d, %Y %I:%M%p",
            "%A %b %d, %Y %I%p",
            "%a %b %d, %Y %I:%M%p",
            "%a %b %d, %Y %I%p",
        ),
    )
    if start_at is None:
        return None

    offset_match = re.fullmatch(r"GMT([+-])(\d{1,2})(?::(\d{2}))?", timezone_match.group(1))
    if not offset_match:
        return None

    sign = 1 if offset_match.group(1) == "+" else -1
    hours = int(offset_match.group(2))
    minutes = int(offset_match.group(3) or "0")
    offset = timezone(sign * timedelta(hours=hours, minutes=minutes))
    return start_at.replace(tzinfo=offset).isoformat()


def _extract_email_event_type(subject: str | None, lines: list[str]) -> str:
    event_type, _, _ = _extract_subject_parts(subject)
    if event_type:
        return event_type

    first_lines = {_normalize_section_label(line) for line in lines[:3] if line}
    if "this event has been canceled." in first_lines:
        return "canceled"
    if "this event has been updated" in first_lines:
        return "updated"
    return "created"


def _is_non_title_line(value: str) -> bool:
    normalized = _normalize_section_label(value)
    return normalized in NON_TITLE_LINES or normalized.startswith("changed:")


class GmailHistoryStateStore:
    """Persist the latest processed historyId per Gmail account."""

    async def get_user_state(self, email_address: str) -> dict[str, Any] | None:
        async with async_session_factory() as session:
            statement = select(GmailHistoryState).where(
                GmailHistoryState.email_address == email_address
            )
            result = await session.exec(statement)
            state = result.first()
            if state is None:
                return None

            return self._to_dict(state)

    async def upsert_user_state(
        self,
        email_address: str,
        history_id: str,
        *,
        last_sync_time: str | None = None,
        watch_expiration: str | None = None,
        status: str | None = None,
        reset_required: bool | None = None,
    ) -> dict[str, Any]:
        next_history_id = _coerce_history_id(history_id)
        if next_history_id is None:
            raise ValueError("history_id is required")

        async with async_session_factory() as session:
            state = await session.get(GmailHistoryState, email_address)
            if state is None:
                state = GmailHistoryState(
                    email_address=email_address,
                    last_history_id=next_history_id,
                )
            else:
                current_history_id = _coerce_history_id(state.last_history_id)
                if current_history_id is not None and int(next_history_id) < int(current_history_id):
                    next_history_id = current_history_id
                state.last_history_id = next_history_id

            if last_sync_time:
                state.last_sync_time = datetime.fromisoformat(last_sync_time)
            else:
                state.last_sync_time = utc_now()

            if watch_expiration is not None:
                state.watch_expiration = watch_expiration
            if status is not None:
                state.status = status
            if reset_required is not None:
                state.reset_required = reset_required

            state.updated_at = utc_now()

            session.add(state)
            await session.commit()
            await session.refresh(state)
            return self._to_dict(state)

    @staticmethod
    def _to_dict(state: GmailHistoryState) -> dict[str, Any]:
        payload = state.model_dump(mode="json")
        payload["last_sync_time"] = state.last_sync_time.isoformat()
        payload["created_at"] = state.created_at.isoformat()
        payload["updated_at"] = state.updated_at.isoformat()
        return payload


gmail_state_store = GmailHistoryStateStore()


async def _execute_gmail_request(request: Any) -> Any:
    return await asyncio.to_thread(request.execute)


def _decode_base64url(value: str | None) -> str:
    if not value:
        return ""

    padding = "=" * (-len(value) % 4)
    decoded = base64.urlsafe_b64decode(value + padding)
    return decoded.decode("utf-8", errors="replace")


def _normalize_whitespace(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"\r\n?", "\n", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _html_to_text(value: str) -> str:
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return _normalize_whitespace(text)


def _split_body_lines(body_text: str) -> list[str]:
    return [line.strip() for line in _normalize_whitespace(body_text).split("\n")]


def _extract_direct_url(value: str) -> str | None:
    match = re.search(r"https?://\S+", value)
    if not match:
        return None

    candidate = match.group(0).rstrip(").,;]")
    parsed = urlparse(candidate)
    if parsed.netloc == "www.google.com" and parsed.path == "/url":
        target = parse_qs(parsed.query).get("q", [None])[0]
        if target:
            return unquote(target)
    return candidate


def _is_likely_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value))


def _extract_meeting_title(subject: str | None, lines: list[str]) -> str | None:
    _, subject_title, _ = _extract_subject_parts(subject)
    if subject_title:
        return subject_title

    for line in lines:
        normalized = _normalize_section_label(line)
        if line and normalized not in CALENDAR_SECTION_HEADERS and not _is_non_title_line(line):
            return line

    return None


def _extract_date_time_text(lines: list[str]) -> str | None:
    pattern = re.compile(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*\s+.+?\d(?:am|pm)\s*[–-]\s*.+", re.IGNORECASE)
    for line in lines:
        if pattern.search(line):
            return line
    return None


def _extract_section_value(lines: list[str], header: str) -> str | None:
    target = _normalize_section_label(header)
    for index, line in enumerate(lines):
        if _normalize_section_label(line) != target:
            continue

        values: list[str] = []
        for next_line in lines[index + 1 :]:
            normalized = _normalize_section_label(next_line)
            if not next_line:
                if values:
                    break
                continue
            if normalized in CALENDAR_SECTION_HEADERS or _is_agenda_header(next_line):
                break
            values.append(next_line)

        if values:
            return "\n".join(values)

    return None


def _extract_agenda(lines: list[str]) -> tuple[list[str], str]:
    for index, line in enumerate(lines):
        if not _is_agenda_header(line):
            continue

        agenda_items: list[str] = []
        for next_line in lines[index + 1 :]:
            normalized = _normalize_section_label(next_line)
            if not next_line:
                if agenda_items:
                    break
                continue
            if normalized in CALENDAR_SECTION_HEADERS or _is_agenda_header(next_line):
                break

            cleaned = re.sub(r"^(?:[-*•]\s+|\d+[.)]\s+)", "", next_line).strip()
            if cleaned:
                agenda_items.append(cleaned)

        deduped_items = list(dict.fromkeys(agenda_items))
        if deduped_items:
            return deduped_items, "explicit"

    return [], "none"


def extract_meeting_details(subject: str | None, body_text: str) -> dict[str, Any] | None:
    lines = _split_body_lines(body_text)
    if not lines:
        return None

    email_event_type = _extract_email_event_type(subject, lines)
    has_meeting_subject = bool(
        subject
        and re.match(r"(?:Invitation|Updated invitation|Canceled event):\s*.+\s*@\s*.+$", subject)
    )
    is_canceled = email_event_type == "canceled"

    join_url = None
    for line in lines:
        url = _extract_direct_url(line)
        if url and any(host in url for host in ("zoom.us", "meet.google.com", "teams.microsoft.com")):
            join_url = url
            break

    meeting_id_match = re.search(r"Meeting ID:\s*([^\n]+)", body_text, re.IGNORECASE)
    passcode_match = re.search(r"Passcode:\s*([^\n]+)", body_text, re.IGNORECASE)

    location = _extract_section_value(lines, "Location")
    organizer_block = _extract_section_value(lines, "Organizer")
    guests_block = _extract_section_value(lines, "Guests")
    agenda, agenda_confidence = _extract_agenda(lines)

    timezone_text = None
    date_time_text = _extract_date_time_text(lines)
    if date_time_text:
        try:
            date_line_index = lines.index(date_time_text)
        except ValueError:
            date_line_index = -1
        if date_line_index >= 0:
            for candidate in lines[date_line_index + 1 : date_line_index + 4]:
                if candidate and not _is_calendar_section_header(candidate):
                    timezone_text = candidate
                    break

    join_at = _extract_join_at_from_body(date_time_text, body_text)
    if join_at is None:
        join_at = _extract_join_at_from_subject(subject)

    organizer = None
    if organizer_block:
        organizer = organizer_block.splitlines()[0].strip()

    guests: list[str] = []
    if guests_block:
        for line in guests_block.splitlines():
            cleaned = line.strip()
            if _is_likely_email(cleaned):
                guests.append(cleaned)

    details = MeetingDetails(
        title=_extract_meeting_title(subject, lines),
        calendar_event_id=_extract_calendar_event_id(body_text),
        email_event_type=email_event_type,
        event_status="canceled" if is_canceled else "confirmed",
        is_canceled=is_canceled,
        date_time_text=date_time_text,
        join_at=join_at,
        timezone=timezone_text,
        location=location,
        join_url=join_url,
        meeting_id=meeting_id_match.group(1).strip() if meeting_id_match else None,
        passcode=passcode_match.group(1).strip() if passcode_match else None,
        organizer=organizer,
        guests=guests,
        agenda=agenda,
        agenda_confidence=agenda_confidence,
    )

    has_meeting_evidence = any(
        [
            details.date_time_text,
            details.join_url,
            details.location,
            details.meeting_id,
            details.passcode,
            details.organizer,
            details.guests,
            details.agenda,
        ]
    )

    if not has_meeting_evidence and not has_meeting_subject:
        return None

    return details.to_dict()


async def _get_part_body_text(service: Any, message_id: str, part: dict[str, Any]) -> str:
    body = part.get("body", {})
    data = body.get("data")
    if data:
        return _decode_base64url(data)

    attachment_id = body.get("attachmentId")
    if not attachment_id:
        return ""

    response = await _execute_gmail_request(
        service.users()
        .messages()
        .attachments()
        .get(userId=settings.gmail_user_id, messageId=message_id, id=attachment_id)
    )
    return _decode_base64url(response.get("data"))


async def _find_mime_part_text(
    service: Any,
    message_id: str,
    part: dict[str, Any],
    mime_type: str,
) -> str:
    if part.get("mimeType") == mime_type:
        return await _get_part_body_text(service, message_id, part)

    for child_part in part.get("parts", []):
        text = await _find_mime_part_text(service, message_id, child_part, mime_type)
        if text.strip():
            return text

    return ""


async def _extract_message_body_text(service: Any, message_id: str, payload: dict[str, Any]) -> str:
    plain_text = await _find_mime_part_text(service, message_id, payload, "text/plain")
    if plain_text.strip():
        return plain_text.strip()

    html_text = await _find_mime_part_text(service, message_id, payload, "text/html")
    if html_text.strip():
        return _html_to_text(html_text)

    return ""


async def get_message_summary(service: Any, message_id: str) -> GmailMessageSummary:
    """Fetch message metadata plus decoded body text for downstream processing."""

    response = await _execute_gmail_request(
        service.users()
        .messages()
        .get(
            userId=settings.gmail_user_id,
            id=message_id,
            format="full",
        )
    )

    payload = response.get("payload", {})
    headers = payload.get("headers", [])
    header_map = {
        header.get("name", "").lower(): header.get("value")
        for header in headers
        if header.get("name")
    }
    body_text = await _extract_message_body_text(service, message_id, payload)
    meeting_details = extract_meeting_details(header_map.get("subject"), body_text)

    return GmailMessageSummary(
        id=response["id"],
        thread_id=response.get("threadId"),
        history_id=_coerce_history_id(response.get("historyId")),
        label_ids=response.get("labelIds", []),
        snippet=response.get("snippet", ""),
        subject=header_map.get("subject"),
        sender=header_map.get("from"),
        recipient=header_map.get("to"),
        date=header_map.get("date"),
        body_text=body_text,
        meeting_details=meeting_details,
    )


async def list_history_updates(service: Any, start_history_id: str) -> tuple[list[dict[str, Any]], str]:
    """Return all Gmail history pages after the provided historyId."""

    history_records: list[dict[str, Any]] = []
    latest_history_id = start_history_id
    page_token: str | None = None

    try:
        while True:
            request = service.users().history().list(
                userId=settings.gmail_user_id,
                startHistoryId=start_history_id,
                historyTypes=settings.gmail_history_types,
                pageToken=page_token,
            )
            response = await _execute_gmail_request(request)
            latest_history_id = _coerce_history_id(response.get("historyId")) or latest_history_id
            history_records.extend(response.get("history", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
    except HttpError as exc:
        if exc.resp.status == 404:
            raise HistoryIdExpiredError(
                f"Stored historyId {start_history_id} is too old; full mailbox resync required"
            ) from exc
        raise

    return history_records, latest_history_id


def get_new_message_ids(history_records: list[dict[str, Any]]) -> list[str]:
    """Extract unique message ids from history messageAdded records."""

    message_ids: list[str] = []
    seen: set[str] = set()

    for record in history_records:
        for message_added in record.get("messagesAdded", []):
            message = message_added.get("message", {})
            message_id = message.get("id")
            if message_id and message_id not in seen:
                seen.add(message_id)
                message_ids.append(message_id)

    return message_ids


async def bootstrap_history_state(
    email_address: str,
    history_id: str,
    *,
    watch_expiration: str | None = None,
    status: str = "watch_initialized",
) -> dict[str, Any]:
    """Persist the baseline historyId returned by watch() or first push event."""

    return await gmail_state_store.upsert_user_state(
        email_address,
        history_id,
        watch_expiration=watch_expiration,
        status=status,
        reset_required=False,
    )


async def process_gmail_push_notification(
    email_address: str,
    published_history_id: str,
) -> dict[str, Any]:
    """Process a Gmail Pub/Sub push notification using history.list."""

    allowed_emails = settings.gmail_allowed_email_addresses
    if allowed_emails and email_address not in allowed_emails:
        logger.info("Ignoring Gmail push for non-whitelisted account %s", email_address)
        return {
            "status": "ignored",
            "reason": "email_not_whitelisted",
            "email_address": email_address,
        }

    stored_state = await gmail_state_store.get_user_state(email_address)
    if not stored_state or not stored_state.get("last_history_id"):
        logger.info(
            "No stored historyId for %s; saving %s as the baseline and skipping backfill",
            email_address,
            published_history_id,
        )
        await bootstrap_history_state(
            email_address,
            published_history_id,
            status="initialized_from_push",
        )
        return {
            "status": "initialized",
            "email_address": email_address,
            "last_history_id": published_history_id,
            "messages": [],
        }

    start_history_id = str(stored_state["last_history_id"])
    if int(published_history_id) <= int(start_history_id):
        logger.info(
            "Skipping stale or duplicate Gmail push for %s; published=%s stored=%s",
            email_address,
            published_history_id,
            start_history_id,
        )
        return {
            "status": "duplicate",
            "email_address": email_address,
            "last_history_id": start_history_id,
            "messages": [],
        }

    service = await asyncio.to_thread(get_gmail_service)

    try:
        history_records, latest_history_id = await list_history_updates(service, start_history_id)
    except HistoryIdExpiredError:
        logger.warning("Gmail history expired for %s; manual resync required", email_address)
        await gmail_state_store.upsert_user_state(
            email_address,
            published_history_id,
            status="resync_required",
            reset_required=True,
        )
        raise

    messages = []
    for message_id in get_new_message_ids(history_records):
        summary = await get_message_summary(service, message_id)
        await meeting_invite_store.upsert_from_message(email_address, summary)
        messages.append(summary.to_dict())

    await gmail_state_store.upsert_user_state(
        email_address,
        latest_history_id,
        status="active",
        reset_required=False,
    )

    logger.info(
        "Processed Gmail push for %s: %s history records, %s new messages, latest=%s",
        email_address,
        len(history_records),
        len(messages),
        latest_history_id,
    )

    return {
        "status": "processed",
        "email_address": email_address,
        "history_records": len(history_records),
        "messages": messages,
        "last_history_id": latest_history_id,
    }
