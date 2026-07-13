from app import create_app
from config import TestConfig


def test_internal_pages_require_login():
    app = create_app(TestConfig)
    client = app.test_client()
    for path in ["/teams", "/teams/ranking", "/courts", "/api/teams/search"]:
        response = client.get(path)
        assert response.status_code in (302, 401)


def test_security_headers_are_set():
    app = create_app(TestConfig)
    response = app.test_client().get("/")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Security-Policy" in response.headers
