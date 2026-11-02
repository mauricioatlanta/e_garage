from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse


def post_activation_login_redirect(request):
    path = (request.path_info or request.path or "").lower()

    if path.startswith("/us/"):
        ns = "usa"
    elif path.startswith("/cl/"):
        ns = "chile"
    else:
        ns = None

    # Si viene con /us/ o /cl/, intentamos ese login sí o sí.
    if ns:
        try:
            return redirect(reverse(f"{ns}:account_login"))
        except NoReverseMatch:
            # Fallback explícito (nunca reverse("account_login") sin namespace)
            return redirect(reverse("chile:account_login"))

    # Si no se pudo inferir país por la URL, fallback explícito.
    return redirect(reverse("chile:account_login"))
