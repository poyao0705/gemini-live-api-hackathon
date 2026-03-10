"""Tests for meeting invite persistence and dashboard shaping."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.testclient import TestClient

from app.api.endpoints.meetings import list_meeting_invites
from app.services.gmail.client import GmailMessageSummary
from app.services.gmail.history import process_gmail_push_notification
from app.services.meetings import invites as invites_module
from app.services.meetings.invites import build_dashboard_payload, meeting_invite_store
from app.web.dashboard import mount_dashboard


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


def test_build_dashboard_payload_splits_past_and_upcoming() -> None:
    payload = build_dashboard_payload(
        [
            {
                "gmail_message_id": "past-1",
                "title": "Sprint Retro",
                "join_at": "2026-03-09T09:00:00+00:00",
                "updated_at": "2026-03-09T10:00:00+00:00",
                "created_at": "2026-03-08T10:00:00+00:00",
                "meeting_status": "scheduled",
                "meeting_details_json": {"date_time_text": "Mon Mar 09, 2026 ⋅ 9am – 9:30am"},
            },
            {
                "gmail_message_id": "current-1",
                "title": "Live Standup",
                "join_at": "2026-03-10T12:00:00+00:00",
                "updated_at": "2026-03-10T11:45:00+00:00",
                "created_at": "2026-03-08T09:30:00+00:00",
                "meeting_status": "scheduled",
                "meeting_details_json": {"date_time_text": "Tue Mar 10, 2026 ⋅ 12pm – 12:30pm"},
            },
            {
                "gmail_message_id": "future-1",
                "title": "Roadmap Review",
                "join_at": "2026-03-11T15:00:00+00:00",
                "updated_at": "2026-03-10T10:00:00+00:00",
                "created_at": "2026-03-08T11:00:00+00:00",
                "meeting_status": "scheduled",
                "meeting_details_json": {"date_time_text": "Wed Mar 11, 2026 ⋅ 3pm – 3:30pm"},
            },
            {
                "gmail_message_id": "future-2",
                "title": "Customer Debrief",
                "join_at": "2026-03-12T12:00:00+00:00",
                "updated_at": "2026-03-10T12:00:00+00:00",
                "created_at": "2026-03-08T12:00:00+00:00",
                "meeting_status": "canceled",
                "meeting_details_json": {"date_time_text": "Thu Mar 12, 2026 ⋅ 12pm – 12:30pm"},
            },
            {
                "gmail_message_id": "unknown-time",
                "title": "Inbox-only Update",
                "join_at": None,
                "updated_at": "2026-03-10T09:00:00+00:00",
                "created_at": "2026-03-08T09:00:00+00:00",
                "meeting_status": "scheduled",
            },
        ],
        now=invites_module.datetime.fromisoformat("2026-03-10T12:00:00+00:00"),
    )

    assert payload["counts"]["past_meetings"] == 2
    assert payload["counts"]["upcoming_events"] == 2
    assert payload["counts"]["canceled"] == 1
    assert [item["gmail_message_id"] for item in payload["upcoming_events"]] == [
        "future-1",
        "future-2",
    ]
    assert [item["gmail_message_id"] for item in payload["past_meetings"]] == [
        "current-1",
        "past-1",
    ]
    assert payload["past_meetings"][0]["is_ongoing"] is True
    assert payload["past_meetings"][1]["is_ongoing"] is False
    assert all(item["gmail_message_id"] != "unknown-time" for item in payload["past_meetings"])
    assert payload["upcoming_by_date"]["2026-03-11"][0]["gmail_message_id"] == "future-1"


def test_dashboard_mount_renders_meeting_sections(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    mount_dashboard(app)

    async def fake_dashboard_payload(*, email_address=None, now=None):
        del email_address, now
        return {
            "generated_at": "2026-03-10T12:00:00+00:00",
            "calendar_month": 3,
            "calendar_year": 2026,
            "counts": {
                "past_meetings": 2,
                "upcoming_events": 3,
                "canceled": 1,
            },
            "past_meetings": [
                {
                    "gmail_message_id": "past-1",
                    "title": "Sprint Retro",
                    "join_at": "2026-03-09T09:00:00+00:00",
                    "updated_at": "2026-03-09T10:00:00+00:00",
                    "created_at": "2026-03-08T10:00:00+00:00",
                    "meeting_status": "scheduled",
                    "join_url": "https://meet.google.com/past-link",
                    "is_ongoing": False,
                    "meeting_details_json": {"organizer": "Ops"},
                },
                {
                    "gmail_message_id": "current-1",
                    "title": "Live Standup",
                    "join_at": "2026-03-10T12:00:00+00:00",
                    "updated_at": "2026-03-10T11:45:00+00:00",
                    "created_at": "2026-03-08T10:30:00+00:00",
                    "meeting_status": "scheduled",
                    "join_url": "https://meet.google.com/live-link",
                    "is_ongoing": True,
                    "meeting_details_json": {"organizer": "Ops"},
                }
            ],
            "upcoming_events": [
                {
                    "gmail_message_id": "future-1",
                    "title": "Roadmap Review",
                    "join_at": "2026-03-11T15:00:00+00:00",
                    "updated_at": "2026-03-10T10:00:00+00:00",
                    "created_at": "2026-03-08T11:00:00+00:00",
                    "meeting_status": "scheduled",
                    "join_url": "https://meet.google.com/future-link",
                    "meeting_details_json": {"organizer": "Product"},
                }
            ,
                {
                    "gmail_message_id": "future-1b",
                    "title": "Partner Check-in",
                    "join_at": "2026-03-11T17:00:00+00:00",
                    "updated_at": "2026-03-10T10:30:00+00:00",
                    "created_at": "2026-03-08T11:30:00+00:00",
                    "meeting_status": "scheduled",
                    "join_url": "https://meet.google.com/future-link-b",
                    "meeting_details_json": {"organizer": "Partnerships"},
                },
                {
                    "gmail_message_id": "future-2",
                    "title": "Hiring Sync",
                    "join_at": "2026-03-12T11:00:00+00:00",
                    "updated_at": "2026-03-10T11:00:00+00:00",
                    "created_at": "2026-03-08T12:00:00+00:00",
                    "meeting_status": "canceled",
                    "join_url": "https://meet.google.com/future-link-2",
                    "meeting_details_json": {"organizer": "Talent"},
                }
            ],
            "upcoming_by_date": {
                "2026-03-11": [
                    {
                        "gmail_message_id": "future-1",
                        "title": "Roadmap Review",
                        "join_at": "2026-03-11T15:00:00+00:00",
                        "updated_at": "2026-03-10T10:00:00+00:00",
                        "created_at": "2026-03-08T11:00:00+00:00",
                        "meeting_status": "scheduled",
                        "join_url": "https://meet.google.com/future-link",
                        "meeting_details_json": {"organizer": "Product"},
                    },
                    {
                        "gmail_message_id": "future-1b",
                        "title": "Partner Check-in",
                        "join_at": "2026-03-11T17:00:00+00:00",
                        "updated_at": "2026-03-10T10:30:00+00:00",
                        "created_at": "2026-03-08T11:30:00+00:00",
                        "meeting_status": "scheduled",
                        "join_url": "https://meet.google.com/future-link-b",
                        "meeting_details_json": {"organizer": "Partnerships"},
                    }
                ],
                "2026-03-12": [
                    {
                        "gmail_message_id": "future-2",
                        "title": "Hiring Sync",
                        "join_at": "2026-03-12T11:00:00+00:00",
                        "updated_at": "2026-03-10T11:00:00+00:00",
                        "created_at": "2026-03-08T12:00:00+00:00",
                        "meeting_status": "canceled",
                        "join_url": "https://meet.google.com/future-link-2",
                        "meeting_details_json": {"organizer": "Talent"},
                    }
                ]
            },
        }

    monkeypatch.setattr(
        "app.web.dashboard.meeting_invite_store.get_dashboard_payload",
        fake_dashboard_payload,
    )

    client = TestClient(app)
    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert "Meetloaf" in response.text
    assert "Past meetings" in response.text
    assert "Upcoming calendar" in response.text
    assert "Sprint Retro" in response.text
    assert "Roadmap Review" in response.text
    assert "htmx.min.js" in response.text
    assert "selected_date=2026-03-11" in response.text
    assert 'hx-get="/dashboard/upcoming-panel?selected_date=2026-03-11"' in response.text
    assert 'hx-target="#upcoming-calendar-panel"' in response.text
    assert 'hx-swap="outerHTML"' in response.text
    assert 'hx-push-url="false"' in response.text
    assert "Showing 2 events for Wednesday, Mar 11." in response.text
    assert "https://meet.google.com/past-link" not in response.text
    assert "https://meet.google.com/live-link" in response.text
    assert "https://meet.google.com/future-link-2" not in response.text
    assert 'target="_blank"' in response.text
    assert 'rel="noopener noreferrer"' in response.text
    assert response.text.count("calendar-day-dot") == 2

    selected_response = client.get("/dashboard/upcoming-panel?selected_date=2026-03-12")

    assert selected_response.status_code == 200
    assert "Showing 1 event for Thursday, Mar 12." in selected_response.text
    assert "Hiring Sync" in selected_response.text
    assert "Meeting was canceled" in selected_response.text
    assert "https://meet.google.com/future-link-2" not in selected_response.text
    assert "Roadmap Review" not in selected_response.text


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
            "app.services.gmail.state.gmail_state_store.get_user_state",
            new_callable=AsyncMock,
            return_value={"last_history_id": "200"},
        ),
        patch(
            "app.services.gmail.state.gmail_state_store.upsert_user_state",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch("app.integrations.google.client.get_gmail_service", return_value=object()),
        patch(
            "app.services.gmail.history.list_history_updates",
            new_callable=AsyncMock,
            return_value=([{"messagesAdded": [{"message": {"id": "msg-2"}}]}], "301"),
        ),
        patch(
            "app.services.gmail.client.get_message_summary",
            new_callable=AsyncMock,
            return_value=summary,
        ),
        patch(
            "app.services.meetings.invites.meeting_invite_store.upsert_from_message",
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