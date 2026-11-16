"""Incremental evaluation state and durable recipient discovery history.

Revision ID: 20261115_0009
Revises: 20261115_0008
"""

import sqlalchemy as sa

from alembic import op

revision = "20261115_0009"
down_revision = "20261115_0008"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "tenders", sa.Column("match_version", sa.Integer(), nullable=False, server_default="1")
    )
    # Reclassify existing TED projections before any profile can notify on them.
    op.execute("""
        UPDATE tenders SET status = 'closed', match_version = match_version + 1
        WHERE source = 'ted' AND (
            raw_metadata->>'notice-type' LIKE 'can-%'
            OR raw_metadata->>'notice-type' IN ('veat', 'cont-modif', 'compl'))
    """)
    op.execute("""
        UPDATE tenders SET status = 'planning', match_version = match_version + 1
        WHERE source = 'ted' AND raw_metadata->>'notice-type'
            IN ('pin-only', 'pin-rtl', 'pin-buyer', 'pin-tran', 'pmc')
    """)
    op.create_table(
        "match_evaluations",
        sa.Column(
            "company_id",
            sa.Uuid(),
            sa.ForeignKey("company_profiles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tender_id",
            sa.Uuid(),
            sa.ForeignKey("tenders.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("profile_fingerprint", sa.String(64), nullable=False),
        sa.Column("tender_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tender_version", sa.Integer(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tenders_matching_updated", "tenders", ["updated_at", "id"])
    op.create_table(
        "digest_opportunities",
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column(
            "tender_id",
            sa.Uuid(),
            sa.ForeignKey("tenders.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("delivery_id", sa.Uuid(), sa.ForeignKey("deliveries.id", ondelete="SET NULL")),
        sa.Column(
            "company_id", sa.Uuid(), sa.ForeignKey("company_profiles.id", ondelete="SET NULL")
        ),
        sa.Column("profile_fingerprint", sa.String(64)),
        sa.Column("tender_version", sa.Integer()),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_digest_opportunities_delivery_id", "digest_opportunities", ["delivery_id"])
    # Preserve known historical assignments, including drafts, from the original
    # explicit workspace links. Unknown history is never invented.
    op.execute("""
        INSERT INTO digest_opportunities (organization_id, user_id, tender_id, delivery_id, selected_at)
        SELECT d.organization_id, d.user_id, t.id, d.id, d.created_at
        FROM deliveries d
        CROSS JOIN LATERAL regexp_matches(d.text_body, '/tenders/([0-9a-fA-F-]{36})', 'g') AS links(value)
        JOIN tenders t ON t.id::text = lower(links.value[1])
        WHERE d.category = 'digest' AND d.organization_id IS NOT NULL
        ORDER BY d.created_at, d.id
        ON CONFLICT DO NOTHING
    """)


def downgrade():
    raise RuntimeError("Do not discard recipient history on rollback; restore a verified backup.")
