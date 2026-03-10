"""Gmail history processing utilities for Pub/Sub push notifications.

This module is the slim orchestration layer.  Pure parsing, DB state, and
Gmail API helpers live in the focused sub-modules:

    app.services.gmail.parsing  – pure parsing / meeting-detail extraction
    app.services.gmail.state    – DB/ORM history-state persistence
    app.services.gmail.client   – Gmail API interaction helpers
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
from typing import Any

# ── re-exports for backward compatibility ────────────────────────────────────
# Parsing is pure stdlib – always safe to import eagerly.
from app.services.gmail.parsing import (  # noqa: F401
    AGENDA_SECTION_HEADERS,
    CALENDAR_SECTION_HEADERS,
    NON_TITLE_LINES,
    SUBJECT_EVENT_TYPES,
    MeetingDetails,
    _coerce_history_id,
    extract_meeting_details,
)

# state and client have heavy optional dependencies (sqlmodel, google-api-python-
# client).  Provide them via module-level __getattr__ so that lightweight test
# environments that only import extract_meeting_details are not broken.
_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "GmailHistoryStateStore": ("app.services.gmail.state", "GmailHistoryStateStore"),
    "bootstrap_history_state": ("app.services.gmail.state", "bootstrap_history_state"),
    "gmail_state_store": ("app.services.gmail.state", "gmail_state_store"),
    "GmailMessageSummary": ("app.services.gmail.client", "GmailMessageSummary"),
    "get_message_summary": ("app.services.gmail.client", "get_message_summary"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_EXPORTS:
        import importlib
        module_path, attr = _LAZY_EXPORTS[name]
        module = importlib.import_module(module_path)
        value = getattr(module, attr)
        # Cache in module globals so subsequent accesses are direct.
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

logger = logging.getLogger(__name__)


# ── custom exceptions ─────────────────────────────────────────────────────────

class InvalidPubSubPayloadError(ValueError):
    """Raised when the Pub/Sub payload is not valid Gmail push JSON."""


class HistoryIdExpiredError(RuntimeError):
    """Raised when Gmail no longer has history for the stored historyId."""


# ── Pub/Sub decoding ──────────────────────────────────────────────────────────

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


# ── Gmail history orchestration ───────────────────────────────────────────────


async def _execute_gmail_request(request: Any) -> Any:
    return await asyncio.to_thread(request.execute)


async def list_history_updates(service: Any, start_history_id: str) -> tuple[list[dict[str, Any]], str]:
    """Return all Gmail history pages after the provided historyId."""

    # Local imports so this module remains importable without heavy deps
    from googleapiclient.errors import HttpError  # noqa: PLC0415
    from app.core.config import settings  # noqa: PLC0415

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


async def process_gmail_push_notification(
    email_address: str,
    published_history_id: str,
) -> dict[str, Any]:
    """Process a Gmail Pub/Sub push notification using history.list."""

    # Local imports so this module remains importable without heavy deps
    from app.core.config import settings  # noqa: PLC0415
    from app.integrations.google.client import get_gmail_service  # noqa: PLC0415
    from app.services.gmail.client import get_message_summary  # noqa: PLC0415
    from app.services.gmail.state import (  # noqa: PLC0415
        bootstrap_history_state,
        gmail_state_store,
    )
    from app.services.meetings.invites import meeting_invite_store  # noqa: PLC0415

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
        try:
            summary = await get_message_summary(service, message_id)
            await meeting_invite_store.upsert_from_message(email_address, summary)
            messages.append(summary.to_dict())
        except Exception:
            logger.exception(
                "Failed to process message %s for %s; skipping and continuing",
                message_id,
                email_address,
            )

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
