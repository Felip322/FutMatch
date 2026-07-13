from datetime import date, time

from app import create_app
from app.extensions import db
from app.models import FriendlyMatchPost, FriendlyMatchRequest, Match, Team, User
from app.routes.matches import attach_match_uniforms
from app.services.uniform_service import build_uniform_description, parse_uniform_description
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


def test_owner_can_update_friendly_uniform_colors():
    app = create_app(TestConfig)
    with app.app_context():
        user = User(name="Dono", email="uniforme@example.com", city="Sao Paulo", state="SP")
        user.set_password("Senha123!")
        db.session.add(user)
        db.session.flush()
        team = Team(name="Uniforme FC", slug="uniforme-fc", city="Sao Paulo", state="SP", owner_id=user.id)
        db.session.add(team)
        db.session.flush()
        post = FriendlyMatchPost(
            team_id=team.id,
            match_date=date.today(),
            start_time=time(20),
            location_name="Quadra Teste",
            address="Rua Teste, 10",
            city="Sao Paulo",
            state="SP",
        )
        db.session.add(post)
        db.session.commit()
        user_id = user.id
        post_id = post.id

    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)

    response = client.post(f"/friendlies/{post_id}/uniform", data={
        "shirt_color_hex": "#ff0000",
        "shorts_color_hex": "#000000",
        "socks_color_hex": "#ffffff",
    })

    assert response.status_code == 302
    with app.app_context():
        post = db.session.get(FriendlyMatchPost, post_id)
        assert post.uniform == "Camisa: #FF0000 / Calção: #000000 / Meião: #FFFFFF"


def test_match_detail_uniforms_come_from_confirmed_friendly():
    app = create_app(TestConfig)
    with app.app_context():
        home_owner = User(name="Mandante", email="mandante@example.com", city="Sao Paulo", state="SP")
        away_owner = User(name="Visitante", email="visitante@example.com", city="Sao Paulo", state="SP")
        home_owner.set_password("Senha123!")
        away_owner.set_password("Senha123!")
        db.session.add_all([home_owner, away_owner])
        db.session.flush()
        home = Team(name="Mandante FC", slug="mandante-fc", city="Sao Paulo", state="SP", owner_id=home_owner.id)
        away = Team(name="Visitante FC", slug="visitante-fc", city="Sao Paulo", state="SP", owner_id=away_owner.id)
        db.session.add_all([home, away])
        db.session.flush()
        post = FriendlyMatchPost(
            team_id=home.id,
            match_date=date.today(),
            start_time=time(20),
            location_name="Quadra Teste",
            address="Rua Teste, 10",
            city="Sao Paulo",
            state="SP",
            uniform="Camisa: #FF0000 / Calção: #000000 / Meião: #FFFFFF",
        )
        db.session.add(post)
        db.session.flush()
        request = FriendlyMatchRequest(
            post_id=post.id,
            requester_team_id=away.id,
            status="Aceita",
            uniform_color="Camisa: #0000FF / Calção: #FFFFFF / Meião: #0000FF",
        )
        db.session.add(request)
        db.session.flush()
        post.accepted_request_id = request.id
        match = Match(home_team_id=home.id, away_team_id=away.id, match_date=post.match_date, start_time=post.start_time)
        db.session.add(match)
        db.session.commit()

        attach_match_uniforms(match)

        assert match.home_uniform_parts[0] == {"label": "Camisa", "color": "#FF0000"}
        assert match.away_uniform_parts[0] == {"label": "Camisa", "color": "#0000FF"}
