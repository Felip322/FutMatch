from app.extensions import db
from app.models import Notification


def notify(user_id, title, message, notification_type, link=None):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )
    db.session.add(notification)
    return notification
