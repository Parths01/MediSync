import os
import asyncio

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def grant_cleanup_permissions(database_url: str, ssl_mode: str, required: bool) -> None:
    if database_url.startswith(("postgres://", "postgresql://")):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, connect_args={"ssl": ssl_mode}, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            cleanup_role_exists = await connection.scalar(
                text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'medisync_cleanup')")
            )
            if not cleanup_role_exists:
                if required:
                    raise RuntimeError("Required cleanup database role is missing")
                return
            for grant in (
                "GRANT DELETE ON TABLE user_sessions, ai_conversations, "
                "ai_usage_events, operator_audit_events TO medisync_cleanup",
                "GRANT SELECT (expires_at) ON user_sessions, ai_conversations TO medisync_cleanup",
                "GRANT SELECT (created_at) ON ai_usage_events, operator_audit_events TO medisync_cleanup",
            ):
                await connection.execute(text(grant))
    finally:
        await engine.dispose()


def main() -> None:
    migration_url = os.environ.get("MIGRATION_DATABASE_URL")
    previous_url = os.environ.get("DATABASE_URL")
    if migration_url:
        os.environ["DATABASE_URL"] = migration_url
    try:
        command.upgrade(Config("alembic.ini"), "head")
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is required to configure cleanup privileges")
        asyncio.run(
            grant_cleanup_permissions(
                database_url,
                os.environ.get("DATABASE_SSL_MODE", "prefer"),
                os.environ.get("APP_ENV", "development").lower() in {"production", "prod"},
            )
        )
    finally:
        if migration_url:
            if previous_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = previous_url


if __name__ == "__main__":
    main()
