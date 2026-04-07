from django.shortcuts import redirect
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie

from taller.views.country_aware_auth import country_aware_login

app_name = "usa"


def _canonical_usa_path(legacy_path: str = "", default_lang: str = "en") -> str:
    legacy_path = (legacy_path or "").strip("/")
    lang = default_lang

    if legacy_path.startswith("es/"):
        lang = "es"
        legacy_path = legacy_path[3:]
    elif legacy_path.startswith("en/"):
        lang = "en"
        legacy_path = legacy_path[3:]

    aliases = {
        "": "",
        "login": "accounts/login",
        "accounts/login": "accounts/login",
        "signup": "accounts/signup",
        "accounts/signup": "accounts/signup",
        "dashboard": "dashboard",
        "workspace": "workspace",
        "pricing": "pricing",
        "plans": "pricing",
        "settings": "settings",
        "configuracion": "settings",
        "configuracion/empresa": "settings",
        "centro-operaciones": "centro-operaciones",
        "centro-operaciones-espacial": "centro-operaciones-espacial",
    }
    legacy_path = aliases.get(legacy_path, legacy_path)

    base = f"/us/{lang}/"
    return base if not legacy_path else f"{base}{legacy_path}/"


def usa_legacy_redirect(request, legacy_path: str = "", lang: str = "en"):
    return redirect(_canonical_usa_path(legacy_path, default_lang=lang))


@ensure_csrf_cookie
def usa_login_view(request):
    request.country = "US"
    request.country_code = "US"
    return country_aware_login(request)


def usa_signup_view(request):
    from django.utils.translation import activate

    from taller.views_extra.custom_signup import CustomSignupView

    request.country = "US"
    request.country_code = "US"
    request.eg_us_public_signup_lang = "en"
    activate("en")
    request.session["django_language"] = "en"
    request.session.modified = True
    return CustomSignupView.as_view(template_name="taller/us/en/auth/signup.html")(request)


def usa_signup_view_es(request):
    from django.utils.translation import activate

    from taller.views_extra.custom_signup import CustomSignupView

    request.country = "US"
    request.country_code = "US"
    request.eg_us_public_signup_lang = "es"
    activate("es")
    request.session["django_language"] = "es"
    request.session.modified = True
    return CustomSignupView.as_view(template_name="taller/us/es/auth/signup.html")(request)


urlpatterns = [
    path("", usa_legacy_redirect, name="home"),
    path(
        "accounts/login/",
        usa_legacy_redirect,
        {"legacy_path": "accounts/login"},
        name="account_login",
    ),
    path("signup/", usa_legacy_redirect, {"legacy_path": "accounts/signup"}, name="account_signup"),
    path("dashboard/", usa_legacy_redirect, {"legacy_path": "dashboard"}, name="dashboard"),
    path("workspace/", usa_legacy_redirect, {"legacy_path": "workspace"}, name="centro_trabajo"),
    path("pricing/", usa_legacy_redirect, {"legacy_path": "pricing"}, name="pricing"),
    path("plans/", usa_legacy_redirect, {"legacy_path": "pricing"}, name="plans"),
    path("settings/", usa_legacy_redirect, {"legacy_path": "settings"}, name="company_settings"),
    path("configuracion/", usa_legacy_redirect, {"legacy_path": "settings"}, name="configuracion"),
    path(
        "configuracion/empresa/",
        usa_legacy_redirect,
        {"legacy_path": "settings"},
        name="configuracion_empresa",
    ),
    path("<path:legacy_path>", usa_legacy_redirect, name="legacy_redirect"),
]
