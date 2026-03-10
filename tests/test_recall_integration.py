"""Tests for the Recall AI integration client and webhook handler."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.integrations.recall.client import create_bot, list_bots_for_meeting, stop_bot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(status_code: int, json_body: Any) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_body
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=response
        )
    else:
        response.raise_for_status.return_value = None
    return response


# ---------------------------------------------------------------------------
# create_bot
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_bot_returns_bot_dict() -> None:
    bot_payload = {"id": "bot-123", "status": "joining"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_response(200, bot_payload))

    with patch("app.integrations.recall.client.httpx.AsyncClient", return_value=mock_client):
        result = await create_bot("https://zoom.us/j/123", bot_name="TestBot")

    assert result == bot_payload
    mock_client.post.assert_awaited_once()
    _, kwargs = mock_client.post.call_args
    assert kwargs["json"]["meeting_url"] == "https://zoom.us/j/123"
    assert kwargs["json"]["bot_name"] == "TestBot"


@pytest.mark.anyio
async def test_create_bot_uses_default_bot_name() -> None:
    bot_payload = {"id": "bot-456"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_response(200, bot_payload))

    with (
        patch("app.integrations.recall.client.httpx.AsyncClient", return_value=mock_client),
        patch("app.integrations.recall.client.settings") as mock_settings,
    ):
        mock_settings.recall_ai_token = "tok"
        mock_settings.recall_ai_base_url = "https://example.recall.ai/api/v1"
        mock_settings.recall_ai_bot_name = "Default Bot"
        result = await create_bot("https://zoom.us/j/999")

    assert result == bot_payload
    _, kwargs = mock_client.post.call_args
    assert kwargs["json"]["bot_name"] == "Default Bot"


@pytest.mark.anyio
async def test_create_bot_raises_on_api_error() -> None:
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_response(422, {"detail": "bad request"}))

    with patch("app.integrations.recall.client.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await create_bot("https://zoom.us/j/bad")


# ---------------------------------------------------------------------------
# stop_bot
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_stop_bot_calls_leave_endpoint() -> None:
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_response(200, {}))

    with (
        patch("app.integrations.recall.client.httpx.AsyncClient", return_value=mock_client),
        patch("app.integrations.recall.client.settings") as mock_settings,
    ):
        mock_settings.recall_ai_token = "tok"
        mock_settings.recall_ai_base_url = "https://example.recall.ai/api/v1"
        await stop_bot("bot-abc")

    mock_client.post.assert_awaited_once()
    url_arg = mock_client.post.call_args[0][0]
    assert "bot-abc" in url_arg
    assert "leave_call" in url_arg


@pytest.mark.anyio
async def test_stop_bot_raises_on_api_error() -> None:
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_response(404, {"detail": "not found"}))

    with patch("app.integrations.recall.client.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await stop_bot("nonexistent-bot")


# ---------------------------------------------------------------------------
# list_bots_for_meeting
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_bots_for_meeting_returns_results() -> None:
    api_response = {
        "results": [{"id": "bot-1"}, {"id": "bot-2"}],
        "count": 2,
    }

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_mock_response(200, api_response))

    with patch("app.integrations.recall.client.httpx.AsyncClient", return_value=mock_client):
        bots = await list_bots_for_meeting("https://zoom.us/j/123")

    assert bots == [{"id": "bot-1"}, {"id": "bot-2"}]
    _, kwargs = mock_client.get.call_args
    assert kwargs["params"]["meeting_url"] == "https://zoom.us/j/123"


@pytest.mark.anyio
async def test_list_bots_for_meeting_returns_empty_when_no_results() -> None:
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_mock_response(200, {"results": [], "count": 0}))

    with patch("app.integrations.recall.client.httpx.AsyncClient", return_value=mock_client):
        bots = await list_bots_for_meeting("https://zoom.us/j/empty")

    assert bots == []


# ---------------------------------------------------------------------------
# Webhook _handle_recall_bots helper
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_handle_recall_bots_creates_bot_for_invitation() -> None:
    from app.api.endpoints.webhooks import _handle_recall_bots

    gmail_result = {
        "messages": [
            {
                "meeting_details": {
                    "join_url": "https://zoom.us/j/111",
                    "is_canceled": False,
                }
            }
        ]
    }

    with patch("app.api.endpoints.webhooks.create_bot", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {"id": "bot-new"}
        await _handle_recall_bots(gmail_result)

    mock_create.assert_awaited_once_with("https://zoom.us/j/111")


@pytest.mark.anyio
async def test_handle_recall_bots_stops_bots_for_cancellation() -> None:
    from app.api.endpoints.webhooks import _handle_recall_bots

    gmail_result = {
        "messages": [
            {
                "meeting_details": {
                    "join_url": "https://zoom.us/j/222",
                    "is_canceled": True,
                }
            }
        ]
    }

    with (
        patch(
            "app.api.endpoints.webhooks.list_bots_for_meeting",
            new_callable=AsyncMock,
        ) as mock_list,
        patch(
            "app.api.endpoints.webhooks.stop_bot",
            new_callable=AsyncMock,
        ) as mock_stop,
    ):
        mock_list.return_value = [{"id": "bot-old-1"}, {"id": "bot-old-2"}]
        await _handle_recall_bots(gmail_result)

    mock_list.assert_awaited_once_with("https://zoom.us/j/222")
    assert mock_stop.await_count == 2


@pytest.mark.anyio
async def test_handle_recall_bots_skips_messages_without_meeting_details() -> None:
    from app.api.endpoints.webhooks import _handle_recall_bots

    gmail_result = {"messages": [{"meeting_details": None}, {}]}

    with (
        patch("app.api.endpoints.webhooks.create_bot", new_callable=AsyncMock) as mock_create,
        patch(
            "app.api.endpoints.webhooks.list_bots_for_meeting", new_callable=AsyncMock
        ) as mock_list,
    ):
        await _handle_recall_bots(gmail_result)

    mock_create.assert_not_awaited()
    mock_list.assert_not_awaited()


@pytest.mark.anyio
async def test_handle_recall_bots_skips_messages_without_join_url() -> None:
    from app.api.endpoints.webhooks import _handle_recall_bots

    gmail_result = {
        "messages": [
            {
                "meeting_details": {
                    "join_url": None,
                    "is_canceled": False,
                }
            }
        ]
    }

    with patch("app.api.endpoints.webhooks.create_bot", new_callable=AsyncMock) as mock_create:
        await _handle_recall_bots(gmail_result)

    mock_create.assert_not_awaited()


@pytest.mark.anyio
async def test_handle_recall_bots_logs_error_on_create_failure() -> None:
    from app.api.endpoints.webhooks import _handle_recall_bots

    gmail_result = {
        "messages": [
            {
                "meeting_details": {
                    "join_url": "https://zoom.us/j/fail",
                    "is_canceled": False,
                }
            }
        ]
    }

    err = httpx.HTTPStatusError("error", request=MagicMock(), response=MagicMock())
    with patch(
        "app.api.endpoints.webhooks.create_bot", new_callable=AsyncMock, side_effect=err
    ):
        # Should not raise; error is logged instead
        await _handle_recall_bots(gmail_result)


@pytest.mark.anyio
async def test_handle_recall_bots_logs_error_on_stop_failure() -> None:
    from app.api.endpoints.webhooks import _handle_recall_bots

    gmail_result = {
        "messages": [
            {
                "meeting_details": {
                    "join_url": "https://zoom.us/j/cancel-fail",
                    "is_canceled": True,
                }
            }
        ]
    }

    err = httpx.HTTPStatusError("error", request=MagicMock(), response=MagicMock())
    with patch(
        "app.api.endpoints.webhooks.list_bots_for_meeting",
        new_callable=AsyncMock,
        side_effect=err,
    ):
        # Should not raise; error is logged instead
        await _handle_recall_bots(gmail_result)
