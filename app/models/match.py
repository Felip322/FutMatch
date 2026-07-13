from datetime import datetime, timezone

from app.extensions import db


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey("court.id"))
    match_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(40), default="Confirmado")
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    notes = db.Column(db.Text)
    proof_image = db.Column(db.String(255))
    result_status = db.Column(db.String(40), default="Pendente")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    home_team = db.relationship("Team", foreign_keys=[home_team_id])
    away_team = db.relationship("Team", foreign_keys=[away_team_id])
    court = db.relationship("Court")
    confirmations = db.relationship("MatchResultConfirmation", back_populates="match", cascade="all, delete-orphan")
    simple_reviews = db.relationship("SimpleFairPlayReview", back_populates="match", cascade="all, delete-orphan")


class MatchResultConfirmation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id", ondelete="CASCADE"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    happened = db.Column(db.Boolean, nullable=False)
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    notes = db.Column(db.Text)
    proof_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    match = db.relationship("Match", back_populates="confirmations")
    team = db.relationship("Team")


class SimpleFairPlayReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id", ondelete="CASCADE"), nullable=False)
    reviewer_team_id = db.Column(db.Integer, db.ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    reviewed_team_id = db.Column(db.Integer, db.ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    showed_up = db.Column(db.Boolean, default=True)
    punctual = db.Column(db.Boolean, default=True)
    respected_agreement = db.Column(db.Boolean, default=True)
    good_behavior = db.Column(db.Boolean, default=True)
    comment = db.Column(db.String(280))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    match = db.relationship("Match", back_populates="simple_reviews")
    reviewer_team = db.relationship("Team", foreign_keys=[reviewer_team_id])
    reviewed_team = db.relationship("Team", foreign_keys=[reviewed_team_id])
