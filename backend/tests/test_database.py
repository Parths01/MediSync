import pytest

from app.database import _normalize_database_url


@pytest.mark.parametrize(
    ("database_url", "expected_url"),
    [
        (
            "postgres://user:password@host:5432/medisync",
            "postgresql+asyncpg://user:password@host:5432/medisync",
        ),
        (
            "postgresql://user:password@host:5432/medisync",
            "postgresql+asyncpg://user:password@host:5432/medisync",
        ),
        (
            "postgresql+asyncpg://user:password@host:5432/medisync",
            "postgresql+asyncpg://user:password@host:5432/medisync",
        ),
        (
            "sqlite+aiosqlite:///medisync.db",
            "sqlite+aiosqlite:///medisync.db",
        ),
    ],
)
def test_normalize_database_url(database_url: str, expected_url: str) -> None:
    assert _normalize_database_url(database_url) == expected_url
