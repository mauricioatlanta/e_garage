from django.utils import translation

ALLOWED_BY_COUNTRY = {
    "US": ("en", "es"),  # USA puede en/es
    "CL": ("es",),  # Chile solo es
    "MX": ("es",),  # México español
    "CO": ("es",),  # Colombia español
    "EC": ("es",),  # Ecuador español
    "VE": ("es",),  # Venezuela español
    "UY": ("es",),  # Uruguay español
    "AR": ("es",),  # Argentina español
    "PE": ("es",),  # Perú español
    "BR": ("pt-br",),  # Brasil portugués
}

DEFAULT_BY_COUNTRY = {
    "US": "en",
    "CL": "es",
    "MX": "es",
    "CO": "es",
    "EC": "es",
    "VE": "es",
    "UY": "es",
    "AR": "es",
    "PE": "es",
    "BR": "pt-br",
}

# Django i18n usa esta clave por defecto
DJANGO_LANGUAGE_SESSION_KEY = "django_language"  # Clave estándar de Django
SESSION_KEY = "preferred_lang"  # clave alternativa si queremos


class LanguagePolicyMiddleware:
    """
    Reglas:
    - Si empresa.pais == CL: forzar 'es'
    - Si empresa.pais == US:
        - usar sesión/usuario si está entre los permitidos (en/es)
        - si no, usar default 'en'
    - Cualquier otro país: caer a LANGUAGE_CODE global
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Detectar país desde empresa O desde request.country (URL)
            pais = getattr(getattr(request, "empresa", None), "pais", None)

            # Si no hay empresa (usuario no autenticado), usar request.country desde URL
            if not pais:
                pais = getattr(request, "country", None)

            # Si aún no hay país, detectar desde URL directamente
            if not pais:
                segmentos = request.path.strip("/").split("/")
                if segmentos:
                    posible_pais = segmentos[0].upper()
                    if posible_pais in DEFAULT_BY_COUNTRY:
                        pais = posible_pais

            # Asegurar que pais esté en mayúsculas
            pais = pais.upper() if pais else None

            # SOLUCIÓN SIMPLE: Solo para USA, respetar preferencia de sesión
            if pais == "US":
                # PRIORIDAD 1: La URL explícita /us/en/... o /us/es/... manda sobre sesión/cookie.
                # Así, al entrar desde el selector de país a /us/en/bienvenida/ se muestra siempre en inglés.
                if request.path.startswith("/us/en/"):
                    lang = "en"
                    request.session[DJANGO_LANGUAGE_SESSION_KEY] = "en"
                    print(f"[DEBUG] USA - Idioma desde URL /us/en/: {lang}")
                elif request.path.startswith("/us/es/"):
                    lang = "es"
                    request.session[DJANGO_LANGUAGE_SESSION_KEY] = "es"
                    print(f"[DEBUG] USA - Idioma desde URL /us/es/: {lang}")
                else:
                    # Leer idioma de la sesión (LocaleMiddleware ya lo estableció)
                    session_lang = request.session.get(DJANGO_LANGUAGE_SESSION_KEY)

                    # Si hay idioma en sesión y es válido para USA, usarlo
                    if session_lang in ALLOWED_BY_COUNTRY["US"]:
                        lang = session_lang
                        print(f"[DEBUG] USA - Usando idioma de sesión: {lang}")
                    else:
                        # Verificar si hay idioma en cookie (LocaleMiddleware lo puede leer)
                        cookie_lang = request.COOKIES.get("django_language")
                        if cookie_lang in ALLOWED_BY_COUNTRY["US"]:
                            lang = cookie_lang
                            # Guardar en sesión para consistencia
                            request.session[DJANGO_LANGUAGE_SESSION_KEY] = lang
                            print(
                                f"[DEBUG] USA - Usando idioma de cookie y guardando en sesión: {lang}"
                            )
                        else:
                            lang = DEFAULT_BY_COUNTRY["US"]
                            print(f"[DEBUG] USA - Sin preferencia, usando default: {lang}")
            else:
                # Para otros países, usar default
                lang = DEFAULT_BY_COUNTRY.get(pais, "es")
                print(f"[DEBUG] País {pais} - Usando default: {lang}")

            # Activar idioma
            translation.activate(lang)
            request.LANGUAGE_CODE = lang

            print("[DEBUG] ===== LanguagePolicyMiddleware =====")
            print(f"[DEBUG] País: {pais}")
            print(f"[DEBUG] Idioma aplicado: {lang}")
            print(f"[DEBUG] URL: {request.path}")
            print("[DEBUG] ===========================================")

            response = self.get_response(request)
            return response

        except Exception as e:
            print(f"[ERROR] LanguagePolicyMiddleware: {e}")
            # En caso de error, continuar sin modificar idioma
            response = self.get_response(request)
            return response
