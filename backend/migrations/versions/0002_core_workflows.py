"""Add PostgreSQL tables for the patient and admin workflows.

Revision ID: 0002_core_workflows
Revises: 0001_doctors_baseline
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_core_workflows"
down_revision = "0001_doctors_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    workflow_tables = {
        "users",
        "appointments",
        "medical_history",
        "contact_messages",
        "feedback",
        "user_sessions",
    }
    conflicts = existing_tables & workflow_tables
    if conflicts:
        names = ", ".join(sorted(conflicts))
        raise RuntimeError(
            f"Existing workflow tables require a reviewed migration plan: {names}"
        )

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("user_id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("dob", sa.Date(), nullable=False),
            sa.Column("gender", sa.String(length=16), nullable=False),
            sa.Column("contact", sa.String(length=15), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("blood_group", sa.String(length=3), nullable=True),
            sa.Column(
                "role",
                sa.String(length=16),
                server_default="patient",
                nullable=False,
            ),
            sa.Column(
                "registration_date",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=True,
            ),
            sa.CheckConstraint(
                "gender IN ('Male', 'Female', 'Other')",
                name="ck_users_gender",
            ),
            sa.CheckConstraint("role IN ('patient', 'admin')", name="ck_users_role"),
            sa.CheckConstraint(
                "blood_group IS NULL OR blood_group IN "
                "('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
                name="ck_users_blood_group",
            ),
            sa.PrimaryKeyConstraint("user_id"),
        )
        op.create_index(
            "uq_users_email_normalized",
            "users",
            [sa.text("lower(email)")],
            unique=True,
        )

    if "appointments" not in existing_tables:
        op.create_table(
            "appointments",
            sa.Column("appointment_id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("doctor_id", sa.Integer(), nullable=False),
            sa.Column("appointment_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "status",
                sa.String(length=16),
                server_default="pending",
                nullable=False,
            ),
            sa.Column("assigned_by", sa.String(length=8), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=True,
            ),
            sa.CheckConstraint(
                "status IN ('pending', 'confirmed', 'completed', 'rejected', 'cancelled')",
                name="ck_appointments_status",
            ),
            sa.CheckConstraint(
                "assigned_by IN ('user', 'admin')",
                name="ck_appointments_assigned_by",
            ),
            sa.ForeignKeyConstraint(
                ["doctor_id"],
                ["doctors.doctor_id"],
                name="fk_appointments_doctor_id_doctors",
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.user_id"],
                name="fk_appointments_user_id_users",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("appointment_id"),
        )
        op.create_index("ix_appointments_user_id", "appointments", ["user_id"])
        op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
        op.create_index(
            "uq_appointments_active_doctor_slot",
            "appointments",
            ["doctor_id", "appointment_date"],
            unique=True,
            postgresql_where=sa.text("status NOT IN ('rejected', 'cancelled')"),
        )

    if "medical_history" not in existing_tables:
        op.create_table(
            "medical_history",
            sa.Column("history_id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("diagnosis", sa.String(length=255), nullable=False),
            sa.Column("treatment", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("recorded_at", sa.Date(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.user_id"],
                name="fk_medical_history_user_id_users",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("history_id"),
        )
        op.create_index("ix_medical_history_user_id", "medical_history", ["user_id"])

    if "contact_messages" not in existing_tables:
        op.create_table(
            "contact_messages",
            sa.Column("contact_id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column(
                "status",
                sa.String(length=8),
                server_default="open",
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=True,
            ),
            sa.CheckConstraint(
                "status IN ('open', 'closed')",
                name="ck_contact_messages_status",
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.user_id"],
                name="fk_contact_messages_user_id_users",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("contact_id"),
        )
        op.create_index("ix_contact_messages_user_id", "contact_messages", ["user_id"])

    if "feedback" not in existing_tables:
        op.create_table(
            "feedback",
            sa.Column("feedback_id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.user_id"],
                name="fk_feedback_user_id_users",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("feedback_id"),
        )
        op.create_index("ix_feedback_user_id", "feedback", ["user_id"])

    if "user_sessions" not in existing_tables:
        op.create_table(
            "user_sessions",
            sa.Column("session_id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.user_id"],
                name="fk_user_sessions_user_id_users",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("session_id"),
            sa.UniqueConstraint("token_hash", name="uq_user_sessions_token_hash"),
        )
        op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_table("feedback")
    op.drop_index("ix_contact_messages_user_id", table_name="contact_messages")
    op.drop_table("contact_messages")
    op.drop_index("ix_medical_history_user_id", table_name="medical_history")
    op.drop_table("medical_history")
    op.drop_index("uq_appointments_active_doctor_slot", table_name="appointments")
    op.drop_index("ix_appointments_doctor_id", table_name="appointments")
    op.drop_index("ix_appointments_user_id", table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("users")
