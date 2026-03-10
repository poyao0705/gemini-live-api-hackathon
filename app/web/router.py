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
:root {
  --bg: #f4efe4;
  --surface: rgba(255, 250, 242, 0.84);
  --surface-strong: #fffaf1;
  --ink: #1f1a16;
  --muted: #5b5148;
  --accent: #c65a2e;
  --accent-soft: #f2c8a9;
  --border: rgba(31, 26, 22, 0.12);
  --shadow: 0 22px 60px rgba(92, 57, 31, 0.12);
}

body {
  margin: 0;
  min-height: 100vh;
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.78), transparent 36%),
    radial-gradient(circle at top right, rgba(198, 90, 46, 0.12), transparent 28%),
    linear-gradient(180deg, #efe2cf 0%, var(--bg) 48%, #efe7da 100%);
  background-attachment: fixed;
}

/* Chat message bubbles — created dynamically by app.js */
.message { display: flex; margin-bottom: 1rem; animation: slideIn 0.3s ease-out; }
.message.user { justify-content: flex-end; }
.message.agent { justify-content: flex-start; }
.bubble { max-width: 70%; padding: 0.875rem 1.25rem; border-radius: 1.5rem; word-wrap: break-word; position: relative; font-size: 0.95rem; box-shadow: none; }
.message.user .bubble { background-color: rgba(31, 26, 22, 0.05); color: var(--ink); border: 1px solid var(--border); border-bottom-right-radius: 0.5rem; }
.message.agent .bubble { background-color: transparent; color: var(--ink); border: none; box-shadow: none; padding-left: 0; }
.bubble-text { margin: 0; line-height: 1.6; }
.message.interrupted .bubble { opacity: 0.7; background-color: var(--surface); border-left: 3px solid var(--accent); }
.message.interrupted .bubble::after { content: "interrupted"; display: block; font-size: 0.75rem; color: var(--muted); font-style: italic; margin-top: 0.25rem; }
.message.transcription.user .bubble { opacity: 0.9; border: 1px solid var(--border); }
.message.transcription.user .bubble::before { content: "🎤"; opacity: 0.8; margin-right: 0.25rem; }
.typing-indicator { display: inline-block; margin-left: 0.25rem; color: var(--muted); }
.typing-indicator::after { content: "..."; animation: ellipsis 1.5s infinite; }
@keyframes ellipsis { 0%,20% { content: "."; } 40% { content: ".."; } 60%,100% { content: "..."; } }
@keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.bubble.image-bubble { padding: 0.25rem; max-width: 80%; border: none !important; background: transparent !important; box-shadow: none !important; }
.bubble-image { max-width: 100%; max-height: 300px; width: auto; height: auto; border-radius: 1rem; display: block; object-fit: contain; }

/* System messages */
.system-message { background-color: var(--surface-strong) !important; color: var(--muted) !important; border: 1px solid var(--border) !important; box-shadow: none !important; padding: 0.5rem 1rem !important; border-radius: 9999px !important; font-size: 0.85rem; font-weight: normal; margin-top: 0.5rem; margin-bottom: 0.5rem; }

/* Status indicator dot — toggled by app.js */
.status-indicator { width: 8px; height: 8px; border-radius: 50%; background-color: #10a37f; display: inline-block; }
.status-indicator.disconnected { background-color: #ef4444; }

/* Console entries — created dynamically by app.js - Light Theme */
.console-entry { margin-bottom: 0.75rem; padding: 0.75rem; border-left: 3px solid transparent; background-color: var(--surface); border-radius: 0.5rem; border: 1px solid var(--border); transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
.console-entry.outgoing { border-left-color: var(--accent); }
.console-entry.incoming { border-left-color: #10a37f; }
.console-entry.error { border-left-color: #ef4444; background-color: rgba(239,68,68,0.05); }
.console-entry.expandable { cursor: pointer; }
.console-entry.expandable:hover { background-color: var(--surface-strong); border-color: rgba(31, 26, 22, 0.2); }
.console-entry.expanded { background-color: var(--surface-strong); }
.console-entry-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.375rem; }
.console-entry-left { display: flex; align-items: center; gap: 0.5rem; }
.console-entry-emoji { font-size: 0.9rem; line-height: 1; display: inline-block; user-select: none; min-width: 16px; text-align: center; }
.console-expand-icon { font-size: 0.6rem; color: var(--muted); width: 12px; display: inline-block; transition: transform 0.2s ease; user-select: none; }
.console-entry-type { font-weight: 600; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; }
.console-entry.outgoing .console-entry-type { color: var(--accent); }
.console-entry.incoming .console-entry-type { color: #10a37f; }
.console-entry.error .console-entry-type { color: #ef4444; }
.console-entry-author { font-size: 0.65rem; font-weight: 500; padding: 0.125rem 0.375rem; border-radius: 0.25rem; text-transform: lowercase; letter-spacing: 0.3px; border: 1px solid; background-color: rgba(0,0,0,0.05); color: var(--ink); border-color: rgba(0,0,0,0.1); }
.console-entry-author[data-author="user"] { background-color: rgba(198, 90, 46, 0.1); color: var(--accent); border-color: rgba(198, 90, 46, 0.2); }
.console-entry-author[data-author="system"] { background-color: rgba(91, 81, 72, 0.1); color: var(--muted); border-color: rgba(91, 81, 72, 0.2); }
.console-entry-timestamp { color: var(--muted); font-size: 0.65rem; }
.console-entry-content { color: var(--ink); white-space: pre-wrap; word-break: break-word; font-size: 0.75rem; line-height: 1.5; padding-left: 2rem; }
.console-entry-content:empty { display: none; }
.console-entry-json { background-color: rgba(0,0,0,0.03); padding: 0.75rem; border-radius: 0.5rem; margin-top: 0.5rem; overflow-x: auto; max-height: 400px; overflow-y: auto; transition: all 0.3s ease; border: 1px solid rgba(0,0,0,0.05); }
.console-entry-json.collapsed { display: none; }
.console-entry-json pre { margin: 0; color: var(--ink); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.7rem; }

/* Event cards - styling events created by recall.js */
.event.card { background-color: var(--surface-strong) !important; border-color: var(--border) !important; box-shadow: none !important; color: var(--ink) !important; padding: 1rem; border-radius: 1rem; margin-bottom: 0.75rem; }
.event.card p { color: var(--ink) !important; margin: 0; }
.event.card p strong { color: var(--ink) !important; }
.event.card p.meta { color: var(--muted) !important; margin-top: 0.25rem !important; }
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
                cls="navbar bg-[var(--surface-strong)] shadow-sm px-4 py-2 flex-wrap gap-4 border-b border-[var(--border)]",
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
                                cls="input input-bordered flex-1 bg-transparent border-[var(--border)] text-[var(--ink)] focus:outline-none focus:border-gray-400 placeholder:text-gray-400",
                            ),
                            Button("Send", type="submit", id="sendButton", cls="btn bg-transparent border border-[var(--border)] text-gray-700 hover:bg-[var(--border)] shadow-none", disabled=True),
                            Button("Start Audio", type="button", id="startAudioButton", cls="btn bg-transparent border border-[var(--border)] text-gray-700 hover:bg-[var(--border)] shadow-none"),
                            Button("📷 Camera", type="button", id="cameraButton", cls="btn bg-transparent border border-[var(--border)] text-gray-700 hover:bg-[var(--border)] shadow-none"),
                            id="messageForm",
                            cls="flex gap-2 w-full items-center",
                        ),
                        cls="p-4 bg-transparent border-t border-[var(--border)]",
                    ),
                    cls="flex-[2] flex flex-col bg-transparent rounded-2xl shadow-sm border border-[var(--border)] overflow-hidden",
                ),
                # Console panel
                Div(
                    Div(
                        H2(
                            "Event Console",
                            cls="text-sm font-semibold text-[var(--muted)] uppercase tracking-wider",
                        ),
                        Div(
                            Label(
                                Input(type="checkbox", id="showAudioEvents", cls="checkbox checkbox-xs border-[var(--border)]"),
                                Span("Show audio", cls="label-text text-[var(--muted)] text-xs"),
                                cls="label cursor-pointer gap-2 p-0",
                            ),
                            Button("Clear", id="clearConsole", cls="btn btn-xs btn-ghost text-[var(--muted)] hover:bg-[var(--border)]"),
                            cls="flex items-center gap-3",
                        ),
                        cls="flex justify-between items-center p-3 bg-[var(--surface)] border-b border-[var(--border)]",
                    ),
                    Div(id="consoleContent", cls="flex-1 overflow-y-auto p-3 text-xs leading-relaxed bg-transparent"),
                    cls=(
                        "flex-1 flex flex-col bg-transparent text-[var(--ink)] rounded-2xl shadow-sm border border-[var(--border)] "
                        "overflow-hidden max-h-[70vh] lg:max-h-full font-mono"
                    ),
                ),
                cls="flex-1 flex flex-col lg:flex-row gap-4 p-4 max-w-[1800px] mx-auto w-full overflow-hidden bg-transparent",
            ),
            # ── Camera modal (DaisyUI dialog) ──────────────────────────────────
            Dialog(
                Div(
                    H3("Camera Preview", cls="font-bold text-lg mb-4 text-[var(--ink)]"),
                    Div(
                        Video(id="cameraPreview", autoplay=True, playsinline=True, cls="max-w-full h-auto"),
                        cls="bg-black rounded-box overflow-hidden flex justify-center mb-4",
                    ),
                    Div(
                        Button("Cancel", id="cancelCamera", cls="btn bg-transparent border border-gray-300 text-[var(--ink)] hover:bg-gray-100"),
                        Button("📷 Send Image", id="captureImage", cls="btn bg-transparent border border-gray-300 text-[var(--ink)] hover:bg-gray-100"),
                        cls="modal-action",
                    ),
                    cls="modal-box w-11/12 max-w-2xl bg-[var(--surface-strong)]",
                ),
                Form(
                    Button("close", id="closeCameraModal", aria_label="Close"),
                    method="dialog",
                    cls="modal-backdrop",
                ),
                id="cameraModal",
                cls="modal",
            ),
            cls="min-h-screen flex flex-col",
        ),
    )


def _recall_page() -> Html:
    return Html(
        _frontend_head(
            title="Gemini Live Runtime",
            css=_STYLE_CSS,
            script_href="/assets/js/recall.js?v=20260308",
        ),
        Body(
            Main(
                # ── Debug Controls (hidden unless debug mode) ──────────────────
                Section(
                    Div(
                        H2("Debug Controls", cls="card-title text-[var(--ink)]"),
                        P(
                            "Local-only controls for testing the same conversational runtime.",
                            cls="text-sm opacity-70 mb-4 text-[var(--muted)]",
                        ),
                        # Input grid
                        Div(
                            Div(
                                Label(
                                    Span("WebSocket URL", cls="label-text text-[var(--ink)]"),
                                    cls="label",
                                ),
                                Input(type="text", id="wsUrl", spellcheck="false", cls="input input-bordered input-sm w-full bg-transparent border-gray-300"),
                                cls="form-control",
                            ),
                            Div(
                                Label(Span("User ID", cls="label-text text-[var(--ink)]"), cls="label"),
                                Input(type="text", id="userId", spellcheck="false", cls="input input-bordered input-sm w-full bg-transparent border-gray-300"),
                                cls="form-control",
                            ),
                            Div(
                                Label(Span("Session ID", cls="label-text text-[var(--ink)]"), cls="label"),
                                Input(type="text", id="sessionId", spellcheck="false", cls="input input-bordered input-sm w-full bg-transparent border-gray-300"),
                                cls="form-control",
                            ),
                            Div(
                                Label(Span("Input source", cls="label-text text-[var(--ink)]"), cls="label"),
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
                                Span("Auto reconnect", cls="label-text text-[var(--ink)]"),
                                cls="label cursor-pointer gap-2",
                            ),
                            Label(
                                Input(type="checkbox", id="autoEnableAudio", checked=True, cls="checkbox checkbox-primary checkbox-sm border-gray-300"),
                                Span("Enable audio output on connect", cls="label-text text-[var(--ink)]"),
                                cls="label cursor-pointer gap-2",
                            ),
                            cls="flex flex-wrap gap-6 mb-4",
                        ),
                        # Action buttons
                        Div(
                            Button("Connect", type="button", id="connectButton", cls="btn bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-100 shadow-none btn-sm"),
                            Button("Disconnect", type="button", id="disconnectButton", cls="btn bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-100 shadow-none btn-sm", disabled=True),
                            Button("Start Input", type="button", id="startInputButton", cls="btn bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-100 shadow-none btn-sm", disabled=True),
                            Button("Stop Input", type="button", id="stopInputButton", cls="btn bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-100 shadow-none btn-sm", disabled=True),
                            Button("Enable Audio Output", type="button", id="enableAudioButton", cls="btn bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-100 shadow-none btn-sm"),
                            Button("Clear Feed", type="button", id="resetFeedButton", cls="btn bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-100 shadow-none btn-sm"),
                            cls="flex flex-wrap gap-2 mb-6",
                        ),
                        # Status stats
                        Div(
                            Div(
                                Div("Connection", cls="stat-title text-xs text-[var(--muted)]"),
                                Div("idle", id="connectionState", cls="stat-value text-sm font-bold text-[var(--ink)]"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Input", cls="stat-title text-xs text-[var(--muted)]"),
                                Div("none", id="inputState", cls="stat-value text-sm font-bold text-[var(--ink)]"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Audio Output", cls="stat-title text-xs text-[var(--muted)]"),
                                Div("disabled", id="audioOutputState", cls="stat-value text-sm font-bold text-[var(--ink)]"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Session", cls="stat-title text-xs text-[var(--muted)]"),
                                Div("unassigned", id="sessionState", cls="stat-value text-sm font-bold break-all text-[var(--ink)]"),
                                cls="stat p-3",
                            ),
                            Div(
                                Div("Last Event", cls="stat-title text-xs text-[var(--muted)]"),
                                Div("waiting", id="lastEventState", cls="stat-value text-sm font-bold text-[var(--ink)]"),
                                cls="stat p-3",
                            ),
                            cls="stats stats-vertical lg:stats-horizontal shadow-sm bg-[var(--surface)] border border-[var(--border)]",
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
                            Button("Send", type="submit", id="sendTextButton", cls="btn bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-100 shadow-none", disabled=True),
                            id="textForm",
                            cls="mt-6 flex gap-2",
                        ),
                        cls="card-body p-6",
                    ),
                    cls="card bg-[var(--surface-strong)] shadow-sm border border-[var(--border)] debug-only",
                    hidden=True,
                ),
                # ── Agent Feed ─────────────────────────────────────────────────
                Section(
                    Div(
                        H2("Agent Feed", cls="card-title border-b border-[var(--border)] pb-2 text-[var(--ink)]"),
                        Div(id="agentFeed", cls="flex-1 overflow-y-auto space-y-3 p-2 bg-transparent"),
                        cls="card-body p-4 flex flex-col bg-transparent",
                    ),
                    cls="card bg-transparent shadow-sm border border-[var(--border)] flex-1 min-h-[60vh]",
                ),
                cls="max-w-5xl mx-auto flex flex-col gap-4 w-full",
            ),
            cls="min-h-screen p-4 flex flex-col",
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
