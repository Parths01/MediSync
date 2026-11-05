"""
backend/app/database.py
Async SQLAlchemy engine + session factory.
"""
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings
from app.db_tls import get_database_ssl_argument

settings = get_settings()


def _normalize_database_url(url: str) -> str:
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return f"postgresql+asyncpg://{url.removeprefix(prefix)}"
    return url


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Create the database engine on first use, not while importing the app.

    Import-time engine construction imports asyncpg's native extension. Deferring
    it allows API modules and tests with overridden database dependencies to be
    imported on Windows hosts where application-control policy blocks that DLL.
    Actual database access still requires the configured driver and fails normally.
    """
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(
            _normalize_database_url(settings.database_url),
            pool_pre_ping=True,
            connect_args={"ssl": get_database_ssl_argument(settings.database_ssl_mode, settings.pgsslrootcert)},
            # SQL echo includes bind values (which may be health information).
            # Keep it disabled in every environment; use structured, redacted logs.
            echo=False,
        )
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
