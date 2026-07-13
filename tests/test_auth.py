from app import create_app
from app.extensions import db
from config import TestConfig


def test_register_creates_user():
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.post("/register", data={
        "name": "Teste Usuario",
        "email": "teste@example.com",
        "phone": "11999999999",
        "birth_date": "1995-01-01",
        "city": "Sao Paulo",
        "state": "SP",
        "neighborhood": "Centro",
        "password": "Senha123!",
        "confirm_password": "Senha123!",
        "accept_terms": "y",
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.execute(db.select(__import__("app.models", fromlist=["User"]).User).filter_by(email="teste@example.com")).scalar_one()
