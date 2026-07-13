from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from app.models import Court, FriendlyMatchPost, Match, Team, User

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    stats = {
        "teams": Team.query.count(),
        "users": User.query.count(),
        "matches": Match.query.count(),
        "courts": Court.query.filter_by(approved=True).count(),
    }
    return render_template("index.html", stats=stats)


@main_bp.route("/api/teams/search")
@login_required
def api_team_search():
    query = Team.query
    city = request.args.get("city")
    level = request.args.get("skill_level")
    category = request.args.get("category")
    if city:
        query = query.filter(Team.city.ilike(f"%{city}%"))
    if level:
        query = query.filter_by(skill_level=level)
    if category:
        query = query.filter_by(category=category)
    return jsonify([
        {
            "id": team.id,
            "name": team.name,
            "city": team.city,
            "neighborhood": team.neighborhood,
            "skill_level": team.skill_level,
            "category": team.category,
            "fair_play": team.fair_play_score,
        }
        for team in query.limit(30)
    ])


@main_bp.route("/search")
@login_required
def search():
    term = (request.args.get("q") or "").strip()
    teams = []
    courts = []
    friendlies = []
    if term:
        like = f"%{term}%"
        teams = Team.query.filter(
            (Team.name.ilike(like)) | (Team.city.ilike(like)) | (Team.neighborhood.ilike(like))
        ).order_by(Team.name).limit(8).all()
        courts = Court.query.filter(
            Court.approved.is_(True),
            (Court.name.ilike(like)) | (Court.city.ilike(like)) | (Court.neighborhood.ilike(like))
        ).order_by(Court.name).limit(8).all()
        friendlies = FriendlyMatchPost.query.filter(
            (FriendlyMatchPost.location_name.ilike(like))
            | (FriendlyMatchPost.city.ilike(like))
            | (FriendlyMatchPost.neighborhood.ilike(like))
        ).order_by(FriendlyMatchPost.match_date, FriendlyMatchPost.start_time).limit(8).all()
    return render_template("search.html", term=term, teams=teams, courts=courts, friendlies=friendlies)
