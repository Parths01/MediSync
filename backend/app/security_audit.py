"""Durable, privacy-minimized audit records for privileged route access."""
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import OperatorAuditEvent, User
from app.security import get_admin_user

logger = logging.getLogger(__name__)


async def audit_privileged_access(
    request: Request,
    db: AsyncSession = Depends(get_db),
    operator: User = Depends(get_admin_user),
) -> AsyncIterator[None]:
    route = request.scope.get("route")
    route_template = getattr(route, "path", "unknown")
    event = OperatorAuditEvent(
        actor_user_id=operator.user_id,
        action=f"{request.method.upper()} {route_template}"[:256],
        outcome="started",
    )
    db.add(event)
    try:
        await db.flush()
        event_id = event.event_id
        await db.commit()
    except Exception as error:
        await db.rollback()
        logger.error("privileged audit preflight failed (%s)", type(error).__name__)
        raise HTTPException(status_code=503, detail="Privileged access audit is unavailable") from None

    outcome = "completed"
    try:
        yield
    except BaseException:
        outcome = "failed"
        raise
    finally:
        try:
            if outcome == "failed":
                await db.rollback()
            await db.execute(
                update(OperatorAuditEvent)
                .where(OperatorAuditEvent.event_id == event_id)
                .values(outcome=outcome, finished_at=datetime.now(timezone.utc))
            )
            await db.commit()
        except Exception as error:
            await db.rollback()
            # The committed 'started' event remains as evidence of the access attempt.
            logger.error("privileged audit completion update failed (%s)", type(error).__name__)
