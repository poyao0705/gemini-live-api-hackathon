from app.services.gmail.history import extract_meeting_details


def test_extract_meeting_details_from_google_calendar_zoom_invite() -> None:
    subject = "Invitation: 黃柏堯's Zoom Meeting @ Tue Mar 10, 2026 10am - 10:30am (GMT+11) (jobmate.agent@gmail.com)"
    body_text = """黃柏堯's Zoom Meeting
Tuesday Mar 10, 2026 ⋅ 10am – 10:30am
Australian Eastern Time - Sydney

Location
https://us05web.zoom.us/j/81132542477?pwd=lJyysC5hCZ0qc89OYbiyEBUTxaLKP8.1

黃柏堯 is inviting you to a scheduled Zoom meeting.
Join Zoom Meeting
https://us05web.zoom.us/j/81132542477?pwd=lJyysC5hCZ0qc89OYbiyEBUTxaLKP8.1

Meeting ID: 811 3254 2477
Passcode: 1fUAdN

Organizer
Po-Yao Huang
poyaohg0705@gmail.com

Guests
jobmate.agent@gmail.com
View all guest info
"""

    details = extract_meeting_details(subject, body_text)

    assert details is not None
    assert details["title"] == "黃柏堯's Zoom Meeting"
    assert details["date_time_text"] == "Tuesday Mar 10, 2026 ⋅ 10am – 10:30am"
    assert details["timezone"] == "Australian Eastern Time - Sydney"
    assert details["join_url"] == "https://us05web.zoom.us/j/81132542477?pwd=lJyysC5hCZ0qc89OYbiyEBUTxaLKP8.1"
    assert details["meeting_id"] == "811 3254 2477"
    assert details["passcode"] == "1fUAdN"
    assert details["organizer"] == "Po-Yao Huang"
    assert details["guests"] == ["jobmate.agent@gmail.com"]
    assert details["agenda"] == []
    assert details["agenda_confidence"] == "none"
    assert details["event_status"] == "confirmed"
    assert details["is_canceled"] is False


def test_extract_meeting_details_with_explicit_agenda_section() -> None:
    subject = "Invitation: Product Sync @ Wed Mar 11, 2026 9am - 9:30am"
    body_text = """Product Sync
Wednesday Mar 11, 2026 ⋅ 9am – 9:30am
Australia/Sydney

Agenda
- Launch timeline
- Hiring updates
3. Scope decisions

Organizer
Po-Yao Huang
"""

    details = extract_meeting_details(subject, body_text)

    assert details is not None
    assert details["agenda"] == ["Launch timeline", "Hiring updates", "Scope decisions"]
    assert details["agenda_confidence"] == "explicit"


def test_extract_meeting_details_with_agenda_colon_header() -> None:
    subject = "Canceled event: 黃柏堯's Zoom Meeting @ Tue Mar 10, 2026 10:45am - 11:15am (GMT+11)"
    body_text = """This event has been canceled.

黃柏堯's Zoom Meeting
Tuesday Mar 10, 2026 ⋅ 10:45am – 11:15am
Australian Eastern Time - Sydney

Join Zoom Meeting
https://us05web.zoom.us/j/89733529902?pwd=GJEfYamSvwLOrJV12P20LsOkqAH7T1.1

Meeting ID: 897 3352 9902
Passcode: 0wKMdN

agenda:
- discuss ai agent development details

Organizer
Po-Yao Huang
"""

    details = extract_meeting_details(subject, body_text)

    assert details is not None
    assert details["title"] == "黃柏堯's Zoom Meeting"
    assert details["event_status"] == "canceled"
    assert details["is_canceled"] is True
    assert details["agenda"] == ["discuss ai agent development details"]
    assert details["agenda_confidence"] == "explicit"


def test_extract_meeting_details_with_agenda_sentence_header() -> None:
    subject = "Canceled event: 黃柏堯's Zoom Meeting @ Tue Mar 10, 2026 11:30am - 12pm (GMT+11)"
    body_text = """This event has been canceled.

黃柏堯's Zoom Meeting
Tuesday Mar 10, 2026 ⋅ 11:30am – 12pm
Australian Eastern Time - Sydney

Join Zoom Meeting
https://us05web.zoom.us/j/84968761971?pwd=iINJVT39OY2EbBzk49ePPFuaneABVD.1

The agenda of this meeting is:
- discuss our current ai agent development process:
- discuss future action items of the new ai research

Organizer
Po-Yao Huang
"""

    details = extract_meeting_details(subject, body_text)

    assert details is not None
    assert details["title"] == "黃柏堯's Zoom Meeting"
    assert details["event_status"] == "canceled"
    assert details["is_canceled"] is True
    assert details["agenda"] == [
        "discuss our current ai agent development process:",
        "discuss future action items of the new ai research",
    ]
    assert details["agenda_confidence"] == "explicit"


def test_extract_meeting_details_returns_none_for_non_meeting_email() -> None:
    details = extract_meeting_details(
        "test",
        "This is a test mail with no calendar details or meeting links.",
    )

    assert details is None