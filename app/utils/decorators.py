from functools import wraps

from flask import abort
from flask_login import current_user


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def owner_required(get_owner_id):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            owner_id = get_owner_id(*args, **kwargs)
            if not current_user.is_authenticated or (current_user.id != owner_id and not current_user.is_admin):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
