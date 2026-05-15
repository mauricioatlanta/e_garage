from django.shortcuts import redirect
from django.urls import reverse


class CountryAwareLogoutRedirectAdapter:
    """
    Adapter para redirigir el logout a la URL de login correcta según país.
    """

    def __call__(self, request):
        # PRIORIDAD 1: Detectar país desde usuario autenticado (empresa)
        if request.user.is_authenticated:
            try:
                # Buscar en empresa (prioridad más alta)
                if hasattr(request.user, "empresa") and hasattr(request.user.empresa, "pais"):
                    if request.user.empresa.pais == "US":
                        return redirect(reverse("usa:account_login"))
                    elif request.user.empresa.pais == "CL":
                        return redirect(reverse("chile:account_login"))
                    elif request.user.empresa.pais == "MX":
                        return redirect(reverse("mexico:account_login"))
                # Buscar en perfil
                elif hasattr(request.user, "perfil") and hasattr(request.user.perfil, "pais"):
                    if request.user.perfil.pais == "US":
                        return redirect(reverse("usa:account_login"))
                    elif request.user.perfil.pais == "CL":
                        return redirect(reverse("chile:account_login"))
                    elif request.user.perfil.pais == "MX":
                        return redirect(reverse("mexico:account_login"))
            except Exception:
                pass

        # PRIORIDAD 2: Detectar país por path actual
        path = request.path
        if path.startswith("/cl/") or "cl" in request.GET.get("country", ""):
            return redirect(reverse("chile:account_login"))
        if (
            path.startswith("/us")
            or path.startswith("/usa")
            or "us" in request.GET.get("country", "")
            or "usa" in request.GET.get("country", "")
        ):
            return redirect(reverse("usa:account_login"))
        if path.startswith("/mx") or "mx" in request.GET.get("country", ""):
            return redirect(reverse("mexico:account_login"))

        # PRIORIDAD 3: Detectar país por sesión
        country = request.session.get("country")
        if country == "us" or country == "usa":
            return redirect(reverse("usa:account_login"))
        elif country == "cl" or country == "chile":
            return redirect(reverse("chile:account_login"))
        elif country == "mx" or country == "mexico":
            return redirect(reverse("mexico:account_login"))

        # FALLBACK: Redirigir a Chile por defecto
        return redirect(reverse("chile:account_login"))
