from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import Badge, Court, FriendlyMatchPost, Match, Report, SimpleFairPlayReview, Team, TeamBadge, TeamPost, User
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("")
@login_required
@admin_required
def index():
    stats = {
        "users": User.query.count(),
        "teams": Team.query.count(),
        "courts": Court.query.count(),
        "matches": Match.query.count(),
        "reports": Report.query.filter_by(status="Pendente").count(),
        "blocked": User.query.filter_by(is_active=False).count(),
        "friendlies": FriendlyMatchPost.query.count(),
        "missing_scores": Match.query.filter(Match.home_score.is_(None), Match.away_score.is_(None)).count(),
        "score_conflicts": Match.query.filter_by(result_status="Divergente").count(),
        "recent_images": TeamPost.query.filter((TeamPost.image_path.isnot(None)) | (TeamPost.image_url.isnot(None))).count(),
    }
    return render_template("admin/index.html", stats=stats)


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    return render_template("admin/users.html", users=User.query.order_by(User.created_at.desc()).all())


@admin_bp.route("/users/<int:id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    flash("Status do usuario atualizado.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/teams")
@login_required
@admin_required
def teams():
    return render_template("admin/teams.html", teams=Team.query.all())


@admin_bp.route("/courts")
@login_required
@admin_required
def courts():
    return render_template("admin/courts.html", courts=Court.query.all())


@admin_bp.route("/courts/<int:id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_court(id):
    court = Court.query.get_or_404(id)
    court.approved = True
    db.session.commit()
    flash("Quadra aprovada.", "success")
    return redirect(url_for("admin.courts"))


@admin_bp.route("/reviews")
@login_required
@admin_required
def reviews():
    return render_template("admin/reviews.html", reviews=SimpleFairPlayReview.query.all())


@admin_bp.route("/reports")
@login_required
@admin_required
def reports():
    reports = Report.query.order_by(Report.status.asc(), Report.created_at.desc()).all()
    post_map = {post.id: post for post in TeamPost.query.filter(TeamPost.id.in_([item.target_id for item in reports if item.target_type == "team_post"])).all()}
    return render_template("admin/reports.html", reports=reports, post_map=post_map)


@admin_bp.route("/reports/<int:id>/resolve", methods=["POST"])
@login_required
@admin_required
def resolve_report(id):
    report = Report.query.get_or_404(id)
    action = request.form.get("action")
    if report.target_type == "team_post":
        post = TeamPost.query.get(report.target_id)
        if post and action == "hide":
            post.is_hidden = True
        if post and action == "remove_image":
            post.image_path = None
            post.image_url = None
    report.status = "Resolvida"
    db.session.commit()
    flash("Denuncia resolvida.", "success")
    return redirect(url_for("admin.reports"))


@admin_bp.route("/media")
@login_required
@admin_required
def media():
    posts = TeamPost.query.filter((TeamPost.image_path.isnot(None)) | (TeamPost.image_url.isnot(None))).order_by(TeamPost.created_at.desc()).limit(60).all()
    courts_with_images = Court.query.filter(Court.cover_image.isnot(None)).order_by(Court.created_at.desc()).limit(40).all()
    courts_pending_image = Court.query.filter(Court.cover_image.is_(None)).order_by(Court.created_at.desc()).limit(40).all()
    return render_template("admin/media.html", posts=posts, courts_with_images=courts_with_images, courts_pending_image=courts_pending_image)


@admin_bp.route("/badges")
@login_required
@admin_required
def badges():
    catalog = Badge.query.order_by(Badge.category, Badge.sort_order).all()
    awarded = TeamBadge.query.order_by(TeamBadge.awarded_at.desc()).limit(80).all()
    return render_template("admin/badges.html", catalog=catalog, awarded=awarded)


@admin_bp.route("/friendlies")
@login_required
@admin_required
def friendlies():
    posts = FriendlyMatchPost.query.order_by(FriendlyMatchPost.created_at.desc()).all()
    return render_template("admin/friendlies.html", posts=posts)


@admin_bp.route("/matches-review")
@login_required
@admin_required
def matches_review():
    matches = Match.query.filter((Match.result_status == "Divergente") | (Match.home_score.is_(None) & Match.away_score.is_(None))).order_by(Match.match_date.desc()).all()
    return render_template("admin/matches_review.html", matches=matches)
