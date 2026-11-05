"""Add configurable expiry to patient-owned AI conversations.

Revision ID: 0007_ai_retention
Revises: 0006_ai_shared_rate_limits
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_ai_retention"
down_revision = "0006_ai_shared_rate_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_conversations", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE ai_conversations SET expires_at = updated_at + INTERVAL '90 days' WHERE expires_at IS NULL")
    op.alter_column("ai_conversations", "expires_at", nullable=False)
    op.create_index("ix_ai_conversations_expires_at", "ai_conversations", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_conversations_expires_at", table_name="ai_conversations")
    op.drop_column("ai_conversations", "expires_at")
