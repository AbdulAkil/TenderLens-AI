"""add company profiles, tender matches, saves, and analysis records

Revision ID: 20260829_0006
Revises: 20260829_0005
Create Date: 2026-08-29 00:00:05
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260829_0006"
down_revision = "20260829_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=256), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("services", postgresql.JSONB(), nullable=False),
        sa.Column("industries", postgresql.JSONB(), nullable=False),
        sa.Column("skills", postgresql.JSONB(), nullable=False),
        sa.Column("certifications", postgresql.JSONB(), nullable=False),
        sa.Column("preferred_locations", postgresql.JSONB(), nullable=False),
        sa.Column("cpv_codes", postgresql.JSONB(), nullable=False),
        sa.Column("languages", postgresql.JSONB(), nullable=False),
        sa.Column("minimum_contract_value", sa.Numeric(18, 2)),
        sa.Column("maximum_contract_value", sa.Numeric(18, 2)),
        sa.Column("company_size", sa.String(length=64)),
        sa.Column("embedding", Vector(1536)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_table(
        "saved_tenders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "company_id",
            sa.Uuid(),
            sa.ForeignKey("company_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tender_id", sa.Uuid(), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("company_id", "tender_id", name="uq_saved_tenders_company_tender"),
    )
    op.create_table(
        "tender_matches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "company_id",
            sa.Uuid(),
            sa.ForeignKey("company_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tender_id", sa.Uuid(), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("component_scores", postgresql.JSONB(), nullable=False),
        sa.Column("reasons", postgresql.JSONB(), nullable=False),
        sa.Column("blockers", postgresql.JSONB(), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("company_id", "tender_id", name="uq_tender_matches_company_tender"),
    )
    op.create_table(
        "tender_requirements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tender_id", sa.Uuid(), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("field_name", sa.String(length=128), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column(
            "source_document_id",
            sa.Uuid(),
            sa.ForeignKey("tender_documents.id", ondelete="SET NULL"),
        ),
        sa.Column("source_chunk_ids", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("extraction_method", sa.String(length=32), nullable=False),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("tender_id", "field_name", name="uq_tender_requirements_tender_field"),
    )
    op.create_table(
        "tender_analyses",
        sa.Column(
            "tender_id",
            sa.Uuid(),
            sa.ForeignKey("tenders.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("key_requirements", postgresql.JSONB(), nullable=False),
        sa.Column("potential_blockers", postgresql.JSONB(), nullable=False),
        sa.Column("required_documents", postgresql.JSONB(), nullable=False),
        sa.Column("evaluation_criteria", postgresql.JSONB(), nullable=False),
        sa.Column("source_chunk_ids", postgresql.JSONB(), nullable=False),
        sa.Column("generation_method", sa.String(length=32), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_saved_tenders_company_id", "saved_tenders", ["company_id"])
    op.create_index(
        "ix_tender_matches_company_score", "tender_matches", ["company_id", "overall_score"]
    )
    op.create_index("ix_tender_requirements_tender_id", "tender_requirements", ["tender_id"])


def downgrade() -> None:
    op.drop_index("ix_tender_requirements_tender_id", table_name="tender_requirements")
    op.drop_index("ix_tender_matches_company_score", table_name="tender_matches")
    op.drop_index("ix_saved_tenders_company_id", table_name="saved_tenders")
    op.drop_table("tender_analyses")
    op.drop_table("tender_requirements")
    op.drop_table("tender_matches")
    op.drop_table("saved_tenders")
    op.drop_table("company_profiles")
