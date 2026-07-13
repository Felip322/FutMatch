import sys
from datetime import date, time, timedelta
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db
from app.models import (
    Court,
    CourtAvailability,
    FriendlyMatchHistory,
    FriendlyMatchPost,
    FriendlyMatchRequest,
    Match,
    MatchResultConfirmation,
    Notification,
    SimpleFairPlayReview,
    Team,
    TeamPost,
    User,
)
from app.utils.helpers import slugify


LEGACY_TABLES = [
    "booking",
    "challenge",
    "challenge_history",
    "match_message",
    "match_player",
    "player_availability",
    "player_profile",
    "quick_match",
    "review",
    "team_availability",
    "team_member",
    "team_vacancy",
    "vacancy_application",
]


def user(name, email, password, city="Sao Paulo", admin=False, index=0):
    item = User(
        name=name,
        nickname=name.split()[0],
        email=email,
        phone=f"1199{index:06d}",
        birth_date=date(1994, 1, 1) + timedelta(days=index * 180),
        city=city,
        state="SP",
        neighborhood=["Pinheiros", "Mooca", "Tatuape", "Vila Mariana"][index % 4],
        is_admin=admin,
    )
    item.set_password(password)
    db.session.add(item)
    db.session.flush()
    return item


def drop_legacy_tables():
    if not str(db.engine.url).startswith("sqlite"):
        return
    for table in LEGACY_TABLES:
        db.session.execute(text(f"DROP TABLE IF EXISTS {table}"))
    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        db.drop_all()
        drop_legacy_tables()
        db.create_all()

        admin = user("Administrador FutMatch", "admin@futmatch.local", "Admin123!", admin=True)
        demo = user("Usuario Demo", "usuario@futmatch.local", "Usuario123!", index=1)
        users = [admin, demo]
        for i in range(2, 10):
            users.append(user(f"Responsavel {i:02d}", f"responsavel{i}@futmatch.local", "Usuario123!", index=i))

        teams = []
        names = ["Raio Verde FC", "Atlhetico Norte", "Furia da Quadra", "Bola 10 Futsal", "Unidos do Bairro", "Nova Geracao"]
        for i, name in enumerate(names):
            team = Team(
                name=name,
                short_name="".join(part[0] for part in name.split()[:2]).upper(),
                slug=slugify(name),
                city="Sao Paulo",
                state="SP",
                neighborhood=["Pinheiros", "Mooca", "Tatuape", "Vila Mariana", "Santana", "Ipiranga"][i],
                foundation_year=2012 + i,
                category=["Masculino", "Misto", "Feminino"][i % 3],
                age_group=["Livre", "30+", "Sub-20"][i % 3],
                gender=["Masculino", "Misto", "Feminino"][i % 3],
                skill_level=["Recreativo", "Intermediario", "Competitivo"][i % 3],
                floor_type=["Sintetico", "Madeira", "Cimento"][i % 3],
                description=f"{name} joga com intensidade, organizacao e respeito.",
                whatsapp=f"11988{i}0000",
                home_location=f"Quadra base {i + 1}",
                max_travel_distance=8 + i * 3,
                fair_play_score=4.2 + (i % 4) / 10,
                reliability_score=86 + i * 2,
                attendance_rate=88 + i,
                owner_id=users[i + 1].id,
            )
            db.session.add(team)
            db.session.flush()
            teams.append(team)

        courts = []
        for i in range(4):
            court = Court(
                owner_id=users[i + 2].id,
                name=f"Arena FutMatch {i + 1}",
                slug=f"arena-futmatch-{i + 1}",
                description="Quadra bem localizada com boa estrutura para amistosos.",
                address="Rua do Futsal",
                address_number=str(100 + i),
                city="Sao Paulo",
                state="SP",
                neighborhood=["Pinheiros", "Mooca", "Tatuape", "Vila Mariana"][i],
                zip_code=f"0100{i}-000",
                latitude=-23.55 + i / 100,
                longitude=-46.63 - i / 100,
                floor_type=["Sintetico", "Madeira", "Cimento", "Borracha"][i],
                is_covered=i % 2 == 0,
                size="38x20",
                phone=f"11333{i}0000",
                whatsapp=f"11977{i}0000",
                parking=True,
                locker_room=True,
                shower=True,
                snack_bar=i % 2 == 0,
                bleachers=i % 2 == 1,
                approved=True,
            )
            db.session.add(court)
            db.session.flush()
            courts.append(court)
            for weekday in ("Segunda", "Quarta", "Sexta"):
                db.session.add(CourtAvailability(court_id=court.id, weekday=weekday, start_time=time(18, 0), end_time=time(23, 0)))

        for i in range(4):
            post = FriendlyMatchPost(
                team_id=teams[i].id,
                court_id=courts[i % len(courts)].id,
                match_date=date.today() + timedelta(days=i + 1),
                start_time=time(20 + i % 2, 30),
                location_name=courts[i % len(courts)].name,
                address=f"{courts[i % len(courts)].address}, {courts[i % len(courts)].address_number}",
                city="Sao Paulo",
                state="SP",
                neighborhood=courts[i % len(courts)].neighborhood,
                notes="Buscamos adversario para amistoso organizado.",
                status="Com solicitacoes" if i < 2 else "Aberto",
            )
            db.session.add(post)
            db.session.flush()
            db.session.add(FriendlyMatchHistory(post_id=post.id, user_id=post.team.owner_id, new_status=post.status, description="Amistoso publicado para receber solicitacoes."))
            if i < 2:
                db.session.add(FriendlyMatchRequest(
                    post_id=post.id,
                    requester_team_id=teams[(i + 2) % len(teams)].id,
                    message="Confirmamos horario e local.",
                    confirms_time=True,
                    accepts_location=True,
                    uniform_color="Claro",
                ))

        feed_messages = [
            "Treino forte hoje. Time preparado para amistosos no fim de semana.",
            "Vitoria importante ontem e muito respeito ao adversario. Seguimos evoluindo.",
            "Buscamos adversario de nivel intermediario para sexta a noite.",
            "Uniforme novo chegou. Em breve tem foto oficial do elenco.",
        ]
        for i, message in enumerate(feed_messages):
            db.session.add(TeamPost(
                team_id=teams[i].id,
                user_id=teams[i].owner_id,
                content=message,
                image_url=None,
            ))

        match = Match(
            home_team_id=teams[0].id,
            away_team_id=teams[1].id,
            court_id=courts[0].id,
            match_date=date.today() - timedelta(days=2),
            start_time=time(20, 30),
            status="Finalizado",
            home_score=5,
            away_score=3,
            result_status="Confirmado",
            notes="Partida de demonstracao.",
        )
        db.session.add(match)
        db.session.flush()
        db.session.add_all([
            MatchResultConfirmation(match_id=match.id, team_id=teams[0].id, happened=True, home_score=5, away_score=3),
            MatchResultConfirmation(match_id=match.id, team_id=teams[1].id, happened=True, home_score=5, away_score=3),
            SimpleFairPlayReview(match_id=match.id, reviewer_team_id=teams[0].id, reviewed_team_id=teams[1].id, comment="Jogo limpo e bem combinado."),
            Notification(user_id=demo.id, title="Bem-vindo ao FutMatch", message="Publique um amistoso ou responda uma solicitacao.", notification_type="demo", link="/dashboard"),
        ])

        db.session.commit()
        print("Banco populado. Admin: admin@futmatch.local / Admin123! Usuario: usuario@futmatch.local / Usuario123!")


if __name__ == "__main__":
    main()
