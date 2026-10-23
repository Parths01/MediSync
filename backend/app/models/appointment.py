from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'completed', 'rejected', 'cancelled')",
            name="ck_appointments_status",
        ),
        CheckConstraint("assigned_by IN ('user', 'admin')", name="ck_appointments_assigned_by"),
        Index(
            "uq_appointments_active_doctor_slot",
            "doctor_id",
            "appointment_date",
            unique=True,
            postgresql_where=text("status IN ('pending','confirmed')"),
        ),
    )

    appointment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.doctor_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    appointment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16),
        default="pending",
        server_default="pending",
        nullable=False,
    )
    assigned_by: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
