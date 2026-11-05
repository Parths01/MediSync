"""Add shared per-patient assistant rate limit buckets.

Revision ID: 0006_ai_shared_rate_limits
Revises: 0005_ai_usage_feedback
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_ai_shared_rate_limits"
down_revision = "0005_ai_usage_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_rate_limits",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("request_count >= 1", name="ck_ai_rate_limit_count_positive"),
    )


def downgrade() -> None:
    op.drop_table("ai_rate_limits")
