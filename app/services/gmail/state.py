"""Gmail history state persistence (DB/ORM)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import select

from app.db.session import async_session_factory
from app.db.models.meeting import GmailHistoryState, utc_now
from app.services.gmail.parsing import _coerce_history_id


class GmailHistoryStateStore:
    """Persist the latest processed historyId per Gmail account."""

    async def get_user_state(self, email_address: str) -> dict[str, Any] | None:
        async with async_session_factory() as session:
            statement = select(GmailHistoryState).where(
                GmailHistoryState.email_address == email_address
            )
            result = await session.exec(statement)
            state = result.first()
            if state is None:
                return None

            return self._to_dict(state)

    async def upsert_user_state(
        self,
        email_address: str,
        history_id: str,
        *,
        last_sync_time: str | None = None,
        watch_expiration: str | None = None,
        status: str | None = None,
        reset_required: bool | None = None,
    ) -> dict[str, Any]:
        next_history_id = _coerce_history_id(history_id)
        if next_history_id is None:
            raise ValueError("history_id is required")

        async with async_session_factory() as session:
            state = await session.get(GmailHistoryState, email_address)
            if state is None:
                state = GmailHistoryState(
                    email_address=email_address,
                    last_history_id=next_history_id,
                )
            else:
                current_history_id = _coerce_history_id(state.last_history_id)
                if current_history_id is not None and int(next_history_id) < int(current_history_id):
                    next_history_id = current_history_id
                state.last_history_id = next_history_id

            if last_sync_time:
                state.last_sync_time = datetime.fromisoformat(last_sync_time)
            else:
                state.last_sync_time = utc_now()

            if watch_expiration is not None:
                state.watch_expiration = watch_expiration
            if status is not None:
                state.status = status
            if reset_required is not None:
                state.reset_required = reset_required

            state.updated_at = utc_now()

            session.add(state)
            await session.commit()
            await session.refresh(state)
            return self._to_dict(state)

    @staticmethod
    def _to_dict(state: GmailHistoryState) -> dict[str, Any]:
        payload = state.model_dump(mode="json")
        payload["last_sync_time"] = state.last_sync_time.isoformat()
        payload["created_at"] = state.created_at.isoformat()
        payload["updated_at"] = state.updated_at.isoformat()
        return payload


gmail_state_store = GmailHistoryStateStore()


async def bootstrap_history_state(
    email_address: str,
    history_id: str,
    *,
    watch_expiration: str | None = None,
    status: str = "watch_initialized",
) -> dict[str, Any]:
    """Persist the baseline historyId returned by watch() or first push event."""

    return await gmail_state_store.upsert_user_state(
        email_address,
        history_id,
        watch_expiration=watch_expiration,
        status=status,
        reset_required=False,
    )
