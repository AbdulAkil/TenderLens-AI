from fastapi.testclient import TestClient

from tenderlens.main import app


def test_local_frontend_origin_passes_cors_preflight() -> None:
    response = TestClient(app).options(
        "/api/v1/tenders",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "GET" in response.headers["access-control-allow-methods"]


def test_untrusted_origin_is_not_allowed() -> None:
    response = TestClient(app).get(
        "/health", headers={"Origin": "https://untrusted.example"}
    )

    assert "access-control-allow-origin" not in response.headers
