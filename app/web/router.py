"""Web router for FastHTML-rendered frontend pages and browser assets."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import fasthtml.common as fh

from app.web.common import page_head

# FastHTML symbols used only by the recall page — accessed via getattr to avoid
# shadowing identically-named FastAPI exports (Header, Form, etc.).
Body = getattr(fh, "Body")
Button = getattr(fh, "Button")
Div = getattr(fh, "Div")
Form = getattr(fh, "Form")
H2 = getattr(fh, "H2")
Html = getattr(fh, "Html")
Input = getattr(fh, "Input")
Label = getattr(fh, "Label")
Main = getattr(fh, "Main")
Option = getattr(fh, "Option")
P = getattr(fh, "P")
Section = getattr(fh, "Section")
Select = getattr(fh, "Select")
Span = getattr(fh, "Span")
to_xml = fh.to_xml

router = APIRouter()

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


@router.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the main streaming demo page as a static HTML file."""
    html_file = ASSETS_DIR / "index.html"
    return HTMLResponse(html_file.read_text())


def _recall_page() -> Html:
    return Html(
        page_head(
            title="Gemini Live Runtime",
            page_script_src="/assets/js/recall.js?v=20260308",
        ),
        Body(
            Main(
                # ── Debug Controls (hidden unless debug mode) ──────────────────
                Section(
                    Div(
                        H2("Debug Controls", cls="card-title text-ink"),
                        P(
                            "Local-only controls for testing the same conversational runtime.",
                            cls="text-sm opacity-70 mb-4 text-muted",
                        ),
                        # Input grid
                        Div(
                            Div(
                                Label(
                                    Span("WebSocket URL", cls="label-text text-ink"),
                                    cls="label",
                                ),
                                Input(type="text", id="wsUrl", spellcheck="false", cls="input input-bordered input-sm w-full bg-transparent border-gray-300"),
                                cls="form-control",
                            ),
                            Div(
                                Label(Span("User ID", cls="label-text text-ink"), cls="label"),
                                Input(type="text", id="userId", spellcheck="false", cls="input input-bordered input-sm w-full bg-transparent border-gray-300"),
                                cls="form-control",
                            ),
                            Div(
                                Label(Span("Session ID", cls="label-text text-ink"), cls="label"),
                                Input(type="text", id="sessionId", spellcheck="false", cls="input input-bordered input-sm w-full bg-transparent border-gray-300"),
                                cls="form-control",
                            ),
                            Div(
                                Label(Span("Input source", cls="label-text text-ink"), cls="label"),
                                Select(
                                    Option("None", value="none"),
                                    Option("Microphone", value="microphone"),
                                    id="inputSource",
                                    cls="select select-bordered select-sm w-full bg-transparent border-gray-300",
                                ),
                                cls="form-control",
                            ),
                            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4",
                        ),
                        # Toggle checkboxes
                        Div(
                            Label(
                                Input(type="checkbox", id="autoReconnect", checked=True, cls="checkbox checkbox-primary checkbox-sm border-gray-300"),
                                Span("Auto reconnect", cls="label-text text-ink"),
                                cls="label cursor-pointer gap-2",
                            ),
                            Label(
                                Input(type="checkbox", id="autoEnableAudio", checked=True, cls="checkbox checkbox-primary checkbox-sm border-gray-300"),
                                Span("Enable audio output on connect", cls="label-text text-ink"),
                                cls="label cursor-pointer gap-2",
                            ),
                            cls="flex flex-wrap gap-6 mb-4",
                        ),
                        # Action buttons
                        Div(
                            Button("Connect", type="button", id="connectButton", cls="btn btn-ghost border border-gray-200 btn-sm"),
                            Button("Disconnect", type="button", id="disconnectButton", cls="btn btn-ghost border border-gray-200 btn-sm", disabled=True),
                            Button("Start Input", type="button", id="startInputButton", cls="btn btn-ghost border border-gray-200 btn-sm", disabled=True),
                            Button("Stop Input", type="button", id="stopInputButton", cls="btn btn-ghost border border-gray-200 btn-sm", disabled=True),
                            Button("Enable Audio Output", type="button", id="enableAudioButton", cls="btn btn-ghost border border-gray-200 btn-sm"),
                            Button("Clear Feed", type="button", id="resetFeedButton", cls="btn btn-ghost border border-gray-200 btn-sm"),
                            cls="flex flex-wrap gap-2 mb-6",
                        ),
                        # Status stats
                        Div(
                            Div(
                                Div("Connection", cls="stat-title text-xs text-muted"),
                                Div("idle", id="connectionState", cls="stat-value text-sm font-bold text-ink"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Input", cls="stat-title text-xs text-muted"),
                                Div("none", id="inputState", cls="stat-value text-sm font-bold text-ink"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Audio Output", cls="stat-title text-xs text-muted"),
                                Div("disabled", id="audioOutputState", cls="stat-value text-sm font-bold text-ink"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Session", cls="stat-title text-xs text-muted"),
                                Div("unassigned", id="sessionState", cls="stat-value text-sm font-bold break-all text-ink"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Last Event", cls="stat-title text-xs text-muted"),
                                Div("waiting", id="lastEventState", cls="stat-value text-sm font-bold text-ink"),
                                cls="stat p-3",
                            ),
                            cls="stats stats-vertical lg:stats-horizontal shadow-sm bg-surface border border-border",
                        ),
                        # Text prompt form
                        Form(
                            Input(
                                type="text",
                                id="textPrompt",
                                placeholder="Ask the agent something without using audio",
                                autocomplete="off",
                                cls="input input-bordered flex-1 bg-transparent border-gray-300",
                            ),
                            Button("Send", type="submit", id="sendTextButton", cls="btn btn-ghost border border-gray-200", disabled=True),
                            id="textForm",
                            cls="mt-6 flex gap-2",
                        ),
                        cls="card-body p-6",
                    ),
                    cls="card bg-surface-strong shadow-sm border border-border debug-only",
                    hidden=True,
                ),
                # ── Agent Feed ─────────────────────────────────────────────────
                Section(
                    Div(
                        H2("Agent Feed", cls="card-title border-b border-border pb-2 text-ink"),
                        Div(id="agentFeed", cls="flex-1 overflow-y-auto space-y-3 p-2 bg-transparent"),
                        cls="card-body p-4 flex flex-col bg-transparent",
                    ),
                    cls="card bg-transparent shadow-sm border border-border flex-1 min-h-[60vh]",
                ),
                cls="max-w-5xl mx-auto flex flex-col gap-4 w-full",
            ),
            cls="min-h-screen p-4 flex flex-col",
        ),
    )


@router.get("/recall", response_class=HTMLResponse)
async def recall_root() -> HTMLResponse:
    """Serve the Recall runtime page as FastHTML."""

    return HTMLResponse(to_xml(_recall_page()))


@router.get("/assets/{asset_path:path}")
async def frontend_asset(asset_path: str) -> FileResponse:
    """Serve browser assets from the app-owned asset directory."""

    asset_file = (ASSETS_DIR / asset_path).resolve()
    if not asset_file.is_file() or ASSETS_DIR.resolve() not in asset_file.parents:
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(asset_file)
