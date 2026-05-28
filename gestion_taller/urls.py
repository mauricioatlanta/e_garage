from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog
from django.urls import path, include
from django.shortcuts import redirect
from taller.views_extra.pwa import dynamic_service_worker, dynamic_manifest
from taller.views_extra.lang_switch import set_language_us

urlpatterns = [
    path("lang/set/", set_language_us, name="set_language_us"),
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
    path("ar/es/", include(("taller.urls_extra.argentina", "argentina"), namespace="argentina")),
    path("uy/es/", include(("taller.urls_extra.uruguay", "uruguay"), namespace="uruguay")),
    path("mx/es/", include("taller.urls_extra.mexico", namespace="mexico")),
    path("pe/es/", include("taller.urls_extra.peru", namespace="peru")),
    path("br/", include("taller.urls_extra.brasil", namespace="brasil")),
    path("ve/es/", include("taller.urls_extra.venezuela", namespace="venezuela")),
    path("co/es/", include("taller.urls_extra.colombia", namespace="colombia")),
    path("ec/es/", include("taller.urls_extra.ecuador", namespace="ecuador")),

    # Catch-all: /xx/<path> → /xx/es/<path> para países sin prefijo de idioma en URLs cortas
    path("ar/<path:rest>", lambda r, rest: redirect(f"/ar/es/{rest}")),
    path("uy/<path:rest>", lambda r, rest: redirect(f"/uy/es/{rest}")),
    path("mx/<path:rest>", lambda r, rest: redirect(f"/mx/es/{rest}")),
    path("pe/<path:rest>", lambda r, rest: redirect(f"/pe/es/{rest}")),
    path("ve/<path:rest>", lambda r, rest: redirect(f"/ve/es/{rest}")),
    path("co/<path:rest>", lambda r, rest: redirect(f"/co/es/{rest}")),
    path("ec/<path:rest>", lambda r, rest: redirect(f"/ec/es/{rest}")),

    path("", include(("taller.urls", "taller"), namespace="taller")),

    path("cl/admin/subcriptores/", include("taller.urls_admin_suscriptores")),
    path("cl/documentos/", include("taller.documentos.urls", namespace="cl_documentos")),
    path("us/documentos/", include("taller.documentos.urls", namespace="us_documentos")),
    path("uy/documentos/", include("taller.documentos.urls", namespace="uy_documentos")),
    path("ar/documentos/", include("taller.documentos.urls", namespace="ar_documentos")),
    path("mx/documentos/", include("taller.documentos.urls", namespace="mx_documentos")),
    path("pe/documentos/", include("taller.documentos.urls", namespace="pe_documentos")),
    path("br/documentos/", include("taller.documentos.urls", namespace="br_documentos")),
    path("ve/documentos/", include("taller.documentos.urls", namespace="ve_documentos")),
    path("co/documentos/", include("taller.documentos.urls", namespace="co_documentos")),
    path("ec/documentos/", include("taller.documentos.urls", namespace="ec_documentos")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
