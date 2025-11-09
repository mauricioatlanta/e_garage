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
        # Debug: mostrar información del request
        print(f"[DEBUG] SimpleCountryRedirect: {request.path}")
        print(f"   User authenticated: {request.user.is_authenticated}")

        # Solo procesar si el usuario está autenticado
        if not request.user.is_authenticated:
            print("   [SKIP] Usuario no autenticado")
            return None

        # Solo procesar si el usuario tiene una empresa
        if not hasattr(request.user, "empresa") or not request.user.empresa:
            print(f"   [SKIP] Usuario {request.user.username} no tiene empresa")
            return None

        # Obtener el país de la empresa del usuario
        user_country = request.user.empresa.pais
        print(f"   User country: {user_country}")

        if not user_country:
            print("   [SKIP] Usuario no tiene país")
            return None

        # Obtener el país de la URL actual
        path = request.path.lower()
        url_country = None
        url_lang = None

        if path.startswith("/cl/"):
            url_country = "CL"
            # Verificar si tiene idioma
            if path.startswith("/cl/es/"):
                url_lang = "es"
            elif path.startswith("/cl/en/"):
                url_lang = "en"
        elif path.startswith("/us/"):
            url_country = "US"
            # Verificar si tiene idioma
            if path.startswith("/us/es/"):
                url_lang = "es"
            elif path.startswith("/us/en/"):
                url_lang = "en"

        print(f"   URL country: {url_country}, URL lang: {url_lang}")

        # Determinar el idioma correcto para el país del usuario
        if user_country == "US":
            correct_lang = "en"  # USA usa inglés por defecto
        elif user_country == "CL":
            correct_lang = "es"  # Chile usa español
        else:
            correct_lang = "es"  # Fallback a español

        # Verificar si hay conflicto de país
        if url_country and url_country != user_country:
            # Conflicto de país - redirigir
            print("   [REDIRECT] CONFLICTO DE PAÍS DETECTADO! Redirigiendo...")
            redirect_needed = True
        # Verificar si hay conflicto de idioma (mismo país pero idioma incorrecto)
        elif url_country == user_country and url_lang and url_lang != correct_lang:
            # Conflicto de idioma - redirigir
            print("   [REDIRECT] CONFLICTO DE IDIOMA DETECTADO! Redirigiendo...")
            redirect_needed = True
        # Verificar si falta el idioma (mismo país pero sin idioma)
        elif url_country == user_country and not url_lang:
            # Falta idioma - redirigir
            print("   [REDIRECT] FALTA IDIOMA DETECTADO! Redirigiendo...")
            redirect_needed = True
        else:
            # No hay conflicto
            print(
                f"   [OK] No hay conflicto (URL: {url_country}/{url_lang}, User: {user_country}/{correct_lang})"
            )
            return None

        # Redirigir a la URL correcta
        # Remover el prefijo de país actual (incluyendo idioma si existe)
        if path.startswith(f"/{url_country.lower()}/"):
            # Remover "/cl/" o "/us/" y también el idioma si existe
            new_path = path[4:]  # Remover "/cl/" o "/us/"
            # Si el path restante empieza con "es/" o "en/", removerlo también
            if new_path.startswith("es/") or new_path.startswith("en/"):
                new_path = new_path[3:]  # Remover "es/" o "en/"
        elif path.startswith(f"/{url_country.lower()}"):
            new_path = path[3:]  # Remover "/cl" o "/us"
        else:
            new_path = path

        # Agregar el prefijo del país correcto con idioma correcto
        correct_prefix = f"/{user_country.lower()}/{correct_lang}"
        if new_path.startswith("/"):
            new_url = f"{correct_prefix}{new_path}"
        else:
            new_url = f"{correct_prefix}/{new_path}"

        # Debug logging
        print(f"[REDIRECT] SimpleCountryRedirect: {path} -> {new_url}")
        print(
            f"   User: {request.user.username}, Empresa: {request.user.empresa.nombre_taller}, País: {user_country}"
        )

        # Redirección 302 (temporal)
        return HttpResponseRedirect(new_url)
