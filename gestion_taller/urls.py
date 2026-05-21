from django.views.i18n import JavaScriptCatalog
from django.urls import path, include, include

urlpatterns = [
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path("cl/es/", include(("taller.urls_extra.chile", "chile"), namespace="chile")),

    path("", include(("taller.urls", "taller"), namespace="taller")),

    path("cl/documentos/", include("taller.documentos.urls", namespace="cl_documentos")),
    path("us/documentos/", include("taller.documentos.urls", namespace="us_documentos")),
    path("uy/documentos/", include("taller.documentos.urls", namespace="uy_documentos")),
    path("ar/documentos/", include("taller.documentos.urls", namespace="ar_documentos")),
    path("cl/documentos/api/obtener-numero-documento/", include("taller.documentos.urls")),
    path("us/documentos/api/obtener-numero-documento/", include("taller.documentos.urls")),
]
