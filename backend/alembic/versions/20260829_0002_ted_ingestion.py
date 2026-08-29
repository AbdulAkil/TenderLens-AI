"""add TED discovery fields

Revision ID: 20260829_0002
Revises: 20260829_0001
Create Date: 2026-08-29 00:00:01
"""

import sqlalchemy as sa

from alembic import op

revision = "20260829_0002"
down_revision = "20260829_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("buyers", "country_code", type_=sa.String(length=3))
    op.alter_column("tenders", "country_code", type_=sa.String(length=3))
    op.create_table(
        "tender_cpv_codes",
        sa.Column(
            "tender_id",
            sa.Uuid(),
            sa.ForeignKey("tenders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.PrimaryKeyConstraint("tender_id", "code"),
    )


def downgrade() -> None:
    op.drop_table("tender_cpv_codes")
    op.alter_column("tenders", "country_code", type_=sa.String(length=2))
    op.alter_column("buyers", "country_code", type_=sa.String(length=2))
