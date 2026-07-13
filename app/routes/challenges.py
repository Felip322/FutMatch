from datetime import date, datetime, time, timedelta
from math import asin, cos, radians, sin, sqrt

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Court, FriendlyMatchHistory, FriendlyMatchPost, FriendlyMatchRequest, Match, Team
from app.services.notification_service import notify
from app.services.badge_service import award_team_badges, visible_friendly_card_badges
from app.services.statistics_service import team_record
from app.services.uniform_service import build_uniform_description, parse_uniform_description

challenges_bp = Blueprint("challenges", __name__)


def current_team():
    return Team.query.filter_by(owner_id=current_user.id).first()


def add_friendly_history(post, new_status, description, previous_status=None):
    db.session.add(FriendlyMatchHistory(
        post_id=post.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        previous_status=previous_status,
        new_status=new_status,
        description=description,
    ))


def time_ranges_overlap(start_a, duration_a, start_b, duration_b):
    base = date(2000, 1, 1)
    a_start = datetime.combine(base, start_a)
    a_end = a_start + timedelta(minutes=duration_a or 60)
    b_start = datetime.combine(base, start_b)
    b_end = b_start + timedelta(minutes=duration_b or 60)
    return a_start < b_end and b_start < a_end


def distance_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    radius = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return round(2 * radius * asin(sqrt(a)), 1)


def court_has_conflict(court_id, match_date, start_time, duration_minutes, ignore_post_id=None):
    if not court_id:
        return False
    busy_statuses = ["Aberto", "Com solicitacoes", "Confirmado"]
    query = FriendlyMatchPost.query.filter(
        FriendlyMatchPost.court_id == court_id,
        FriendlyMatchPost.match_date == match_date,
        FriendlyMatchPost.status.in_(busy_statuses),
    )
    if ignore_post_id:
        query = query.filter(FriendlyMatchPost.id != ignore_post_id)
    return any(time_ranges_overlap(start_time, duration_minutes, post.start_time, post.duration_minutes) for post in query)


@challenges_bp.route("/opponents")
@login_required
def opponents():
    return redirect(url_for("challenges.friendlies"))


@challenges_bp.route("/friendlies")
@login_required
def friendlies():
    team = current_team()
    query = FriendlyMatchPost.query
    if not current_user.is_admin and team:
        query = query.filter(FriendlyMatchPost.team_id != team.id)
    if request.args.get("city"):
        query = query.filter(FriendlyMatchPost.city.ilike(f"%{request.args['city']}%"))
    if request.args.get("neighborhood"):
        query = query.filter(FriendlyMatchPost.neighborhood.ilike(f"%{request.args['neighborhood']}%"))
    if request.args.get("date"):
        query = query.filter(FriendlyMatchPost.match_date == date.fromisoformat(request.args["date"]))
    if request.args.get("time"):
        query = query.filter(FriendlyMatchPost.start_time >= time.fromisoformat(request.args["time"]))
    if request.args.get("status"):
        query = query.filter(FriendlyMatchPost.status == request.args["status"])
    if request.args.get("level"):
        query = query.join(Team).filter(Team.skill_level == request.args["level"])
    if request.args.get("category"):
        query = query.join(Team).filter(Team.category == request.args["category"])
    posts = query.order_by(FriendlyMatchPost.match_date, FriendlyMatchPost.start_time).all()
    if team and team.home_latitude and team.home_longitude:
        for post in posts:
            post.distance_km = distance_km(team.home_latitude, team.home_longitude, post.court.latitude, post.court.longitude) if post.court else None
    for post in posts:
        post.team_badges = visible_friendly_card_badges(post.team, limit=3)
        post.team_card_stats = team_record(post.team_id)
        post.team_cancellations = FriendlyMatchPost.query.filter_by(team_id=post.team_id, status="Cancelado").count()
    map_points = [
        {
            "lat": post.court.latitude,
            "lng": post.court.longitude,
            "title": post.team.name,
            "text": f"{post.location_name} - {post.match_date.strftime('%d/%m')} {post.start_time.strftime('%H:%M')}",
            "route": f"https://www.google.com/maps?q={post.court.latitude},{post.court.longitude}",
        }
        for post in posts
        if post.court and post.court.latitude and post.court.longitude
    ]
    my_posts = FriendlyMatchPost.query.filter_by(team_id=team.id).order_by(FriendlyMatchPost.created_at.desc()).all() if team else []
    my_requests = FriendlyMatchRequest.query.filter_by(requester_team_id=team.id).order_by(FriendlyMatchRequest.created_at.desc()).all() if team else []
    return render_template("challenges/friendlies.html", posts=posts, my_posts=my_posts, my_requests=my_requests, team=team, map_points=map_points)


@challenges_bp.route("/friendlies/create", methods=["GET", "POST"])
@login_required
def create_friendly():
    team = current_team()
    if not team:
        flash("Crie seu time antes de publicar um amistoso.", "warning")
        return redirect(url_for("teams.create_team"))
    courts = Court.query.filter_by(approved=True).order_by(Court.name).all()
    if request.method == "POST":
        court_id = int(request.form.get("court_id") or 0) or None
        selected_court = db.session.get(Court, court_id) if court_id else None
        match_date = date.fromisoformat(request.form["match_date"])
        start_time = time.fromisoformat(request.form["start_time"])
        duration_minutes = int(request.form.get("duration_minutes") or 60)
        if court_has_conflict(court_id, match_date, start_time, duration_minutes):
            flash("Essa quadra ja tem jogo marcado nesse horario. Escolha outro horario ou outra quadra.", "danger")
            return render_template("challenges/friendly_form.html", team=team, courts=courts)
        if not selected_court and not all((request.form.get("location_name"), request.form.get("address"), request.form.get("city"), request.form.get("state"))):
            flash("Informe uma quadra cadastrada ou preencha os dados do local manual.", "danger")
            return render_template("challenges/friendly_form.html", team=team, courts=courts)
        post = FriendlyMatchPost(
            team_id=team.id,
            court_id=court_id,
            match_date=match_date,
            start_time=start_time,
            location_name=selected_court.name if selected_court else request.form.get("location_name"),
            address=selected_court.address if selected_court else request.form.get("address"),
            city=selected_court.city if selected_court else request.form.get("city"),
            state=(selected_court.state if selected_court else request.form.get("state")).upper(),
            neighborhood=selected_court.neighborhood if selected_court else request.form.get("neighborhood"),
            duration_minutes=duration_minutes,
            players_count=int(request.form.get("players_count") or 5),
            tolerance_minutes=int(request.form.get("tolerance_minutes") or 10),
            uniform=build_uniform_description(request.form),
            rules=request.form.get("rules"),
            notes=request.form.get("notes"),
        )
        db.session.add(post)
        db.session.flush()
        add_friendly_history(post, "Aberto", "Amistoso publicado para receber solicitacoes.")
        db.session.commit()
        award_team_badges(team)
        flash("Amistoso publicado. Agora outros times podem solicitar a partida.", "success")
        return redirect(url_for("challenges.friendlies"))
    return render_template("challenges/friendly_form.html", team=team, courts=courts)


@challenges_bp.route("/friendlies/<int:id>")
@login_required
def friendly_detail(id):
    post = FriendlyMatchPost.query.get_or_404(id)
    team = current_team()
    existing_request = FriendlyMatchRequest.query.filter_by(post_id=post.id, requester_team_id=team.id).first() if team else None
    post.uniform_parts = parse_uniform_description(post.uniform)
    for item in post.requests:
        item.uniform_parts = parse_uniform_description(item.uniform_color)
    return render_template("challenges/friendly_detail.html", post=post, team=team, existing_request=existing_request)


@challenges_bp.route("/friendlies/<int:id>/request", methods=["POST"])
@login_required
def request_friendly(id):
    post = FriendlyMatchPost.query.get_or_404(id)
    team = current_team()
    if not team:
        flash("Crie seu time antes de solicitar um amistoso.", "warning")
        return redirect(url_for("teams.create_team"))
    if post.team_id == team.id:
        flash("Seu proprio time ja e o dono deste amistoso.", "warning")
        return redirect(url_for("challenges.friendly_detail", id=id))
    existing = FriendlyMatchRequest.query.filter_by(post_id=post.id, requester_team_id=team.id).first()
    if existing:
        flash("Seu time ja enviou uma solicitacao para este amistoso.", "info")
        return redirect(url_for("challenges.friendly_detail", id=id))
    friendly_request = FriendlyMatchRequest(
        post_id=post.id,
        requester_team_id=team.id,
        message=request.form.get("message"),
        confirms_time=bool(request.form.get("confirms_time")),
        accepts_location=bool(request.form.get("accepts_location")),
        uniform_color=build_uniform_description(request.form),
    )
    db.session.add(friendly_request)
    if post.status == "Aberto":
        previous = post.status
        post.status = "Com solicitacoes"
        add_friendly_history(post, post.status, f"{team.name} enviou uma solicitacao.", previous)
    notify(post.team.owner_id, "Nova solicitacao de amistoso", f"{team.name} quer jogar contra voce.", "amistoso_solicitado", url_for("challenges.friendly_detail", id=post.id))
    db.session.commit()
    award_team_badges(team)
    flash("Solicitacao enviada. O responsavel pelo amistoso vai aceitar ou recusar.", "success")
    return redirect(url_for("challenges.friendlies"))


@challenges_bp.route("/friendlies/<int:id>/uniform", methods=["POST"])
@login_required
def update_friendly_uniform(id):
    post = FriendlyMatchPost.query.get_or_404(id)
    if post.team.owner_id != current_user.id and not current_user.is_admin:
        return render_template("errors/403.html"), 403
    post.uniform = build_uniform_description(request.form)
    add_friendly_history(post, post.status, "Uniforme do time mandante atualizado.", post.status)
    db.session.commit()
    flash("Uniforme do amistoso atualizado.", "success")
    return redirect(url_for("challenges.friendly_detail", id=post.id))


@challenges_bp.route("/friendlies/requests/<int:id>/accept", methods=["POST"])
@login_required
def accept_friendly_request(id):
    friendly_request = FriendlyMatchRequest.query.get_or_404(id)
    post = friendly_request.post
    if post.team.owner_id != current_user.id and not current_user.is_admin:
        return render_template("errors/403.html"), 403
    friendly_request.status = "Aceita"
    previous = post.status
    post.status = "Confirmado"
    post.accepted_request_id = friendly_request.id
    for other in post.requests:
        if other.id != friendly_request.id and other.status == "Pendente":
            other.status = "Recusada"
    match = Match(
        home_team_id=post.team_id,
        away_team_id=friendly_request.requester_team_id,
        court_id=post.court_id,
        match_date=post.match_date,
        start_time=post.start_time,
        status="Confirmado",
        notes=f"Amistoso confirmado em {post.location_name}. {post.address}",
    )
    db.session.add(match)
    db.session.flush()
    add_friendly_history(post, "Confirmado", f"Solicitacao de {friendly_request.requester_team.name} aceita.", previous)
    notify(friendly_request.requester_team.owner_id, "Amistoso confirmado", f"{post.team.name} aceitou jogar contra seu time.", "amistoso_confirmado", url_for("matches.detail", id=match.id))
    db.session.commit()
    flash("Solicitacao aceita e partida criada.", "success")
    return redirect(url_for("challenges.friendly_detail", id=post.id))


@challenges_bp.route("/friendlies/requests/<int:id>/reject", methods=["POST"])
@login_required
def reject_friendly_request(id):
    friendly_request = FriendlyMatchRequest.query.get_or_404(id)
    post = friendly_request.post
    if post.team.owner_id != current_user.id and not current_user.is_admin:
        return render_template("errors/403.html"), 403
    friendly_request.status = "Recusada"
    if not any(item.status == "Pendente" for item in post.requests if item.id != friendly_request.id):
        previous = post.status
        post.status = "Recusado" if post.status == "Com solicitacoes" else post.status
        add_friendly_history(post, post.status, f"Solicitacao de {friendly_request.requester_team.name} recusada.", previous)
    notify(friendly_request.requester_team.owner_id, "Solicitacao recusada", f"{post.team.name} recusou a solicitacao de amistoso.", "amistoso_recusado", url_for("challenges.friendlies"))
    db.session.commit()
    flash("Solicitacao recusada.", "info")
    return redirect(url_for("challenges.friendly_detail", id=post.id))


@challenges_bp.route("/friendlies/<int:id>/cancel", methods=["POST"])
@login_required
def cancel_friendly(id):
    post = FriendlyMatchPost.query.get_or_404(id)
    if post.team.owner_id != current_user.id and not current_user.is_admin:
        return render_template("errors/403.html"), 403
    previous = post.status
    post.status = "Cancelado"
    post.cancellation_reason = request.form.get("reason")
    post.cancellation_notes = request.form.get("notes")
    add_friendly_history(post, "Cancelado", f"Cancelado por motivo: {post.cancellation_reason}.", previous)
    accepted_request = FriendlyMatchRequest.query.get(post.accepted_request_id) if post.accepted_request_id else None
    if accepted_request:
        notify(accepted_request.requester_team.owner_id, "Amistoso cancelado", f"{post.team.name} cancelou o amistoso.", "amistoso_cancelado", url_for("challenges.friendly_detail", id=post.id))
    db.session.commit()
    flash("Amistoso cancelado com motivo registrado.", "info")
    return redirect(url_for("challenges.friendly_detail", id=id))


@challenges_bp.route("/friendlies/<int:id>/receipt")
@login_required
def friendly_receipt(id):
    post = FriendlyMatchPost.query.get_or_404(id)
    accepted_request = FriendlyMatchRequest.query.get(post.accepted_request_id) if post.accepted_request_id else None
    post.uniform_parts = parse_uniform_description(post.uniform)
    if accepted_request:
        accepted_request.uniform_parts = parse_uniform_description(accepted_request.uniform_color)
    return render_template("challenges/friendly_receipt.html", post=post, accepted_request=accepted_request)
