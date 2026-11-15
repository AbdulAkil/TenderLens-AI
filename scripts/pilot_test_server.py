"""Ephemeral loopback-only integration server. Never use for a deployment.

SQLite tests application behavior, not PostgreSQL search/migration semantics.
Test-only token access is defined in this script, outside the shipped API package.
"""

# The test environment must be configured before importing the application.
# ruff: noqa: E402

import os
import tempfile
from pathlib import Path

test_directory = tempfile.TemporaryDirectory(prefix="tenderlens-browser-")
test_database = Path(test_directory.name) / "browser.sqlite"

os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = f"sqlite:///{test_database.as_posix()}"
os.environ["EMAIL_PROVIDER"] = "dry_run"
os.environ["ADMIN_EMAILS"] = "pilot@example.com"

import re
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from tenderlens.database.base import Base
from tenderlens.database.session import get_session
from tenderlens.main import app
from tenderlens.models.tender import Tender
from tenderlens.saas.models import Delivery, User
from tenderlens.saas.worker import build_digests


@compiles(JSONB, "sqlite")
def jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(TSVECTOR, "sqlite")
def tsvector_sqlite(type_, compiler, **kw):
    return "TEXT"


# Concurrent browser requests require separate connections. StaticPool shares one
# in-memory SQLite connection across threads and can corrupt transaction state.
engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def configure(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")
    connection.create_function("to_tsvector", 2, lambda config, value: value, deterministic=True)


Base.metadata.create_all(engine)


def sessions():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = sessions
with Session(engine) as session:
    session.add(
        Tender(
            source="ted",
            source_id="browser-fixture",
            source_url="https://ted.europa.eu/en/notice/-/detail/browser-fixture",
            title="TEST FIXTURE: Cybersecurity software development",
            description="TEST FIXTURE ONLY. Python cybersecurity software development.",
            country_code="BEL",
            raw_metadata={"test_fixture": True},
            ingested_at=datetime.now(UTC),
            submission_deadline=datetime.now(UTC) + timedelta(days=10),
        )
    )
    session.commit()


@app.get("/__test/token")
def test_token(email: str):
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.email == email))
        if not user:
            raise HTTPException(404)
        delivery = session.scalar(
            select(Delivery)
            .where(Delivery.user_id == user.id, Delivery.category == "verify")
            .order_by(Delivery.created_at.desc())
        )
        return {"token": re.search(r"#token=([\w-]+)", delivery.text_body)[1]}


@app.post("/__test/digest")
def test_digest():
    with Session(engine) as session:
        return {"created": build_digests(session)}


if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        engine.dispose()
        test_directory.cleanup()
