from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog
from django.urls import path, include
from taller.views_extra.pwa import dynamic_service_worker, dynamic_manifest

urlpatterns = [
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('accounts/', include('allauth.urls')),
    # PWA: service worker y manifest dinámicos por país/idioma
    path("<str:pais>/<str:idioma>/service-worker.js", dynamic_service_worker, name="service_worker"),
    path("<str:pais>/<str:idioma>/manifest.json", dynamic_manifest, name="pwa_manifest"),
    path('', include('taller.urls_payment')),
    path("us/en/", include(("taller.urls", "taller"), namespace="us_en")),
    path("us/es/", include(("taller.urls", "taller"), namespace="us_es")),
    path("us/", include(("taller.urls_extra.usa", "usa"), namespace="usa")),

    path("cl/es/", include(("taller.urls_extra.chile", "chile"), namespace="chile")),

    path("", include(("taller.urls", "taller"), namespace="taller")),

    path("cl/admin/subcriptores/", include("taller.urls_admin_suscriptores")),
    path("cl/documentos/", include("taller.documentos.urls", namespace="cl_documentos")),
    path("us/documentos/", include("taller.documentos.urls", namespace="us_documentos")),
    path("uy/documentos/", include("taller.documentos.urls", namespace="uy_documentos")),
    path("ar/documentos/", include("taller.documentos.urls", namespace="ar_documentos")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
