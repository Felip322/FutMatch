from datetime import date

from app.models import Match


def filtered_matches_query(team_id, period="all"):
    query = Match.query.filter(
        ((Match.home_team_id == team_id) | (Match.away_team_id == team_id)),
        Match.home_score.isnot(None),
        Match.away_score.isnot(None),
    )
    today = date.today()
    if period == "month":
        query = query.filter(Match.match_date >= date(today.year, today.month, 1))
    elif period == "season":
        query = query.filter(Match.match_date >= date(2026, 1, 1), Match.match_date <= date(2026, 12, 31))
    return query.order_by(Match.match_date.desc())


def team_record(team_id, period="all"):
    query = filtered_matches_query(team_id, period)
    matches = query.limit(10).all() if period == "last10" else query.all()
    wins = draws = losses = goals_for = goals_against = 0
    for match in matches:
        own = match.home_score if match.home_team_id == team_id else match.away_score
        other = match.away_score if match.home_team_id == team_id else match.home_score
        goals_for += own
        goals_against += other
        if own > other:
            wins += 1
        elif own == other:
            draws += 1
        else:
            losses += 1
    total = len(matches)
    points = wins * 3 + draws
    return {
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "goal_balance": goals_for - goals_against,
        "played": total,
        "performance": round(points / (total * 3) * 100, 1) if total else 0,
    }


def last_opponents(team_id, limit=5):
    matches = Match.query.filter(
        ((Match.home_team_id == team_id) | (Match.away_team_id == team_id)),
        Match.home_score.isnot(None),
        Match.away_score.isnot(None),
    ).order_by(Match.match_date.desc()).limit(limit).all()
    items = []
    for match in matches:
        opponent = match.away_team if match.home_team_id == team_id else match.home_team
        own = match.home_score if match.home_team_id == team_id else match.away_score
        other = match.away_score if match.home_team_id == team_id else match.home_score
        items.append({"team": opponent, "match": match, "score": f"{own} x {other}"})
    return items


def ranked_teams(teams, period="all"):
    rows = []
    for team in teams:
        stats = team_record(team.id, period)
        rows.append({"team": team, "stats": stats})
    return sorted(rows, key=lambda row: (row["stats"]["wins"], row["stats"]["performance"], row["stats"]["goal_balance"], row["team"].fair_play_score or 0), reverse=True)
