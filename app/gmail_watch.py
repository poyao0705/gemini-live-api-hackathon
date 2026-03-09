"""Start a Gmail watch subscription and store the returned baseline historyId."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.config import settings
from app.gmail_history import bootstrap_history_state
from app.gmail_service import get_gmail_service


def main() -> None:
    if not settings.gmail_watch_topic:
        raise RuntimeError("GMAIL_WATCH_TOPIC must be configured before running gmail_watch.py")

    service: Any = get_gmail_service()
    users_resource = getattr(service, "users")()
    profile = users_resource.getProfile(userId=settings.gmail_user_id).execute()
    email_address = profile["emailAddress"]

    request: dict[str, object] = {"topicName": settings.gmail_watch_topic}
    if settings.gmail_watch_label_ids:
        request["labelIds"] = settings.gmail_watch_label_ids

    response = users_resource.watch(
        userId=settings.gmail_user_id,
        body=request,
    ).execute()

    asyncio.run(
        bootstrap_history_state(
            email_address,
            str(response["historyId"]),
            watch_expiration=response.get("expiration"),
        )
    )

    print(
        json.dumps(
            {
                "emailAddress": email_address,
                **response,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()