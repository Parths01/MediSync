"""Limit appointment slot uniqueness to pending and confirmed bookings.

Revision ID: 0003_active_appointment_slots
Revises: 0002_core_workflows
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_active_appointment_slots"
down_revision = "0002_core_workflows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("uq_appointments_active_doctor_slot", table_name="appointments")
    op.create_index(
        "uq_appointments_active_doctor_slot",
        "appointments",
        ["doctor_id", "appointment_date"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending','confirmed')"),
    )


def downgrade() -> None:
    op.drop_index("uq_appointments_active_doctor_slot", table_name="appointments")
    op.create_index(
        "uq_appointments_active_doctor_slot",
        "appointments",
        ["doctor_id", "appointment_date"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('rejected', 'cancelled')"),
    )
