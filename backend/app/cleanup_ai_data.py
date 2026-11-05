"""Scheduled privacy cleanup for expired conversations and aggregate telemetry.

Run periodically (for example, daily) as a one-shot job after migrations.
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.database import get_session_factory, _normalize_database_url
from app.db_tls import get_database_ssl_argument
from app.models import AIConversation, AIUsageEvent, OperatorAuditEvent, UserSession


async def cleanup(database_url: str | None = None) -> tuple[int, int, int, int]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    engine = None
    if database_url:
        engine = create_async_engine(
            _normalize_database_url(database_url),
            pool_pre_ping=True,
            connect_args={"ssl": get_database_ssl_argument(settings.database_ssl_mode, settings.pgsslrootcert)},
            echo=False,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
    else:
        session_factory = get_session_factory()
    try:
        async with session_factory.begin() as db:
            sessions = await db.execute(delete(UserSession).where(UserSession.expires_at <= now))
            conversations = await db.execute(
                delete(AIConversation).where(AIConversation.expires_at <= now)
            )
            usage = await db.execute(
                delete(AIUsageEvent).where(
                    AIUsageEvent.created_at < now - timedelta(days=settings.ai_analytics_retention_days)
                )
            )
            audits = await db.execute(
                delete(OperatorAuditEvent).where(
                    OperatorAuditEvent.created_at < now - timedelta(days=settings.operator_audit_retention_days)
                )
            )
        return sessions.rowcount or 0, conversations.rowcount or 0, usage.rowcount or 0, audits.rowcount or 0
    finally:
        if engine is not None:
            await engine.dispose()


if __name__ == "__main__":
    try:
        sessions, conversations, analytics, audits = asyncio.run(cleanup())
    except Exception as error:
        print(f"AI privacy cleanup failed ({type(error).__name__})")
        raise SystemExit(1) from None
    print(
        "Privacy cleanup complete: "
        f"{sessions} expired sessions, {conversations} expired conversations, "
        f"{analytics} old aggregate usage events, {audits} expired audit events removed"
    )
