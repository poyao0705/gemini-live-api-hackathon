"""Gmail Pub/Sub webhook endpoints."""

import asyncio
import logging
import uuid
from datetime import datetime

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Response
from googleapiclient.errors import HttpError
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import SQLAlchemyError

from app.integrations.recall.client import create_bot, delete_bot, list_bots_for_meeting, stop_bot, update_bot
from app.services.recall.failures import recall_failure_queue_store
from app.services.gmail.history import (
    HistoryIdExpiredError,
    InvalidPubSubPayloadError,
    decode_pubsub_message,
    process_gmail_push_notification,
)

logger = logging.getLogger(__name__)

router = APIRouter()

RECALL_AUTOMATION_ERRORS = (httpx.HTTPStatusError, ValueError, RuntimeError, OSError)


def _log_manual_recall_action(
    *,
    action: str,
    join_url: str,
    title: str | None,
    join_at: str | None,
    error: Exception,
    bot_ids: list[str] | None = None,
) -> None:
    logger.warning(
        "Recall bot automation failed; manual action required. "
        "action=%s title=%s join_url=%s join_at=%s bot_ids=%s manual_update_endpoint=/api/recall/bots/{bot_id} error=%s",
        action,
        title,
        join_url,
        join_at,
        bot_ids or [],
        error,
    )


async def _cancel_recall_bot(bot_id: str) -> None:
    try:
        await delete_bot(bot_id)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code != 405:
            raise
        await stop_bot(bot_id)


async def _enqueue_manual_recall_action(
    *,
    action: str,
    join_url: str,
    error: Exception,
    email_address: str | None,
    title: str | None,
    join_at: str | None,
    bot_ids: list[str] | None = None,
) -> None:
    try:
        record = await recall_failure_queue_store.enqueue(
            action=action,
            join_url=join_url,
            error=error,
            email_address=email_address,
            title=title,
            join_at=join_at,
            bot_ids=bot_ids,
            metadata={"manual_update_endpoint": "/api/recall/bots/{bot_id}"},
        )
    except SQLAlchemyError:
        logger.exception("Failed to persist Recall manual action queue item")
        return

    logger.warning("Stored Recall manual action queue item %s", record["id"])


async def _handle_recall_bots(gmail_result: dict) -> None:
    """Create or stop Recall AI bots based on meeting details in *gmail_result*."""
    for message in gmail_result.get("messages", []):
        details = message.get("meeting_details")
        if not details:
            continue

        email_address: str | None = gmail_result.get("email_address")

        join_url: str | None = details.get("join_url")
        if not join_url:
            continue

        is_canceled: bool = details.get("is_canceled", False)
        email_event_type: str = details.get("email_event_type", "created")
        title: str | None = details.get("title")
        join_at: str | None = details.get("join_at")

        if is_canceled:
            try:
                bots = await list_bots_for_meeting(join_url)
                bot_ids = [bot.get("id") for bot in bots if bot.get("id")]
                await asyncio.gather(*(_cancel_recall_bot(bot_id) for bot_id in bot_ids))
            except RECALL_AUTOMATION_ERRORS as exc:
                logger.exception("Failed to stop Recall AI bot(s) for meeting %s", join_url)
                _log_manual_recall_action(
                    action="stop",
                    join_url=join_url,
                    title=title,
                    join_at=join_at,
                    error=exc,
                )
                await _enqueue_manual_recall_action(
                    action="stop",
                    join_url=join_url,
                    error=exc,
                    email_address=email_address,
                    title=title,
                    join_at=join_at,
                )
        elif email_event_type == "updated":
            bot_ids: list[str] = []
            try:
                bots = await list_bots_for_meeting(join_url)
                bot_ids = [bot.get("id") for bot in bots if bot.get("id")]
                if bot_ids:
                    await asyncio.gather(
                        *(
                            update_bot(
                                bot_id,
                                meeting_url=join_url,
                                bot_name=title,
                                join_at=join_at,
                            )
                            for bot_id in bot_ids
                        )
                    )
                else:
                    await create_bot(join_url, bot_name=title, join_at=join_at)
            except RECALL_AUTOMATION_ERRORS as exc:
                logger.exception("Failed to update Recall AI bot(s) for meeting %s", join_url)
                _log_manual_recall_action(
                    action="update",
                    join_url=join_url,
                    title=title,
                    join_at=join_at,
                    error=exc,
                    bot_ids=bot_ids,
                )
                await _enqueue_manual_recall_action(
                    action="update",
                    join_url=join_url,
                    error=exc,
                    email_address=email_address,
                    title=title,
                    join_at=join_at,
                    bot_ids=bot_ids,
                )
        else:
            try:
                await create_bot(join_url, bot_name=title, join_at=join_at)
            except RECALL_AUTOMATION_ERRORS as exc:
                logger.exception("Failed to create Recall AI bot for meeting %s", join_url)
                _log_manual_recall_action(
                    action="create",
                    join_url=join_url,
                    title=title,
                    join_at=join_at,
                    error=exc,
                )
                await _enqueue_manual_recall_action(
                    action="create",
                    join_url=join_url,
                    error=exc,
                    email_address=email_address,
                    title=title,
                    join_at=join_at,
                )


class PubSubMessage(BaseModel):
    data: str
    messageId: str


class PubSubBody(BaseModel):
    message: PubSubMessage
    subscription: str


class RecallBotUpdateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meeting_url: str | None = None
    bot_name: str | None = None
    join_at: datetime | None = None


class RecallFailureResolutionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "resolved"


@router.post("/gmail/webhook")
async def receive_email(body: PubSubBody, background_tasks: BackgroundTasks) -> dict:
    try:
        decoded_json = decode_pubsub_message(body.message.data)
    except InvalidPubSubPayloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    history_id = decoded_json.get("historyId")
    email_address = decoded_json.get("emailAddress", "").lower()

    if not history_id or not email_address:
        raise HTTPException(
            status_code=400,
            detail="Pub/Sub payload must include emailAddress and historyId",
        )

    session_id = str(uuid.uuid4())
    logger.info(
        "Queued Gmail push notification for %s at historyId=%s",
        email_address,
        history_id,
    )

    async def run_gmail_sync() -> None:
        try:
            result = await process_gmail_push_notification(
                email_address=email_address,
                published_history_id=str(history_id),
            )
            logger.info("Gmail sync result: %s", result)
            await _handle_recall_bots(result)
        except HistoryIdExpiredError:
            logger.exception("Stored Gmail historyId expired for %s", email_address)
        except (HttpError, OSError, ValueError):
            logger.exception("Failed to process Gmail push notification for %s", email_address)

    background_tasks.add_task(run_gmail_sync)

    return {
        "status": "accepted",
        "session_id": session_id,
        "history_id": str(history_id),
        "email_address": email_address,
        "message_id": body.message.messageId,
    }


@router.post("/api/recall/audio-event")
async def recall_audio_event_compat() -> Response:
    """No-op compatibility route for stale cached Recall pages."""
    return Response(status_code=204)


@router.patch("/api/recall/bots/{bot_id}")
async def update_recall_bot(bot_id: str, body: RecallBotUpdateBody) -> dict:
    payload = body.model_dump(exclude_none=True, mode="json")
    if not payload:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    try:
        return await update_bot(bot_id, **payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc


@router.get("/api/recall/failures")
async def list_recall_failures(status: str = "pending") -> dict:
    items = await recall_failure_queue_store.list_items(status=status or None)
    return {"items": items, "count": len(items)}


@router.post("/api/recall/failures/{queue_id}/resolve")
async def resolve_recall_failure(queue_id: str, body: RecallFailureResolutionBody) -> dict:
    if body.status != "resolved":
        raise HTTPException(status_code=400, detail="Only status='resolved' is supported")

    item = await recall_failure_queue_store.resolve(queue_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Recall failure queue item not found")
    return item
