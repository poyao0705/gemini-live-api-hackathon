"""Gmail history processing utilities for Pub/Sub push notifications."""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from googleapiclient.errors import HttpError
from sqlmodel import select

from app.config import settings
from app.db import async_session_factory
from app.gmail_service import get_gmail_service
from app.models import GmailHistoryState, utc_now


logger = logging.getLogger(__name__)

MESSAGE_METADATA_HEADERS = ["From", "To", "Subject", "Date"]


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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


async def get_message_summary(service: Any, message_id: str) -> GmailMessageSummary:
    """Fetch a lightweight message view for downstream processing."""

    response = await _execute_gmail_request(
        service.users()
        .messages()
        .get(
            userId=settings.gmail_user_id,
            id=message_id,
            format="metadata",
            metadataHeaders=MESSAGE_METADATA_HEADERS,
        )
    )

    headers = response.get("payload", {}).get("headers", [])
    header_map = {
        header.get("name", "").lower(): header.get("value")
        for header in headers
        if header.get("name")
    }

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