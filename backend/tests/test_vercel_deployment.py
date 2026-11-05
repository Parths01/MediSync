import os
from types import SimpleNamespace

import httpx
import pytest

from app import main
from app.db_tls import get_database_ssl_argument
import init_db


@pytest.mark.asyncio
async def test_cleanup_cron_requires_secret_and_separate_cleanup_database(monkeypatch):
    settings = SimpleNamespace(cron_secret="a-long-test-secret-value", cleanup_database_url=None)
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="https://medisync.test"
    ) as client:
        unauthorized = await client.get("/api/cron/cleanup")
        not_configured = await client.get(
            "/api/cron/cleanup", headers={"Authorization": "Bearer a-long-test-secret-value"}
        )
    assert unauthorized.status_code == 401
    assert not_configured.status_code == 503


@pytest.mark.asyncio
async def test_cleanup_cron_calls_cleanup_only_with_valid_secret_and_cleanup_url(monkeypatch):
    settings = SimpleNamespace(
        cron_secret="a-long-test-secret-value",
        cleanup_database_url="postgresql+asyncpg://cleanup@db/medisync",
    )
    called_with = []

    async def fake_cleanup(url):
        called_with.append(url)
        return 1, 2, 3, 4

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "cleanup", fake_cleanup)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="https://medisync.test"
    ) as client:
        response = await client.get(
            "/api/cron/cleanup", headers={"Authorization": "Bearer a-long-test-secret-value"}
        )
    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "expired_sessions": 1,
        "expired_conversations": 2,
        "expired_usage_events": 3,
        "expired_audit_events": 4,
    }
    assert called_with == [settings.cleanup_database_url]


def test_verify_full_uses_chain_and_hostname_verification():
    import ssl

    context = get_database_ssl_argument("verify-full")
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


def test_empty_optional_environment_values_do_not_break_local_configuration():
    import ssl

    from app.config import Settings

    settings = Settings(
        database_url="postgresql+asyncpg://test:test@localhost/db",
        cron_secret="",
        pgsslrootcert="",
    )
    context = get_database_ssl_argument("verify-full", settings.pgsslrootcert)
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED


def test_preview_origin_is_scoped_to_exact_vercel_deployment():
    from app.config import Settings

    settings = Settings(
        database_url="postgresql+asyncpg://test:test@localhost/db",
        frontend_url="https://medisync.example",
        vercel_env="preview",
        vercel_url="medisync-git-feature-example.vercel.app",
    )
    assert settings.allowed_frontend_origins == [
        "https://medisync.example",
        "https://medisync-git-feature-example.vercel.app",
    ]


def test_migration_command_uses_distinct_migration_url_and_restores_runtime_url(monkeypatch):
    observed = {}
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql+asyncpg://migrator@db/medisync")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://runtime@db/medisync")
    monkeypatch.setattr(
        init_db.command,
        "upgrade",
        lambda _config, _revision: observed.setdefault("migration_url", os.environ["DATABASE_URL"]),
    )

    async def fake_grant(url, _ssl_mode, _required):
        observed["grant_url"] = url

    monkeypatch.setattr(init_db, "grant_cleanup_permissions", fake_grant)
    init_db.main()

    expected = "postgresql+asyncpg://migrator@db/medisync"
    assert observed == {"migration_url": expected, "grant_url": expected}
    assert os.environ["DATABASE_URL"] == "postgresql+asyncpg://runtime@db/medisync"
