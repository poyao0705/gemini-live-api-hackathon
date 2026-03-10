"""Gmail API interaction helpers."""

from __future__ import annotations

import asyncio
import base64
from dataclasses import asdict, dataclass
from typing import Any

from app.core.config import settings
from app.services.gmail.parsing import _coerce_history_id, html_to_text, extract_meeting_details


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


async def _execute_gmail_request(request: Any) -> Any:
    return await asyncio.to_thread(request.execute)


def _decode_base64url(value: str | None) -> str:
    if not value:
        return ""

    padding = "=" * (-len(value) % 4)
    decoded = base64.urlsafe_b64decode(value + padding)
    return decoded.decode("utf-8", errors="replace")


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
        return html_to_text(html_text)

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
