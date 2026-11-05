import pytest

import init_db


class FakeConnection:
    def __init__(self, role_exists: bool):
        self.role_exists = role_exists
        self.statements = []

    async def scalar(self, _statement):
        return self.role_exists

    async def execute(self, statement):
        self.statements.append(str(statement))


class FakeTransaction:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, *_args):
        return False


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection
        self.disposed = False

    def begin(self):
        return FakeTransaction(self.connection)

    async def dispose(self):
        self.disposed = True


@pytest.mark.asyncio
async def test_cleanup_grants_are_limited_to_cleanup_tables(monkeypatch):
    connection = FakeConnection(role_exists=True)
    engine = FakeEngine(connection)
    monkeypatch.setattr(init_db, "create_async_engine", lambda *_args, **_kwargs: engine)

    await init_db.grant_cleanup_permissions(
        "postgresql+asyncpg://medisync_migrator@db/medisync",
        "verify-full",
        required=True,
    )

    assert len(connection.statements) == 3
    assert "GRANT DELETE ON TABLE user_sessions, ai_conversations" in connection.statements[0]
    assert "ai_usage_events, operator_audit_events TO medisync_cleanup" in connection.statements[0]
    assert "GRANT SELECT (expires_at) ON user_sessions, ai_conversations" in connection.statements[1]
    assert "GRANT SELECT (created_at) ON ai_usage_events, operator_audit_events" in connection.statements[2]
    assert all("ON ALL TABLES" not in statement for statement in connection.statements)
    assert engine.disposed


@pytest.mark.asyncio
async def test_production_migration_fails_closed_if_cleanup_role_is_missing(monkeypatch):
    connection = FakeConnection(role_exists=False)
    engine = FakeEngine(connection)
    monkeypatch.setattr(init_db, "create_async_engine", lambda *_args, **_kwargs: engine)

    with pytest.raises(RuntimeError, match="Required cleanup database role is missing"):
        await init_db.grant_cleanup_permissions(
            "postgresql+asyncpg://medisync_migrator@db/medisync",
            "verify-full",
            required=True,
        )

    assert not connection.statements
    assert engine.disposed
