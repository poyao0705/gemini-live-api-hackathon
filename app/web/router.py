"""Web router for serving HTML template pages."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


@router.get("/")
async def root() -> FileResponse:
    """Serve the index.html page."""
    return FileResponse(TEMPLATES_DIR / "index.html")


@router.get("/recall")
async def recall_root() -> FileResponse:
    """Serve minimal webpage runtime for Recall output media."""
    return FileResponse(TEMPLATES_DIR / "recall.html")
