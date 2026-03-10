"""Mounted FastHTML dashboard for meeting history and upcoming events."""

from __future__ import annotations

import calendar
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from fasthtml.common import *  # noqa: F403

from app.services.meetings.invites import meeting_invite_store
from app.web.common import page_head

# Dashboard uses a serif display font; this one-liner is passed as extra_css
# to page_head() so it only applies here and avoids modifying the shared body rule.
_DASHBOARD_FONT_CSS = (
    'body { font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif; }'
)

dashboard_app, rt = fast_app(pico=False, default_hdrs=False)


def _meeting_badge_class(status: str) -> str:
    color_cls = {
        "scheduled": "bg-[rgba(198,90,46,0.12)] text-[#8b3d1d] border-[rgba(198,90,46,0.24)]",
        "canceled":  "bg-[rgba(95,43,35,0.12)]  text-[#6b2a22] border-[rgba(95,43,35,0.2)]",
        "ongoing":   "bg-[rgba(16,163,127,0.12)] text-[#0d6b53] border-[rgba(16,163,127,0.24)]",
        "ended":     "bg-[rgba(91,81,72,0.10)] text-[#5b5148] border-[rgba(91,81,72,0.18)]",
    }.get(status, "")
    return (
        f"badge badge-outline font-label text-[0.76rem] font-bold "
        f"tracking-[0.08em] uppercase px-[10px] py-[6px] rounded-full {color_cls}"
    ).strip()


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

    cells = [
        Div(
            cls=(
                "invisible min-h-[72px] max-[640px]:min-h-[64px] "
                "p-[10px] border border-[rgba(31,26,22,0.08)] rounded-2xl"
            ),
        )
        for _ in range(blanks)
    ]
    for day in range(1, days_in_month + 1):
        iso_key = f"{year:04d}-{month:02d}-{day:02d}"
        events = upcoming_by_date.get(iso_key, [])
        is_selected = iso_key == selected_date

        # Compute background and border explicitly so no !important overrides are needed
        if events:
            bg_cls = "bg-[rgba(198,90,46,0.14)]"
            border_cls = (
                "border-[rgba(198,90,46,0.72)] shadow-[inset_0_0_0_1px_rgba(198,90,46,0.24)]"
                if is_selected
                else "border-[rgba(198,90,46,0.24)]"
            )
        else:
            bg_cls = "bg-[rgba(255,255,255,0.55)]"
            border_cls = (
                "border-[rgba(198,90,46,0.72)] shadow-[inset_0_0_0_1px_rgba(198,90,46,0.24)]"
                if is_selected
                else "border-[rgba(31,26,22,0.08)]"
            )

        cell_cls = (
            f"min-h-[72px] max-[640px]:min-h-[64px] p-[10px] max-[640px]:p-2 "
            f"border rounded-2xl {bg_cls} {border_cls}"
        )

        content = [
            Span(str(day), cls="block font-label font-bold leading-none"),
        ]
        if events:
            content.append(
                Span(
                    "",
                    cls="block w-2 h-2 mt-2 rounded-full bg-accent",
                    aria_label="Upcoming meeting",
                )
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
                    cls="flex flex-col items-center justify-center min-h-full no-underline hover:no-underline",
                ) if events else Div(
                    *content,
                    cls="flex flex-col items-center justify-center min-h-full cursor-default",
                ),
                cls=cell_cls,
            )
        )

    return Div(
        Header(
            P(
                "Upcoming calendar",
                cls="m-0 mb-[10px] text-accent font-label text-[0.82rem] font-bold tracking-[0.18em] uppercase",
            ),
            H3(f"{month_name} {year}", cls="m-0"),
            cls="mb-[14px]",
        ),
        Div(
            *[
                Span(
                    label,
                    cls="text-center font-label text-[0.76rem] font-bold tracking-[0.08em] uppercase",
                )
                for label in weekday_labels
            ],
            cls="grid grid-cols-[repeat(7,minmax(0,1fr))] gap-2 max-[640px]:gap-[6px]",
        ),
        Div(
            *cells,
            cls="grid grid-cols-[repeat(7,minmax(0,1fr))] gap-2 max-[640px]:gap-[6px]",
        ),
        cls=(
            "mb-5 p-5 rounded-3xl "
            "bg-[linear-gradient(180deg,rgba(255,250,242,0.94),rgba(245,232,217,0.78))]"
        ),
    )


def _meeting_card(item: dict[str, Any], *, compact: bool = False, allow_join_link: bool = True) -> Article:
    details = item.get("meeting_details_json") or {}
    status = item.get("meeting_status", "scheduled")

    # Derive display label from temporal flags already set by build_dashboard_payload
    if status == "canceled":
        display_status = "canceled"
    elif item.get("is_ongoing"):
        display_status = "ongoing"
    elif item.get("is_past"):
        display_status = "ended"
    else:
        display_status = status

    padding_cls = "p-4" if compact else "p-[18px]"
    card_cls = f"{padding_cls} border border-[rgba(31,26,22,0.08)] rounded-[20px] bg-surface-strong"
    join_link = None
    if status == "canceled":
        join_link = P("Meeting was canceled", cls="mt-2 text-muted font-label font-bold")
    elif allow_join_link and item.get("join_url"):
        join_link = A(
            "Open join link",
            href=item.get("join_url"),
            target="_blank",
            rel="noopener noreferrer",
            cls="btn btn-link btn-sm px-0 no-underline hover:no-underline",
        )
    elif item.get("is_ongoing"):
        join_link = P("Join link unavailable", cls="mt-2 text-muted font-label font-bold")
    elif item.get("join_url"):
        join_link = P("Meeting has ended", cls="mt-2 text-muted font-label font-bold")
    else:
        join_link = P("Join link unavailable", cls="mt-2 text-muted font-label font-bold")

    return Article(
        Div(
            Span(display_status.title(), cls=_meeting_badge_class(display_status)),
            Small(_format_meeting_datetime(item.get("join_at")), cls="font-label tracking-wide"),
            cls="flex items-center justify-between gap-3",
        ),
        H3(item.get("title") or item.get("subject") or "Untitled meeting", cls="mt-3 text-[1.25rem] m-0"),
        P(details.get("organizer") or item.get("sender") or "Organizer unavailable", cls="mt-2 text-muted"),
        join_link,
        cls=card_cls,
    )


def _upcoming_agenda(upcoming_by_date: dict[str, list[dict[str, Any]]]) -> Section:
    if not upcoming_by_date:
        return Section(
            P("No upcoming invites have been captured yet.", cls="text-muted mt-2"),
            cls="grid gap-[14px]",
        )

    sections: list[Any] = []
    for day in sorted(upcoming_by_date.keys()):
        sections.append(
            Div(
                P(_format_day_label(day), cls="text-muted"),
                Div(
                    *[_meeting_card(item, compact=True, allow_join_link=True) for item in upcoming_by_date[day]],
                    cls="grid gap-[14px]",
                ),
                cls="grid gap-[14px]",
            )
        )

    return Section(*sections, cls="grid gap-[14px]")


def _selected_upcoming_agenda(
    upcoming_by_date: dict[str, list[dict[str, Any]]],
    *,
    selected_date: str | None,
) -> Section:
    if not upcoming_by_date:
        return Section(
            P("No upcoming invites have been captured yet.", cls="text-muted mt-2"),
            cls="grid gap-[14px]",
        )

    if selected_date and selected_date in upcoming_by_date:
        return Section(
            Div(
                P(_format_day_label(selected_date), cls="text-muted"),
                Div(
                    *[_meeting_card(item, compact=True, allow_join_link=True) for item in upcoming_by_date[selected_date]],
                    cls="grid gap-[14px]",
                ),
                cls="grid gap-[14px]",
            ),
            cls="grid gap-[14px]",
        )

    if selected_date:
        return Section(
            P("No invite-backed events are available for that date.", cls="text-muted mt-2"),
            cls="grid gap-[14px]",
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
            H2("Upcoming calendar", cls="m-0"),
            P(
                f"Showing {selected_count} event{'s' if selected_count != 1 else ''} for {selected_label}.",
                cls="text-muted",
            ),
            cls="mb-[18px]",
        ),
        _selected_upcoming_agenda(
            upcoming_by_date,
            selected_date=selected_date,
        ),
        id="upcoming-calendar-panel",
        cls=(
            "p-6 max-[640px]:p-5 border border-border rounded-[28px] max-[640px]:rounded-[22px] "
            "bg-surface backdrop-blur-[10px] shadow-[0_22px_60px_rgba(92,57,31,0.12)]"
        ),
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

    # Hero stats widget
    count_block = Div(
        Div(
            Span(str(payload["counts"]["past_meetings"]), cls="block text-[2rem] font-bold"),
            Small("Past meetings", cls="block text-[0.95rem] leading-[1.25] font-label tracking-wide"),
            cls="min-w-0 p-[18px_16px] border border-[rgba(198,90,46,0.18)] rounded-[22px] bg-[rgba(255,250,242,0.84)]",
        ),
        Div(
            Span(str(payload["counts"]["upcoming_events"]), cls="block text-[2rem] font-bold"),
            Small("Upcoming events", cls="block text-[0.95rem] leading-[1.25] font-label tracking-wide"),
            cls="min-w-0 p-[18px_16px] border border-[rgba(198,90,46,0.18)] rounded-[22px] bg-[rgba(255,250,242,0.84)]",
        ),
        Div(
            Span(str(payload["counts"]["canceled"]), cls="block text-[2rem] font-bold"),
            Small("Canceled", cls="block text-[0.95rem] leading-[1.25] font-label tracking-wide"),
            cls="min-w-0 p-[18px_16px] border border-[rgba(198,90,46,0.18)] rounded-[22px] bg-[rgba(255,250,242,0.84)]",
        ),
        cls=(
            "grid gap-3 w-[min(380px,100%)] max-[1100px]:w-full max-[1100px]:max-w-full "
            "grid-cols-[repeat(3,minmax(0,1fr))] max-[780px]:grid-cols-1 "
            "p-3 border border-[rgba(198,90,46,0.12)] rounded-[26px] "
            "bg-[rgba(255,250,242,0.72)] shadow-[0_16px_36px_rgba(92,57,31,0.08)] backdrop-blur-[12px]"
        ),
    )

    return Html(
        page_head(
            title="Meetloaf Dashboard",
            extra_scripts=[Script(src="https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js")],
            extra_css=_DASHBOARD_FONT_CSS,
        ),
        Body(
            Main(
                # ── Hero ──────────────────────────────────────────────────────
                Header(
                    Div(
                        P(
                            "Meetings, shaped into one glance.",
                            cls="m-0 mb-[10px] text-accent font-label text-[0.82rem] font-bold tracking-[0.18em] uppercase",
                        ),
                        H1(
                            "Meetloaf",
                            cls="m-0 max-w-[7ch] max-[640px]:max-w-none text-[clamp(3rem,7vw,5.4rem)] leading-[0.9] tracking-[-0.05em]",
                        ),
                        P(
                            "A lightweight meeting dashboard mounted into the existing FastAPI app. "
                            "Upcoming events come from captured Gmail invite emails.",
                            cls="max-w-[34rem] max-[640px]:max-w-none mt-4 text-[1.05rem] leading-[1.65] text-muted",
                        ),
                        cls="min-w-0 w-full justify-self-start self-start mr-auto text-left",
                    ),
                    Div(
                        count_block,
                        cls=(
                            "flex justify-end justify-self-end self-center w-max max-w-full "
                            "max-[1100px]:justify-start max-[1100px]:w-full max-[1100px]:max-w-full max-[1100px]:self-stretch"
                        ),
                    ),
                    cls=(
                        "grid grid-cols-[minmax(0,1fr)_auto] max-[1100px]:flex max-[1100px]:flex-col "
                        "gap-8 max-[1100px]:gap-6 items-start max-[1100px]:items-stretch "
                        "p-8 max-[640px]:p-5 border border-border rounded-[28px] max-[640px]:rounded-[22px] "
                        "bg-[linear-gradient(135deg,rgba(255,252,247,0.94),rgba(255,243,229,0.88)),linear-gradient(45deg,rgba(198,90,46,0.08),transparent_60%)] "
                        "shadow-[0_22px_60px_rgba(92,57,31,0.12)]"
                    ),
                ),
                # ── Main grid ─────────────────────────────────────────────────
                Div(
                    Section(
                        Div(
                            H2("Past meetings", cls="m-0"),
                            P("Recent invite history, newest first.", cls="text-muted"),
                            cls="mb-[18px]",
                        ),
                        Div(
                            *[_meeting_card(item, allow_join_link=bool(item.get("is_ongoing"))) for item in past_meetings[:18]],
                            cls="grid gap-[14px]",
                        ) if past_meetings else P("No past meetings available yet.", cls="text-muted mt-2"),
                        cls=(
                            "p-6 max-[640px]:p-5 border border-border rounded-[28px] max-[640px]:rounded-[22px] "
                            "bg-surface backdrop-blur-[10px] shadow-[0_22px_60px_rgba(92,57,31,0.12)]"
                        ),
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
                        cls=(
                            "p-6 max-[640px]:p-5 border border-border rounded-[28px] max-[640px]:rounded-[22px] "
                            "bg-surface backdrop-blur-[10px] shadow-[0_22px_60px_rgba(92,57,31,0.12)]"
                        ),
                    ),
                    cls=(
                        "grid grid-cols-[minmax(0,1.4fr)_minmax(320px,0.95fr)] max-[1100px]:grid-cols-1 "
                        "gap-6 mt-6 items-start"
                    ),
                ),
                cls="max-w-[1180px] w-full mx-auto px-4 max-[1100px]:px-[10px] pt-8 max-[1100px]:pt-5 pb-14",
            ),
            data_theme="lofi",
            cls="min-h-screen",
        ),
    )