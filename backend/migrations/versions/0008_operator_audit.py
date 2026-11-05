"""Add privacy-minimized privileged operator audit events.

Revision ID: 0008_operator_audit
Revises: 0007_ai_retention
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_operator_audit"
down_revision = "0007_ai_retention"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operator_audit_events",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(256), nullable=False),
        sa.Column("outcome", sa.String(16), server_default="started", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("outcome IN ('started', 'completed', 'failed')", name="ck_operator_audit_outcome"),
    )
    op.create_index("ix_operator_audit_created_at", "operator_audit_events", ["created_at"])
    op.create_index("ix_operator_audit_actor_created", "operator_audit_events", ["actor_user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_operator_audit_actor_created", table_name="operator_audit_events")
    op.drop_index("ix_operator_audit_created_at", table_name="operator_audit_events")
    op.drop_table("operator_audit_events")
