"""Read-only schema acceptance after CI applies migrations to its ephemeral database."""

import os

from sqlalchemy import create_engine, inspect, text

engine = create_engine(os.environ["DATABASE_URL"])
with engine.connect() as connection:
    assert (
        connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
        == "20261115_0009"
    )
    tables = set(inspect(connection).get_table_names())
    assert {
        "users",
        "organizations",
        "memberships",
        "company_profiles",
        "jobs",
        "deliveries",
        "notice_revisions",
        "billing_events",
        "match_evaluations",
        "digest_opportunities",
    } <= tables
    columns = {column["name"] for column in inspect(connection).get_columns("company_profiles")}
    assert {"organization_id", "exclusions", "website", "tender_types"} <= columns
    assert {"status", "match_version"} <= {
        column["name"] for column in inspect(connection).get_columns("tenders")
    }
    assert (
        connection.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).scalar()
        == "vector"
    )
print("PostgreSQL migration schema acceptance passed")
