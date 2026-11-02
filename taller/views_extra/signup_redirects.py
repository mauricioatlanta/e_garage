"""
Redirect universal para signup por pais con validacion de cobertura eGarage.
"""
from django.shortcuts import redirect
from django.contrib import messages
billing_module = None

try:
    from billing_countries import validate_signup_country
    billing_module = validate_signup_country
except ImportError:
    pass


def signup_redirect(request, country_code: str):
    code = (country_code or "").strip().upper()
    if billing_module:
        validation = billing_module(code)
        if not validation.get("allowed", False):
            msg = validation.get(
                "message",
                "El servicio de suscripcion no esta disponible en tu region.",
            )
            try:
                messages.warning(request, msg)
            except Exception:
                pass
            return redirect("/suscripcion-bloqueada/?country=" + code.lower())

    country_code_lower = code.lower()
    lang = "en" if country_code_lower == "us" else "es"
    base = f"/{country_code_lower}/{lang}/accounts/signup/"

    params = request.GET.copy()
    params.pop("country", None)
    params.pop("from", None)
    if params:
        base += "?" + params.urlencode()
    return redirect(base)
