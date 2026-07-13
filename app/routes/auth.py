from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urljoin

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms.auth_forms import LoginForm, PasswordChangeForm, ProfileForm, RegisterForm
from app.models import Court, FriendlyMatchPost, Team, TeamPost, User

auth_bp = Blueprint("auth", __name__)


def is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def login_blocked():
    blocked_until = session.get("login_blocked_until")
    if not blocked_until:
        return False
    return datetime.now(timezone.utc) < datetime.fromisoformat(blocked_until)


def register_failed_login():
    attempts = session.get("login_attempts", 0) + 1
    session["login_attempts"] = attempts
    if attempts >= 5:
        session["login_blocked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("Este e-mail ja esta cadastrado.", "danger")
        else:
            user = User(
                name=form.name.data,
                email=form.email.data.lower(),
                phone=form.phone.data,
                birth_date=form.birth_date.data,
                city=form.city.data,
                state=form.state.data.upper(),
                neighborhood=form.neighborhood.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Conta criada. Bem-vindo ao FutMatch!", "success")
            return redirect(url_for("dashboard.dashboard"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    form = LoginForm()
    if login_blocked():
        flash("Muitas tentativas. Aguarde alguns minutos antes de tentar novamente.", "danger")
        return render_template("auth/login.html", form=form), 429
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data) and user.is_active:
            session.pop("login_attempts", None)
            session.pop("login_blocked_until", None)
            login_user(user, remember=form.remember.data)
            flash("Entrada confirmada.", "success")
            next_url = request.args.get("next")
            return redirect(next_url if is_safe_url(next_url) else url_for("dashboard.dashboard"))
        register_failed_login()
        flash("E-mail ou senha invalidos.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Voce saiu da sua conta.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("Se o e-mail existir, enviaremos instrucoes de recuperacao simuladas.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("auth/profile.html")


@auth_bp.route("/responsaveis/<int:id>")
def public_user(id):
    user = User.query.get_or_404(id)
    teams = Team.query.filter_by(owner_id=user.id).all()
    courts = Court.query.filter_by(owner_id=user.id).all()
    posts = TeamPost.query.filter_by(user_id=user.id, is_hidden=False).order_by(TeamPost.created_at.desc()).limit(8).all()
    friendlies = FriendlyMatchPost.query.join(Team).filter(Team.owner_id == user.id).order_by(FriendlyMatchPost.created_at.desc()).limit(8).all()
    reputation = round(sum((team.reliability_score or 0) for team in teams) / len(teams), 1) if teams else 0
    return render_template("auth/public_user.html", user=user, teams=teams, courts=courts, posts=posts, friendlies=friendlies, reputation=reputation)


@auth_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    password_form = PasswordChangeForm()
    if form.validate_on_submit() and form.submit.data:
        form.populate_obj(current_user)
        db.session.commit()
        flash("Perfil atualizado.", "success")
        return redirect(url_for("auth.profile"))
    return render_template("auth/edit_profile.html", form=form, password_form=password_form)


@auth_bp.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit() and current_user.check_password(form.current_password.data):
        current_user.set_password(form.password.data)
        db.session.commit()
        flash("Senha alterada.", "success")
    else:
        flash("Nao foi possivel alterar a senha.", "danger")
    return redirect(url_for("auth.edit_profile"))


@auth_bp.route("/profile/delete", methods=["POST"])
@login_required
def delete_account():
    user = current_user._get_current_object()
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash("Conta excluida.", "info")
    return redirect(url_for("main.index"))
