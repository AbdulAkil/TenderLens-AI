"""make document sources idempotent

Revision ID: 20260829_0004
Revises: 20260829_0003
Create Date: 2026-08-29 00:00:03
"""

from alembic import op

revision = "20260829_0004"
down_revision = "20260829_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_tender_documents_tender_source_url",
        "tender_documents",
        ["tender_id", "source_url"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_tender_documents_tender_source_url",
        "tender_documents",
        type_="unique",
    )
