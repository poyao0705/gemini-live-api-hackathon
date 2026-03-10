"""Shared head builder and CSS constants for all frontend pages."""

from __future__ import annotations

import fasthtml.common as fh

Head = getattr(fh, "Head")
Link = getattr(fh, "Link")
Meta = getattr(fh, "Meta")
NotStr = getattr(fh, "NotStr")
Script = getattr(fh, "Script")
Style = getattr(fh, "Style")
Title = getattr(fh, "Title")

# ---------------------------------------------------------------------------
# Shared Tailwind theme CSS — loaded as <style type="text/tailwindcss"> so the
# browser Tailwind build processes @theme and registers the design tokens as
# utility classes (bg-surface-strong, text-ink, border-border, etc.).
# ---------------------------------------------------------------------------
_SHARED_THEME_CSS = """
@theme {
  /* Warm neutral palette */
  --color-bg:             #f4efe4;
  --color-surface:        rgba(255, 250, 242, 0.84);
  --color-surface-strong: #fffaf1;
  --color-ink:            #1f1a16;
  --color-muted:          #5b5148;
  --color-accent:         #c65a2e;
  --color-accent-soft:    #f2c8a9;
  --color-border:         rgba(31, 26, 22, 0.12);

  /* Avenir Next / Segoe UI — used for labels, badges, eyebrows, weekday headings */
  --font-label: "Avenir Next", "Segoe UI", system-ui, sans-serif;
}

:root {
  color-scheme: light;
}

/* Shared body baseline — background is the same warm gradient on every page */
body {
  color: var(--color-ink);
  background:
    radial-gradient(circle at top left,  rgba(255, 255, 255, 0.78), transparent 36%),
    radial-gradient(circle at top right, rgba(198, 90, 46, 0.12),   transparent 28%),
    linear-gradient(180deg, #efe2cf 0%, #f4efe4 48%, #efe7da 100%);
  background-attachment: fixed;
}

a { color: inherit; }
"""

# ---------------------------------------------------------------------------
# JS-dynamic CSS — classes created at runtime by app.js / recall.js.
# These cannot be expressed as Tailwind utility classes because the browser
# Tailwind JIT only scans server-rendered HTML; it never sees the JS-injected
# class names.
# ---------------------------------------------------------------------------
_JS_DYNAMIC_CSS = """
/* Chat message bubbles — created dynamically by app.js */
.message { display: flex; margin-bottom: 1rem; animation: slideIn 0.3s ease-out; }
.message.user  { justify-content: flex-end; }
.message.agent { justify-content: flex-start; }
.bubble { max-width: 70%; padding: 0.875rem 1.25rem; border-radius: 1.5rem; word-wrap: break-word; position: relative; font-size: 0.95rem; box-shadow: none; }
.message.user  .bubble { background-color: rgba(31, 26, 22, 0.05); color: var(--color-ink); border: 1px solid var(--color-border); border-bottom-right-radius: 0.5rem; }
.message.agent .bubble { background-color: transparent; color: var(--color-ink); border: none; box-shadow: none; padding-left: 0; }
.bubble-text { margin: 0; line-height: 1.6; }
.message.interrupted .bubble { opacity: 0.7; background-color: var(--color-surface); border-left: 3px solid var(--color-accent); }
.message.interrupted .bubble::after { content: "interrupted"; display: block; font-size: 0.75rem; color: var(--color-muted); font-style: italic; margin-top: 0.25rem; }
.message.transcription.user .bubble { opacity: 0.9; border: 1px solid var(--color-border); }
.message.transcription.user .bubble::before { content: "🎤"; opacity: 0.8; margin-right: 0.25rem; }
.typing-indicator { display: inline-block; margin-left: 0.25rem; color: var(--color-muted); }
.typing-indicator::after { content: "..."; animation: ellipsis 1.5s infinite; }
@keyframes ellipsis { 0%,20% { content: "."; } 40% { content: ".."; } 60%,100% { content: "..."; } }
@keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.bubble.image-bubble { padding: 0.25rem; max-width: 80%; border: none !important; background: transparent !important; box-shadow: none !important; }
.bubble-image { max-width: 100%; max-height: 300px; width: auto; height: auto; border-radius: 1rem; display: block; object-fit: contain; }

/* System messages */
.system-message { background-color: var(--color-surface-strong) !important; color: var(--color-muted) !important; border: 1px solid var(--color-border) !important; box-shadow: none !important; padding: 0.5rem 1rem !important; border-radius: 9999px !important; font-size: 0.85rem; font-weight: normal; margin-top: 0.5rem; margin-bottom: 0.5rem; }

/* Status indicator dot — toggled by app.js */
.status-indicator { width: 8px; height: 8px; border-radius: 50%; background-color: #10a37f; display: inline-block; }
.status-indicator.disconnected { background-color: #ef4444; }

/* Console entries — created dynamically by app.js */
.console-entry { margin-bottom: 0.75rem; padding: 0.75rem; border-left: 3px solid transparent; background-color: var(--color-surface); border-radius: 0.5rem; border: 1px solid var(--color-border); transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
.console-entry.outgoing { border-left-color: var(--color-accent); }
.console-entry.incoming { border-left-color: #10a37f; }
.console-entry.error    { border-left-color: #ef4444; background-color: rgba(239,68,68,0.05); }
.console-entry.expandable { cursor: pointer; }
.console-entry.expandable:hover { background-color: var(--color-surface-strong); border-color: rgba(31, 26, 22, 0.2); }
.console-entry.expanded { background-color: var(--color-surface-strong); }
.console-entry-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.375rem; }
.console-entry-left { display: flex; align-items: center; gap: 0.5rem; }
.console-entry-emoji { font-size: 0.9rem; line-height: 1; display: inline-block; user-select: none; min-width: 16px; text-align: center; }
.console-expand-icon { font-size: 0.6rem; color: var(--color-muted); width: 12px; display: inline-block; transition: transform 0.2s ease; user-select: none; }
.console-entry-type { font-weight: 600; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; }
.console-entry.outgoing .console-entry-type { color: var(--color-accent); }
.console-entry.incoming .console-entry-type { color: #10a37f; }
.console-entry.error    .console-entry-type { color: #ef4444; }
.console-entry-author { font-size: 0.65rem; font-weight: 500; padding: 0.125rem 0.375rem; border-radius: 0.25rem; text-transform: lowercase; letter-spacing: 0.3px; border: 1px solid; background-color: rgba(0,0,0,0.05); color: var(--color-ink); border-color: rgba(0,0,0,0.1); }
.console-entry-author[data-author="user"]   { background-color: rgba(198, 90, 46, 0.1); color: var(--color-accent); border-color: rgba(198, 90, 46, 0.2); }
.console-entry-author[data-author="system"] { background-color: rgba(91, 81, 72, 0.1);  color: var(--color-muted);  border-color: rgba(91, 81, 72, 0.2);  }
.console-entry-timestamp { color: var(--color-muted); font-size: 0.65rem; }
.console-entry-content { color: var(--color-ink); white-space: pre-wrap; word-break: break-word; font-size: 0.75rem; line-height: 1.5; padding-left: 2rem; }
.console-entry-content:empty { display: none; }
.console-entry-json { background-color: rgba(0,0,0,0.03); padding: 0.75rem; border-radius: 0.5rem; margin-top: 0.5rem; overflow-x: auto; max-height: 400px; overflow-y: auto; transition: all 0.3s ease; border: 1px solid rgba(0,0,0,0.05); }
.console-entry-json.collapsed { display: none; }
.console-entry-json pre { margin: 0; color: var(--color-ink); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.7rem; }

/* Event cards — created dynamically by recall.js */
.event.card { background-color: var(--color-surface-strong) !important; border-color: var(--color-border) !important; box-shadow: none !important; color: var(--color-ink) !important; padding: 1rem; border-radius: 1rem; margin-bottom: 0.75rem; }
.event.card p          { color: var(--color-ink)  !important; margin: 0; }
.event.card p strong   { color: var(--color-ink)  !important; }
.event.card p.meta     { color: var(--color-muted) !important; margin-top: 0.25rem !important; }
"""


def page_head(
    *,
    title: str,
    extra_scripts: list | None = None,
    page_script_src: str | None = None,
    extra_css: str = "",
) -> Head:
    """Shared ``<head>`` builder used by every frontend page.

    Parameters
    ----------
    title:
        Value for ``<title>``.
    extra_scripts:
        Additional ``<script>`` (or other) elements inserted before the page
        module script.  Useful for htmx on the dashboard.
    page_script_src:
        ``src`` of the per-page JS module (loaded as ``type="module"``).
    extra_css:
        Optional plain CSS appended in an extra ``<style>`` block (e.g. a
        per-page body font override).
    """
    elements: list = [
        Title(title),
        Meta(charset="UTF-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        # DaisyUI component classes (btn, badge, modal, stats, …)
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/daisyui@5",
            type="text/css",
        ),
        # Tailwind CSS v4 browser build — processes <style type="text/tailwindcss">
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        # Design-token @theme block + body gradient (parsed by Tailwind JIT)
        Style(NotStr(_SHARED_THEME_CSS), type="text/tailwindcss"),
        # Plain CSS for JS-dynamic classes (cannot be Tailwind-ified)
        Style(NotStr(_JS_DYNAMIC_CSS)),
    ]
    if extra_css:
        elements.append(Style(NotStr(extra_css)))
    for script in extra_scripts or []:
        elements.append(script)
    if page_script_src:
        elements.append(Script(src=page_script_src, type="module"))
    return Head(*elements)
