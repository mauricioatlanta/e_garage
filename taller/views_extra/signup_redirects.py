"""
Redirect universal para signup por país.

Este módulo proporciona una función de redirect centralizada que redirige
todas las rutas de signup por país (/xx/es/accounts/signup/) a la ruta
unificada /accounts/signup/ con un parámetro ?from=xx para indicar el país.

Esto simplifica el mantenimiento y evita duplicar templates por país.
"""

from django.shortcuts import redirect


def signup_redirect(request, country_code: str):
    """
    Redirige a /accounts/signup/ con el parámetro from=country_code.

    Args:
        request: El objeto request de Django
        country_code: Código del país (ej: "br", "co", "cl", "us")

    Returns:
        HttpResponseRedirect a /accounts/signup/?from=country_code

    Ejemplo:
        >>> signup_redirect(request, "br")
        # Redirige a: /accounts/signup/?from=br
    """
    # Normalizar código de país a minúsculas
    country_code_lower = country_code.lower()
    base = f"/accounts/signup/?from={country_code_lower}"
    # Preservar ?plan=, etc. para que los enlaces de bienvenida/onboarding funcionen
    if request.GET:
        base += "&" + request.GET.urlencode()
    return redirect(base)
