"""Redirecciones limpias para URLs /compat/ que evitan el middleware de país/login.

/compat/settings/ no tiene prefijo de país, por lo que el middleware lo trata como
"zona protegida" y redirige a /cl/accounts/login/?next=/compat/settings/.

En vez de servir settings directamente en /compat/, redirigimos a la URL canónica
por país (Chile por defecto) para que el usuario llegue al destino correcto.
"""

from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "HEAD"])
def compat_settings_redirect(request):
    """Redirige /compat/settings/ a /cl/es/settings/#financial. Acepta GET y HEAD (health-checks)."""
    return HttpResponseRedirect("/cl/es/settings/#financial")
