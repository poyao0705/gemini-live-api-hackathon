"""Database dependency for FastAPI dependency injection."""

from collections.abc import AsyncGenerator

from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a SQLModel async database session."""

    async with async_session_factory() as session:
        yield session
