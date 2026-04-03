from importlib.util import find_spec


def _has_ops_urls() -> bool:
    try:
        return find_spec("taller.ops.urls") is not None
    except ModuleNotFoundError:
        return False


from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import RedirectView, TemplateView

from taller import ajax_views
from taller.views_extra.views import dashboard_suscripciones
from taller.views_extra.bienvenida_usa import bienvenida_usa
from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.dashboard_empresa import (
    dashboard_centro_operaciones,
)
from taller.views_extra.centro_trabajo import (
    centro_trabajo,
    centro_trabajo_buscar,
    vehiculo_historial,
)
from taller.views_extra.futuristic_company_settings_views import (
    futuristic_company_settings_view,
)
from taller.views_extra.views import dashboard
from taller.views_extra.views_configuracion import configuracion_tecnicos
from taller.views_extra.views_suscripciones import precios
from taller.views_extra.views_trial_activate import activar_trial
from taller.documentos import views_country_aware as views_documentos

# from taller.views_extra.crear_motor_caja import crear_motor, crear_caja, crear_color  # ❌ Desactivado - usando views_create_parts

app_name = "usa"


class USAComposeLoginView:
    """
    LoginView que SIEMPRE muestra el formulario de login, nunca redirige.
    Usa allauth internamente pero evita el redirect de usuarios autenticados.
    """

    def __init__(self, template_name, success_url):
        self.template_name = template_name
        self.success_url = success_url

    def __call__(self, request):
        from allauth.account.views import LoginView
        from django.utils.decorators import method_decorator

        # Vista que hereda de LoginView pero sin redirigir usuarios autenticados
        class _USALoginView(LoginView):
            template_name = self.template_name
            success_url = self.success_url

            def dispatch(self, request, *args, **kwargs):
                # NUNCA redirigir: siempre mostrar el formulario de login
                from django.views.generic.base import View

                if request.method.lower() in self.http_method_names:
                    handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
                else:
                    handler = self.http_method_not_allowed
                return handler(request, *args, **kwargs)

        return _USALoginView.as_view()(request)


def _add_no_cache_headers(response):
    """Evita caché en la página de login para que CSRF cookie y token coincidan."""
    if response is not None:
        response["Cache-Control"] = "no-store, no-cache, max-age=0, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
    return response


def _usa_login_form(request):
    """Form para el template: siempre devuelve un form con login y password (allauth)."""
    from allauth.account.forms import LoginForm

    if request.method == "POST":
        return LoginForm(request=request, data=request.POST)
    return LoginForm(request=request)


@ensure_csrf_cookie
def usa_login_view(request):
    """
    Login USA: /us/login/
    NO depende de /accounts/login/ (hoy devuelve 403).
    Acepta username o email en el campo 'login'.
    """
    from django.contrib.auth import authenticate, login as dj_login, get_user_model
    from django.shortcuts import redirect, render
    from django.urls import reverse

    # Forzar contexto USA (tu middleware usa esto)
    request.country = "US"
    request.country_code = "US"

    lang = getattr(request, "LANGUAGE_CODE", "en")
    if lang not in ("en", "es"):
        lang = "en"

    template_name = f"us/{lang}/account/login.html"
    # Canonical workspace para USA: /us/en/workspace/ (evita loop; usa:centro_trabajo → /us/workspace/ redirige)
    success_url = reverse("us_en:centro_trabajo")

    if request.method == "POST":
        login_value = (request.POST.get("login") or "").strip()
        password = request.POST.get("password") or ""

        User = get_user_model()
        user = None

        # DEBUG vars
        found_by = "none"
        found_id = ""
        pwd_ok = "0"
        active_ok = "0"

        # 1) Intenta authenticate normal (username)
        user = authenticate(request, username=login_value, password=password)

        # 2) Fallback manual: buscar por email o username y validar password
        if user is None:
            if "@" in login_value:
                u = User.objects.filter(email__iexact=login_value).first()
                found_by = "email"
            else:
                u = User.objects.filter(username__iexact=login_value).first()
                found_by = "username"

            if u:
                found_id = str(u.pk)
                pwd_ok = "1" if u.check_password(password) else "0"
                active_ok = "1" if getattr(u, "is_active", False) else "0"

                if pwd_ok == "1" and active_ok == "1":
                    # Re-autenticar usando username real
                    user = authenticate(request, username=u.get_username(), password=password)

        # Si aún no hay user, devolvemos response con headers debug (form para que se vean los campos)
        if user is None:
            resp = render(
                request,
                template_name,
                {
                    "form": _usa_login_form(request),
                    "error": "Credenciales inválidas",
                    "country": "US",
                },
            )
            resp["Cache-Control"] = "no-store, no-cache, max-age=0, must-revalidate"
            resp["Pragma"] = "no-cache"
            resp["Expires"] = "0"
            resp["X-USA-LOGIN-VIEW"] = "1"
            resp["X-FOUND-BY"] = found_by
            resp["X-FOUND-ID"] = found_id
            resp["X-PWD-OK"] = pwd_ok
            resp["X-ACTIVE-OK"] = active_ok
            return resp

        # Login OK
        dj_login(request, user)

        # No arrastrar flashes viejos (ni duplicar “signed in”) al workspace
        from django.contrib.messages import get_messages

        list(get_messages(request))

        from django.utils.http import url_has_allowed_host_and_scheme

        next_url = (request.POST.get("next") or request.GET.get("next") or "").strip()
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            success = next_url
        else:
            success = success_url

        resp = redirect(success)
        resp["X-USA-LOGIN-VIEW"] = "1"
        resp["X-FOUND-BY"] = found_by
        resp["X-FOUND-ID"] = found_id
        resp["X-PWD-OK"] = pwd_ok
        resp["X-ACTIVE-OK"] = active_ok
        return resp

    resp = render(
        request,
        template_name,
        {"form": _usa_login_form(request), "country": "US"},
        status=200,
    )
    # Evitar cache: página de login no debe cachearse (token CSRF debe ser siempre fresco)
    resp["Cache-Control"] = "no-store, no-cache, max-age=0, must-revalidate"
    resp["Pragma"] = "no-cache"
    resp["Expires"] = "0"
    resp["X-USA-LOGIN-VIEW"] = "BYPASS-V2"
    resp["X-REQ-METHOD"] = request.method
    resp["X-POST-HAS-LOGIN"] = "1" if "login" in request.POST else "0"
    resp["X-POST-HAS-PASSWORD"] = "1" if "password" in request.POST else "0"
    resp["X-LOGIN-LEN"] = str(len((request.POST.get("login") or "").strip()))
    resp["X-LOGIN-RAW"] = (request.POST.get("login") or "").strip()[:40]  # 40 chars max
    return resp


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
    # 1) Home y páginas específicas USA
    path("", bienvenida_usa, name="home"),
    # Página de bienvenida USA ES (misma vista; idioma por sesión/URL)
    path(
        "es/bienvenida/",
        bienvenida_usa,
        name="bienvenida_usa_es",
    ),
    # Página de bienvenida USA EN (misma vista; idioma por sesión/URL)
    path(
        "en/bienvenida/",
        bienvenida_usa,
        name="bienvenida_usa_en",
    ),
    # Centro de Trabajo / Recepción Vehicular (nueva home post-login)
    path("workspace/", centro_trabajo, name="centro_trabajo"),
    path("workspace/buscar/", centro_trabajo_buscar, name="centro_trabajo_buscar"),
    path("vehiculos/<int:vehiculo_id>/historial/", vehiculo_historial, name="vehiculo_historial"),
    path("dashboard/", dashboard, name="dashboard"),  # si existe en taller, este gana por orden
    path("en/dashboard/", dashboard, name="dashboard_en_redirect"),
    path("es/dashboard/", dashboard, name="dashboard_es_redirect"),
    # Centro de operaciones real (dashboard con KPIs; destino post-login)
    path(
        "centro-operaciones/",
        dashboard_centro_operaciones,
        name="centro_operaciones",
    ),
    path(
        "centro-operaciones-espacial/",
        dashboard_centro_operaciones,
        name="centro_operaciones_espacial",
    ),
    path(
        "es/centro-operaciones/",
        dashboard_centro_operaciones,
        name="centro_operaciones_es",
    ),
    path(
        "es/centro-operaciones-espacial/",
        dashboard_centro_operaciones,
        name="centro_operaciones_espacial_es",
    ),
    path("admin/dashboard/", dashboard_suscripciones, name="dashboard_suscripciones"),
    # 2) Configuración — /us/configuracion/ redirige a Settings Center (evita 403)
    path(
        "configuracion/",
        RedirectView.as_view(url="/us/settings/", permanent=False),
        name="configuracion",
    ),
    # Legacy configuracion/empresa/ → redirige a settings (evita 403 de la vista antigua)
    path(
        "configuracion/empresa/",
        RedirectView.as_view(pattern_name="usa:company_settings", permanent=False),
        name="configuracion_empresa",
    ),
    path(
        "en/configuracion/empresa/",
        RedirectView.as_view(pattern_name="us_en:company_settings", permanent=False),
        name="configuracion_empresa_en",
    ),
    path(
        "es/configuracion/empresa/",
        RedirectView.as_view(pattern_name="us_es:company_settings", permanent=False),
        name="configuracion_empresa_es",
    ),
    path("configuracion/tecnicos/", configuracion_tecnicos, name="configuracion_tecnicos"),
    path("settings/", company_settings_view, name="company_settings"),
    path(
        "en/settings/",
        company_settings_view,  # Usar la misma vista que /us/settings/
        name="futuristic_company_settings",
    ),
    # 3) Auth Allauth para USA
    path("accounts/login/", usa_login_view, name="account_login"),
    path("signup/", usa_signup_view, name="account_signup"),
    path("es/signup/", usa_signup_view_es, name="account_signup_es"),
    # 4) Trial y onboarding
    path("activar-trial/", activar_trial, name="activar_trial"),
    path(
        "registro/",
        include(("scripts.onboarding_urls", "onboarding"), namespace="usa_onboarding"),
    ),
    # 4.5) Pricing and subscription
    path("pricing/", precios, name="pricing"),
    path("plans/", precios, name="plans"),
    # 5) AJAX específicos USA
    path("ajax/load-modelos/", ajax_views.load_modelos, name="ajax_load_modelos"),
    path("ajax/load-motores/", ajax_views.load_motores, name="ajax_load_motores"),
    path("ajax/load-cajas/", ajax_views.load_cajas, name="ajax_load_cajas"),
    path(
        "ajax/load-motores-cajas/",
        ajax_views.load_motores_cajas,
        name="ajax_load_motores_cajas",
    ),
    # AJAX endpoints compartidos (clientes, vehículos, marcas, modelos, etc.)
    path("ajax/", include(("taller.ajax.urls", "ajax"), namespace="ajax")),
    # 6) APIs
    path("api/", include(("taller.api.urls", "api"), namespace="api")),
    # 6.1) Autocomplete y creadores rápidos (verifica que no se dupliquen en taller.urls)
    path(
        "autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    ),
    # Centro de Ingreso Pro (kiosk recepción) — solo si existe el módulo taller.ops
    # path("ops/", include(("taller.ops.urls", "ops"), namespace="ops")),
    # path("vehiculos/crear-motor/", crear_motor, name="crear_motor"),  # ❌ Desactivado - usar vehiculos:crear_motor
    # path("vehiculos/crear-caja/", crear_caja, name="crear_caja"),    # ❌ Desactivado - usar vehiculos:crear_caja
    # path("vehiculos/crear-color/", crear_color, name="crear_color"), # ❌ Desactivado - usar vehiculos:crear_color
    # 6) Módulos principales del sistema (antes de taller.urls)
    path(
        "clientes/",
        include(("taller.clientes.urls", "clientes"), namespace="clientes"),
    ),
    path(
        "vehiculos/",
        include(("taller.vehiculos.urls", "vehiculos"), namespace="vehiculos"),
    ),
    path(
        "documentos/",
        include(("taller.documentos.urls", "documentos"), namespace="documentos"),
    ),
    # =========================
    # Documentos USA EN (vistas genéricas country-aware)
    # =========================
    # Lista de documentos USA EN
    path(
        "en/documentos/",
        views_documentos.documentos_listar,
        {"country_code": "us", "lang_code": "en"},
        name="lista_documentos_us",
    ),
    # Crear documento USA EN
    path(
        "en/documentos/new/",
        views_documentos.documento_crear,
        {"country_code": "us", "lang_code": "en"},
        name="crear_documento_us",
    ),
    # Ver documento USA EN
    path(
        "en/documentos/<int:pk>/",
        views_documentos.documento_ver,
        {"country_code": "us", "lang_code": "en"},
        name="ver_documento_us",
    ),
    # Editar documento USA EN
    path(
        "en/documentos/<int:pk>/edit/",
        views_documentos.documento_editar,
        {"country_code": "us", "lang_code": "en"},
        name="editar_documento_us",
    ),
    path(
        "repuestos/",
        include(("taller.repuestos.urls", "repuestos"), namespace="repuestos"),
    ),
    path(
        "servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios"),
    ),
    path(
        "reportes/",
        include(("taller.reportes.urls", "reportes"), namespace="reportes"),
    ),
    path(
        "tecnicos/",
        include(("taller.tecnicos.urls", "tecnicos"), namespace="tecnicos"),
    ),
    # 7) Analytics (antes de taller si sus rutas son más específicas)
    path("", include("taller.analytics.urls_suscriptor")),
    # 8) Núcleo de taller (último para que no opaque lo anterior)
    path("", include(("taller.urls", "taller"), namespace="taller")),
]
if _has_ops_urls():
    urlpatterns += [
        path("ops/", include(("taller.ops.urls", "ops"), namespace="ops")),
    ]
