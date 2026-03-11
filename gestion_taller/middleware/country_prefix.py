# gestion_taller/middleware/country_prefix.py
import logging

from django.shortcuts import redirect

from taller.utils.empresa import get_or_create_empresa

logger = logging.getLogger(__name__)


EXCLUDED_PREFIXES = (
    "/accounts/",
    "/admin/",
    "/static/",
    "/media/",
    "/api/",
)


class EnforceCountryPrefixMiddleware:
    """
    Middleware que asegura que el prefijo de URL coincida con el país de la empresa del usuario.

    Si un usuario de Chile navega por /us/, lo redirige a /cl/, y viceversa.
    Esto evita confusiones en formularios y endpoints AJAX.
    No interfiere con allauth, admin, static, media ni API.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for prefix in EXCLUDED_PREFIXES:
            if request.path.startswith(prefix):
                return self.get_response(request)

        try:
            # Solo aplicar para usuarios autenticados
            if request.user.is_authenticated:
                empresa = get_or_create_empresa(request)
                expected_prefix = (
                    "/cl/" if (getattr(empresa, "pais", "") or "").upper() == "CL" else "/us/"
                )

                path = request.path or "/"
                current_prefix = None

                # Detectar prefijo actual
                if path.startswith("/cl/"):
                    current_prefix = "/cl/"
                elif path.startswith("/us/"):
                    current_prefix = "/us/"

                # Si hay prefijo y no coincide con el esperado, redirigir
                if current_prefix and current_prefix != expected_prefix:
                    # Construir nueva URL cambiando el prefijo
                    new_path = expected_prefix + path[len(current_prefix) :]

                    # Preservar query string
                    if request.GET:
                        from urllib.parse import urlencode

                        new_path += "?" + urlencode(request.GET, doseq=True)

                    logger.info(
                        f"Redirigiendo usuario de {getattr(empresa, 'nombre_taller', 'Unknown')} ({empresa.pais}) de {path} a {new_path}"
                    )
                    return redirect(new_path)

        except Exception as e:
            logger.warning(f"Error en EnforceCountryPrefixMiddleware: {e}")
            pass

        return self.get_response(request)
