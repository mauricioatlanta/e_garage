"""
Middleware simple para redirigir usuarios a la URL correcta basándose en su país de empresa.
Solo redirige cuando hay un conflicto claro entre la URL y el país de la empresa.
"""

from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin


class SimpleCountryRedirectMiddleware(MiddlewareMixin):
    """
    Middleware simple que redirige usuarios a la URL correcta basándose en su país de empresa.
    Solo redirige cuando hay un conflicto claro.
    """

    def process_request(self, request):
        # Solo procesar si el usuario está autenticado
        if not request.user.is_authenticated:
            return None

        # Solo procesar si el usuario tiene una empresa
        if not hasattr(request.user, "empresa") or not request.user.empresa:
            return None

        # Obtener el país de la empresa del usuario
        user_country = request.user.empresa.pais
        if not user_country:
            return None

        # Obtener el país de la URL actual
        path = request.path.lower()
        url_country = None

        if path.startswith("/cl/"):
            url_country = "CL"
        elif path.startswith("/us/"):
            url_country = "US"

        # Si no hay conflicto, no hacer nada
        if not url_country or url_country == user_country:
            return None

        # Hay conflicto - redirigir a la URL correcta
        # Remover el prefijo de país actual
        if path.startswith(f"/{url_country.lower()}/"):
            new_path = path[4:]  # Remover "/cl/" o "/us/"
        elif path.startswith(f"/{url_country.lower()}"):
            new_path = path[3:]  # Remover "/cl" o "/us"
        else:
            new_path = path

        # Agregar el prefijo del país correcto
        correct_prefix = f"/{user_country.lower()}"
        if new_path.startswith("/"):
            new_url = f"{correct_prefix}{new_path}"
        else:
            new_url = f"{correct_prefix}/{new_path}"

        # Debug logging
        if (
            getattr(request, "user", None)
            and hasattr(request, "user")
            and request.user.is_authenticated
        ):
            print(f"🔄 SimpleCountryRedirect: {path} → {new_url}")
            print(
                f"   User: {request.user.username}, Empresa: {request.user.empresa.nombre_taller}, País: {user_country}"
            )

        # Redirección 302 (temporal)
        return HttpResponseRedirect(new_url)
