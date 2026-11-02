"""
Vistas para generación y descarga de PDFs, y envío por WhatsApp
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST

from taller.models.documento import Documento
from taller.services.document_output_service import DocumentOutputService


def _get_documento_for_request(request, pk):
    queryset = Documento.objects.select_related("empresa", "cliente").prefetch_related(
        "lineas_repuesto__repuesto", "lineas_servicio", "lineas_otro_servicio"
    )
    if getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False):
        return get_object_or_404(queryset, pk=pk)

    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asociada.")
        return None

    return get_object_or_404(queryset, pk=pk, empresa=empresa)


@login_required
@require_GET
def descargar_pdf_documento(request, pk):
    """
    Genera y descarga el PDF de un documento.

    Args:
        pk: ID del documento

    Returns:
        HttpResponse con PDF o error
    """
    documento = _get_documento_for_request(request, pk)
    if documento is None:
        return redirect("documentos:lista_documentos")

    try:
        pdf_bytes, filename = DocumentOutputService.generate_pdf(documento, request)

        # Crear respuesta HTTP
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        # 'inline' para ver en navegador, 'attachment' para descargar directo
        disposition = request.GET.get("disposition", "inline")
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'

        messages.success(request, f"PDF generado exitosamente: {filename}")
        return response

    except ImportError as e:
        messages.error(
            request, f"WeasyPrint no está disponible. Contacta al administrador. Error: {str(e)}"
        )
        return redirect("documentos:ver_documento", pk=pk)
    except Exception as e:
        messages.error(request, f"Error al generar PDF: {str(e)}")
        return redirect("documentos:ver_documento", pk=pk)


@login_required
@require_GET
def generar_enlace_whatsapp(request, pk):
    """
    Genera un enlace de WhatsApp para enviar el documento al cliente.

    Args:
        pk: ID del documento

    Returns:
        JsonResponse con URL de WhatsApp o error
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse(
            {"success": False, "error": "Usuario sin empresa asociada."}, status=400
        )

    # Seguridad Multi-tenant
    documento = get_object_or_404(
        Documento.objects.select_related("empresa", "cliente"),
        pk=pk,
        empresa=empresa,  # 🔒 Multi-tenant
    )

    # Generar URL de PDF si está disponible
    pdf_url = None
    try:
        from django.urls import reverse

        pdf_url = request.build_absolute_uri(
            reverse("documentos:descargar_pdf", kwargs={"pk": documento.id})
        )
    except Exception:
        pass

    try:
        whatsapp_url = DocumentOutputService.generate_whatsapp_link(
            documento, request=request, pdf_url=pdf_url
        )

        if not whatsapp_url:
            return JsonResponse(
                {"success": False, "error": "El cliente no tiene número de teléfono registrado."},
                status=400,
            )

        return JsonResponse(
            {
                "success": True,
                "whatsapp_url": whatsapp_url,
                "message": "Enlace de WhatsApp generado exitosamente.",
            }
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Error al generar enlace de WhatsApp: {str(e)}"},
            status=500,
        )


@login_required
@require_POST
def enviar_por_whatsapp(request, pk):
    """
    Vista helper que redirige al enlace de WhatsApp.

    En el frontend, puedes usar un botón que haga POST a esta vista,
    y luego redirigir al usuario al enlace de WhatsApp.
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asociada.")
        return redirect("documentos:lista_documentos")

    # Seguridad Multi-tenant
    documento = get_object_or_404(
        Documento.objects.select_related("empresa", "cliente"),
        pk=pk,
        empresa=empresa,  # 🔒 Multi-tenant
    )

    # Generar URL de PDF
    pdf_url = None
    try:
        from django.urls import reverse

        pdf_url = request.build_absolute_uri(
            reverse("documentos:descargar_pdf", kwargs={"pk": documento.id})
        )
    except Exception:
        pass

    try:
        whatsapp_url = DocumentOutputService.generate_whatsapp_link(
            documento, request=request, pdf_url=pdf_url
        )

        if not whatsapp_url:
            messages.error(
                request,
                f"El cliente {documento.cliente.nombre} no tiene número de teléfono registrado.",
            )
            return redirect("documentos:ver_documento", pk=pk)

        # Redirigir al enlace de WhatsApp
        return redirect(whatsapp_url)

    except Exception as e:
        messages.error(request, f"Error al generar enlace de WhatsApp: {str(e)}")
        return redirect("documentos:ver_documento", pk=pk)
