from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OperatorAuditEvent(Base):
    """Minimal privileged-access record; request and patient content are excluded."""

    __tablename__ = "operator_audit_events"
    __table_args__ = (
        CheckConstraint("outcome IN ('started', 'completed', 'failed')", name="ck_operator_audit_outcome"),
        Index("ix_operator_audit_created_at", "created_at"),
        Index("ix_operator_audit_actor_created", "actor_user_id", "created_at"),
    )

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(256), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False, server_default="started")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
