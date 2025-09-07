from django.shortcuts import redirect
from django.urls import reverse


class CountryAwareLogoutRedirectAdapter:
    """
    Adapter para redirigir el logout a la URL de login correcta según país.
    """

    def __call__(self, request):
        path = request.path
        # Detectar país por path
        if path.startswith("/cl/") or "cl" in request.GET.get("country", ""):
            return redirect(reverse("chile:account_login"))
        if (
            path.startswith("/us")
            or path.startswith("/usa")
            or "us" in request.GET.get("country", "")
            or "usa" in request.GET.get("country", "")
        ):
            return redirect(reverse("usa:account_login"))
        country = request.session.get("country")
        if country == "usa":
            return redirect(reverse("usa:account_login"))
        return redirect(reverse("chile:account_login"))
