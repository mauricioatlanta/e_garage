from django.urls import path

from . import views_public

app_name = "reciclaje"

urlpatterns = [
    path("consulta-catalitico/", views_public.consulta_catalitico, name="consulta_catalitico"),
    path("catalitico/<int:pk>/", views_public.detalle_catalitico, name="detalle_catalitico"),
    path("chatarra/", views_public.catalogo_chatarra, name="catalogo_chatarra"),
    path(
        "api/consulta-sugerencias/",
        views_public.api_consulta_sugerencias,
        name="api_consulta_sugerencias",
    ),
]
