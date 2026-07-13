def calculate_fair_play_index(team, reviews=None, cancellations=0, no_shows=0):
    reviews = reviews or []
    if reviews:
        review_average = sum(r.fair_play + r.respect + r.agreement_compliance for r in reviews) / (len(reviews) * 3)
    else:
        review_average = team.fair_play_score or 4.5
    base = review_average * 20
    penalty = cancellations * 3 + no_shows * 8
    attendance_bonus = min(8, (team.attendance_rate or 0) / 100 * 8)
    return max(0, min(100, round(base - penalty + attendance_bonus, 1)))


def has_reliability_badge(team, matches_count):
    return (
        matches_count >= 3
        and (team.attendance_rate or 0) >= 85
        and (team.fair_play_score or 0) >= 4
        and (team.reliability_score or 0) >= 80
    )


def simple_review_score(review):
    checks = [review.showed_up, review.punctual, review.respected_agreement, review.good_behavior]
    return sum(1 for item in checks if item) / len(checks) * 5
