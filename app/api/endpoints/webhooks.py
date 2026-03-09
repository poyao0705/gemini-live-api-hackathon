"""Gmail Pub/Sub webhook endpoints."""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response
from googleapiclient.errors import HttpError
from pydantic import BaseModel

from app.services.gmail.history import (
    HistoryIdExpiredError,
    InvalidPubSubPayloadError,
    decode_pubsub_message,
    process_gmail_push_notification,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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
