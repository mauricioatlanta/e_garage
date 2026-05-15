# taller/documentos/urls_ejemplo.py
from django.urls import path

from . import views_ejemplo

app_name = "documentos"

urlpatterns = [
    # Vistas principales
    path("crear/", views_ejemplo.documento_crear, name="crear"),
    path("<int:pk>/editar/", views_ejemplo.documento_editar, name="editar"),
    # Vistas PDF
    path("<int:pk>/pdf/", views_ejemplo.documento_ver_pdf, name="ver_pdf"),
    path("<int:pk>/pdf-html/", views_ejemplo.documento_pdf_html, name="pdf_html"),
    path(
        "<int:pk>/pdf-weasyprint/",
        views_ejemplo.documento_pdf_weasyprint,
        name="pdf_weasyprint",
    ),
    path(
        "<int:pk>/pdf-wkhtmltopdf/",
        views_ejemplo.documento_pdf_wkhtmltopdf,
        name="pdf_wkhtmltopdf",
    ),
]
