"""Gmail Pub/Sub webhook endpoints."""

import logging
import uuid

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Response
from googleapiclient.errors import HttpError
from pydantic import BaseModel

from app.integrations.recall.client import create_bot, list_bots_for_meeting, stop_bot
from app.services.gmail.history import (
    HistoryIdExpiredError,
    InvalidPubSubPayloadError,
    decode_pubsub_message,
    process_gmail_push_notification,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _handle_recall_bots(gmail_result: dict) -> None:
    """Create or stop Recall AI bots based on meeting details in *gmail_result*."""
    for message in gmail_result.get("messages", []):
        details = message.get("meeting_details")
        if not details:
            continue

        join_url: str | None = details.get("join_url")
        if not join_url:
            continue

        is_canceled: bool = details.get("is_canceled", False)

        if is_canceled:
            try:
                bots = await list_bots_for_meeting(join_url)
                bot_ids = [bot.get("id") for bot in bots if bot.get("id")]
                for bot_id in bot_ids:
                    await stop_bot(bot_id)
            except httpx.HTTPStatusError:
                logger.exception("Failed to stop Recall AI bot(s) for meeting %s", join_url)
        else:
            try:
                await create_bot(join_url)
            except httpx.HTTPStatusError:
                logger.exception("Failed to create Recall AI bot for meeting %s", join_url)


class PubSubMessage(BaseModel):
    data: str
    messageId: str


class PubSubBody(BaseModel):
    message: PubSubMessage
    subscription: str


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
