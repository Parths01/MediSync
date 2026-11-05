"""Normalize PostgreSQL URLs for SQLAlchemy's asyncpg dialect."""
from sqlalchemy.engine import make_url


def normalize_asyncpg_url(url: str) -> str:
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            url = f"postgresql+asyncpg://{url.removeprefix(prefix)}"
            break
    parsed = make_url(url)
    if parsed.drivername == "postgresql+asyncpg" and any(
        option in parsed.query for option in ("channel_binding", "sslmode")
    ):
        # Neon URLs may carry libpq's channel_binding and sslmode options,
        # which SQLAlchemy's asyncpg dialect passes as unsupported arguments.
        # TLS is enforced independently by the explicit SSLContext passed by
        # the application, so removing sslmode does not weaken verification.
        query = dict(parsed.query)
        query.pop("channel_binding", None)
        query.pop("sslmode", None)
        url = parsed.set(query=query).render_as_string(hide_password=False)
    return url
