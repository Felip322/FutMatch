from datetime import date, timedelta

from flask import Blueprint, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Court, FriendlyMatchPost, FriendlyMatchRequest, Match, Notification, Team, TeamPost
from app.services.notification_service import notify

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        teams = Team.query.all()
    else:
        teams = Team.query.filter_by(owner_id=current_user.id).all()
    team_ids = [team.id for team in teams]
    matches = Match.query.filter(
        (Match.home_team_id.in_(team_ids)) | (Match.away_team_id.in_(team_ids))
    ).order_by(Match.match_date.asc()).limit(5).all() if team_ids else []
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    urgent_notifications = [item for item in notifications if item.notification_type in ("placar_pendente", "placar_divergente", "jogo_hoje")]
    normal_notifications = [item for item in notifications if item.notification_type in ("amistoso_solicitado", "amistoso_confirmado", "amistoso_recusado", "jogo_amanha")]
    history_notifications = [item for item in notifications if item not in urgent_notifications and item not in normal_notifications]
    friendly_posts = FriendlyMatchPost.query.filter(FriendlyMatchPost.team_id.in_(team_ids)).order_by(FriendlyMatchPost.created_at.desc()).limit(5).all() if team_ids else []
    friendly_requests = FriendlyMatchRequest.query.join(FriendlyMatchPost).filter(FriendlyMatchPost.team_id.in_(team_ids)).order_by(FriendlyMatchRequest.created_at.desc()).limit(8).all() if team_ids else []
    sent_friendly_requests = FriendlyMatchRequest.query.filter(FriendlyMatchRequest.requester_team_id.in_(team_ids)).order_by(FriendlyMatchRequest.created_at.desc()).limit(5).all() if team_ids else []
    pending_results = Match.query.filter(Match.match_date <= date.today(), Match.home_score.is_(None), Match.away_score.is_(None))
    if not current_user.is_admin:
        pending_results = pending_results.filter((Match.home_team_id.in_(team_ids)) | (Match.away_team_id.in_(team_ids)))
    pending_results = pending_results.order_by(Match.match_date.desc()).limit(6).all()
    for match in pending_results:
        link = url_for("matches.confirm_result", id=match.id)
        existing = Notification.query.filter_by(user_id=current_user.id, link=link, notification_type="placar_pendente").first()
        if not existing:
            notify(current_user.id, "O jogo aconteceu?", f"Informe se {match.home_team.name} x {match.away_team.name} foi realizado e registre o placar.", "placar_pendente", link)
    for match in matches:
        if match.match_date in (date.today(), date.today() + timedelta(days=1)):
            kind = "jogo_hoje" if match.match_date == date.today() else "jogo_amanha"
            title = "Jogo hoje" if kind == "jogo_hoje" else "Jogo amanha"
            link = url_for("matches.detail", id=match.id)
            existing = Notification.query.filter_by(user_id=current_user.id, link=link, notification_type=kind).first()
            if not existing:
                notify(current_user.id, title, f"{match.home_team.name} x {match.away_team.name} as {match.start_time.strftime('%H:%M')}.", kind, link)
    db.session.commit()
    activity_items = []
    for post in TeamPost.query.order_by(TeamPost.created_at.desc()).limit(6).all():
        activity_items.append({
            "kind": "post",
            "icon": "bi-images",
            "title": f"{post.team.name} publicou no feed",
            "text": post.content[:120],
            "date": post.created_at,
            "link": url_for("feed.feed"),
        })
    for post in FriendlyMatchPost.query.order_by(FriendlyMatchPost.created_at.desc()).limit(6).all():
        activity_items.append({
            "kind": "friendly",
            "icon": "bi-calendar-plus",
            "title": f"{post.team.name} publicou amistoso",
            "text": f"{post.match_date.strftime('%d/%m')} as {post.start_time.strftime('%H:%M')} em {post.location_name}",
            "date": post.created_at,
            "link": url_for("challenges.friendly_detail", id=post.id),
        })
    for match in Match.query.filter_by(result_status="Confirmado").order_by(Match.created_at.desc()).limit(4).all():
        activity_items.append({
            "kind": "score",
            "icon": "bi-trophy",
            "title": f"{match.home_team.name} confirmou placar",
            "text": f"{match.home_team.name} {match.home_score} x {match.away_score} {match.away_team.name}",
            "date": match.created_at,
            "link": url_for("matches.detail", id=match.id),
        })
    for court in Court.query.filter_by(approved=True).order_by(Court.created_at.desc()).limit(4).all():
        activity_items.append({
            "kind": "court",
            "icon": "bi-geo-alt",
            "title": f"{court.name} foi cadastrada",
            "text": f"{court.city}{', ' + court.neighborhood if court.neighborhood else ''}",
            "date": court.created_at,
            "link": url_for("courts.detail", slug=court.slug),
        })
    activity_items = sorted(activity_items, key=lambda item: item["date"], reverse=True)[:10]
    today = date.today()
    if not current_user.is_admin and not team_ids:
        week_matches = []
    else:
        week_matches_query = Match.query.filter(
            Match.match_date >= today,
            Match.match_date <= today + timedelta(days=7),
        )
        if not current_user.is_admin:
            week_matches_query = week_matches_query.filter((Match.home_team_id.in_(team_ids)) | (Match.away_team_id.in_(team_ids)))
        week_matches = week_matches_query.order_by(Match.match_date, Match.start_time).limit(8).all()
    calendar_days = []
    for index in range(7):
        day = today + timedelta(days=index)
        calendar_days.append({
            "date": day,
            "label": "Hoje" if index == 0 else "Amanha" if index == 1 else day.strftime("%a"),
            "matches": [match for match in week_matches if match.match_date == day],
            "pending": [match for match in pending_results if match.match_date == day],
        })
    return render_template(
        "dashboard/index.html",
        teams=teams,
        matches=matches,
        notifications=notifications,
        urgent_notifications=urgent_notifications,
        normal_notifications=normal_notifications,
        history_notifications=history_notifications,
        activity_items=activity_items,
        week_matches=week_matches,
        calendar_days=calendar_days,
        friendly_posts=friendly_posts,
        friendly_requests=friendly_requests,
        sent_friendly_requests=sent_friendly_requests,
        pending_results=pending_results,
    )
