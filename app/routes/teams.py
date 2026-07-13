from datetime import date, time

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms.team_forms import TeamForm
from app.models import Court, DirectFriendlyProposal, FriendlyMatchPost, FriendlyMatchRequest, Match, Team, TeamPost
from app.services.fair_play_service import has_reliability_badge
from app.services.badge_service import award_team_badges, visible_team_badges
from app.services.notification_service import notify
from app.services.statistics_service import last_opponents, ranked_teams, team_record
from app.utils.file_upload import save_upload
from app.utils.helpers import slugify

teams_bp = Blueprint("teams", __name__)


def unique_slug(name):
    base = slugify(name)
    slug = base
    counter = 2
    while Team.query.filter_by(slug=slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def parse_coordinate(value):
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


@teams_bp.route("/teams")
@login_required
def list_teams():
    q = Team.query
    if request.args.get("city"):
        q = q.filter(Team.city.ilike(f"%{request.args['city']}%"))
    teams = q.order_by(Team.created_at.desc()).all()
    return render_template("teams/list.html", teams=teams)


@teams_bp.route("/me/team")
@login_required
def my_team():
    team = Team.query.filter_by(owner_id=current_user.id).first()
    if not team:
        flash("Crie seu time para comecar a marcar amistosos.", "info")
        return redirect(url_for("teams.create_team"))
    return redirect(url_for("teams.detail", slug=team.slug))


@teams_bp.route("/teams/ranking")
@login_required
def ranking():
    q = Team.query
    period = request.args.get("period", "all")
    if request.args.get("city"):
        q = q.filter(Team.city.ilike(f"%{request.args['city']}%"))
    if request.args.get("neighborhood"):
        q = q.filter(Team.neighborhood.ilike(f"%{request.args['neighborhood']}%"))
    rows = ranked_teams(q.all(), period)
    for row in rows:
        row["badges"] = visible_team_badges(row["team"], limit=3)
    highlights = {
        "most_active": max(rows, key=lambda row: row["stats"]["played"], default=None),
        "best_fair_play": max(rows, key=lambda row: row["team"].fair_play_score or 0, default=None),
        "best_balance": max(rows, key=lambda row: row["stats"]["goal_balance"], default=None),
        "neighborhood": rows[0] if rows else None,
    }
    return render_template("teams/ranking.html", rows=rows, highlights=highlights, period=period)


@teams_bp.route("/teams/create", methods=["GET", "POST"])
@login_required
def create_team():
    existing_team = Team.query.filter_by(owner_id=current_user.id).first()
    if existing_team and not current_user.is_admin:
        flash("Cada usuario pode administrar apenas um time nesta versao.", "warning")
        return redirect(url_for("teams.detail", slug=existing_team.slug))
    form = TeamForm()
    if form.validate_on_submit():
        team = Team(owner_id=current_user.id, slug=unique_slug(form.name.data))
        form.populate_obj(team)
        team.home_latitude = parse_coordinate(form.home_latitude.data)
        team.home_longitude = parse_coordinate(form.home_longitude.data)
        try:
            team.logo = save_upload(request.files.get("logo"), "teams") or team.logo
            team.banner_image = save_upload(request.files.get("banner_image"), "teams") or team.banner_image
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("teams/form.html", form=form, title="Criar equipe", team=None)
        db.session.add(team)
        db.session.commit()
        award_team_badges(team)
        flash("Equipe criada.", "success")
        return redirect(url_for("teams.detail", slug=team.slug))
    return render_template("teams/form.html", form=form, title="Criar equipe", team=None)


@teams_bp.route("/teams/<slug>")
@login_required
def detail(slug):
    team = Team.query.filter_by(slug=slug).first_or_404()
    matches_count = Match.query.filter((Match.home_team_id == team.id) | (Match.away_team_id == team.id)).count()
    period = request.args.get("period", "all")
    stats = team_record(team.id, period)
    local_rows = ranked_teams(Team.query.filter_by(city=team.city, neighborhood=team.neighborhood).all(), period)
    local_position = next((index + 1 for index, row in enumerate(local_rows) if row["team"].id == team.id), None)
    activity_level = "Alto" if matches_count >= 8 else "Medio" if matches_count >= 3 else "Inicial"
    team_posts = TeamPost.query.filter_by(team_id=team.id).order_by(TeamPost.created_at.desc()).limit(4).all()
    badges = visible_team_badges(team)
    return render_template(
        "teams/detail.html",
        team=team,
        stats=stats,
        trusted=has_reliability_badge(team, matches_count),
        last_opponents=last_opponents(team.id),
        local_position=local_position,
        activity_level=activity_level,
        team_posts=team_posts,
        period=period,
        badges=badges,
    )


@teams_bp.route("/t/<slug>")
def public_detail(slug):
    team = Team.query.filter_by(slug=slug).first_or_404()
    matches_count = Match.query.filter((Match.home_team_id == team.id) | (Match.away_team_id == team.id)).count()
    stats = team_record(team.id)
    team_posts = TeamPost.query.filter_by(team_id=team.id, is_hidden=False).order_by(TeamPost.created_at.desc()).limit(6).all()
    return render_template("teams/public_detail.html", team=team, stats=stats, trusted=has_reliability_badge(team, matches_count), last_opponents=last_opponents(team.id), team_posts=team_posts, badges=visible_team_badges(team, limit=8))


@teams_bp.route("/teams/<slug>/invite", methods=["GET", "POST"])
@login_required
def invite(slug):
    target = Team.query.filter_by(slug=slug).first_or_404()
    my_team = Team.query.filter_by(owner_id=current_user.id).first()
    if not my_team:
        flash("Crie seu time antes de convidar outro time.", "warning")
        return redirect(url_for("teams.create_team"))
    if target.id == my_team.id:
        flash("Voce nao precisa convidar o proprio time.", "info")
        return redirect(url_for("teams.detail", slug=target.slug))
    my_posts = FriendlyMatchPost.query.filter(
        FriendlyMatchPost.team_id == my_team.id,
        FriendlyMatchPost.status.in_(["Aberto", "Com solicitacoes"]),
    ).order_by(FriendlyMatchPost.match_date, FriendlyMatchPost.start_time).all()
    courts = Court.query.filter_by(approved=True).order_by(Court.name).all()
    if request.method == "POST":
        if request.form.get("mode") == "existing":
            post = FriendlyMatchPost.query.filter_by(id=int(request.form["post_id"]), team_id=my_team.id).first_or_404()
            notify(target.owner_id, "Convite para amistoso", f"{my_team.name} convidou seu time para um amistoso.", "amistoso_solicitado", url_for("challenges.friendly_detail", id=post.id))
            flash("Convite enviado ao responsavel do time.", "success")
        else:
            court_id = int(request.form.get("court_id") or 0) or None
            court = db.session.get(Court, court_id) if court_id else None
            if not court and not all((request.form.get("location_name"), request.form.get("address"), request.form.get("city"), request.form.get("state"))):
                flash("Informe uma quadra cadastrada ou preencha local, endereco, cidade e estado.", "danger")
                return render_template("teams/invite.html", target=target, my_team=my_team, my_posts=my_posts, courts=courts)
            proposal = DirectFriendlyProposal(
                proposer_team_id=my_team.id,
                target_team_id=target.id,
                court_id=court_id,
                match_date=date.fromisoformat(request.form["match_date"]),
                start_time=time.fromisoformat(request.form["start_time"]),
                location_name=court.name if court else request.form.get("location_name"),
                address=court.address if court else request.form.get("address"),
                city=court.city if court else request.form.get("city"),
                state=(court.state if court else request.form.get("state")).upper(),
                neighborhood=court.neighborhood if court else request.form.get("neighborhood"),
                message=request.form.get("message"),
            )
            db.session.add(proposal)
            db.session.flush()
            notify(target.owner_id, "Nova proposta direta", f"{my_team.name} sugeriu data e local para amistoso.", "amistoso_solicitado", url_for("teams.proposal_detail", id=proposal.id))
            db.session.commit()
            flash("Proposta direta enviada ao responsavel do time.", "success")
        return redirect(url_for("teams.detail", slug=target.slug))
    return render_template("teams/invite.html", target=target, my_team=my_team, my_posts=my_posts, courts=courts)


@teams_bp.route("/proposals/<int:id>")
@login_required
def proposal_detail(id):
    proposal = DirectFriendlyProposal.query.get_or_404(id)
    if not current_user.is_admin and current_user.id not in (proposal.proposer_team.owner_id, proposal.target_team.owner_id):
        return render_template("errors/403.html"), 403
    return render_template("teams/proposal_detail.html", proposal=proposal)


@teams_bp.route("/proposals/<int:id>/accept", methods=["POST"])
@login_required
def accept_proposal(id):
    proposal = DirectFriendlyProposal.query.get_or_404(id)
    if proposal.target_team.owner_id != current_user.id and not current_user.is_admin:
        return render_template("errors/403.html"), 403
    proposal.status = "Aceita"
    match = Match(
        home_team_id=proposal.proposer_team_id,
        away_team_id=proposal.target_team_id,
        court_id=proposal.court_id,
        match_date=proposal.match_date,
        start_time=proposal.start_time,
        status="Confirmado",
        notes=f"Proposta direta confirmada em {proposal.location_name}. {proposal.address}",
    )
    db.session.add(match)
    db.session.flush()
    notify(proposal.proposer_team.owner_id, "Proposta aceita", f"{proposal.target_team.name} aceitou o amistoso.", "amistoso_confirmado", url_for("matches.detail", id=match.id))
    db.session.commit()
    flash("Proposta aceita e partida criada.", "success")
    return redirect(url_for("matches.detail", id=match.id))


@teams_bp.route("/proposals/<int:id>/reject", methods=["POST"])
@login_required
def reject_proposal(id):
    proposal = DirectFriendlyProposal.query.get_or_404(id)
    if proposal.target_team.owner_id != current_user.id and not current_user.is_admin:
        return render_template("errors/403.html"), 403
    proposal.status = "Recusada"
    notify(proposal.proposer_team.owner_id, "Proposta recusada", f"{proposal.target_team.name} recusou a proposta direta.", "amistoso_recusado", url_for("teams.proposal_detail", id=proposal.id))
    db.session.commit()
    flash("Proposta recusada.", "info")
    return redirect(url_for("teams.proposal_detail", id=proposal.id))


@teams_bp.route("/teams/<slug>/agenda")
@login_required
def agenda(slug):
    team = Team.query.filter_by(slug=slug).first_or_404()
    if team.owner_id != current_user.id and not current_user.is_admin:
        return render_template("errors/403.html"), 403
    upcoming = Match.query.filter(
        ((Match.home_team_id == team.id) | (Match.away_team_id == team.id)),
        Match.status == "Confirmado",
    ).order_by(Match.match_date.asc()).all()
    pending_posts = FriendlyMatchPost.query.filter_by(team_id=team.id).filter(FriendlyMatchPost.status.in_(["Aberto", "Com solicitacoes"])).order_by(FriendlyMatchPost.match_date.asc()).all()
    pending_requests = FriendlyMatchRequest.query.filter_by(requester_team_id=team.id, status="Pendente").all()
    pending_results = Match.query.filter(
        ((Match.home_team_id == team.id) | (Match.away_team_id == team.id)),
        Match.home_score.is_(None),
        Match.away_score.is_(None),
    ).order_by(Match.match_date.desc()).all()
    history = Match.query.filter(
        ((Match.home_team_id == team.id) | (Match.away_team_id == team.id)),
        Match.status.in_(["Finalizado", "Nao realizado", "Em revisao"]),
    ).order_by(Match.match_date.desc()).limit(12).all()
    return render_template("teams/agenda.html", team=team, upcoming=upcoming, pending_posts=pending_posts, pending_requests=pending_requests, pending_results=pending_results, history=history)


@teams_bp.route("/teams/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit_team(slug):
    team = Team.query.filter_by(slug=slug).first_or_404()
    if team.owner_id != current_user.id and not current_user.is_admin:
        return render_template("errors/403.html"), 403
    form = TeamForm(obj=team)
    if form.validate_on_submit():
        form.populate_obj(team)
        team.home_latitude = parse_coordinate(form.home_latitude.data)
        team.home_longitude = parse_coordinate(form.home_longitude.data)
        try:
            team.logo = save_upload(request.files.get("logo"), "teams") or team.logo
            team.banner_image = save_upload(request.files.get("banner_image"), "teams") or team.banner_image
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("teams/form.html", form=form, title="Editar equipe", team=team)
        db.session.commit()
        award_team_badges(team)
        flash("Equipe atualizada.", "success")
        return redirect(url_for("teams.detail", slug=team.slug))
    return render_template("teams/form.html", form=form, title="Editar equipe", team=team)
