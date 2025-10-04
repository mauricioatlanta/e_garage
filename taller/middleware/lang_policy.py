from django.utils import translation

ALLOWED_BY_COUNTRY = {
    "US": ("en", "es"),  # USA puede en/es
    "CL": ("es",),  # Chile solo es
}

DEFAULT_BY_COUNTRY = {
    "US": "en",
    "CL": "es",
}

SESSION_KEY = "preferred_lang"  # dónde guardamos preferencia del usuario


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
        pais = getattr(getattr(request, "empresa", None), "pais", None)
        allowed = ALLOWED_BY_COUNTRY.get(pais)
        default_lang = DEFAULT_BY_COUNTRY.get(pais)

        # 1) Chile: forzar español
        if pais == "CL":
            lang = "es"

        # 2) USA: preferencia por sesión/usuario, si es válida
        elif pais == "US":
            lang = None
            # a) preferencia en sesión
            pref = request.session.get(SESSION_KEY)
            if pref and allowed and pref in allowed:
                lang = pref
            # b) preferencia en perfil de usuario (opcional)
            elif request.user.is_authenticated:
                user_pref = getattr(
                    getattr(request.user, "perfil", None), "idioma", None
                )
                if user_pref and allowed and user_pref in allowed:
                    lang = user_pref
            # c) default país
            if not lang:
                lang = default_lang or "en"

        # 3) Otros: dejar global o forzar español si quieres
        else:
            lang = default_lang or "es"

        # Debug logging
        print(f"[DEBUG] LanguagePolicyMiddleware: pais={pais}, selected_lang={lang}")
        print(f"[DEBUG] User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")

        # Activar
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        response = self.get_response(request)
        translation.deactivate()
        return response
