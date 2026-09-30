from functools import wraps

from django.core.exceptions import PermissionDenied


CONTROL_TOWER_EMAIL = "mauricioatlanta@gmail.com"


def is_control_tower_user(user):
    """Return True only for Mauricio's explicitly authorized superuser account."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    email = (getattr(user, "email", "") or "").strip().lower()
    return email == CONTROL_TOWER_EMAIL and bool(getattr(user, "is_superuser", False))


def control_tower_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not is_control_tower_user(getattr(request, "user", None)):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped
