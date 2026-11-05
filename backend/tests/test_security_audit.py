from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.config import Settings
from app.api.routes.admin import router as admin_router
from app.api.routes.doctors import router as doctors_router
from app.models import OperatorAuditEvent, User
from app.security_audit import audit_privileged_access


class AuditSession:
    def __init__(self, *, fail_flush=False):
        self.added = []
        self.statements = []
        self.commits = 0
        self.rollbacks = 0
        self.fail_flush = fail_flush

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        if self.fail_flush:
            raise RuntimeError("database details must not escape")
        self.added[-1].event_id = 42

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1

    async def execute(self, statement):
        self.statements.append(statement)


def request_with_template() -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/api/v1/admin/dashboard",
        "raw_path": b"/api/v1/admin/dashboard",
        "query_string": b"patient=private-value",
        "root_path": "",
        "headers": [],
        "client": ("127.0.0.1", 1234),
        "server": ("test", 443),
        "route": SimpleNamespace(path="/api/v1/admin/dashboard"),
    }
    return Request(scope)


def admin_user() -> User:
    return User(
        user_id=7,
        name="Admin",
        dob=date(1980, 1, 1),
        gender="Other",
        contact="0000000000",
        email="admin@example.test",
        password_hash="unused",
        role="admin",
    )


@pytest.mark.asyncio
async def test_operator_audit_persists_template_action_without_query_data():
    session = AuditSession()
    dependency = audit_privileged_access(request_with_template(), db=session, operator=admin_user())

    await anext(dependency)
    event = session.added[0]
    assert isinstance(event, OperatorAuditEvent)
    assert event.actor_user_id == 7
    assert event.action == "GET /api/v1/admin/dashboard"
    assert "private-value" not in event.action
    with pytest.raises(StopAsyncIteration):
        await anext(dependency)

    assert session.commits == 2
    assert "operator_audit_events" in str(session.statements[-1])
    assert "finished_at" in str(session.statements[-1])


@pytest.mark.asyncio
async def test_failed_privileged_operation_updates_audit_outcome_and_propagates():
    session = AuditSession()
    dependency = audit_privileged_access(request_with_template(), db=session, operator=admin_user())
    await anext(dependency)

    with pytest.raises(RuntimeError, match="operation failed"):
        await dependency.athrow(RuntimeError("operation failed"))

    assert session.rollbacks == 1
    assert session.commits == 2
    assert "operator_audit_events" in str(session.statements[-1])


@pytest.mark.asyncio
async def test_audit_storage_failure_blocks_privileged_work_with_generic_error():
    session = AuditSession(fail_flush=True)
    dependency = audit_privileged_access(request_with_template(), db=session, operator=admin_user())

    with pytest.raises(HTTPException) as error:
        await anext(dependency)

    assert error.value.status_code == 503
    assert error.value.detail == "Privileged access audit is unavailable"
    assert "database details" not in error.value.detail


def test_production_requires_verified_postgresql_tls_and_long_audit_retention():
    with pytest.raises(ValueError, match="DATABASE_SSL_MODE=verify-full"):
        Settings(
            database_url="postgresql+asyncpg://user:pass@db.example.test/medisync",
            app_env="production",
            session_cookie_secure=True,
            database_ssl_mode="require",
        )

    secure = Settings(
        database_url="postgresql+asyncpg://user:pass@db.example.test/medisync",
        app_env="production",
        session_cookie_secure=True,
        database_ssl_mode="verify-full",
    )
    assert secure.database_ssl_mode == "verify-full"
    assert secure.operator_audit_retention_days == 365
    with pytest.raises(ValueError):
        Settings(
            database_url="postgresql+asyncpg://user:pass@db.example.test/medisync",
            operator_audit_retention_days=179,
        )


def test_admin_router_and_doctor_mutations_are_audited():
    assert any(dependency.dependency is audit_privileged_access for dependency in admin_router.dependencies)

    doctor_mutations = [route for route in doctors_router.routes if route.path not in {"", "/photos/{filename}"}]
    protected_writes = [route for route in doctor_mutations if "POST" in route.methods or "PUT" in route.methods or "PATCH" in route.methods or "DELETE" in route.methods]
    assert protected_writes
    assert all(
        any(dependency.dependency is audit_privileged_access for dependency in route.dependencies)
        for route in protected_writes
    )
