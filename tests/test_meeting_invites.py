"""Tests for meeting invite persistence."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.endpoints.meetings import list_meeting_invites
from app.services.gmail.history import GmailMessageSummary, process_gmail_push_notification
from app.services.meetings import invites as invites_module
from app.services.meetings.invites import meeting_invite_store


@pytest.fixture
async def setup_meeting_invite_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[None]:
    db_path = tmp_path / "meeting-invites.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

    monkeypatch.setattr(invites_module, "async_session_factory", session_factory)

    try:
        yield
    finally:
        await engine.dispose()


@pytest.mark.anyio
@pytest.mark.usefixtures("setup_meeting_invite_db")
async def test_meeting_invite_store_persists_invite_with_status() -> None:
    message = GmailMessageSummary(
        id="msg-1",
        thread_id="thread-1",
        history_id="200",
        label_ids=["INBOX"],
        snippet="meeting snippet",
        subject="Invitation: Product Sync @ Wed Mar 11, 2026 9am - 9:30am",
        sender="Po-Yao Huang <poyaohg0705@gmail.com>",
        recipient="jobmate.agent@gmail.com",
        date="Tue, 10 Mar 2026 02:52:51 +0000",
        body_text="meeting body",
        meeting_details={
            "title": "Product Sync",
            "calendar_event_id": "event-123",
            "email_event_type": "created",
            "event_status": "confirmed",
            "is_canceled": False,
            "date_time_text": "Wednesday Mar 11, 2026 ⋅ 9am – 9:30am",
            "join_at": "2026-03-11T09:00:00+11:00",
            "timezone": "Australia/Sydney",
            "location": None,
            "join_url": "https://meet.google.com/abc-defg-hij",
            "meeting_id": None,
            "passcode": None,
            "organizer": "Po-Yao Huang",
            "guests": ["jobmate.agent@gmail.com"],
            "agenda": ["Launch timeline"],
            "agenda_confidence": "explicit",
        },
    )

    record = await meeting_invite_store.upsert_from_message("jobmate.agent@gmail.com", message)

    assert record is not None
    assert record["gmail_message_id"] == "msg-1"
    assert record["meeting_status"] == "scheduled"
    assert record["email_event_type"] == "created"
    assert record["calendar_event_id"] == "event-123"
    assert record["join_at"] == "2026-03-11T09:00:00+11:00"

    items = await meeting_invite_store.list_invites(email_address="jobmate.agent@gmail.com")
    assert len(items) == 1
    assert items[0]["gmail_message_id"] == "msg-1"


@pytest.mark.anyio
@pytest.mark.usefixtures("setup_meeting_invite_db")
async def test_list_meeting_invites_endpoint_filters_by_status() -> None:
    created_message = GmailMessageSummary(
        id="msg-created",
        thread_id="thread-created",
        history_id="201",
        label_ids=["INBOX"],
        snippet="meeting snippet",
        subject="Invitation: Product Sync @ Wed Mar 11, 2026 9am - 9:30am",
        sender="Po-Yao Huang <poyaohg0705@gmail.com>",
        recipient="jobmate.agent@gmail.com",
        date="Tue, 10 Mar 2026 02:52:51 +0000",
        body_text="meeting body",
        meeting_details={
            "title": "Product Sync",
            "calendar_event_id": "event-created",
            "email_event_type": "created",
            "event_status": "confirmed",
            "is_canceled": False,
            "date_time_text": "Wednesday Mar 11, 2026 ⋅ 9am – 9:30am",
            "join_at": "2026-03-11T09:00:00+11:00",
            "timezone": "Australia/Sydney",
            "location": None,
            "join_url": "https://meet.google.com/created-meeting",
            "meeting_id": None,
            "passcode": None,
            "organizer": "Po-Yao Huang",
            "guests": ["jobmate.agent@gmail.com"],
            "agenda": [],
            "agenda_confidence": "none",
        },
    )
    canceled_message = GmailMessageSummary(
        id="msg-canceled",
        thread_id="thread-canceled",
        history_id="202",
        label_ids=["INBOX"],
        snippet="meeting snippet",
        subject="Canceled event: Product Sync @ Wed Mar 11, 2026 9am - 9:30am",
        sender="Po-Yao Huang <poyaohg0705@gmail.com>",
        recipient="jobmate.agent@gmail.com",
        date="Tue, 10 Mar 2026 02:52:51 +0000",
        body_text="meeting body",
        meeting_details={
            "title": "Product Sync",
            "calendar_event_id": "event-canceled",
            "email_event_type": "canceled",
            "event_status": "canceled",
            "is_canceled": True,
            "date_time_text": "Wednesday Mar 11, 2026 ⋅ 9am – 9:30am",
            "join_at": "2026-03-11T09:00:00+11:00",
            "timezone": "Australia/Sydney",
            "location": None,
            "join_url": "https://meet.google.com/canceled-meeting",
            "meeting_id": None,
            "passcode": None,
            "organizer": "Po-Yao Huang",
            "guests": ["jobmate.agent@gmail.com"],
            "agenda": [],
            "agenda_confidence": "none",
        },
    )

    await meeting_invite_store.upsert_from_message("jobmate.agent@gmail.com", created_message)
    await meeting_invite_store.upsert_from_message("jobmate.agent@gmail.com", canceled_message)

    result = await list_meeting_invites(
        email_address="jobmate.agent@gmail.com",
        meeting_status="canceled",
    )

    assert result["count"] == 1
    assert result["items"][0]["gmail_message_id"] == "msg-canceled"
    assert result["items"][0]["meeting_status"] == "canceled"


@pytest.mark.anyio
@pytest.mark.usefixtures("setup_meeting_invite_db")
async def test_cancellation_updates_existing_invite_row() -> None:
    """A cancellation email for the same calendar event must mutate the existing row."""
    invite_message = GmailMessageSummary(
        id="msg-orig",
        thread_id="thread-standup-shared",
        history_id="300",
        label_ids=["INBOX"],
        snippet="original invite",
        subject="Invitation: Team Standup @ Thu Mar 12, 2026 10am",
        sender="organizer@example.com",
        recipient="jobmate.agent@gmail.com",
        date="Tue, 10 Mar 2026 08:00:00 +0000",
        body_text="join url body",
        meeting_details={
            "title": "Team Standup",
            "calendar_event_id": "event-same-abc",
            "email_event_type": "created",
            "event_status": "confirmed",
            "is_canceled": False,
            "join_url": "https://meet.google.com/xyz-1234",
            "join_at": "2026-03-12T10:00:00+11:00",
            "timezone": "Australia/Sydney",
            "date_time_text": "Thursday Mar 12, 2026 ⋅ 10am",
            "location": None,
            "meeting_id": None,
            "passcode": None,
            "organizer": "organizer@example.com",
            "guests": [],
            "agenda": [],
            "agenda_confidence": "none",
        },
    )
    cancel_message = GmailMessageSummary(
        id="msg-cancel",  # different message ID
        thread_id="thread-standup-shared",  # same thread — Google sends all calendar emails for one event in one thread
        history_id="301",
        label_ids=["INBOX"],
        snippet="event canceled",
        subject="Canceled event: Team Standup @ Thu Mar 12, 2026 10am",
        sender="organizer@example.com",
        recipient="jobmate.agent@gmail.com",
        date="Tue, 10 Mar 2026 09:00:00 +0000",
        body_text="event canceled body",
        meeting_details={
            "title": "Team Standup",
            "calendar_event_id": "event-same-abc",  # same calendar event
            "email_event_type": "canceled",
            "event_status": "canceled",
            "is_canceled": True,
            "join_url": None,
            "join_at": None,
            "timezone": "Australia/Sydney",
            "date_time_text": "Thursday Mar 12, 2026 ⋅ 10am",
            "location": None,
            "meeting_id": None,
            "passcode": None,
            "organizer": "organizer@example.com",
            "guests": [],
            "agenda": [],
            "agenda_confidence": "none",
        },
    )

    await meeting_invite_store.upsert_from_message("jobmate.agent@gmail.com", invite_message)
    await meeting_invite_store.upsert_from_message("jobmate.agent@gmail.com", cancel_message)

    items = await meeting_invite_store.list_invites(email_address="jobmate.agent@gmail.com")

    # Must be ONE row, not two
    assert len(items) == 1
    assert items[0]["calendar_event_id"] == "event-same-abc"
    assert items[0]["meeting_status"] == "canceled"
    assert items[0]["is_canceled"] is True
    assert items[0]["email_event_type"] == "canceled"


@pytest.mark.anyio
async def test_process_gmail_push_notification_persists_meeting_email() -> None:
    summary = GmailMessageSummary(
        id="msg-2",
        thread_id="thread-2",
        history_id="300",
        label_ids=["INBOX"],
        snippet="meeting snippet",
        subject="Updated invitation: Product Sync @ Wed Mar 11, 2026 9am - 9:30am",
        sender="Po-Yao Huang <poyaohg0705@gmail.com>",
        recipient="jobmate.agent@gmail.com",
        date="Tue, 10 Mar 2026 02:52:51 +0000",
        body_text="meeting body",
        meeting_details={
            "title": "Product Sync",
            "calendar_event_id": "event-456",
            "email_event_type": "updated",
            "event_status": "confirmed",
            "is_canceled": False,
            "date_time_text": "Wednesday Mar 11, 2026 ⋅ 9am – 9:30am",
            "join_at": "2026-03-11T09:00:00+11:00",
            "timezone": "Australia/Sydney",
            "location": None,
            "join_url": "https://meet.google.com/abc-defg-hij",
            "meeting_id": None,
            "passcode": None,
            "organizer": "Po-Yao Huang",
            "guests": ["jobmate.agent@gmail.com"],
            "agenda": [],
            "agenda_confidence": "none",
        },
    )

    with (
        patch(
            "app.services.gmail.history.gmail_state_store.get_user_state",
            new_callable=AsyncMock,
            return_value={"last_history_id": "200"},
        ),
        patch(
            "app.services.gmail.history.gmail_state_store.upsert_user_state",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch("app.services.gmail.history.get_gmail_service", return_value=object()),
        patch(
            "app.services.gmail.history.list_history_updates",
            new_callable=AsyncMock,
            return_value=([{"messagesAdded": [{"message": {"id": "msg-2"}}]}], "301"),
        ),
        patch(
            "app.services.gmail.history.get_message_summary",
            new_callable=AsyncMock,
            return_value=summary,
        ),
        patch(
            "app.services.gmail.history.meeting_invite_store.upsert_from_message",
            new_callable=AsyncMock,
        ) as mock_upsert,
    ):
        result = await process_gmail_push_notification(
            email_address="jobmate.agent@gmail.com",
            published_history_id="301",
        )

    mock_upsert.assert_awaited_once_with("jobmate.agent@gmail.com", summary)
    assert result["status"] == "processed"
    assert len(result["messages"]) == 1