"""Adopt or create the PostgreSQL doctors table.

Revision ID: 0001_doctors_baseline
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_doctors_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table("doctors"):
        op.create_table(
            "doctors",
            sa.Column("doctor_id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("specialization", sa.String(length=255), nullable=False),
            sa.Column("experience", sa.Integer(), nullable=False),
            sa.Column("contact_details", sa.String(length=255), nullable=False),
            sa.Column("photo", sa.String(length=255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("doctor_id"),
        )


def downgrade() -> None:
    # This baseline may have adopted a pre-existing doctors table and must not drop it.
    pass
