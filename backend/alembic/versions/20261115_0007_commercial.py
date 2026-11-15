"""Add commercial tenant domain; legacy profiles remain unassigned and inaccessible.

Revision ID: 20261115_0007
Revises: 20260829_0006
"""

import sqlalchemy as sa

from alembic import op

revision = "20261115_0007"
down_revision = "20260829_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Explicit frozen schema: do not import evolving ORM models into migrations.
    uid = sa.Uuid

    def dt():
        return sa.DateTime(timezone=True)

    def fk(target, **kw):
        return sa.ForeignKey(target, **kw)

    op.create_table(
        "users",
        sa.Column("id", uid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", dt(), nullable=False),
    )
    op.create_table(
        "organizations",
        sa.Column("id", uid(), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("plan", sa.String(32), nullable=False),
        sa.Column("subscription_status", sa.String(32), nullable=False),
        sa.Column("trial_ends_at", dt()),
        sa.Column("stripe_customer_id", sa.String(128), unique=True),
        sa.Column("stripe_subscription_id", sa.String(128), unique=True),
        sa.Column("billing_event_created", sa.Integer(), nullable=False),
        sa.Column("deletion_requested_at", dt()),
        sa.Column("created_at", dt(), nullable=False),
    )
    op.create_table(
        "memberships",
        sa.Column("user_id", uid(), fk("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "organization_id", uid(), fk("organizations.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("role", sa.String(16), nullable=False),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", uid(), fk("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "organization_id", uid(), fk("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("expires_at", dt(), nullable=False),
    )
    op.create_table(
        "action_tokens",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", uid(), fk("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(24), nullable=False),
        sa.Column("expires_at", dt(), nullable=False),
    )
    op.create_table(
        "notification_preferences",
        sa.Column("user_id", uid(), fk("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "organization_id", uid(), fk("organizations.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("frequency", sa.String(16), nullable=False),
        sa.Column("minimum_score", sa.Integer(), nullable=False),
        sa.Column("deadline_reminders", sa.Boolean(), nullable=False),
        sa.Column("updates", sa.Boolean(), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
    )
    op.add_column(
        "company_profiles",
        sa.Column("organization_id", uid(), fk("organizations.id", ondelete="CASCADE")),
    )
    op.add_column("company_profiles", sa.Column("website", sa.String(2048)))
    from sqlalchemy.dialects.postgresql import JSONB

    op.add_column(
        "company_profiles", sa.Column("exclusions", JSONB(), nullable=False, server_default="[]")
    )
    op.add_column(
        "company_profiles", sa.Column("tender_types", JSONB(), nullable=False, server_default="[]")
    )
    op.drop_constraint("company_profiles_name_key", "company_profiles", type_="unique")
    op.create_table(
        "tender_feedback",
        sa.Column("id", uid(), primary_key=True),
        sa.Column(
            "company_id", uid(), fk("company_profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("tender_id", uid(), fk("tenders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.String(24), nullable=False),
        sa.Column("created_at", dt(), nullable=False),
        sa.UniqueConstraint("company_id", "tender_id", name="uq_feedback_company_tender"),
    )
    op.create_table(
        "deliveries",
        sa.Column("id", uid(), primary_key=True),
        sa.Column("organization_id", uid(), fk("organizations.id", ondelete="CASCADE")),
        sa.Column("user_id", uid(), fk("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dedup_key", sa.String(256), nullable=False, unique=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("recipient", sa.String(320), nullable=False),
        sa.Column("subject", sa.String(256), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", dt(), nullable=False),
        sa.Column("provider_id", sa.String(128)),
        sa.Column("last_error", sa.String(256)),
        sa.Column("created_at", dt(), nullable=False),
    )
    op.create_table(
        "jobs",
        sa.Column("id", uid(), primary_key=True),
        sa.Column("dedup_key", sa.String(256), nullable=False, unique=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", dt(), nullable=False),
        sa.Column("lease_until", dt()),
        sa.Column("last_error", sa.String(256)),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", dt(), nullable=False),
    )
    op.create_table(
        "billing_events",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("processed_at", dt(), nullable=False),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", uid(), primary_key=True),
        sa.Column("organization_id", uid(), fk("organizations.id", ondelete="CASCADE")),
        sa.Column("user_id", uid(), fk("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("created_at", dt(), nullable=False),
    )
    op.create_table(
        "usage_records",
        sa.Column("id", uid(), primary_key=True),
        sa.Column(
            "organization_id", uid(), fk("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("units", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_eur", sa.Float(), nullable=False),
        sa.Column("created_at", dt(), nullable=False),
    )
    op.create_table(
        "rate_buckets",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("expires_at", dt(), nullable=False),
    )
    op.create_table(
        "pilot_leads",
        sa.Column("id", uid(), primary_key=True),
        sa.Column("email", sa.String(320), unique=True, nullable=False),
        sa.Column("company_name", sa.String(256), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", dt(), nullable=False),
    )
    op.create_table(
        "notice_revisions",
        sa.Column("id", uid(), primary_key=True),
        sa.Column("tender_id", uid(), fk("tenders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column("created_at", dt(), nullable=False),
        sa.UniqueConstraint("tender_id", "content_hash", name="uq_revision_hash"),
    )
    for table, fields in {
        "company_profiles": ["organization_id"],
        "auth_sessions": ["user_id", "expires_at"],
        "tender_feedback": ["company_id"],
        "deliveries": ["organization_id", "status"],
        "jobs": ["kind", "status", "available_at"],
        "audit_events": ["organization_id"],
        "usage_records": ["organization_id"],
        "rate_buckets": ["expires_at"],
        "notice_revisions": ["tender_id"],
    }.items():
        for field in fields:
            op.create_index(f"ix_{table}_{field}", table, [field])


def downgrade() -> None:
    raise RuntimeError(
        "Commercial migration is forward-only: restore a verified backup to roll back tenant data safely."
    )
