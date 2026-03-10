"""Pure parsing helpers for extracting meeting details from Gmail messages."""

from __future__ import annotations

import html
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, unquote, urlparse
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


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

# Datetime parse formats shared between body and subject extraction
_DATETIME_FORMATS = (
    "%A %b %d, %Y %I:%M%p",
    "%A %b %d, %Y %I%p",
    "%a %b %d, %Y %I:%M%p",
    "%a %b %d, %Y %I%p",
)


def _coerce_history_id(value: str | int | None) -> str | None:
    """Coerce a raw historyId value to a string, or return None."""
    if value is None:
        return None
    return str(value)


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

        # Google uses two domains for calendar event URLs:
        #   • calendar.google.com/?eid=...
        #   • www.google.com/calendar/event?eid=...
        # Cancellation emails tend to use the www.google.com form.
        is_calendar_url = (
            parsed.netloc == "calendar.google.com"
            or (
                parsed.netloc in ("www.google.com", "google.com")
                and parsed.path.startswith("/calendar")
            )
        )
        if not is_calendar_url:
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
    start_at = _parse_datetime_with_formats(start_text, _DATETIME_FORMATS)
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
    start_at = _parse_datetime_with_formats(start_text, _DATETIME_FORMATS)
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


def _normalize_whitespace(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"\r\n?", "\n", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def html_to_text(value: str) -> str:
    text = re.sub(r"<style\b[^>]*>.*?</style[^>]*>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<script\b[^>]*>.*?</script[^>]*>", " ", text, flags=re.IGNORECASE | re.DOTALL)
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
        (
            details.date_time_text,
            details.join_url,
            details.location,
            details.meeting_id,
            details.passcode,
            details.organizer,
            details.guests,
            details.agenda,
        )
    )

    if not has_meeting_evidence and not has_meeting_subject:
        return None

    return details.to_dict()
