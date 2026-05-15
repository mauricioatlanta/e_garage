from django.shortcuts import redirect
from django.utils.translation import activate, get_language

from taller.views_extra.signup_complete import signup_complete


class CountryAwareSignupView:
    """
    Vista de signup que detecta el país/idioma y redirige al template correcto.
    Similar a CountryAwareLoginView pero para signup.
    """

    @staticmethod
    def _detect_country(request):
        """Detecta el país desde múltiples fuentes (igual que CountryAwareLoginView)"""
        next_url = request.GET.get("next", "") or ""
        country_param = (request.GET.get("country", "") or "").upper()
        from_param = (request.GET.get("from", "") or "").upper()

        # Detectar desde parámetro ?from=cl (prioridad alta)
        if from_param in ["CL", "CHILE"]:
            return "CL"
        if from_param in ["US", "USA"]:
            return "US"
        if from_param in ["MX", "MEXICO"]:
            return "MX"

        # Detectar desde next URL
        if next_url.startswith("/us/"):
            return "US"
        if next_url.startswith("/cl/"):
            return "CL"
        if next_url.startswith("/mx/"):
            return "MX"

        # Detectar desde parámetro country
        if country_param in ["US", "USA"]:
            return "US"
        if country_param in ["CL", "CHILE"]:
            return "CL"
        if country_param in ["MX", "MEXICO"]:
            return "MX"

        # Detectar desde path
        path = (request.path or "").lower()
        if path.startswith("/us/") or path == "/us":
            return "US"
        if path.startswith("/cl/") or path == "/cl":
            return "CL"
        if path.startswith("/mx/") or path == "/mx":
            return "MX"

        # Detectar desde referer
        referer = request.headers.get("referer", "")
        if "/us/" in referer or "/usa/" in referer:
            return "US"
        if "/cl/" in referer or "/chile/" in referer:
            return "CL"
        if "/mx/" in referer or "/mexico/" in referer:
            return "MX"

        # Fallback a CL
        return "CL"

    @staticmethod
    def as_view():
        """Wrapper funcional para mantener compatibilidad con las URLs actuales."""

        def view(request, *args, **kwargs):
            country = CountryAwareSignupView._detect_country(request)
            request.country = country
            request.country_code = country
            request.session["preferred_country"] = country

            # Activar idioma según país
            if country == "US":
                activate("en")
                request.session["django_language"] = "en"
                # Redirigir a signup con template de USA
                return redirect(f"/us/en/accounts/signup/?from=us")
            elif country == "MX":
                activate("es")
                request.session["django_language"] = "es"
                return redirect(f"/mx/es/accounts/signup/?from=mx")
            else:  # CL u otros países en español
                activate("es")
                request.session["django_language"] = "es"
                return redirect(f"/cl/es/accounts/signup/?from=cl")

        return view


def country_aware_signup(request, *args, **kwargs):
    """Wrapper funcional para mantener compatibilidad con las URLs actuales."""
    view = CountryAwareSignupView.as_view()
    return view(request, *args, **kwargs)
