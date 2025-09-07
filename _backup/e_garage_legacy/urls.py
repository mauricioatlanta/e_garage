from allauth.account import views as allauth_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog

import urls_signup
from taller.taller_main_urls import company_settings_view

# Landing principal y patrones por país (MIGRACIÓN COMPLETA)
urlpatterns = [
    path("admin/", admin.site.urls),
    # Página principal - selector de país
    path(
        "",
        TemplateView.as_view(template_name="selector-pais-egarage.html"),
        name="home",
    ),
    # NUEVOS PATRONES POR PAÍS (MIGRACIÓN COMPLETA)
    path("cl/", include("taller.urls_extra.chile")),  # Chile (español)
    path("us/", include("taller.urls_extra.usa")),  # USA (inglés)
    # REDIRECCIONES LEGACY /es/ → /cl/ y /en/ → /us/
    # Se manejan automáticamente en CountryURLRedirectMiddleware
    # APIs globales (sin prefijo de país)
    path("api/v1/", include("taller.api.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    # Configuración global para suscriptores (enlazamos la vista directamente)
    path("settings/", company_settings_view, name="company_settings"),
    # Auth global (Django auth + Allauth)
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/login/", allauth_views.LoginView.as_view(), name="account_login"),
    path("accounts/", include("allauth.urls")),
    path(
        "accounts/resend-email/",
        __import__(
            "taller.views_extra.resend_email", fromlist=["resend_email_view"]
        ).resend_email_view,
        name="resend_email",
    ),
    # Password reset específico
    path(
        "accounts/password/reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "accounts/password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    # Endpoints específicos
    path("ubicacion/", include("ubicacion.urls")),
    path("registro/", include("onboarding_urls")),
    path("signup/", include(urls_signup)),
    path("accounts/signup/", include(urls_signup)),  # Redirección para enlaces legacy
    # Selector de país (legacy)
    path(
        "selector-pais-egarage/",
        TemplateView.as_view(template_name="selector-pais-egarage.html"),
        name="selector_pais_egarage",
    ),
    # Página de historial de cambios
    path(
        "changelog/",
        TemplateView.as_view(template_name="changelog.html"),
        name="changelog",
    ),
    # Namespaces globales (acceso sin prefijo país)
    path(
        "documentos/",
        include(("taller.documentos.urls", "documentos"), namespace="documentos"),
    ),
    path(
        "servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios"),
    ),
]

# Static files en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    print(f"🔧 DEBUG Media Config:")
    print(f"   MEDIA_URL: {settings.MEDIA_URL}")
    print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"   Static config added for media files")
