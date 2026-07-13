from app import create_app
from app.extensions import db
from app.models import User
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
        user = db.session.execute(db.select(User).filter_by(email="teste@example.com")).scalar_one()
        assert user
        assert user.is_admin is False
