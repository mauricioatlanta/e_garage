from allauth.account.views import LoginView
from django.conf import settings
from django.utils.translation import get_language


class CountryAwareLoginView(LoginView):
    """
    Implementación de LoginView que detecta el país/idioma antes de delegar en allauth.
    """

    template_name = "cl/es/account/login.html"

    def dispatch(self, request, *args, **kwargs):
        self._apply_country_context(request)
        return super().dispatch(request, *args, **kwargs)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _apply_country_context(self, request):
        country = self._detect_country(request)
        request.country = country
        request.country_code = country
        request.session["preferred_country"] = country

    def _detect_country(self, request):
        # /accounts/login/ sin país en path: limpiar sesión para no arrastrar UY/otro, pero
        # SÍ respetar ?country=, ?from=, next, referer. Solo si no hay pistas → default CL.
        path_raw = (request.path or "").rstrip("/")
        if path_raw == "/accounts/login":
            request.session.pop("preferred_country", None)

        next_url = request.GET.get("next", "") or ""
        country_param = (request.GET.get("country", "") or "").upper()
        from_param = (request.GET.get("from", "") or "").upper()

        # Detectar desde parámetro ?from= (ej. /accounts/login/?from=co)
        if from_param in ["US", "USA"]:
            return "US"
        if from_param in ["UY", "URUGUAY"]:
            return "UY"
        if from_param in ["AR", "ARGENTINA"]:
            return "AR"
        if from_param in ["CO", "COLOMBIA"]:
            return "CO"
        if from_param in ["EC", "ECUADOR"]:
            return "EC"
        if from_param in ["PE", "PERU", "PERÚ"]:
            return "PE"
        if from_param in ["VE", "VENEZUELA"]:
            return "VE"
        if from_param in ["BR", "BRASIL", "BRAZIL"]:
            return "BR"
        if from_param in ["MX", "MEXICO"]:
            return "MX"

        # Detectar desde next URL
        if next_url.startswith("/us/"):
            return "US"
        if next_url.startswith("/cl/"):
            return "CL"
        if next_url.startswith("/uy/"):
            return "UY"
        if next_url.startswith("/ar/"):
            return "AR"
        if next_url.startswith("/mx/"):
            return "MX"
        if next_url.startswith("/co/"):
            return "CO"
        if next_url.startswith("/ec/"):
            return "EC"
        if next_url.startswith("/pe/"):
            return "PE"
        if next_url.startswith("/ve/"):
            return "VE"
        if next_url.startswith("/br/"):
            return "BR"

        # Detectar desde parámetro country (prioridad alta)
        if country_param in ["US", "USA"]:
            return "US"
        if country_param in ["CL", "CHILE"]:
            return "CL"
        if country_param in ["MX", "MEXICO"]:
            return "MX"
        if country_param in ["CO", "COLOMBIA"]:
            return "CO"
        if country_param in ["EC", "ECUADOR"]:
            return "EC"
        if country_param in ["PE", "PERU", "PERÚ"]:
            return "PE"
        if country_param in ["VE", "VENEZUELA"]:
            return "VE"
        if country_param in ["BR", "BRASIL", "BRAZIL"]:
            return "BR"
        if country_param in ["UY", "URUGUAY"]:
            return "UY"
        if country_param in ["AR", "ARGENTINA"]:
            return "AR"

        # Detectar desde sesión guardada
        saved = (request.session.get("preferred_country") or "").upper()
        if saved in ["US", "USA"]:
            return "US"
        if saved in ["CL", "CHILE"]:
            return "CL"
        if saved in ["MX", "MEXICO"]:
            return "MX"
        if saved in ["CO", "COLOMBIA"]:
            return "CO"
        if saved in ["EC", "ECUADOR"]:
            return "EC"
        if saved in ["PE", "PERU", "PERÚ"]:
            return "PE"
        if saved in ["VE", "VENEZUELA"]:
            return "VE"
        if saved in ["BR", "BRASIL", "BRAZIL"]:
            return "BR"
        if saved in ["UY", "URUGUAY"]:
            return "UY"
        if saved in ["AR", "ARGENTINA"]:
            return "AR"

        # Detectar desde referer
        referer = request.headers.get("referer", "")
        if "/us/" in referer or "/usa/" in referer:
            return "US"
        if "/cl/" in referer or "/chile/" in referer:
            return "CL"
        if "/mx/" in referer or "/mexico/" in referer:
            return "MX"
        if "/co/" in referer or "/colombia/" in referer:
            return "CO"
        if "/ec/" in referer or "/ecuador/" in referer:
            return "EC"
        if "/pe/" in referer or "/peru/" in referer or "/perú/" in referer:
            return "PE"
        if "/ve/" in referer or "/venezuela/" in referer:
            return "VE"
        if "/br/" in referer or "/brasil/" in referer or "/brazil/" in referer:
            return "BR"
        if "/uy/" in referer or "/uruguay/" in referer:
            return "UY"
        if "/ar/" in referer or "/argentina/" in referer:
            return "AR"

        # Detectar desde usuario autenticado
        if request.user.is_authenticated:
            empresa_country = getattr(getattr(request.user, "empresa", None), "pais", None)
            if empresa_country:
                return empresa_country.upper()
            perfil_country = getattr(getattr(request.user, "perfil", None), "pais", None)
            if perfil_country:
                return perfil_country.upper()

        # Detectar desde path
        path = (request.path or "").lower()
        if path.startswith("/us/") or path == "/us":
            return "US"
        if path.startswith("/mx/") or path == "/mx":
            return "MX"
        if path.startswith("/cl/") or path == "/cl":
            return "CL"
        if path.startswith("/co/") or path == "/co":
            return "CO"
        if path.startswith("/ec/") or path == "/ec":
            return "EC"
        if path.startswith("/pe/") or path == "/pe":
            return "PE"
        if path.startswith("/ve/") or path == "/ve":
            return "VE"
        if path.startswith("/br/") or path == "/br":
            return "BR"
        if path.startswith("/uy/") or path == "/uy":
            return "UY"
        if path.startswith("/ar/") or path == "/ar":
            return "AR"

        # Fallback: país por defecto de settings (Chile, no Uruguay)
        return getattr(settings, "EGARAGE_DEFAULT_COUNTRY", "cl").upper()

    # ------------------------------------------------------------------ #
    # Overrides de LoginView
    # ------------------------------------------------------------------ #
    def get_template_names(self):
        country = getattr(self.request, "country", "CL")
        lang = get_language() or "es"

        if country == "US":
            return ["account/login.html"]  # misma gráfica; labels EN vía {% if country == 'US' %}
        if country == "UY":
            return ["uy/es/account/login.html"]
        if country == "MX" and lang == "en":
            return ["us/en/account/login.html"]
        # Venezuela: template propio ve/es/account/login.html
        if country == "VE":
            return ["ve/es/account/login.html"]
        # MX, CL, AR, CO, EC, PE: base_login + _login_form (reutilizable, misma gráfica)
        if country in ("MX", "CL", "AR", "CO", "EC", "PE"):
            return ["account/login.html"]

        if lang == "en":
            return ["us/en/account/login.html"]
        return ["account/login.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["country"] = getattr(self.request, "country", "CL")
        context["LANGUAGE_CODE"] = get_language() or "es"
        context["debug"] = True
        # Ocultar starfield del base; el login usa su propio fondo (Vanta/grid)
        context["enable_space_bg"] = 0
        return context


# Vista funcional como alternativa
def country_aware_login(request, *args, **kwargs):
    """Wrapper funcional para mantener compatibilidad con las URLs actuales."""
    view = CountryAwareLoginView.as_view()
    return view(request, *args, **kwargs)
