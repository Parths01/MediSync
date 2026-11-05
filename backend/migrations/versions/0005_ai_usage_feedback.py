"""Add privacy-minimized assistant usage and feedback.

Revision ID: 0005_ai_usage_feedback
Revises: 0004_ai_conversations
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_ai_usage_feedback"
down_revision = "0004_ai_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_usage_events",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("succeeded", sa.Boolean(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("latency_ms >= 0", name="ck_ai_usage_latency_nonnegative"),
        sa.CheckConstraint("input_tokens IS NULL OR input_tokens >= 0", name="ck_ai_usage_input_tokens_nonnegative"),
        sa.CheckConstraint("output_tokens IS NULL OR output_tokens >= 0", name="ck_ai_usage_output_tokens_nonnegative"),
    )
    op.create_table(
        "ai_feedback",
        sa.Column("feedback_id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("ai_messages.message_id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "message_id", name="uq_ai_feedback_user_message"),
        sa.CheckConstraint("rating IN ('helpful', 'not_helpful')", name="ck_ai_feedback_rating"),
    )
    op.create_index("ix_ai_feedback_user_id", "ai_feedback", ["user_id"])
    op.create_index("ix_ai_feedback_message_id", "ai_feedback", ["message_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_feedback_message_id", table_name="ai_feedback")
    op.drop_index("ix_ai_feedback_user_id", table_name="ai_feedback")
    op.drop_table("ai_feedback")
    op.drop_table("ai_usage_events")
