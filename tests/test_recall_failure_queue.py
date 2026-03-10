"""Tests for the persisted Recall failure queue."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.endpoints.webhooks import (
    _handle_recall_bots,
    list_recall_failures,
    resolve_recall_failure,
    RecallFailureResolutionBody,
)
from app.services.recall import failures as failures_module
from app.services.recall.failures import recall_failure_queue_store


@pytest.fixture
async def setup_recall_queue_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[None]:
    db_path = tmp_path / "recall-failures.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

    monkeypatch.setattr(failures_module, "async_session_factory", session_factory)

    try:
        yield
    finally:
        await engine.dispose()


@pytest.mark.anyio
@pytest.mark.usefixtures("setup_recall_queue_db")
async def test_recall_failure_queue_store_enqueue_list_and_resolve() -> None:
    record = await recall_failure_queue_store.enqueue(
        action="create",
        join_url="https://meet.google.com/afi-dqnj-bib?hs=224",
        error=RuntimeError("schedule failed"),
        email_address="jobmate.agent@gmail.com",
        title="test meeting",
        join_at="2026-03-10T14:15:00+11:00",
        metadata={"manual_update_endpoint": "/api/recall/bots/{bot_id}"},
    )

    assert record["status"] == "pending"
    assert record["error_type"] == "RuntimeError"

    items = await recall_failure_queue_store.list_items(status="pending")
    assert len(items) == 1
    assert items[0]["id"] == record["id"]

    resolved = await recall_failure_queue_store.resolve(record["id"])
    assert resolved is not None
    assert resolved["status"] == "resolved"


@pytest.mark.anyio
@pytest.mark.usefixtures("setup_recall_queue_db")
async def test_handle_recall_bots_persists_failed_manual_action() -> None:
    gmail_result = {
        "email_address": "jobmate.agent@gmail.com",
        "messages": [
            {
                "meeting_details": {
                    "join_url": "https://meet.google.com/afi-dqnj-bib?hs=224",
                    "title": "test meeting",
                    "join_at": "2026-03-10T14:15:00+11:00",
                    "is_canceled": False,
                }
            }
        ],
    }

    error = httpx.HTTPStatusError(
        "error",
        request=httpx.Request("POST", "https://x"),
        response=httpx.Response(422),
    )

    from unittest.mock import AsyncMock, patch

    with patch("app.api.endpoints.webhooks.create_bot", new_callable=AsyncMock, side_effect=error):
        await _handle_recall_bots(gmail_result)

    items = await recall_failure_queue_store.list_items(status="pending")
    assert len(items) == 1
    assert items[0]["action"] == "create"
    assert items[0]["email_address"] == "jobmate.agent@gmail.com"
    assert items[0]["join_url"] == "https://meet.google.com/afi-dqnj-bib?hs=224"


@pytest.mark.anyio
@pytest.mark.usefixtures("setup_recall_queue_db")
async def test_recall_failure_endpoints_list_and_resolve() -> None:
    record = await recall_failure_queue_store.enqueue(
        action="update",
        join_url="https://meet.google.com/afi-dqnj-bib?hs=224",
        error=RuntimeError("update failed"),
    )

    listed = await list_recall_failures()
    assert listed["count"] == 1
    assert listed["items"][0]["id"] == record["id"]

    resolved = await resolve_recall_failure(record["id"], RecallFailureResolutionBody())
    assert resolved["status"] == "resolved"