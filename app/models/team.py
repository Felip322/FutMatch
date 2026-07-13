from datetime import datetime, timezone

from app.extensions import db


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    short_name = db.Column(db.String(30))
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    logo = db.Column(db.String(255))
    banner_image = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    neighborhood = db.Column(db.String(100))
    foundation_year = db.Column(db.Integer)
    category = db.Column(db.String(40))
    age_group = db.Column(db.String(40))
    gender = db.Column(db.String(40))
    skill_level = db.Column(db.String(40))
    floor_type = db.Column(db.String(40))
    description = db.Column(db.Text)
    instagram = db.Column(db.String(120))
    whatsapp = db.Column(db.String(40))
    home_location = db.Column(db.String(180))
    home_latitude = db.Column(db.Float)
    home_longitude = db.Column(db.Float)
    max_travel_distance = db.Column(db.Integer, default=10)
    fair_play_score = db.Column(db.Float, default=4.6)
    reliability_score = db.Column(db.Float, default=90.0)
    attendance_rate = db.Column(db.Float, default=92.0)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    owner = db.relationship("User", back_populates="teams_owned", foreign_keys=[owner_id])
    friendly_posts = db.relationship("FriendlyMatchPost", back_populates="team", cascade="all, delete-orphan")
    social_posts = db.relationship("TeamPost", back_populates="team", cascade="all, delete-orphan")
    badges = db.relationship("TeamBadge", back_populates="team", cascade="all, delete-orphan")


class TeamPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    image_path = db.Column(db.String(255))
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    is_hidden = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    team = db.relationship("Team", back_populates="social_posts")
    user = db.relationship("User")
    likes = db.relationship("TeamPostLike", back_populates="post", cascade="all, delete-orphan")
    comments = db.relationship("TeamPostComment", back_populates="post", cascade="all, delete-orphan")


class TeamPostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("team_post.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    post = db.relationship("TeamPost", back_populates="likes")
    user = db.relationship("User")


class TeamPostComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("team_post.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    post = db.relationship("TeamPost", back_populates="comments")
    user = db.relationship("User")


class FriendlyMatchPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey("court.id"))
    match_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    location_name = db.Column(db.String(140), nullable=False)
    address = db.Column(db.String(180), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    neighborhood = db.Column(db.String(100))
    price = db.Column(db.Numeric(10, 2), default=0)
    notes = db.Column(db.Text)
    status = db.Column(db.String(40), default="Aberto", index=True)
    accepted_request_id = db.Column(db.Integer)
    duration_minutes = db.Column(db.Integer, default=60)
    players_count = db.Column(db.Integer, default=5)
    tolerance_minutes = db.Column(db.Integer, default=10)
    uniform = db.Column(db.String(80))
    rules = db.Column(db.Text)
    cancellation_reason = db.Column(db.String(80))
    cancellation_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    team = db.relationship("Team", back_populates="friendly_posts", foreign_keys=[team_id])
    court = db.relationship("Court")
    requests = db.relationship("FriendlyMatchRequest", back_populates="post", cascade="all, delete-orphan", foreign_keys="FriendlyMatchRequest.post_id")
    history = db.relationship("FriendlyMatchHistory", back_populates="post", cascade="all, delete-orphan")


class FriendlyMatchRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("friendly_match_post.id", ondelete="CASCADE"), nullable=False)
    requester_team_id = db.Column(db.Integer, db.ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    message = db.Column(db.Text)
    confirms_time = db.Column(db.Boolean, default=False)
    accepts_location = db.Column(db.Boolean, default=False)
    uniform_color = db.Column(db.String(40))
    status = db.Column(db.String(40), default="Pendente", index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    post = db.relationship("FriendlyMatchPost", back_populates="requests", foreign_keys=[post_id])
    requester_team = db.relationship("Team", foreign_keys=[requester_team_id])


class FriendlyMatchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("friendly_match_post.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    previous_status = db.Column(db.String(40))
    new_status = db.Column(db.String(40), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    post = db.relationship("FriendlyMatchPost", back_populates="history")
    user = db.relationship("User")


class DirectFriendlyProposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposer_team_id = db.Column(db.Integer, db.ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    target_team_id = db.Column(db.Integer, db.ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey("court.id"))
    match_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    location_name = db.Column(db.String(140), nullable=False)
    address = db.Column(db.String(180), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    neighborhood = db.Column(db.String(100))
    message = db.Column(db.Text)
    status = db.Column(db.String(40), default="Pendente", index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    proposer_team = db.relationship("Team", foreign_keys=[proposer_team_id])
    target_team = db.relationship("Team", foreign_keys=[target_team_id])
    court = db.relationship("Court")
