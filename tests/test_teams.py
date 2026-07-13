from app import create_app
from app.extensions import db
from app.models import Team, User
from config import TestConfig


def test_team_slug_is_accessible():
    app = create_app(TestConfig)
    with app.app_context():
        user = User(name="Dono", email="dono@example.com", city="Sao Paulo", state="SP")
        user.set_password("Senha123!")
        db.session.add(user)
        db.session.flush()
        db.session.add(Team(name="Time Teste", slug="time-teste", city="Sao Paulo", state="SP", owner_id=user.id))
        db.session.commit()
        user_id = user.id
    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
    response = client.get("/teams/time-teste")
    assert response.status_code == 200
    assert b"Time Teste" in response.data
