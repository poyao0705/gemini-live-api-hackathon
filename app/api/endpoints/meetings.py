"""Meeting-related API endpoints."""

from fastapi import APIRouter

from app.services.meetings.invites import meeting_invite_store

router = APIRouter()

# In-memory store for meeting agenda items
meetings_store: dict = {}


@router.post("/api/meetings/{session_id}/agenda")
async def set_agenda(session_id: str, body: dict) -> dict:
    """Set the meeting agenda for a given session."""
    clean_items = body.get("agenda", [])
    return {"status": "ok", "session_id": session_id, "agenda": clean_items}


@router.get("/api/meetings/invites")
async def list_meeting_invites(
    email_address: str | None = None,
    meeting_status: str | None = None,
) -> dict:
    """List persisted meeting invite emails with optional filters."""

    items = await meeting_invite_store.list_invites(
        email_address=email_address,
        meeting_status=meeting_status,
    )
    return {"items": items, "count": len(items)}
