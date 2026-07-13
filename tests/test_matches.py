from datetime import date, time

from app import create_app
from app.extensions import db
from app.models import Match, Team, User
from config import TestConfig


def create_user(email, name):
    user = User(name=name, email=email, city="SAO PAULO", state="SP")
    user.set_password("Senha123!")
    db.session.add(user)
    db.session.flush()
    return user


def test_user_only_sees_own_matches():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        user = create_user("dono@example.com", "Dono")
        other_a = create_user("outro-a@example.com", "Outro A")
        other_b = create_user("outro-b@example.com", "Outro B")
        own_team = Team(name="MEU TIME", slug="meu-time", city="SAO PAULO", state="SP", owner_id=user.id)
        other_team_a = Team(name="OUTRO A", slug="outro-a", city="SAO PAULO", state="SP", owner_id=other_a.id)
        other_team_b = Team(name="OUTRO B", slug="outro-b", city="SAO PAULO", state="SP", owner_id=other_b.id)
        db.session.add_all([own_team, other_team_a, other_team_b])
        db.session.flush()
        own_match = Match(home_team_id=own_team.id, away_team_id=other_team_a.id, match_date=date.today(), start_time=time(20))
        hidden_match = Match(home_team_id=other_team_a.id, away_team_id=other_team_b.id, match_date=date.today(), start_time=time(21))
        db.session.add_all([own_match, hidden_match])
        db.session.commit()
        own_id = own_match.id
        hidden_id = hidden_match.id

    client.post("/login", data={"email": "dono@example.com", "password": "Senha123!"})
    response = client.get("/matches")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "MEU TIME" in body
    assert "OUTRO B" not in body
    assert client.get(f"/matches/{own_id}").status_code == 200
    assert client.get(f"/matches/{hidden_id}").status_code == 403
