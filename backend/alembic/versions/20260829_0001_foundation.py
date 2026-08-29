"""create foundation schema

Revision ID: 20260829_0001
Revises:
Create Date: 2026-08-29 00:00:00
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = "20260829_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "buyers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", "country_code", name="uq_buyers_name_country"),
    )
    op.create_table(
        "tenders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("buyer_id", sa.Uuid(), sa.ForeignKey("buyers.id"), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("region_code", sa.String(16), nullable=True),
        sa.Column("publication_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submission_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("procedure_type", sa.String(128), nullable=True),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_last_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("source", "source_id", name="uq_tenders_source_source_id"),
    )
    op.create_index(
        "ix_tenders_country_deadline", "tenders", ["country_code", "submission_deadline"]
    )
    op.create_index("ix_tenders_publication_date", "tenders", ["publication_date"])
    op.create_table(
        "tender_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tender_id", sa.Uuid(), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("file_name", sa.String(512), nullable=True),
        sa.Column("media_type", sa.String(128), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("processing_status", sa.String(32), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "document_id",
            sa.Uuid(),
            sa.ForeignKey("tender_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(512), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_index"),
    )


def downgrade() -> None:
    op.drop_table("document_chunks")
    op.drop_table("tender_documents")
    op.drop_index("ix_tenders_publication_date", table_name="tenders")
    op.drop_index("ix_tenders_country_deadline", table_name="tenders")
    op.drop_table("tenders")
    op.drop_table("buyers")
