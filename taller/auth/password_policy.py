from taller.models.perfil_usuario import PerfilUsuario


def get_or_create_user_profile(user):
    if not getattr(user, "is_authenticated", False):
        return None
    profile, _created = PerfilUsuario.objects.get_or_create(user=user)
    return profile


def user_must_change_password(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return False
    profile = get_or_create_user_profile(user)
    return bool(profile and profile.must_change_password)


def set_user_must_change_password(user, value: bool) -> None:
    profile = get_or_create_user_profile(user)
    if profile and profile.must_change_password != value:
        profile.must_change_password = value
        profile.save(update_fields=["must_change_password"])


def install_user_password_change_property():
    from django.contrib.auth.models import User

    if hasattr(User, "must_change_password"):
        return

    def _get(user):
        return user_must_change_password(user)

    def _set(user, value):
        if getattr(user, "pk", None):
            set_user_must_change_password(user, bool(value))

    User.must_change_password = property(_get, _set)
