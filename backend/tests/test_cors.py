"""CORS: the kiosk frontend runs on a different origin than the API.

Deployment (plan §8 Phase 4 部署说明) serves the built frontend from its
own origin; the browser must be allowed to call the API cross-origin.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_preflight_from_frontend_origin_is_allowed() -> None:
    res = client.options(
        "/api/sessions",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "*"


def test_api_response_carries_allow_origin_header() -> None:
    res = client.get("/api/health", headers={"Origin": "http://kiosk.lan:5173"})

    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "*"
