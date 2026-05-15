"""
Redirect universal para signup por país.

Este módulo proporciona una función de redirect centralizada que redirige
las rutas cortas de signup por país (/xx/accounts/signup/) a la ruta completa
con país + idioma (/{pais}/{lang}/accounts/signup/).
"""

from django.shortcuts import redirect


def signup_redirect(request, country_code: str):
    """
    Redirige al signup country-aware con país + idioma en el path.

    Args:
        request: El objeto request de Django
        country_code: Código del país (ej: "br", "co", "cl", "us")

    Returns:
        HttpResponseRedirect a /{country}/{lang}/accounts/signup/

    Ejemplo:
        >>> signup_redirect(request, "us")
        # Redirige a: /us/en/accounts/signup/
    """
    # Normalizar código de país a minúsculas
    country_code_lower = country_code.lower()
    lang = "en" if country_code_lower == "us" else "es"
    base = f"/{country_code_lower}/{lang}/accounts/signup/"
    # Preservar ?plan=, next=, etc.; no propagar country/from (país en path)
    params = request.GET.copy()
    params.pop("country", None)
    params.pop("from", None)
    if params:
        base += "?" + params.urlencode()
    return redirect(base)
