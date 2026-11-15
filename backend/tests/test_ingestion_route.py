import pytest
from fastapi.testclient import TestClient

from tenderlens.main import app
from tenderlens.saas.security import current_identity, require_admin


@pytest.fixture(autouse=True)
def operator_identity():
    # These tests exercise feature flags as an authorized operator. Separate
    # commercial tests assert anonymous callers receive 401 and tenants 403.
    app.dependency_overrides[current_identity] = lambda: object()
    app.dependency_overrides[require_admin] = lambda: object()
    yield
    app.dependency_overrides.clear()


def test_ted_ingestion_is_disabled_by_default() -> None:
    response = TestClient(app).post(
        "/api/v1/ingestions/ted",
        json={"query": "PD = 20260812"},
    )

    assert response.status_code == 503
    assert "disabled" in response.json()["detail"]


def test_document_processing_is_disabled_by_default() -> None:
    response = TestClient(app).post(
        "/api/v1/tenders/00000000-0000-0000-0000-000000000000/documents/process"
    )

    assert response.status_code == 503
    assert "disabled" in response.json()["detail"]


def test_embedding_is_disabled_by_default() -> None:
    response = TestClient(app).post(
        "/api/v1/tenders/00000000-0000-0000-0000-000000000000/embeddings"
    )

    assert response.status_code == 503
    assert "disabled" in response.json()["detail"]
