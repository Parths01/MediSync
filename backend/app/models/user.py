from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("gender IN ('Male', 'Female', 'Other')", name="ck_users_gender"),
        CheckConstraint("role IN ('patient', 'admin')", name="ck_users_role"),
        CheckConstraint(
            "blood_group IS NULL OR blood_group IN "
            "('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="ck_users_blood_group",
        ),
        Index("uq_users_email_normalized", text("lower(email)"), unique=True),
    )

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)
    contact: Mapped[str] = mapped_column(String(15), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    blood_group: Mapped[str | None] = mapped_column(String(3), nullable=True)
    role: Mapped[str] = mapped_column(
        String(16),
        default="patient",
        server_default="patient",
        nullable=False,
    )
    registration_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
