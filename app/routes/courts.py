from math import asin, cos, radians, sin, sqrt

from flask import Blueprint, jsonify, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms.court_forms import CourtForm
from app.models import Court, Team
from app.utils.file_upload import save_upload
from app.utils.helpers import slugify

courts_bp = Blueprint("courts", __name__)


def unique_court_slug(name):
    base = slugify(name)
    slug = base
    counter = 2
    while Court.query.filter_by(slug=slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def parse_coordinate(value):
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def distance_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    radius = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return round(2 * radius * asin(sqrt(a)), 1)


@courts_bp.route("/courts")
@login_required
def list_courts():
    query = Court.query
    if not current_user.is_admin:
        query = query.filter((Court.approved.is_(True)) | (Court.owner_id == current_user.id))
    courts = query.order_by(Court.approved.desc(), Court.created_at.desc()).all()
    team = Team.query.filter_by(owner_id=current_user.id).first()
    if team and team.home_latitude and team.home_longitude:
        for court in courts:
            court.distance_km = distance_km(team.home_latitude, team.home_longitude, court.latitude, court.longitude)
    return render_template("courts/list.html", courts=courts)


@courts_bp.route("/courts/create", methods=["GET", "POST"])
@login_required
def create_court():
    form = CourtForm()
    if form.validate_on_submit():
        court = Court(owner_id=current_user.id, slug=unique_court_slug(form.name.data))
        form.populate_obj(court)
        try:
            court.cover_image = save_upload(request.files.get("cover_image"), "courts")
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("courts/form.html", form=form, title="Cadastrar quadra")
        court.latitude = parse_coordinate(form.latitude.data)
        court.longitude = parse_coordinate(form.longitude.data)
        db.session.add(court)
        db.session.commit()
        flash("Quadra cadastrada e enviada para aprovacao.", "success")
        return redirect(url_for("courts.detail", slug=court.slug))
    return render_template("courts/form.html", form=form, title="Cadastrar quadra")


@courts_bp.route("/courts/<slug>")
@login_required
def detail(slug):
    court = Court.query.filter_by(slug=slug).first_or_404()
    if not court.approved and court.owner_id != current_user.id and not current_user.is_admin:
        return render_template("errors/403.html"), 403
    return render_template("courts/detail.html", court=court)


@courts_bp.route("/q/<slug>")
def public_detail(slug):
    court = Court.query.filter_by(slug=slug, approved=True).first_or_404()
    return render_template("courts/public_detail.html", court=court)


@courts_bp.route("/courts/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit_court(slug):
    court = Court.query.filter_by(slug=slug).first_or_404()
    if court.owner_id != current_user.id and not current_user.is_admin:
        return render_template("errors/403.html"), 403
    form = CourtForm(obj=court)
    if form.validate_on_submit():
        form.populate_obj(court)
        try:
            court.cover_image = save_upload(request.files.get("cover_image"), "courts") or court.cover_image
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("courts/form.html", form=form, title="Editar quadra")
        court.latitude = parse_coordinate(form.latitude.data)
        court.longitude = parse_coordinate(form.longitude.data)
        db.session.commit()
        flash("Quadra atualizada.", "success")
        return redirect(url_for("courts.detail", slug=court.slug))
    return render_template("courts/form.html", form=form, title="Editar quadra")

@courts_bp.route("/api/courts/<int:id>/availability")
@login_required
def api_availability(id):
    court = Court.query.get_or_404(id)
    return jsonify([{"weekday": a.weekday, "start": a.start_time.strftime("%H:%M"), "end": a.end_time.strftime("%H:%M")} for a in court.availabilities])
