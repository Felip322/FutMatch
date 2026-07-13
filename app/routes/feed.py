from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Report, Team, TeamPost, TeamPostComment, TeamPostLike
from app.services.badge_service import award_team_badges
from app.utils.file_upload import save_upload

feed_bp = Blueprint("feed", __name__)


def current_team():
    return Team.query.filter_by(owner_id=current_user.id).first()


@feed_bp.route("/feed")
@login_required
def feed():
    posts = TeamPost.query.order_by(TeamPost.likes_count.desc(), TeamPost.comments_count.desc(), TeamPost.created_at.desc()).limit(60).all()
    posts = [post for post in posts if not post.is_hidden or current_user.is_admin]
    team = current_team()
    return render_template("feed/index.html", posts=posts, team=team)


@feed_bp.route("/feed/posts", methods=["POST"])
@login_required
def create_post():
    team = current_team()
    if not team:
        flash("Crie seu time antes de publicar no feed.", "warning")
        return redirect(url_for("teams.create_team"))
    content = (request.form.get("content") or "").strip()
    image_url = (request.form.get("image_url") or "").strip()
    try:
        image_path = save_upload(request.files.get("image"), "feed")
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("feed.feed"))
    if not content:
        flash("Escreva uma mensagem para publicar.", "danger")
        return redirect(url_for("feed.feed"))
    db.session.add(TeamPost(team_id=team.id, user_id=current_user.id, content=content[:1000], image_url=image_url[:500] or None, image_path=image_path))
    db.session.commit()
    award_team_badges(team)
    flash("Post publicado no feed dos times.", "success")
    return redirect(url_for("feed.feed"))


@feed_bp.route("/feed/posts/<int:id>/like", methods=["POST"])
@login_required
def like_post(id):
    post = TeamPost.query.get_or_404(id)
    existing = TeamPostLike.query.filter_by(post_id=post.id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        post.likes_count = max(0, (post.likes_count or 0) - 1)
    else:
        db.session.add(TeamPostLike(post_id=post.id, user_id=current_user.id))
        post.likes_count = (post.likes_count or 0) + 1
    db.session.commit()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "likes": post.likes_count})
    return redirect(url_for("feed.feed"))


@feed_bp.route("/feed/posts/<int:id>/comments", methods=["POST"])
@login_required
def comment_post(id):
    post = TeamPost.query.get_or_404(id)
    content = (request.form.get("content") or "").strip()
    if content:
        comment = TeamPostComment(post_id=post.id, user_id=current_user.id, content=content[:500])
        db.session.add(comment)
        post.comments_count = (post.comments_count or 0) + 1
        db.session.commit()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": True, "comments": post.comments_count, "author": current_user.display_name, "content": comment.content})
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": False}), 400
    return redirect(url_for("feed.feed"))


@feed_bp.route("/feed/posts/<int:id>/hide", methods=["POST"])
@login_required
def hide_post(id):
    if not current_user.is_admin:
        return render_template("errors/403.html"), 403
    post = TeamPost.query.get_or_404(id)
    post.is_hidden = not post.is_hidden
    db.session.commit()
    flash("Moderacao aplicada ao post.", "success")
    return redirect(url_for("feed.feed"))


@feed_bp.route("/feed/posts/<int:id>/remove-image", methods=["POST"])
@login_required
def remove_image(id):
    if not current_user.is_admin:
        return render_template("errors/403.html"), 403
    post = TeamPost.query.get_or_404(id)
    post.image_path = None
    post.image_url = None
    db.session.commit()
    flash("Imagem removida do post.", "success")
    return redirect(url_for("feed.feed"))


@feed_bp.route("/feed/posts/<int:id>/report", methods=["POST"])
@login_required
def report_post(id):
    post = TeamPost.query.get_or_404(id)
    db.session.add(Report(
        reporter_id=current_user.id,
        target_type="team_post",
        target_id=post.id,
        reason=request.form.get("reason") or "conteudo inadequado",
        description=request.form.get("description"),
    ))
    db.session.commit()
    flash("Denuncia enviada para revisao do admin.", "success")
    return redirect(url_for("feed.feed"))
