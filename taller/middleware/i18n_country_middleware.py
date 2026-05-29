"""
Middleware para configurar idioma automáticamente según el país
Chile: español fijo
USA: selector ES/EN (guarda en cookie/sesión)
"""

from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

# LANGUAGE_SESSION_KEY no está disponible en todas las versiones de Django
LANGUAGE_SESSION_KEY = "django_language"
import logging

logger = logging.getLogger(__name__)

ALLOWED_LANGS = {
    code for code, _ in getattr(settings, "LANGUAGES", (("es", "Español"), ("en", "English")))
}


class CountryLanguageMiddleware(MiddlewareMixin):
    """
    - /cl/...  => fuerza ES siempre
    - /us/...  => respeta cookie/sesión; si llega ?lang=xx (o ?language=xx), persiste y redirige
    - Expone request.country y request.LANGUAGE_CODE
    - Asegura Content-Language y cookie django_language coherentes
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""

        # Determinar país basado en URL y usuario logueado
        url_country = (
            "CL" if path.startswith("/cl/") else ("US" if path.startswith("/us/") else None)
        )

        # Si el usuario está logueado, usar su país de empresa
        user_country = None
        if hasattr(request, "user") and request.user.is_authenticated:
            try:
                # Prioridad: empresa activa en sesión
                empresa_id = request.session.get("empresa_id")
                if empresa_id:
                    try:
                        from taller.models import Empresa

                        emp = Empresa.objects.filter(id=empresa_id).only("id", "pais").first()
                        if emp:
                            user_country = emp.pais
                    except Exception:
                        pass

                # Fallback a user.empresa y perfilusuario
                if user_country is None:
                    if hasattr(request.user, "empresa") and request.user.empresa:
                        user_country = request.user.empresa.pais
                    elif hasattr(request.user, "perfilusuario") and request.user.perfilusuario:
                        user_country = request.user.perfilusuario.pais
            except Exception:
                pass

        # Priorizar el país del usuario sobre la URL
        # Si no hay usuario logueado, usar el país de la URL como fallback
        country = user_country if user_country else url_country

        # Debug logging
        if getattr(settings, "DEBUG", False):
            logger.info(
                f"🌍 CountryLanguageMiddleware: URL={path}, user_country={user_country}, url_country={url_country}, final_country={country}"
            )
        request.country = country

        # Lo que haya decidido LocaleMiddleware (cookie/sesión) antes de nosotros
        lang = getattr(request, "LANGUAGE_CODE", None)

        # ¿Viene conmutación manual por query?
        lang_param = request.GET.get("lang") or request.GET.get("language")

        # Manejar cambio de idioma por parámetro URL
        if lang_param in ALLOWED_LANGS:
            # Si viene un parámetro de idioma válido, permitir el cambio
            lang = lang_param
            # Guardar en sesión
            if hasattr(request, "session"):
                request.session[LANGUAGE_SESSION_KEY] = lang
        else:
            # Configurar idioma según el país del usuario
            if country == "US":
                # USA: inglés predeterminado con opción a español
                user_cookie = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
                if user_cookie and user_cookie in ALLOWED_LANGS:
                    lang = user_cookie  # Respetar preferencia del usuario
                else:
                    lang = "en"  # Inglés por defecto para USA
            elif country == "CL":
                lang = "es"  # Español fijo para Chile
            else:
                # Solo usar cookie si no hay país definido
                user_cookie = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
                if user_cookie and user_cookie in ALLOWED_LANGS:
                    lang = user_cookie
                else:
                    lang = getattr(settings, "LANGUAGE_CODE", "es")  # Fallback

        # Activa lo que hayamos resuelto
        lang = lang or "es"  # Fallback final
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        # Debug logging
        if getattr(settings, "DEBUG", False):
            username = (
                getattr(request.user, "username", "anonymous")
                if hasattr(request, "user")
                else "no_user_yet"
            )
            logger.info(
                f"🗣️ CountryLanguageMiddleware: Final language={lang}, country={country}, user={username}"
            )

        response = self.get_response(request)
        response.headers["Content-Language"] = lang

        # No overwrites: sólo refuerza si no hay cookie
        if not request.COOKIES.get(getattr(settings, "LANGUAGE_COOKIE_NAME", "django_language")):
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                lang,
                max_age=31536000,
                samesite=getattr(settings, "LANGUAGE_COOKIE_SAMESITE", "Lax"),
                secure=getattr(settings, "LANGUAGE_COOKIE_SECURE", False),
                path=getattr(settings, "LANGUAGE_COOKIE_PATH", "/"),
            )
        return response
