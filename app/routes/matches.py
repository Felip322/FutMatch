from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import FriendlyMatchPost, Match, MatchResultConfirmation, SimpleFairPlayReview, Team
from app.services.notification_service import notify
from app.services.badge_service import award_team_badges
from app.services.uniform_service import build_uniform_description, parse_uniform_description
from app.utils.file_upload import save_upload

matches_bp = Blueprint("matches", __name__)


def owned_team_ids():
    return [team.id for team in Team.query.filter_by(owner_id=current_user.id)]


def can_access_match(match):
    if current_user.is_admin:
        return True
    team_ids = owned_team_ids()
    return match.home_team_id in team_ids or match.away_team_id in team_ids


def visible_matches_query():
    query = Match.query
    if current_user.is_admin:
        return query
    team_ids = owned_team_ids()
    if not team_ids:
        return query.filter(False)
    return query.filter((Match.home_team_id.in_(team_ids)) | (Match.away_team_id.in_(team_ids)))


def friendly_post_for_match(match):
    return FriendlyMatchPost.query.filter_by(
        team_id=match.home_team_id,
        match_date=match.match_date,
        start_time=match.start_time,
    ).first()


def attach_match_uniforms(match):
    post = friendly_post_for_match(match)
    accepted_request = None
    if post:
        accepted_request = next((item for item in post.requests if item.id == post.accepted_request_id), None)
        if not accepted_request:
            accepted_request = next((item for item in post.requests if item.status == "Aceita"), None)
    match.friendly_post = post
    match.accepted_request = accepted_request
    match.home_uniform_parts = parse_uniform_description(post.uniform if post else None)
    match.away_uniform_parts = parse_uniform_description(accepted_request.uniform_color if accepted_request else None)
    return match


@matches_bp.route("/matches")
@login_required
def list_matches():
    matches = visible_matches_query().order_by(Match.match_date).all()
    return render_template("matches/list.html", matches=matches)


@matches_bp.route("/matches/<int:id>")
@login_required
def detail(id):
    match = Match.query.get_or_404(id)
    if not can_access_match(match):
        return render_template("errors/403.html"), 403
    attach_match_uniforms(match)
    return render_template("matches/detail.html", match=match)


@matches_bp.route("/matches/<int:id>/uniform", methods=["POST"])
@login_required
def update_uniform(id):
    match = Match.query.get_or_404(id)
    if not can_access_match(match):
        return render_template("errors/403.html"), 403
    attach_match_uniforms(match)
    side = request.form.get("side")
    team_ids = owned_team_ids()
    if side == "home":
        if not current_user.is_admin and match.home_team_id not in team_ids:
            return render_template("errors/403.html"), 403
        if not match.friendly_post:
            flash("Nao encontrei o amistoso original para atualizar o uniforme do mandante.", "danger")
            return redirect(url_for("matches.detail", id=match.id))
        match.friendly_post.uniform = build_uniform_description(request.form)
    elif side == "away":
        if not current_user.is_admin and match.away_team_id not in team_ids:
            return render_template("errors/403.html"), 403
        if not match.accepted_request:
            flash("Nao encontrei a solicitacao aceita para atualizar o uniforme do visitante.", "danger")
            return redirect(url_for("matches.detail", id=match.id))
        match.accepted_request.uniform_color = build_uniform_description(request.form)
    else:
        flash("Lado do uniforme invalido.", "danger")
        return redirect(url_for("matches.detail", id=match.id))
    db.session.commit()
    flash("Uniforme atualizado.", "success")
    return redirect(url_for("matches.detail", id=match.id))


@matches_bp.route("/matches/<int:id>/confirm-result", methods=["GET", "POST"])
@login_required
def confirm_result(id):
    match = Match.query.get_or_404(id)
    team_ids = owned_team_ids()
    if not current_user.is_admin and match.home_team_id not in team_ids and match.away_team_id not in team_ids:
        return render_template("errors/403.html"), 403
    if request.method == "POST":
        happened = request.form.get("happened") == "yes"
        team_id = match.home_team_id if match.home_team_id in team_ids else match.away_team_id
        if current_user.is_admin and request.form.get("team_id"):
            team_id = int(request.form["team_id"])
        existing = MatchResultConfirmation.query.filter_by(match_id=match.id, team_id=team_id).first()
        if existing:
            db.session.delete(existing)
            db.session.flush()
        try:
            proof_image = save_upload(request.files.get("proof_image"), "matches")
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("matches/confirm_result.html", match=match)
        confirmation = MatchResultConfirmation(
            match_id=match.id,
            team_id=team_id,
            happened=happened,
            home_score=int(request.form["home_score"]) if happened else None,
            away_score=int(request.form["away_score"]) if happened else None,
            notes=request.form.get("notes"),
            proof_image=proof_image,
        )
        db.session.add(confirmation)
        db.session.flush()
        confirmations = MatchResultConfirmation.query.filter_by(match_id=match.id).all()
        confirmed_team_ids = {item.team_id for item in confirmations}
        both_teams_confirmed = {match.home_team_id, match.away_team_id}.issubset(confirmed_team_ids)
        if happened:
            matching = all(
                item.happened
                and item.home_score == confirmation.home_score
                and item.away_score == confirmation.away_score
                for item in confirmations
            )
            if both_teams_confirmed and matching:
                match.home_score = confirmation.home_score
                match.away_score = confirmation.away_score
                match.status = "Finalizado"
                match.result_status = "Confirmado"
                match.proof_image = confirmation.proof_image or match.proof_image
                post = FriendlyMatchPost.query.filter_by(team_id=match.home_team_id, match_date=match.match_date, start_time=match.start_time).first()
                if post:
                    post.status = "Realizado"
                award_team_badges(match.home_team)
                award_team_badges(match.away_team)
                flash("Os dois times confirmaram o mesmo placar. Resultado salvo.", "success")
            elif both_teams_confirmed:
                match.result_status = "Divergente"
                match.status = "Em revisao"
                notify(match.home_team.owner_id, "Divergencia no placar", "O placar informado nao bate com o adversario.", "placar_divergente", url_for("matches.detail", id=match.id))
                notify(match.away_team.owner_id, "Divergencia no placar", "O placar informado nao bate com o adversario.", "placar_divergente", url_for("matches.detail", id=match.id))
                flash("Ha divergencia entre os placares. O admin deve revisar.", "warning")
            else:
                match.result_status = "Aguardando adversario"
                other_owner = match.away_team.owner_id if team_id == match.home_team_id else match.home_team.owner_id
                notify(other_owner, "Confirme o placar", "O adversario ja informou o resultado. Confirme para salvar.", "placar_pendente", url_for("matches.confirm_result", id=match.id))
                flash("Sua confirmacao foi salva. Aguardando o outro time.", "success")
        else:
            if both_teams_confirmed and all(not item.happened for item in confirmations):
                match.status = "Nao realizado"
                match.result_status = "Confirmado"
                match.notes = request.form.get("notes") or "Jogo informado como nao realizado pelos dois times."
                post = FriendlyMatchPost.query.filter_by(team_id=match.home_team_id, match_date=match.match_date, start_time=match.start_time).first()
                if post:
                    post.status = "Nao realizado"
                flash("Jogo marcado como nao realizado.", "info")
            elif both_teams_confirmed:
                match.status = "Em revisao"
                match.result_status = "Divergente"
                flash("Ha divergencia sobre a realizacao do jogo. Admin deve revisar.", "warning")
            else:
                match.result_status = "Aguardando adversario"
                flash("Sua confirmacao foi salva. Aguardando o outro time.", "success")
        db.session.commit()
        return redirect(url_for("matches.detail", id=match.id))
    return render_template("matches/confirm_result.html", match=match)


@matches_bp.route("/matches/<int:id>/review", methods=["GET", "POST"])
@login_required
def simple_review(id):
    match = Match.query.get_or_404(id)
    team_ids = owned_team_ids()
    if match.status != "Finalizado":
        flash("Avaliacoes ficam disponiveis apos o resultado final.", "warning")
        return redirect(url_for("matches.detail", id=id))
    if not current_user.is_admin and match.home_team_id not in team_ids and match.away_team_id not in team_ids:
        return render_template("errors/403.html"), 403
    reviewer_team_id = match.home_team_id if match.home_team_id in team_ids else match.away_team_id
    reviewed_team_id = match.away_team_id if reviewer_team_id == match.home_team_id else match.home_team_id
    if request.method == "POST":
        existing = SimpleFairPlayReview.query.filter_by(match_id=match.id, reviewer_team_id=reviewer_team_id, reviewed_team_id=reviewed_team_id).first()
        if existing:
            db.session.delete(existing)
            db.session.flush()
        review = SimpleFairPlayReview(
            match_id=match.id,
            reviewer_team_id=reviewer_team_id,
            reviewed_team_id=reviewed_team_id,
            showed_up=bool(request.form.get("showed_up")),
            punctual=bool(request.form.get("punctual")),
            respected_agreement=bool(request.form.get("respected_agreement")),
            good_behavior=bool(request.form.get("good_behavior")),
            comment=request.form.get("comment"),
        )
        db.session.add(review)
        reviewed_team = Team.query.get(reviewed_team_id)
        score = sum([review.showed_up, review.punctual, review.respected_agreement, review.good_behavior]) / 4 * 5
        reviewed_team.fair_play_score = round(((reviewed_team.fair_play_score or 4) + score) / 2, 2)
        reviewed_team.reliability_score = min(100, round((reviewed_team.reliability_score or 80) + (2 if score >= 4 else -5), 1))
        db.session.commit()
        award_team_badges(reviewed_team)
        flash("Avaliacao fair play salva.", "success")
        return redirect(url_for("matches.detail", id=id))
    return render_template("matches/review.html", match=match, reviewed_team=Team.query.get(reviewed_team_id))


@matches_bp.route("/matches/pending-results")
@login_required
def pending_results():
    team_ids = owned_team_ids()
    query = Match.query.filter(Match.match_date <= date.today(), Match.home_score.is_(None), Match.away_score.is_(None))
    if not current_user.is_admin:
        query = query.filter((Match.home_team_id.in_(team_ids)) | (Match.away_team_id.in_(team_ids)))
    matches = query.order_by(Match.match_date.desc()).all()
    return render_template("matches/pending_results.html", matches=matches)
