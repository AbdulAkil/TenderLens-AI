import os
import uuid

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from tenderlens.database.base import Base
from tenderlens.database.session import get_session
from tenderlens.main import app


@compiles(JSONB, "sqlite")
def jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(TSVECTOR, "sqlite")
def tsvector_sqlite(type_, compiler, **kw):
    return "TEXT"


@pytest.fixture
def db():
    postgres_url = os.environ.get("TEST_DATABASE_URL")
    if postgres_url:
        from sqlalchemy.engine import make_url

        if not (make_url(postgres_url).database or "").endswith("_test"):
            raise RuntimeError("TEST_DATABASE_URL must name a disposable database ending in _test")
        schema = f"test_{uuid.uuid4().hex}"
        admin_engine = create_engine(postgres_url)
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(
            postgres_url,
            connect_args={"options": f"-csearch_path={schema},public"},
            execution_options={"schema_translate_map": {None: schema}},
        )
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as session:
                app.dependency_overrides[get_session] = lambda: session
                yield session
        finally:
            app.dependency_overrides.clear()
            engine.dispose()
            with admin_engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin_engine.dispose()
        return
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def configure(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.create_function("to_tsvector", 2, lambda config, text: text, deterministic=True)

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        app.dependency_overrides[get_session] = lambda: session
        yield session
    app.dependency_overrides.clear()
    engine.dispose()
