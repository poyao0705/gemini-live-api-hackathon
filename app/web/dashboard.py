"""Mounted FastHTML dashboard for meeting history and upcoming events."""

from __future__ import annotations

import calendar
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from fasthtml.common import *  # noqa: F403

from app.services.meetings.invites import meeting_invite_store


_DASHBOARD_CSS = ':root {\n  --bg: #f4efe4;\n  --surface: rgba(255, 250, 242, 0.84);\n  --surface-strong: #fffaf1;\n  --ink: #1f1a16;\n  --muted: #5b5148;\n  --accent: #c65a2e;\n  --accent-soft: #f2c8a9;\n  --border: rgba(31, 26, 22, 0.12);\n  --shadow: 0 22px 60px rgba(92, 57, 31, 0.12);\n}\n\n* {\n  box-sizing: border-box;\n}\n\nbody {\n  margin: 0;\n  min-height: 100vh;\n  color: var(--ink);\n  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;\n  background:\n    radial-gradient(circle at top left, rgba(255, 255, 255, 0.78), transparent 36%),\n    radial-gradient(circle at top right, rgba(198, 90, 46, 0.12), transparent 28%),\n    linear-gradient(180deg, #efe2cf 0%, var(--bg) 48%, #efe7da 100%);\n}\n\na {\n  color: inherit;\n}\n\n.dashboard-shell {\n  width: min(1180px, calc(100vw - 32px));\n  margin: 0 auto;\n  padding: 32px 0 56px;\n}\n\n.hero {\n  display: grid;\n  grid-template-columns: minmax(0, 1fr) auto;\n  gap: 32px;\n  align-items: start;\n  padding: 32px;\n  border: 1px solid var(--border);\n  border-radius: 28px;\n  background:\n    linear-gradient(135deg, rgba(255, 252, 247, 0.94), rgba(255, 243, 229, 0.88)),\n    linear-gradient(45deg, rgba(198, 90, 46, 0.08), transparent 60%);\n  box-shadow: var(--shadow);\n}\n\n.hero-intro {\n  min-width: 0;\n  width: 100%;\n  justify-self: start;\n  align-self: start;\n  margin-right: auto;\n  text-align: left;\n}\n\n.hero-aside {\n  display: flex;\n  justify-content: flex-end;\n  justify-self: end;\n  align-self: center;\n  width: max-content;\n  max-width: 100%;\n}\n\n.eyebrow {\n  margin: 0 0 10px;\n  color: var(--accent);\n  font-family: "Avenir Next", "Segoe UI", sans-serif;\n  font-size: 0.82rem;\n  font-weight: 700;\n  letter-spacing: 0.18em;\n  text-transform: uppercase;\n}\n\n.hero-title {\n  margin: 0;\n  max-width: 7ch;\n  font-size: clamp(3rem, 7vw, 5.4rem);\n  line-height: 0.9;\n  letter-spacing: -0.05em;\n}\n\n.hero-copy,\n.section-copy,\n.meeting-organizer,\n.meeting-link--muted,\n.empty-state,\n.calendar-day-events,\n.agenda-day-label {\n  color: var(--muted);\n}\n\n.hero-copy {\n  max-width: 34rem;\n  margin: 16px 0 0;\n  font-size: 1.05rem;\n  line-height: 1.65;\n}\n\n.hero-stats {\n  display: grid;\n  gap: 12px;\n  width: min(380px, 100%);\n  grid-template-columns: repeat(3, minmax(0, 1fr));\n  padding: 12px;\n  border: 1px solid rgba(198, 90, 46, 0.12);\n  border-radius: 26px;\n  background: rgba(255, 250, 242, 0.72);\n  box-shadow: 0 16px 36px rgba(92, 57, 31, 0.08);\n  backdrop-filter: blur(12px);\n}\n\n.hero-stat {\n  min-width: 0;\n  padding: 18px 16px;\n  border: 1px solid rgba(198, 90, 46, 0.18);\n  border-radius: 22px;\n  background: rgba(255, 250, 242, 0.84);\n}\n\n.hero-stat-value {\n  display: block;\n  font-size: 2rem;\n  font-weight: 700;\n}\n\n.hero-stat-label,\n.meeting-time {\n  font-family: "Avenir Next", "Segoe UI", sans-serif;\n  letter-spacing: 0.02em;\n}\n\n.hero-stat-label {\n  display: block;\n  font-size: 0.95rem;\n  line-height: 1.25;\n}\n\n.dashboard-grid {\n  display: grid;\n  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.95fr);\n  gap: 24px;\n  margin-top: 24px;\n  align-items: start;\n}\n\n.content-panel {\n  padding: 24px;\n  border: 1px solid var(--border);\n  border-radius: 28px;\n  background: var(--surface);\n  backdrop-filter: blur(10px);\n  box-shadow: var(--shadow);\n}\n\n.section-heading h2,\n.calendar-header h3,\n.meeting-title {\n  margin: 0;\n}\n\n.section-heading {\n  margin-bottom: 18px;\n}\n\n.meeting-list,\n.agenda-items,\n.calendar-agenda,\n.agenda-day-group {\n  display: grid;\n  gap: 14px;\n}\n\n.meeting-card {\n  padding: 18px;\n  border: 1px solid rgba(31, 26, 22, 0.08);\n  border-radius: 20px;\n  background: var(--surface-strong);\n}\n\n.meeting-card--compact {\n  padding: 16px;\n}\n\n.meeting-meta-row {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  gap: 12px;\n}\n\n.meeting-badge {\n  display: inline-flex;\n  align-items: center;\n  padding: 6px 10px;\n  border-radius: 999px;\n  font-family: "Avenir Next", "Segoe UI", sans-serif;\n  font-size: 0.76rem;\n  font-weight: 700;\n  letter-spacing: 0.08em;\n  text-transform: uppercase;\n}\n\n.meeting-badge--scheduled {\n  background: rgba(198, 90, 46, 0.12);\n  color: #8b3d1d;\n}\n\n.meeting-badge--canceled {\n  background: rgba(95, 43, 35, 0.12);\n  color: #6b2a22;\n}\n\n.meeting-title {\n  margin-top: 12px;\n  font-size: 1.25rem;\n}\n\n.meeting-organizer,\n.meeting-link,\n.meeting-link--muted,\n.empty-state {\n  margin: 8px 0 0;\n}\n\n.meeting-link {\n  font-family: "Avenir Next", "Segoe UI", sans-serif;\n  font-weight: 700;\n  text-decoration: none;\n}\n\n.meeting-link:hover {\n  text-decoration: underline;\n}\n\n.calendar-shell {\n  margin-bottom: 20px;\n  padding: 20px;\n  border-radius: 24px;\n  background: linear-gradient(180deg, rgba(255, 250, 242, 0.94), rgba(245, 232, 217, 0.78));\n}\n\n.calendar-header {\n  margin-bottom: 14px;\n}\n\n.calendar-weekdays,\n.calendar-grid {\n  display: grid;\n  grid-template-columns: repeat(7, minmax(0, 1fr));\n  gap: 8px;\n}\n\n.calendar-weekday {\n  text-align: center;\n  font-family: "Avenir Next", "Segoe UI", sans-serif;\n  font-size: 0.76rem;\n  font-weight: 700;\n  letter-spacing: 0.08em;\n  text-transform: uppercase;\n}\n\n.calendar-cell {\n  min-height: 72px;\n  padding: 10px;\n  border: 1px solid rgba(31, 26, 22, 0.08);\n  border-radius: 16px;\n  background: rgba(255, 255, 255, 0.55);\n}\n\n.calendar-cell--active {\n  background: rgba(198, 90, 46, 0.14);\n  border-color: rgba(198, 90, 46, 0.24);\n}\n\n.calendar-cell--selected {\n  border-color: rgba(198, 90, 46, 0.72);\n  box-shadow: inset 0 0 0 1px rgba(198, 90, 46, 0.24);\n}\n\n.calendar-cell--empty {\n  visibility: hidden;\n}\n\n.calendar-day-link {\n  display: flex;\n  flex-direction: column;\n  align-items: center;\n  justify-content: center;\n  min-height: 100%;\n  color: inherit;\n  text-decoration: none;\n}\n\n.calendar-day-link:hover {\n  text-decoration: none;\n}\n\n.calendar-day-link--disabled {\n  cursor: default;\n}\n\n.calendar-day-number {\n  display: block;\n  font-family: "Avenir Next", "Segoe UI", sans-serif;\n  font-weight: 700;\n  line-height: 1;\n}\n\n.calendar-day-events {\n  display: block;\n  margin-top: 8px;\n  font-size: 0.82rem;\n}\n\n.calendar-day-dot {\n  display: block;\n  width: 8px;\n  height: 8px;\n  margin-top: 8px;\n  border-radius: 999px;\n  background: var(--accent);\n}\n\n@media (max-width: 1100px) {\n  .dashboard-grid {\n    grid-template-columns: 1fr;\n  }\n\n  .hero {\n    display: flex;\n    flex-direction: column;\n    gap: 24px;\n    align-items: stretch;\n  }\n\n  .hero-aside {\n    justify-content: flex-start;\n    width: 100%;\n    max-width: 100%;\n    align-self: stretch;\n  }\n\n  .hero-stats {\n    width: 100%;\n    max-width: 100%;\n    grid-template-columns: repeat(3, minmax(0, 1fr));\n  }\n\n  .dashboard-shell {\n    width: min(100vw - 20px, 1180px);\n    padding-top: 20px;\n  }\n}\n\n@media (max-width: 780px) {\n  .hero-stats {\n    grid-template-columns: 1fr;\n  }\n}\n\n@media (max-width: 640px) {\n  .hero,\n  .content-panel {\n    padding: 20px;\n    border-radius: 22px;\n  }\n\n  .hero-copy {\n    max-width: none;\n  }\n\n  .hero-title {\n    max-width: none;\n  }\n\n  .calendar-weekdays,\n  .calendar-grid {\n    gap: 6px;\n  }\n\n  .calendar-cell {\n    min-height: 64px;\n    padding: 8px;\n  }\n}'

dashboard_app, rt = fast_app(pico=False, default_hdrs=False)


def _dashboard_head() -> Head:
    return Head(
        Title("Meetloaf Dashboard"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Script(src="https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js"),
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/daisyui@5",
            type="text/css",
        ),
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style(NotStr(_DASHBOARD_CSS)),
        Style(":root { color-scheme: light; }"),
    )


def _meeting_badge_class(status: str) -> str:
    color_variant = {
        "scheduled": "badge-warning",
        "canceled": "badge-error",
    }.get(status, "badge-neutral")
    return f"meeting-badge meeting-badge--{status} badge badge-outline {color_variant}"


def mount_dashboard(app: Any) -> None:
    """Mount the dashboard inside the existing FastAPI app."""

    app.mount("/dashboard", dashboard_app)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _format_meeting_datetime(value: str | None) -> str:
    dt = _parse_iso_datetime(value)
    if dt is None:
        return "Time unavailable"
    return dt.strftime("%a, %b %d at %I:%M %p")


def _format_day_label(value: str) -> str:
    dt = datetime.fromisoformat(value)
    return dt.strftime("%A, %b %d")


def _dashboard_href(*, selected_date: str | None, email_address: str | None) -> str:
    query: dict[str, str] = {}
    if selected_date:
        query["selected_date"] = selected_date
    if email_address:
        query["email_address"] = email_address
    if not query:
        return "/dashboard/"
    return f"/dashboard/?{urlencode(query)}"


def _upcoming_panel_href(*, selected_date: str | None, email_address: str | None) -> str:
    query: dict[str, str] = {}
    if selected_date:
        query["selected_date"] = selected_date
    if email_address:
        query["email_address"] = email_address
    if not query:
        return "/dashboard/upcoming-panel"
    return f"/dashboard/upcoming-panel?{urlencode(query)}"


def _month_grid(
    year: int,
    month: int,
    upcoming_by_date: dict[str, list[dict[str, Any]]],
    *,
    selected_date: str | None,
    email_address: str | None,
) -> Div:
    month_name = calendar.month_name[month]
    first_weekday, days_in_month = calendar.monthrange(year, month)
    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    blanks = first_weekday

    cells = [Div(cls="calendar-cell calendar-cell--empty") for _ in range(blanks)]
    for day in range(1, days_in_month + 1):
        iso_key = f"{year:04d}-{month:02d}-{day:02d}"
        events = upcoming_by_date.get(iso_key, [])
        is_selected = iso_key == selected_date
        cell_class = "calendar-cell"
        if events:
            cell_class += " calendar-cell--active"
        if is_selected:
            cell_class += " calendar-cell--selected"
        content = [Span(str(day), cls="calendar-day-number")]
        if events:
            content.append(
                Span("", cls="calendar-day-dot", aria_label="Upcoming meeting")
            )

        cells.append(
            Div(
                A(
                    *content,
                    href=_dashboard_href(selected_date=iso_key, email_address=email_address),
                    hx_get=_upcoming_panel_href(selected_date=iso_key, email_address=email_address),
                    hx_target="#upcoming-calendar-panel",
                    hx_swap="outerHTML",
                    hx_push_url="false",
                    cls="calendar-day-link",
                ) if events else Div(*content, cls="calendar-day-link calendar-day-link--disabled"),
                cls=cell_class,
            )
        )

    return Div(
        Header(
            P("Upcoming calendar", cls="eyebrow"),
            H3(f"{month_name} {year}"),
            cls="calendar-header",
        ),
        Div(*[Span(label, cls="calendar-weekday") for label in weekday_labels], cls="calendar-weekdays"),
        Div(*cells, cls="calendar-grid"),
        cls="calendar-shell",
    )


def _meeting_card(item: dict[str, Any], *, compact: bool = False, allow_join_link: bool = True) -> Article:
    details = item.get("meeting_details_json") or {}
    status = item.get("meeting_status", "scheduled")
    card_cls = "meeting-card border border-base-200 bg-base-100/70 shadow-sm"
    if compact:
        card_cls += " meeting-card--compact"
    join_link = None
    if status == "canceled":
        join_link = P("Meeting was canceled", cls="meeting-link meeting-link--muted")
    elif allow_join_link and item.get("join_url"):
        join_link = A(
            "Open join link",
            href=item.get("join_url"),
            target="_blank",
            rel="noopener noreferrer",
            cls="meeting-link btn btn-link btn-sm px-0 no-underline hover:no-underline",
        )
    elif item.get("is_ongoing"):
        join_link = P("Join link unavailable", cls="meeting-link meeting-link--muted")
    elif item.get("join_url"):
        join_link = P("Meeting has ended", cls="meeting-link meeting-link--muted")
    else:
        join_link = P("Join link unavailable", cls="meeting-link meeting-link--muted")

    return Article(
        Div(
            Span(status.title(), cls=_meeting_badge_class(status)),
            Small(_format_meeting_datetime(item.get("join_at")), cls="meeting-time"),
            cls="meeting-meta-row",
        ),
        H3(item.get("title") or item.get("subject") or "Untitled meeting", cls="meeting-title"),
        P(details.get("organizer") or item.get("sender") or "Organizer unavailable", cls="meeting-organizer"),
        join_link,
        cls=card_cls,
    )


def _upcoming_agenda(upcoming_by_date: dict[str, list[dict[str, Any]]]) -> Section:
    if not upcoming_by_date:
        return Section(
            P("No upcoming invites have been captured yet.", cls="empty-state"),
            cls="calendar-agenda",
        )

    sections: list[Any] = []
    for day in sorted(upcoming_by_date.keys()):
        sections.append(
            Div(
                P(_format_day_label(day), cls="agenda-day-label"),
                Div(*[_meeting_card(item, compact=True, allow_join_link=True) for item in upcoming_by_date[day]], cls="agenda-items"),
                cls="agenda-day-group",
            )
        )

    return Section(*sections, cls="calendar-agenda")


def _selected_upcoming_agenda(
    upcoming_by_date: dict[str, list[dict[str, Any]]],
    *,
    selected_date: str | None,
) -> Section:
    if not upcoming_by_date:
        return Section(
            P("No upcoming invites have been captured yet.", cls="empty-state"),
            cls="calendar-agenda",
        )

    if selected_date and selected_date in upcoming_by_date:
        return Section(
            Div(
                P(_format_day_label(selected_date), cls="agenda-day-label"),
                Div(
                    *[_meeting_card(item, compact=True, allow_join_link=True) for item in upcoming_by_date[selected_date]],
                    cls="agenda-items",
                ),
                cls="agenda-day-group",
            ),
            cls="calendar-agenda",
        )

    if selected_date:
        return Section(
            P("No invite-backed events are available for that date.", cls="empty-state"),
            cls="calendar-agenda",
        )

    return _upcoming_agenda(upcoming_by_date)


def _build_upcoming_panel(
    *,
    upcoming_events: list[dict[str, Any]],
    upcoming_by_date: dict[str, list[dict[str, Any]]],
    selected_date: str | None,
) -> Section:
    selected_count = len(upcoming_by_date.get(selected_date, [])) if selected_date else len(upcoming_events)
    selected_label = _format_day_label(selected_date) if selected_date else "All upcoming invite dates"
    return Section(
        Div(
            H2("Upcoming calendar"),
            P(
                f"Showing {selected_count} event{'s' if selected_count != 1 else ''} for {selected_label}.",
                cls="section-copy",
            ),
            cls="section-heading",
        ),
        _selected_upcoming_agenda(
            upcoming_by_date,
            selected_date=selected_date,
        ),
        id="upcoming-calendar-panel",
        cls="content-panel content-panel--calendar-details",
    )


async def _get_dashboard_view_model(
    *,
    email_address: str | None,
    selected_date: str | None,
) -> tuple[dict[str, Any], str | None]:
    payload = await meeting_invite_store.get_dashboard_payload(email_address=email_address)
    upcoming_by_date = payload["upcoming_by_date"]
    resolved_selected_date = selected_date
    if resolved_selected_date is None and upcoming_by_date:
        resolved_selected_date = sorted(upcoming_by_date.keys())[0]
    return payload, resolved_selected_date


@rt("/upcoming-panel")
async def upcoming_panel(email_address: str | None = None, selected_date: str | None = None):
    payload, resolved_selected_date = await _get_dashboard_view_model(
        email_address=email_address,
        selected_date=selected_date,
    )
    return _build_upcoming_panel(
        upcoming_events=payload["upcoming_events"],
        upcoming_by_date=payload["upcoming_by_date"],
        selected_date=resolved_selected_date,
    )


@rt("/")
async def dashboard(email_address: str | None = None, selected_date: str | None = None):
    payload, resolved_selected_date = await _get_dashboard_view_model(
        email_address=email_address,
        selected_date=selected_date,
    )
    past_meetings = payload["past_meetings"]
    upcoming_events = payload["upcoming_events"]
    upcoming_by_date = payload["upcoming_by_date"]
    count_block = Div(
        Div(Span(str(payload["counts"]["past_meetings"]), cls="hero-stat-value"), Small("Past meetings", cls="hero-stat-label"), cls="hero-stat"),
        Div(Span(str(payload["counts"]["upcoming_events"]), cls="hero-stat-value"), Small("Upcoming events", cls="hero-stat-label"), cls="hero-stat"),
        Div(Span(str(payload["counts"]["canceled"]), cls="hero-stat-value"), Small("Canceled", cls="hero-stat-label"), cls="hero-stat"),
        cls="hero-stats",
    )

    return Html(
        _dashboard_head(),
        Body(
            Main(
                Header(
                    Div(
                        P("Meetings, shaped into one glance.", cls="eyebrow"),
                        H1("Meetloaf", cls="hero-title"),
                        P(
                            "A lightweight meeting dashboard mounted into the existing FastAPI app. "
                            "Upcoming events come from captured Gmail invite emails.",
                            cls="hero-copy",
                        ),
                        cls="hero-intro",
                    ),
                    Div(count_block, cls="hero-aside"),
                    cls="hero",
                ),
                Div(
                    Section(
                        Div(
                            H2("Past meetings"),
                            P("Recent invite history, newest first.", cls="section-copy"),
                            cls="section-heading",
                        ),
                        Div(
                            *[_meeting_card(item, allow_join_link=bool(item.get("is_ongoing"))) for item in past_meetings[:18]],
                            cls="meeting-list",
                        ) if past_meetings else P("No past meetings available yet.", cls="empty-state"),
                        cls="content-panel content-panel--history",
                    ),
                    Section(
                        _month_grid(
                            payload["calendar_year"],
                            payload["calendar_month"],
                            upcoming_by_date,
                            selected_date=resolved_selected_date,
                            email_address=email_address,
                        ),
                        _build_upcoming_panel(
                            upcoming_events=upcoming_events,
                            upcoming_by_date=upcoming_by_date,
                            selected_date=resolved_selected_date,
                        ),
                        cls="content-panel content-panel--calendar",
                    ),
                    cls="dashboard-grid",
                ),
                cls="dashboard-shell",
            ),
            data_theme="lofi",
            cls="min-h-screen",
        ),
    )