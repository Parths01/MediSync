import hmac

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router import api_router
from app.config import get_settings
from app.cleanup_ai_data import cleanup
from app.database import get_db

settings = get_settings()

app = FastAPI(
    title="MediSync API",
    description="API for MediSync healthcare appointment management.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Accept", "Content-Type", "X-CSRF-Token"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Service dependencies are unavailable") from None
    return {"status": "ready"}


@app.get("/api/cron/cleanup", tags=["operations"])
async def scheduled_privacy_cleanup(request: Request) -> dict[str, str | int]:
    """Protected daily cleanup endpoint; Vercel invokes it with CRON_SECRET."""
    secret = get_settings().cron_secret
    authorization = request.headers.get("authorization", "")
    if not secret or not hmac.compare_digest(authorization, f"Bearer {secret}"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not get_settings().cleanup_database_url:
        raise HTTPException(status_code=503, detail="Cleanup is not configured")
    counts = await cleanup(get_settings().cleanup_database_url)
    return {
        "status": "completed",
        "expired_sessions": counts[0],
        "expired_conversations": counts[1],
        "expired_usage_events": counts[2],
        "expired_audit_events": counts[3],
    }
