"""Mounted FastHTML dashboard for meeting history and upcoming events."""

from __future__ import annotations

import calendar
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from fasthtml.common import *  # noqa: F403

from app.services.meetings.invites import meeting_invite_store


dashboard_app, rt = fast_app(
    pico=False,
    default_hdrs=False,
    hdrs=(
        Script(src="https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js"),
        Link(rel="stylesheet", href="/static/css/dashboard.css", type="text/css"),
        Style(":root { color-scheme: light; }"),
    ),
)


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
    card_cls = "meeting-card meeting-card--compact" if compact else "meeting-card"
    join_link = None
    if status == "canceled":
        join_link = P("Meeting was canceled", cls="meeting-link meeting-link--muted")
    elif allow_join_link and item.get("join_url"):
        join_link = A(
            "Open join link",
            href=item.get("join_url"),
            target="_blank",
            rel="noopener noreferrer",
            cls="meeting-link",
        )
    elif item.get("is_ongoing"):
        join_link = P("Join link unavailable", cls="meeting-link meeting-link--muted")
    elif item.get("join_url"):
        join_link = P("Meeting has ended", cls="meeting-link meeting-link--muted")
    else:
        join_link = P("Join link unavailable", cls="meeting-link meeting-link--muted")

    return Article(
        Div(
            Span(status.title(), cls=f"meeting-badge meeting-badge--{status}"),
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
        Head(
            Title("Meetloaf Dashboard"),
            Script(src="https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js"),
            Link(rel="stylesheet", href="/static/css/dashboard.css", type="text/css"),
        ),
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
                    ),
                    count_block,
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
            )
        ),
    )