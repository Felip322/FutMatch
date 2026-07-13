from datetime import datetime, time, timedelta, timezone

from flask import has_request_context, session

from app.extensions import db
from app.models import Badge, Court, FriendlyMatchPost, FriendlyMatchRequest, Match, MatchResultConfirmation, SimpleFairPlayReview, Team, TeamBadge, TeamPost


BADGE_DEFINITIONS = [
    ("verified_team", "Time Verificado", "Perfil com escudo, cidade, responsável e contato.", "Uso da plataforma", "badge-platform", 10),
    ("active_team", "Time Ativo", "Publicou ou solicitou amistosos recentemente.", "Uso da plataforma", "badge-platform", 20),
    ("organizer", "Organizador", "Marcou vários amistosos pela plataforma.", "Uso da plataforma", "badge-platform", 30),
    ("futmatch_veteran", "Veterano FutMatch", "Time com histórico consistente na plataforma.", "Uso da plataforma", "badge-platform", 40),
    ("first_match", "Primeira Partida", "Realizou o primeiro jogo confirmado.", "Partidas", "badge-match", 100),
    ("matches_5", "5 Jogos Realizados", "Alcançou 5 jogos confirmados.", "Partidas", "badge-match", 110),
    ("matches_10", "10 Jogos Realizados", "Alcançou 10 jogos confirmados.", "Partidas", "badge-match", 120),
    ("matches_25", "25 Jogos Realizados", "Alcançou 25 jogos confirmados.", "Partidas", "badge-match", 130),
    ("matches_50", "50 Jogos Realizados", "Alcançou 50 jogos confirmados.", "Partidas", "badge-match", 140),
    ("first_win", "Primeira Vitória", "Venceu a primeira partida.", "Vitórias", "badge-win", 200),
    ("wins_5", "5 Vitórias", "Alcançou 5 vitórias.", "Vitórias", "badge-win", 210),
    ("wins_10", "10 Vitórias", "Alcançou 10 vitórias.", "Vitórias", "badge-win", 220),
    ("win_streak_3", "Sequência de 3 Vitórias", "Venceu 3 jogos seguidos.", "Vitórias", "badge-win", 230),
    ("win_streak_5", "Sequência de 5 Vitórias", "Venceu 5 jogos seguidos.", "Vitórias", "badge-win", 240),
    ("trusted_team", "Time Confiável", "Alta confiança e bom histórico.", "Fair Play", "badge-fairplay", 300),
    ("fair_play_gold", "Fair Play Ouro", "Nota alta nas avaliações.", "Fair Play", "badge-fairplay", 310),
    ("punctuality", "Pontualidade", "Boa avaliação de pontualidade.", "Fair Play", "badge-fairplay", 320),
    ("no_cancellations", "Sem Cancelamentos", "Sequência de jogos sem cancelamento.", "Fair Play", "badge-fairplay", 330),
    ("honest_score", "Placar Honesto", "Confirma placares corretamente.", "Fair Play", "badge-fairplay", 340),
    ("complete_profile", "Perfil Completo", "Perfil do time bem preenchido.", "Comunidade", "badge-community", 400),
    ("active_feed", "Feed Ativo", "Publica fotos ou posts do time.", "Comunidade", "badge-community", 410),
    ("good_host", "Bom Anfitrião", "Publica amistosos e recebe adversários.", "Comunidade", "badge-community", 420),
    ("court_partner", "Parceiro de Quadra", "Cadastra quadras úteis para a comunidade.", "Comunidade", "badge-community", 430),
    ("event_derby_day", "Derby Day", "Participou de um confronto de bairro.", "Eventos especiais", "badge-event", 500),
    ("event_night_warrior", "Guerreiro da Noite", "Marcação frequente de jogos noturnos.", "Eventos especiais", "badge-event", 510),
    ("event_clean_sheet", "Muralha", "Venceu uma partida sem sofrer gols.", "Eventos especiais", "badge-event", 520),
]


def ensure_badges():
    for code, name, description, category, icon, sort_order in BADGE_DEFINITIONS:
        badge = Badge.query.filter_by(code=code).first()
        if not badge:
            db.session.add(Badge(code=code, name=name, description=description, category=category, icon=icon, sort_order=sort_order))
        else:
            badge.name = name
            badge.description = description
            badge.category = category
            badge.icon = icon
            badge.sort_order = sort_order
            badge.active = True
    db.session.commit()


def team_matches(team_id):
    return Match.query.filter(
        ((Match.home_team_id == team_id) | (Match.away_team_id == team_id)),
        Match.home_score.isnot(None),
        Match.away_score.isnot(None),
    ).order_by(Match.match_date.asc()).all()


def match_numbers(team_id):
    wins = clean_sheet_wins = 0
    streak = best_streak = 0
    for match in team_matches(team_id):
        own = match.home_score if match.home_team_id == team_id else match.away_score
        other = match.away_score if match.home_team_id == team_id else match.home_score
        if own > other:
            wins += 1
            streak += 1
            best_streak = max(best_streak, streak)
            if other == 0:
                clean_sheet_wins += 1
        else:
            streak = 0
    return {"played": len(team_matches(team_id)), "wins": wins, "best_streak": best_streak, "clean_sheet_wins": clean_sheet_wins}


def qualifies(team, code):
    now = datetime.now(timezone.utc)
    numbers = match_numbers(team.id)
    posts_count = FriendlyMatchPost.query.filter_by(team_id=team.id).count()
    requests_count = FriendlyMatchRequest.query.filter_by(requester_team_id=team.id).count()
    feed_count = TeamPost.query.filter_by(team_id=team.id, is_hidden=False).count()
    courts_count = Court.query.filter_by(owner_id=team.owner_id, approved=True).count()
    recent_posts = FriendlyMatchPost.query.filter(FriendlyMatchPost.team_id == team.id, FriendlyMatchPost.created_at >= now - timedelta(days=30)).count()
    recent_requests = FriendlyMatchRequest.query.filter(FriendlyMatchRequest.requester_team_id == team.id, FriendlyMatchRequest.created_at >= now - timedelta(days=30)).count()
    cancellations = FriendlyMatchPost.query.filter_by(team_id=team.id, status="Cancelado").count()
    divergent = Match.query.filter(
        ((Match.home_team_id == team.id) | (Match.away_team_id == team.id)),
        Match.result_status == "Divergente",
    ).count()
    punctual_reviews = SimpleFairPlayReview.query.filter_by(reviewed_team_id=team.id, punctual=True).count()
    confirmations = MatchResultConfirmation.query.filter_by(team_id=team.id).count()
    fields_complete = all((team.name, team.logo, team.city, team.owner_id, team.whatsapp or team.owner.phone))
    profile_complete = all((team.name, team.short_name, team.logo, team.banner_image, team.city, team.state, team.neighborhood, team.description, team.whatsapp))

    rules = {
        "verified_team": fields_complete,
        "active_team": recent_posts + recent_requests >= 1,
        "organizer": posts_count >= 5,
        "futmatch_veteran": numbers["played"] >= 10 or posts_count >= 10,
        "first_match": numbers["played"] >= 1,
        "matches_5": numbers["played"] >= 5,
        "matches_10": numbers["played"] >= 10,
        "matches_25": numbers["played"] >= 25,
        "matches_50": numbers["played"] >= 50,
        "first_win": numbers["wins"] >= 1,
        "wins_5": numbers["wins"] >= 5,
        "wins_10": numbers["wins"] >= 10,
        "win_streak_3": numbers["best_streak"] >= 3,
        "win_streak_5": numbers["best_streak"] >= 5,
        "trusted_team": (team.reliability_score or 0) >= 90 and numbers["played"] >= 3,
        "fair_play_gold": (team.fair_play_score or 0) >= 4.7,
        "punctuality": punctual_reviews >= 3,
        "no_cancellations": numbers["played"] >= 5 and cancellations == 0,
        "honest_score": confirmations >= 5 and divergent == 0,
        "complete_profile": profile_complete,
        "active_feed": feed_count >= 3,
        "good_host": posts_count >= 3 and FriendlyMatchRequest.query.join(FriendlyMatchPost).filter(FriendlyMatchPost.team_id == team.id).count() >= 3,
        "court_partner": courts_count >= 1,
        "event_derby_day": Match.query.filter(
            ((Match.home_team_id == team.id) | (Match.away_team_id == team.id)),
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
        ).count() >= 1,
        "event_night_warrior": FriendlyMatchPost.query.filter(FriendlyMatchPost.team_id == team.id, FriendlyMatchPost.start_time >= time(20, 0)).count() >= 3,
        "event_clean_sheet": numbers["clean_sheet_wins"] >= 1,
    }
    return rules.get(code, False)


def award_team_badges(team):
    ensure_badges()
    awarded_codes = {item.badge.code for item in TeamBadge.query.filter_by(team_id=team.id).all()}
    awarded_now = []
    for badge in Badge.query.filter_by(active=True).order_by(Badge.sort_order).all():
        if badge.code not in awarded_codes and qualifies(team, badge.code):
            db.session.add(TeamBadge(team_id=team.id, badge_id=badge.id, source="automatico"))
            awarded_now.append(badge)
    if awarded_now:
        db.session.commit()
        queue_achievement_overlay(awarded_now)
    return awarded_now


def visible_team_badges(team, limit=None):
    award_team_badges(team)
    query = TeamBadge.query.join(Badge).filter(TeamBadge.team_id == team.id, Badge.active.is_(True)).order_by(Badge.sort_order.asc(), TeamBadge.awarded_at.desc())
    return query.limit(limit).all() if limit else query.all()


def visible_friendly_card_badges(team, limit=3):
    priority_codes = {
        "trusted_team": 10,
        "fair_play_gold": 20,
        "punctuality": 30,
        "no_cancellations": 40,
        "honest_score": 50,
        "verified_team": 60,
        "active_team": 70,
        "organizer": 80,
        "good_host": 90,
        "court_partner": 100,
        "matches_5": 110,
        "wins_5": 120,
    }
    confusing_on_friendly_card = {"first_match", "first_win"}
    badges = visible_team_badges(team)
    preferred = [item for item in badges if item.badge.code in priority_codes]
    preferred.sort(key=lambda item: priority_codes[item.badge.code])
    fallback = [item for item in badges if item.badge.code not in priority_codes and item.badge.code not in confusing_on_friendly_card]
    return (preferred + fallback)[:limit]


def queue_achievement_overlay(badges):
    if not has_request_context():
        return
    queued = session.get("awarded_badges", [])
    existing_codes = {item["code"] for item in queued}
    for badge in badges:
        if badge.code in existing_codes:
            continue
        queued.append({
            "code": badge.code,
            "name": badge.name,
            "description": badge.description,
            "category": badge.category,
            "icon": badge.icon,
        })
    session["awarded_badges"] = queued[-6:]
