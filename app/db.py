"""Database engine and session helpers."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a SQLModel async session."""

    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Create database tables for local development when migrations are skipped."""

    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)