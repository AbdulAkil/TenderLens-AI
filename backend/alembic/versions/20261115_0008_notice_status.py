"""Explicit source status; unknown is never represented as open.

Revision ID: 20261115_0008
Revises: 20261115_0007
"""

import sqlalchemy as sa

from alembic import op

revision = "20261115_0008"
down_revision = "20261115_0007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "tenders", sa.Column("status", sa.String(24), nullable=False, server_default="unknown")
    )
    op.create_index("ix_tenders_status_deadline", "tenders", ["status", "submission_deadline"])


def downgrade():
    op.drop_index("ix_tenders_status_deadline", table_name="tenders")
    op.drop_column("tenders", "status")
