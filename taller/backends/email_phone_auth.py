"""
Backend de autenticación personalizado que permite login con email o celular.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    """
    Backend de autenticación que permite login con email o celular.

    Orden de búsqueda:
    1. Buscar usuario por email
    2. Si no existe, buscar por celular (telefono en Empresa)
    3. Autenticar con contraseña
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("email") or kwargs.get("login")

        if username is None or password is None:
            return None

        try:
            # 1. Intentar buscar por email
            user = User.objects.filter(
                Q(email__iexact=username) | Q(username__iexact=username)
            ).first()

            # 2. Si no se encuentra, buscar por celular (telefono en Empresa)
            if not user:
                try:
                    from taller.models.empresa import Empresa

                    empresa = Empresa.objects.filter(telefono=username).first()
                    if empresa:
                        user = empresa.user
                except Exception:
                    pass

            # 3. Verificar contraseña
            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            pass

        return None
