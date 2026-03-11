"""Web router for static HTML pages and browser assets."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


@router.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the main streaming demo page."""
    html_file = ASSETS_DIR / "index.html"
    return HTMLResponse(html_file.read_text())


@router.get("/recall", response_class=HTMLResponse)
async def recall_root() -> HTMLResponse:
    """Serve the Recall runtime page."""
    html_file = ASSETS_DIR / "recall.html"
    return HTMLResponse(html_file.read_text())


@router.get("/assets/{asset_path:path}")
async def frontend_asset(asset_path: str) -> FileResponse:
    """Serve browser assets from the app-owned asset directory."""
    asset_file = (ASSETS_DIR / asset_path).resolve()
    if not asset_file.is_file() or ASSETS_DIR.resolve() not in asset_file.parents:
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(asset_file)
