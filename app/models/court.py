from datetime import datetime, timezone

from app.extensions import db


class Court(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(140), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(255))
    address = db.Column(db.String(180), nullable=False)
    address_number = db.Column(db.String(30))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    neighborhood = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    floor_type = db.Column(db.String(40))
    is_covered = db.Column(db.Boolean, default=True)
    size = db.Column(db.String(40))
    price_per_hour = db.Column(db.Numeric(10, 2), default=0)
    phone = db.Column(db.String(40))
    whatsapp = db.Column(db.String(40))
    parking = db.Column(db.Boolean, default=False)
    locker_room = db.Column(db.Boolean, default=False)
    shower = db.Column(db.Boolean, default=False)
    snack_bar = db.Column(db.Boolean, default=False)
    bleachers = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    owner = db.relationship("User")
    images = db.relationship("CourtImage", back_populates="court", cascade="all, delete-orphan")
    availabilities = db.relationship("CourtAvailability", back_populates="court", cascade="all, delete-orphan")


class CourtImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    court_id = db.Column(db.Integer, db.ForeignKey("court.id", ondelete="CASCADE"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    position = db.Column(db.Integer, default=0)

    court = db.relationship("Court", back_populates="images")


class CourtAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    court_id = db.Column(db.Integer, db.ForeignKey("court.id", ondelete="CASCADE"), nullable=False)
    weekday = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    court = db.relationship("Court", back_populates="availabilities")
