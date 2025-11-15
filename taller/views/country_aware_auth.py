from allauth.account.views import LoginView
from django.utils.translation import get_language


class CountryAwareLoginView(LoginView):
    """
    Implementación de LoginView que detecta el país/idioma antes de delegar en allauth.
    """

    template_name = "taller/cl/es/account/login.html"

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
        next_url = request.GET.get("next", "") or ""
        country_param = (request.GET.get("country", "") or "").upper()

        if next_url.startswith("/us/"):
            return "US"
        if next_url.startswith("/cl/"):
            return "CL"
        if next_url.startswith("/mx/"):
            return "MX"

        if country_param in ["US", "USA"]:
            return "US"
        if country_param in ["CL", "CHILE"]:
            return "CL"
        if country_param in ["MX", "MEXICO"]:
            return "MX"

        saved = (request.session.get("preferred_country") or "").upper()
        if saved in ["US", "USA"]:
            return "US"
        if saved in ["CL", "CHILE"]:
            return "CL"
        if saved in ["MX", "MEXICO"]:
            return "MX"

        referer = request.headers.get("referer", "")
        if "/us/" in referer or "/usa/" in referer:
            return "US"
        if "/cl/" in referer or "/chile/" in referer:
            return "CL"
        if "/mx/" in referer or "/mexico/" in referer:
            return "MX"

        if request.user.is_authenticated:
            empresa_country = getattr(getattr(request.user, "empresa", None), "pais", None)
            if empresa_country:
                return empresa_country.upper()
            perfil_country = getattr(getattr(request.user, "perfil", None), "pais", None)
            if perfil_country:
                return perfil_country.upper()

        path = (request.path or "").lower()
        if path.startswith("/us/") or path == "/us":
            return "US"
        if path.startswith("/mx/") or path == "/mx":
            return "MX"
        if path.startswith("/cl/") or path == "/cl":
            return "CL"

        return "CL"

    # ------------------------------------------------------------------ #
    # Overrides de LoginView
    # ------------------------------------------------------------------ #
    def get_template_names(self):
        country = getattr(self.request, "country", "CL")
        lang = get_language() or "es"

        if country == "US":
            if lang == "es":
                return ["taller/cl/es/account/login.html"]
            return ["taller/us/en/account/login.html"]
        if country == "MX":
            if lang == "en":
                return ["taller/us/en/account/login.html"]
            return ["taller/mx/es/account/login.html"]

        if lang == "en":
            return ["taller/us/en/account/login.html"]
        return ["taller/cl/es/account/login.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["country"] = getattr(self.request, "country", "CL")
        context["LANGUAGE_CODE"] = get_language() or "es"
        context["debug"] = True
        return context


# Vista funcional como alternativa
def country_aware_login(request, *args, **kwargs):
    """Wrapper funcional para mantener compatibilidad con las URLs actuales."""
    view = CountryAwareLoginView.as_view()
    return view(request, *args, **kwargs)
