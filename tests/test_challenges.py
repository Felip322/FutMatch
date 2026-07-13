from datetime import date, time

from app import create_app
from app.extensions import db
from app.models import FriendlyMatchPost, Team, User
from app.routes.challenges import build_uniform_description, parse_uniform_description
from config import TestConfig


def test_friendly_post_model_persists():
    app = create_app(TestConfig)
    with app.app_context():
        user = User(name="Dono", email="dono@example.com", city="Sao Paulo", state="SP")
        user.set_password("Senha123!")
        db.session.add(user)
        db.session.flush()
        team = Team(name="A", slug="a", city="Sao Paulo", state="SP", owner_id=user.id)
        db.session.add(team)
        db.session.flush()
        db.session.add(FriendlyMatchPost(
            team_id=team.id,
            match_date=date.today(),
            start_time=time(20),
            location_name="Quadra Teste",
            address="Rua Teste, 10",
            city="Sao Paulo",
            state="SP",
        ))
        db.session.commit()
        assert FriendlyMatchPost.query.count() == 1


def test_build_uniform_description_uses_full_uniform_parts():
    uniform = build_uniform_description({
        "shirt_color_hex": "#22c55e",
        "shorts_color_hex": "#111827",
        "socks_color_hex": "#ffffff",
    })

    assert uniform == "Camisa: #22C55E / Calção: #111827 / Meião: #FFFFFF"


def test_parse_uniform_description_returns_visual_parts():
    parts = parse_uniform_description("Camisa: #22C55E / Calção: #111827 / Meião: #FFFFFF")

    assert parts == [
        {"label": "Camisa", "color": "#22C55E"},
        {"label": "Calção", "color": "#111827"},
        {"label": "Meião", "color": "#FFFFFF"},
    ]
