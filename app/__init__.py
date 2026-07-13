from flask import Flask, render_template, request, session
from sqlalchemy import text

from config import Config
from app.extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    app.instance_path and __import__("os").makedirs(app.instance_path, exist_ok=True)
    __import__("os").makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Entre para acessar esta area."

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.challenges import challenges_bp
    from app.routes.courts import courts_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.feed import feed_bp
    from app.routes.main import main_bp
    from app.routes.matches import matches_bp
    from app.routes.notifications import notifications_bp
    from app.routes.teams import teams_bp

    for bp in (
        main_bp,
        auth_bp,
        dashboard_bp,
        teams_bp,
        feed_bp,
        challenges_bp,
        matches_bp,
        courts_bp,
        notifications_bp,
        admin_bp,
    ):
        app.register_blueprint(bp)

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "img-src 'self' data: https: https://*.tile.openstreetmap.org https://tile.openstreetmap.org; "
            "connect-src 'self' https://nominatim.openstreetmap.org https://*.tile.openstreetmap.org https://tile.openstreetmap.org; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers.setdefault("Content-Security-Policy", csp)
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    @app.template_filter("status_label")
    def status_label(value):
        labels = {
            "Com solicitacoes": "Com solicitações",
            "Nao realizado": "Não realizado",
            "Em revisao": "Em revisão",
        }
        return labels.get(value, value)

    @app.context_processor
    def inject_achievements():
        return {"awarded_badges": session.pop("awarded_badges", [])}

    with app.app_context():
        db.create_all()
        _ensure_sqlite_columns()
        from app.services.badge_service import ensure_badges
        ensure_badges()

    return app


def _ensure_sqlite_columns():
    if not str(db.engine.url).startswith("sqlite"):
        return
    columns = {
        row[1]
        for row in db.session.execute(text("PRAGMA table_info(friendly_match_post)")).fetchall()
    }
    if "court_id" not in columns:
        db.session.execute(text("ALTER TABLE friendly_match_post ADD COLUMN court_id INTEGER"))
        db.session.commit()
    court_columns = {
        row[1]
        for row in db.session.execute(text("PRAGMA table_info(court)")).fetchall()
    }
    if "address_number" not in court_columns:
        db.session.execute(text("ALTER TABLE court ADD COLUMN address_number VARCHAR(30)"))
        db.session.commit()
    sqlite_columns = {
        "team": {
            "banner_image": "VARCHAR(255)",
            "home_latitude": "FLOAT",
            "home_longitude": "FLOAT",
        },
        "court": {
            "cover_image": "VARCHAR(255)",
        },
        "match": {
            "proof_image": "VARCHAR(255)",
        },
        "match_result_confirmation": {
            "proof_image": "VARCHAR(255)",
        },
        "team_post": {
            "image_path": "VARCHAR(255)",
            "likes_count": "INTEGER DEFAULT 0",
            "comments_count": "INTEGER DEFAULT 0",
            "is_hidden": "BOOLEAN DEFAULT 0",
        },
    }
    for table, required_columns in sqlite_columns.items():
        existing = {
            row[1]
            for row in db.session.execute(text(f"PRAGMA table_info({table})")).fetchall()
        }
        if not existing:
            continue
        for column, definition in required_columns.items():
            if column not in existing:
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
                db.session.commit()
