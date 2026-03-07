from django.shortcuts import redirect
from django.urls import reverse


def logout_redirect_view(request):
    """
    Vista personalizada de logout que redirige al país correcto.
    Se ejecuta después de que allauth hace el logout.
    """
    # Obtener información del país antes del logout
    country = None

    # PRIORIDAD 1: Detectar país desde usuario autenticado (empresa)
    if request.user.is_authenticated:
        try:
            # Buscar en empresa (prioridad más alta)
            if hasattr(request.user, "empresa") and hasattr(request.user.empresa, "pais"):
                country = request.user.empresa.pais
            # Buscar en perfil
            elif hasattr(request.user, "perfil") and hasattr(request.user.perfil, "pais"):
                country = request.user.perfil.pais
        except Exception:
            pass

    # PRIORIDAD 2: Detectar país por path actual
    if not country:
        path = request.path
        if path.startswith("/cl/") or "cl" in request.GET.get("country", ""):
            country = "CL"
        elif (
            path.startswith("/us")
            or path.startswith("/usa")
            or "us" in request.GET.get("country", "")
            or "usa" in request.GET.get("country", "")
        ):
            country = "US"
        elif path.startswith("/mx") or "mx" in request.GET.get("country", ""):
            country = "MX"

    # PRIORIDAD 3: Detectar país por sesión
    if not country:
        session_country = request.session.get("country")
        if session_country == "us" or session_country == "usa":
            country = "US"
        elif session_country == "cl" or session_country == "chile":
            country = "CL"
        elif session_country == "mx" or session_country == "mexico":
            country = "MX"

    # Redirigir según el país detectado
    if country == "US":
        return redirect(reverse("usa:account_login"))
    elif country == "CL":
        return redirect(reverse("chile:account_login"))
    elif country == "MX":
        return redirect(reverse("mexico:account_login"))
    else:
        # FALLBACK: Redirigir a Chile por defecto
        return redirect(reverse("chile:account_login"))
