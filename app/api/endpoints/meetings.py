"""Meeting-related API endpoints."""

from fastapi import APIRouter

router = APIRouter()

# In-memory store for meeting agenda items
meetings_store: dict = {}


@router.post("/api/meetings/{session_id}/agenda")
async def set_agenda(session_id: str, body: dict) -> dict:
    """Set the meeting agenda for a given session."""
    items = body.get("agenda", [])
    clean_items = ""
    return {"status": "ok", "session_id": session_id, "agenda": clean_items}
