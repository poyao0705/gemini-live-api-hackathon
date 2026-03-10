"""Async client for the Recall AI REST API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _auth_headers() -> dict[str, str]:
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Token {settings.recall_ai_token}",
    }


async def create_bot(meeting_url: str, bot_name: str | None = None) -> dict[str, Any]:
    """Create a Recall AI bot for the given meeting URL.

    Returns the bot object returned by the Recall AI API.

    Args:
        meeting_url: The URL of the meeting to join.
        bot_name: Optional display name for the bot; falls back to the
            ``recall_ai_bot_name`` setting.

    Raises:
        httpx.HTTPStatusError: If the Recall AI API returns a non-2xx status.
    """
    name = bot_name or settings.recall_ai_bot_name
    url = f"{settings.recall_ai_base_url}/bot/"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=_auth_headers(),
            json={"meeting_url": meeting_url, "bot_name": name},
        )
        response.raise_for_status()
        bot: dict[str, Any] = response.json()

    logger.info("Created Recall AI bot %s for meeting %s", bot.get("id"), meeting_url)
    return bot


async def stop_bot(bot_id: str) -> None:
    """Ask the Recall AI bot to leave its meeting.

    Args:
        bot_id: The Recall AI bot identifier.

    Raises:
        httpx.HTTPStatusError: If the Recall AI API returns a non-2xx status.
    """
    url = f"{settings.recall_ai_base_url}/bot/{bot_id}/leave_call/"

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=_auth_headers())
        response.raise_for_status()

    logger.info("Stopped Recall AI bot %s", bot_id)


async def list_bots_for_meeting(meeting_url: str) -> list[dict[str, Any]]:
    """Return all Recall AI bots associated with *meeting_url*.

    Args:
        meeting_url: The URL of the meeting whose bots should be listed.

    Returns:
        A (possibly empty) list of bot objects from the Recall AI API.

    Raises:
        httpx.HTTPStatusError: If the Recall AI API returns a non-2xx status.
    """
    url = f"{settings.recall_ai_base_url}/bot/"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=_auth_headers(),
            params={"meeting_url": meeting_url},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()

    bots: list[dict[str, Any]] = data.get("results", [])
    logger.debug("Found %s Recall AI bot(s) for meeting %s", len(bots), meeting_url)
    return bots
