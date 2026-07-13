from flask import Blueprint, jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Notification

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications")
@login_required
def list_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    urgent = [item for item in notifications if item.notification_type in ("placar_pendente", "placar_divergente", "jogo_hoje")]
    normal = [item for item in notifications if item.notification_type in ("amistoso_solicitado", "amistoso_confirmado", "amistoso_recusado", "jogo_amanha")]
    history = [item for item in notifications if item not in urgent and item not in normal]
    return render_template("notifications/list.html", urgent=urgent, normal=normal, history=history)


@notifications_bp.route("/api/notifications")
@login_required
def api_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify({
        "count": len(notifications),
        "items": [{"id": n.id, "title": n.title, "message": n.message, "link": n.link} for n in notifications],
    })


@notifications_bp.route("/api/notifications/<int:id>/read", methods=["POST"])
@login_required
def api_read(id):
    notification = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return jsonify({"ok": True})


@notifications_bp.route("/notifications/<int:id>/read")
@login_required
def read(id):
    notification = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return redirect(notification.link or url_for("notifications.list_notifications"))
