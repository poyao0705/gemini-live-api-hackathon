"""Web router for FastHTML-rendered frontend pages and browser assets."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import fasthtml.common as fh

Body = getattr(fh, "Body")
Button = getattr(fh, "Button")
Dialog = getattr(fh, "Dialog")
Div = getattr(fh, "Div")
Form = getattr(fh, "Form")
H1 = getattr(fh, "H1")
H2 = getattr(fh, "H2")
H3 = getattr(fh, "H3")
Head = getattr(fh, "Head")
Header = getattr(fh, "Header")
Html = getattr(fh, "Html")
Input = getattr(fh, "Input")
Label = getattr(fh, "Label")
Link = getattr(fh, "Link")
Main = getattr(fh, "Main")
Meta = getattr(fh, "Meta")
Option = getattr(fh, "Option")
P = getattr(fh, "P")
Script = getattr(fh, "Script")
Style = getattr(fh, "Style")
NotStr = getattr(fh, "NotStr")
Section = getattr(fh, "Section")
Select = getattr(fh, "Select")
Span = getattr(fh, "Span")
Title = getattr(fh, "Title")
Video = getattr(fh, "Video")
to_xml = fh.to_xml

# Minimal CSS retained for classes applied dynamically by app.js (message bubbles,
# console entries, status indicator). Page layout is now handled by Tailwind/DaisyUI.
_STYLE_CSS = """
/* Chat message bubbles — created dynamically by app.js */
.message { display: flex; margin-bottom: 0.5rem; animation: slideIn 0.3s ease-out; }
.message.user { justify-content: flex-end; }
.message.agent { justify-content: flex-start; }
.bubble { max-width: 70%; padding: 0.75rem 1rem; border-radius: 1.25rem; word-wrap: break-word; position: relative; }
.message.user .bubble { background-color: #4285f4; color: #fff; border-bottom-right-radius: 0.25rem; }
.message.agent .bubble { background-color: #f1f3f4; color: #202124; border-bottom-left-radius: 0.25rem; }
.bubble-text { margin: 0; line-height: 1.5; }
.message.interrupted .bubble { opacity: 0.6; background-color: #e8eaed; border-left: 3px solid #f4b400; }
.message.interrupted .bubble::after { content: "interrupted"; display: block; font-size: 0.75rem; color: #5f6368; font-style: italic; margin-top: 0.25rem; }
.message.transcription.user .bubble { opacity: 0.9; border: 1px solid rgba(255,255,255,0.3); }
.message.transcription.user .bubble::before { content: "🎤"; opacity: 0.8; margin-right: 0.25rem; }
.typing-indicator { display: inline-block; margin-left: 0.25rem; color: #5f6368; }
.typing-indicator::after { content: "..."; animation: ellipsis 1.5s infinite; }
@keyframes ellipsis { 0%,20% { content: "."; } 40% { content: ".."; } 60%,100% { content: "..."; } }
@keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.bubble.image-bubble { padding: 0.25rem; max-width: 80%; }
.bubble-image { max-width: 100%; max-height: 300px; width: auto; height: auto; border-radius: 0.75rem; display: block; object-fit: contain; }

/* Status indicator dot — toggled by app.js */
.status-indicator { width: 8px; height: 8px; border-radius: 50%; background-color: #34a853; display: inline-block; }
.status-indicator.disconnected { background-color: #ea4335; }

/* Console entries — created dynamically by app.js */
.console-entry { margin-bottom: 0.75rem; padding: 0.5rem; border-left: 3px solid transparent; background-color: rgba(255,255,255,0.06); border-radius: 0.25rem; transition: background-color 0.2s ease; }
.console-entry.outgoing { border-left-color: #4285f4; }
.console-entry.incoming { border-left-color: #34a853; }
.console-entry.error { border-left-color: #ea4335; background-color: rgba(234,67,53,0.15); }
.console-entry.expandable { cursor: pointer; }
.console-entry.expandable:hover { background-color: rgba(255,255,255,0.10); }
.console-entry.expanded { background-color: rgba(255,255,255,0.08); }
.console-entry-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.375rem; }
.console-entry-left { display: flex; align-items: center; gap: 0.5rem; }
.console-entry-emoji { font-size: 0.9rem; line-height: 1; display: inline-block; user-select: none; min-width: 16px; text-align: center; }
.console-expand-icon { font-size: 0.6rem; color: #858585; width: 12px; display: inline-block; transition: transform 0.2s ease; user-select: none; }
.console-entry-type { font-weight: 600; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; }
.console-entry.outgoing .console-entry-type { color: #4285f4; }
.console-entry.incoming .console-entry-type { color: #34a853; }
.console-entry.error .console-entry-type { color: #ea4335; }
.console-entry-author { font-size: 0.65rem; font-weight: 500; padding: 0.125rem 0.375rem; border-radius: 0.25rem; text-transform: lowercase; letter-spacing: 0.3px; border: 1px solid; background-color: rgba(156,220,254,0.15); color: #9cdcfe; border-color: rgba(156,220,254,0.3); }
.console-entry-author[data-author="user"] { background-color: rgba(66,133,244,0.2); color: #80b3ff; border-color: rgba(66,133,244,0.4); }
.console-entry-author[data-author="system"] { background-color: rgba(133,133,133,0.2); color: #b0b0b0; border-color: rgba(133,133,133,0.3); }
.console-entry-timestamp { color: #858585; font-size: 0.65rem; }
.console-entry-content { color: #d4d4d4; white-space: pre-wrap; word-break: break-word; font-size: 0.7rem; line-height: 1.4; padding-left: 2.5rem; }
.console-entry-content:empty { display: none; }
.console-entry-json { background-color: #252526; padding: 0.5rem; border-radius: 0.25rem; margin-top: 0.5rem; overflow-x: auto; max-height: 400px; overflow-y: auto; transition: all 0.3s ease; }
.console-entry-json.collapsed { display: none; }
.console-entry-json pre { margin: 0; color: #9cdcfe; }
"""

router = APIRouter()

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def _frontend_head(*, title: str, css: str, script_href: str) -> Head:
    return Head(
        Title(title),
        Meta(charset="UTF-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/daisyui@5",
            type="text/css",
        ),
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style(NotStr(css)),
        Script(src=script_href, type="module"),
    )


def _main_page() -> Html:
    return Html(
        _frontend_head(
            title="ADK Bidi-streaming Demo",
            css=_STYLE_CSS,
            script_href="/assets/js/app.js",
        ),
        Body(
            # ── Navbar ─────────────────────────────────────────────────────────
            Header(
                Div(
                    H1("ADK Bidi-streaming Demo", cls="text-xl font-bold"),
                    P(
                        "Real-time bidirectional streaming with Google ADK",
                        cls="text-sm opacity-70",
                    ),
                    cls="flex-1 flex flex-col items-start",
                ),
                Div(
                    Label(
                        Input(
                            type="checkbox",
                            id="enableProactivity",
                            cls="checkbox checkbox-primary checkbox-sm",
                        ),
                        Span("Proactivity", cls="label-text"),
                        cls="label cursor-pointer gap-2",
                        title=(
                            "Enable model to proactively respond without explicit prompts "
                            "(Native audio models only)"
                        ),
                    ),
                    Label(
                        Input(
                            type="checkbox",
                            id="enableAffectiveDialog",
                            cls="checkbox checkbox-primary checkbox-sm",
                        ),
                        Span("Affective Dialog", cls="label-text"),
                        cls="label cursor-pointer gap-2",
                        title=(
                            "Enable model to detect and adapt to emotional cues "
                            "(Native audio models only)"
                        ),
                    ),
                    Div(
                        Span(id="statusIndicator", cls="status-indicator"),
                        Span("Connecting...", id="statusText"),
                        cls="badge badge-neutral gap-2 p-3 font-semibold",
                    ),
                    cls="flex-none flex items-center gap-4 flex-wrap",
                ),
                cls="navbar bg-base-100 shadow-md px-4 py-2 flex-wrap gap-4",
            ),
            # ── Main layout ────────────────────────────────────────────────────
            Main(
                # Chat container
                Div(
                    Div(id="messages", cls="flex-1 p-4 overflow-y-auto min-h-[50vh] flex flex-col gap-2"),
                    Div(
                        Form(
                            Input(
                                type="text",
                                id="message",
                                name="message",
                                placeholder="Type your message here...",
                                autocomplete="off",
                                cls="input input-bordered flex-1",
                            ),
                            Button("Send", type="submit", id="sendButton", cls="btn btn-primary", disabled=True),
                            Button("Start Audio", type="button", id="startAudioButton", cls="btn btn-success"),
                            Button("📷 Camera", type="button", id="cameraButton", cls="btn btn-error"),
                            id="messageForm",
                            cls="flex gap-2 w-full items-center",
                        ),
                        cls="p-4 bg-base-200 border-t border-base-300",
                    ),
                    cls="flex-[2] flex flex-col bg-base-100 rounded-box shadow-md overflow-hidden",
                ),
                # Console panel
                Div(
                    Div(
                        H2(
                            "Event Console",
                            cls="text-sm font-semibold text-[#cccccc] uppercase tracking-wider",
                        ),
                        Div(
                            Label(
                                Input(type="checkbox", id="showAudioEvents", cls="checkbox checkbox-xs"),
                                Span("Show audio", cls="label-text text-[#999999] text-xs"),
                                cls="label cursor-pointer gap-2 p-0",
                            ),
                            Button("Clear", id="clearConsole", cls="btn btn-xs btn-ghost text-[#cccccc]"),
                            cls="flex items-center gap-3",
                        ),
                        cls="flex justify-between items-center p-3 bg-[#2d2d2d] border-b border-[#3e3e3e]",
                    ),
                    Div(id="consoleContent", cls="flex-1 overflow-y-auto p-3 text-xs leading-relaxed"),
                    cls=(
                        "flex-1 flex flex-col bg-[#1e1e1e] text-[#d4d4d4] rounded-box shadow-md "
                        "overflow-hidden max-h-[70vh] lg:max-h-full font-mono"
                    ),
                ),
                cls="flex-1 flex flex-col lg:flex-row gap-4 p-4 max-w-[1800px] mx-auto w-full overflow-hidden",
            ),
            # ── Camera modal (DaisyUI dialog) ──────────────────────────────────
            Dialog(
                Div(
                    H3("Camera Preview", cls="font-bold text-lg mb-4"),
                    Div(
                        Video(id="cameraPreview", autoplay=True, playsinline=True, cls="max-w-full h-auto"),
                        cls="bg-black rounded-box overflow-hidden flex justify-center mb-4",
                    ),
                    Div(
                        Button("Cancel", id="cancelCamera", cls="btn"),
                        Button("📷 Send Image", id="captureImage", cls="btn btn-primary"),
                        cls="modal-action",
                    ),
                    cls="modal-box w-11/12 max-w-2xl",
                ),
                Form(
                    Button("close", id="closeCameraModal", aria_label="Close"),
                    method="dialog",
                    cls="modal-backdrop",
                ),
                id="cameraModal",
                cls="modal",
            ),
            data_theme="corporate",
            cls="min-h-screen bg-base-200 text-base-content flex flex-col",
        ),
    )


def _recall_page() -> Html:
    return Html(
        _frontend_head(
            title="Gemini Live Runtime",
            css="",
            script_href="/assets/js/recall.js?v=20260308",
        ),
        Body(
            Main(
                # ── Debug Controls (hidden unless debug mode) ──────────────────
                Section(
                    Div(
                        H2("Debug Controls", cls="card-title"),
                        P(
                            "Local-only controls for testing the same conversational runtime.",
                            cls="text-sm opacity-70 mb-4",
                        ),
                        # Input grid
                        Div(
                            Div(
                                Label(
                                    Span("WebSocket URL", cls="label-text"),
                                    cls="label",
                                ),
                                Input(type="text", id="wsUrl", spellcheck="false", cls="input input-bordered input-sm w-full"),
                                cls="form-control",
                            ),
                            Div(
                                Label(Span("User ID", cls="label-text"), cls="label"),
                                Input(type="text", id="userId", spellcheck="false", cls="input input-bordered input-sm w-full"),
                                cls="form-control",
                            ),
                            Div(
                                Label(Span("Session ID", cls="label-text"), cls="label"),
                                Input(type="text", id="sessionId", spellcheck="false", cls="input input-bordered input-sm w-full"),
                                cls="form-control",
                            ),
                            Div(
                                Label(Span("Input source", cls="label-text"), cls="label"),
                                Select(
                                    Option("None", value="none"),
                                    Option("Microphone", value="microphone"),
                                    id="inputSource",
                                    cls="select select-bordered select-sm w-full",
                                ),
                                cls="form-control",
                            ),
                            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4",
                        ),
                        # Toggle checkboxes
                        Div(
                            Label(
                                Input(type="checkbox", id="autoReconnect", checked=True, cls="checkbox checkbox-primary checkbox-sm"),
                                Span("Auto reconnect", cls="label-text"),
                                cls="label cursor-pointer gap-2",
                            ),
                            Label(
                                Input(type="checkbox", id="autoEnableAudio", checked=True, cls="checkbox checkbox-primary checkbox-sm"),
                                Span("Enable audio output on connect", cls="label-text"),
                                cls="label cursor-pointer gap-2",
                            ),
                            cls="flex flex-wrap gap-6 mb-4",
                        ),
                        # Action buttons
                        Div(
                            Button("Connect", type="button", id="connectButton", cls="btn btn-primary btn-sm"),
                            Button("Disconnect", type="button", id="disconnectButton", cls="btn btn-neutral btn-sm", disabled=True),
                            Button("Start Input", type="button", id="startInputButton", cls="btn btn-secondary btn-sm", disabled=True),
                            Button("Stop Input", type="button", id="stopInputButton", cls="btn btn-warning btn-sm", disabled=True),
                            Button("Enable Audio Output", type="button", id="enableAudioButton", cls="btn btn-accent btn-sm"),
                            Button("Clear Feed", type="button", id="resetFeedButton", cls="btn btn-ghost btn-sm"),
                            cls="flex flex-wrap gap-2 mb-6",
                        ),
                        # Status stats
                        Div(
                            Div(
                                Div("Connection", cls="stat-title text-xs"),
                                Div("idle", id="connectionState", cls="stat-value text-sm font-bold"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Input", cls="stat-title text-xs"),
                                Div("none", id="inputState", cls="stat-value text-sm font-bold"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Audio Output", cls="stat-title text-xs"),
                                Div("disabled", id="audioOutputState", cls="stat-value text-sm font-bold"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Session", cls="stat-title text-xs"),
                                Div("unassigned", id="sessionState", cls="stat-value text-sm font-bold break-all"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Last Event", cls="stat-title text-xs"),
                                Div("waiting", id="lastEventState", cls="stat-value text-sm font-bold"),
                                cls="stat p-3",
                            ),
                            cls="stats stats-vertical lg:stats-horizontal shadow bg-base-200",
                        ),
                        # Text prompt form
                        Form(
                            Input(
                                type="text",
                                id="textPrompt",
                                placeholder="Ask the agent something without using audio",
                                autocomplete="off",
                                cls="input input-bordered flex-1",
                            ),
                            Button("Send", type="submit", id="sendTextButton", cls="btn btn-primary", disabled=True),
                            id="textForm",
                            cls="mt-6 flex gap-2",
                        ),
                        cls="card-body p-6",
                    ),
                    cls="card bg-base-100 shadow-xl debug-only",
                    hidden=True,
                ),
                # ── Agent Feed ─────────────────────────────────────────────────
                Section(
                    Div(
                        H2("Agent Feed", cls="card-title border-b pb-2"),
                        Div(id="agentFeed", cls="flex-1 overflow-y-auto space-y-3 p-2"),
                        cls="card-body p-4 flex flex-col",
                    ),
                    cls="card bg-base-100 shadow-xl flex-1 min-h-[60vh]",
                ),
                cls="max-w-5xl mx-auto flex flex-col gap-4",
            ),
            data_theme="emerald",
            cls="bg-base-200 min-h-screen text-base-content p-4",
        ),
    )


@router.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the main demo page as FastHTML."""

    return HTMLResponse(to_xml(_main_page()))


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
